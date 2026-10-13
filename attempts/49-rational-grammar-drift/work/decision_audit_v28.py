"""All old heads/budgets; new classical lowers and immutable old core costs."""

import argparse
import json
import os
import resource
import subprocess
from fractions import Fraction as F
from pathlib import Path

import numpy as np

from . import public_audit as old
from .audit_external import CTX, clock, deadline, elapsed, failure
from .public_controls import digest
from .tight_control_v28 import controls

WORK = Path(__file__).resolve().parent
GRID = [F(1, 10**j) for j in range(1, 9)]
FORMATS = ["binary32", "binary16", "bfloat16"]


def rational(value):
    if isinstance(value, dict):
        return {k: rational(v) for k, v in value.items()}
    if isinstance(value, str):
        try:
            return F(value)
        except ValueError:
            return value
    return value


def decision(interval, tau):
    if interval is None:
        return "UNRESOLVED"
    lo, hi = interval
    return "ACCEPT" if hi <= tau else "REJECT" if lo > tau else "UNRESOLVED"


def report(frame, kind, historic, bound, costs):
    primary = next(
        r for r in historic if r["engine"] == "ordered_planar" and r["epsilon"] == "1/10"
    )
    base = (
        None
        if bound.get("status") != "CERTIFIED_CLASSICAL_INTERVAL"
        else (bound["lower"], bound["upper"])
    )
    out = dict(
        source_case=frame["case"],
        mask_count=frame["mask_count"],
        format=kind,
        status=bound["status"],
        classical=bound,
        new_costs_wall_cpu=costs,
        historical_intervals=[
            {k: r[k] for k in ["engine", "epsilon", "status"]}
            | {k: r[k] for k in ["lower", "upper", "reason"] if k in r}
            for r in historic
        ],
        historical_costs_wall_cpu=primary["costs_wall_cpu"],
    )
    combined = base
    if base is not None and primary["status"] == "CERTIFIED_ON_ADMITTED_FOREST":
        combined = max(base[0], F(primary["lower"])), min(base[1], F(primary["upper"]))
        assert combined[0] <= combined[1]
    out["combined_interval"] = combined
    out["extra_accept_budgets"] = [combined[1], base[1]] if base and combined[1] < base[1] else None
    out["extra_reject_budgets"] = [base[0], combined[0]] if base and combined[0] > base[0] else None
    out["grid"] = [
        dict(tau=t, classical=decision(base, t), combined=decision(combined, t)) for t in GRID
    ]
    if base is not None:
        baseline = primary["costs_wall_cpu"]
        historic_base = [
            sum(v[i] for k, v in baseline.items() if k != "core_with_process_management")
            for i in [0, 1]
        ]
        extra = costs["classical_lower_and_range"]
        out["mixed_source_classical_accounting_wall_cpu"] = [
            historic_base[i] + extra[i] for i in [0, 1]
        ]
        core = baseline.get("core_with_process_management", [0, 0])
        out["mixed_source_combined_accounting_wall_cpu"] = [
            historic_base[i] + extra[i] + core[i] for i in [0, 1]
        ]
    return out


def worker(source, frame, historic, target):
    os.setsid()
    resource.setrlimit(resource.RLIMIT_AS, (3 << 30, 3 << 30))
    costs, shared, left = {}, None, None
    try:
        start = clock()
        with deadline(150):
            path = source / f"{frame['case']}-{frame['mask_count']}.npy"
            assert digest(path) == frame["probabilities_sha256"]
            matrix = np.load(path, allow_pickle=False)
            adapter = old.CompositionalByteLevelAdapter.from_token_pieces(
                json.loads((source / "vocabulary.json").read_text())
            )
            canvas = tuple(frame["canvas"])
            support = old.build_per_position_support(
                canvas=canvas,
                policy=old.SupportPolicy(old.SupportKind.FULL, adapter.vocabulary_size),
                explicit_support={
                    p: tuple(range(adapter.vocabulary_size)) if t is None else (t,)
                    for p, t in enumerate(canvas)
                },
            )
            state = old.SelectionInput(
                old.normalize_to_cnf(old.json_source_grammar()).grammar,
                canvas,
                (),
                support,
                adapter,
                old.EOSPolicy(old.EOSMode.ABSENT),
            )

            def inputs(table):
                rows = dict(zip(frame["positions"], table, strict=True))
                return old.inputs(state, [rows.get(p, ()) for p in range(len(canvas))])[0]

            first = inputs(matrix)
            costs["replay_input"] = elapsed(start)
            start = clock()
            plan = old.bridge(old.prepare(adapter, canvas), state)
            costs["replay_preparation"] = elapsed(start)
            start = clock()
            left = plan.evaluate(first)
            assert all(
                F(r["first_valid_mass"]) == left.valid_mass
                for r in historic
                if "first_valid_mass" in r
            )
            costs["replay_original_posterior"] = elapsed(start)
    except Exception as exc:
        shared = failure(exc)
        costs["failed_stage"] = elapsed(start)
    with target.open("x") as stream:
        for kind in FORMATS:
            selected = [r for r in historic if r["format"] == kind]
            local = dict(costs)
            result = shared
            if result is None:
                try:
                    with deadline(150):
                        start = clock()
                        second = inputs(old.rounded(matrix, kind))
                        right = plan.evaluate(second)
                        local["replay_second_input_and_posterior"] = elapsed(start)
                        baseline = rational(
                            next(r["controls"] for r in selected if r["controls"] is not None)
                        )
                        start = clock()
                        result = controls(plan, first, second, (left, right), baseline)
                        local["classical_lower_and_range"] = elapsed(start)
                except Exception as exc:
                    result = failure(exc)
                    local["failed_stage"] = elapsed(start)
            stream.write(
                json.dumps(report(frame, kind, selected, result, local), default=str) + "\n"
            )
            stream.flush()


def run(source, output):
    output.mkdir(parents=True, exist_ok=False)
    archived = WORK / "evidence/external-v26/rows.jsonl"
    historic = [json.loads(line) for line in archived.read_text().splitlines()]
    frames = (
        sorted(source.glob("*-4.json"))
        + sorted(source.glob("*-8.json"))
        + sorted(source.glob("*-16.json"))
    )
    assert len(frames) == 15 and len(historic) == 360
    metadata = dict(
        producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        status="DEVELOPMENT_DECISIONS_ONLY",
        new_forwards=0,
        new_core_evaluations=0,
        historical_producer="8216ee0e4add006aed763814ff8d1e99ba9c439c",
        archived_rows_sha256=digest(archived),
        protocol_sha256=digest(WORK / "consolidation-v28.md"),
        grid=list(map(str, GRID)),
        files={
            p.name: digest(p)
            for p in [Path(__file__), WORK / "tight_control_v28.py", WORK / "two_sided_controls.py"]
        },
        interpretation=(
            "All budgets/old heads; mixed-source accounting is not a new timing "
            "measurement or independent confirmation"
        ),
    )
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    rows = []
    for i, path in enumerate(frames):
        frame = json.loads(path.read_text())
        previous = [
            r
            for r in historic
            if r["source_case"] == frame["case"] and r["mask_count"] == frame["mask_count"]
        ]
        assert len(previous) == 24
        target = output / (path.stem + ".jsonl")
        if all(r["controls"] is None for r in previous):
            with target.open("x") as stream:
                for kind in FORMATS:
                    selected = [r for r in previous if r["format"] == kind]
                    result = dict(
                        status="HISTORICAL_SHARED_REFUSAL", reason=selected[0].get("reason")
                    )
                    stream.write(
                        json.dumps(report(frame, kind, selected, result, {}), default=str) + "\n"
                    )
        else:
            process = CTX.Process(target=worker, args=(source, frame, previous, target))
            process.start()
            process.join(620)
            if process.is_alive():
                process.kill()
                process.join()
            assert process.exitcode == 0, (
                f"State worker failed: {path.name} exit={process.exitcode}"
            )
        current = [json.loads(line) for line in target.read_text().splitlines()]
        assert len(current) == 3
        rows.extend(current)
        print(
            json.dumps(dict(state=i + 1, total=15, statuses=[r["status"] for r in current])),
            flush=True,
        )
    assert len(rows) == 45
    (output / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    policies = []
    for frame_path in frames:
        frame = json.loads(frame_path.read_text())
        selected = [
            r
            for r in rows
            if r["source_case"] == frame["case"] and r["mask_count"] == frame["mask_count"]
        ]
        for j, tau in enumerate(GRID):
            entry = dict(source_case=frame["case"], mask_count=frame["mask_count"], tau=str(tau))
            for method in ["classical", "combined"]:
                accepted = [r["format"] for r in selected if r["grid"][j][method] == "ACCEPT"]
                bits = min([32 if f == "binary32" else 16 for f in accepted], default=64)
                entry[method] = dict(word_bits=bits, accepted_formats=accepted)
            policies.append(entry)
    summary = dict(
        status="DEVELOPMENT_DECISIONS_ONLY",
        pairs=45,
        policy_comparisons=len(policies),
        certified_classical=sum(r["status"] == "CERTIFIED_CLASSICAL_INTERVAL" for r in rows),
        extra_accept_regions=sum(r["extra_accept_budgets"] is not None for r in rows),
        extra_reject_regions=sum(r["extra_reject_budgets"] is not None for r in rows),
        grid_extra_accepts=sum(
            g["classical"] == "UNRESOLVED" and g["combined"] == "ACCEPT"
            for r in rows
            for g in r["grid"]
        ),
        grid_extra_rejects=sum(
            g["classical"] == "UNRESOLVED" and g["combined"] == "REJECT"
            for r in rows
            for g in r["grid"]
        ),
        narrower_word_policies=sum(
            p["combined"]["word_bits"] < p["classical"]["word_bits"] for p in policies
        ),
        new_forwards=0,
        independent_confirmation=False,
        actual_memory_saving_measured=False,
    )
    (output / "policy.json").write_text(json.dumps(policies, indent=2) + "\n")
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)
