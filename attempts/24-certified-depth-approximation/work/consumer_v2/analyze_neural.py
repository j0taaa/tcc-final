"""Audit every pilot trajectory and the frozen full-cost paired decision."""

import argparse
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from statistics import median

import numpy as np

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .benchmark import digest


def analyze(directory, original):
    meta = json.loads((directory / "metadata.json").read_text())
    protocol, capture = meta["protocol"], meta["input_capture"]
    if digest(original / "metadata.json") != meta["input_capture_sha256"]:
        raise ValueError("initial input capture changed")
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        json.loads((original / "vocabulary.json").read_text())
    )
    rows = [json.loads(s) for s in (directory / "rows.jsonl").read_text().splitlines()]
    keys = {
        (c["key"], masks, seed, method)
        for c in capture["selected"]
        for masks in (4, 8, 16)
        for seed in protocol["seeds"]
        for method in protocol["methods"]
    }
    index, errors, heads = {}, [], {}
    first_heads, exact_masses, approximate = defaultdict(set), {}, []
    matches, mass_checks, fixed_checks, head_checks = 0, 0, 0, 0
    for row in rows:
        key = row["case"], row["masks"], row["seed"], row["method"]
        if key not in keys or key in index:
            raise ValueError("unknown or duplicate pilot record")
        index[key] = row
        initial = json.loads((original / f"{row['case']}-{row['masks']}.json").read_text())
        canvas, delta = list(initial["canvas"]), Fraction()
        if row["new_forwards"] != len(row["steps"]):
            errors.append([key, "forward/step mismatch"])
        for step, record in enumerate(row["steps"]):
            positions = [p for p, t in enumerate(canvas) if t is None]
            if record["step"] != step or record["input_canvas"] != canvas:
                errors.append([key, "divergent original canvas", step])
            if record["positions"] != positions:
                errors.append([key, "divergent original positions", step])
            path = directory / "heads" / record["head_name"]
            sha = digest(path)
            if sha != record["head_sha256"]:
                errors.append([key, "changed head", step])
            if sha not in heads:
                head = np.load(path, allow_pickle=False)
                if (
                    head.dtype != np.float64
                    or head.shape != (len(positions), adapter.vocabulary_size)
                    or not np.isfinite(head).all()
                    or (head < 0).any()
                    or head[:, capture["config"]["mask_token_id"]].any()
                    or not (head.sum(axis=1) > 0).all()
                ):
                    errors.append([key, "invalid full represented head", step])
                heads[sha] = dict(bytes=path.stat().st_size, representative=path.name)
            head_checks += 1
            if step == 0:
                first_heads[row["case"], row["masks"]].add(sha)
            response = record["response"]
            if response["status"] != "complete":
                if step != len(row["steps"]) - 1 or row["status"] == "complete":
                    errors.append([key, "progress after refusal", step])
                continue
            word, commits = response["sample"], response["committed"]
            if len(word) != len(canvas) or any(
                t is not None and t != word[p] for p, t in enumerate(canvas)
            ):
                errors.append([key, "sample changed fixed IDs", step])
            json.loads(adapter.detokenize_bytes(word).decode("utf8"), parse_constant=reject)
            fixed_checks += 1
            if (
                not commits
                or len(set(commits)) != len(commits)
                or any(p not in positions for p in commits)
            ):
                errors.append([key, "invalid progress", step])
            delta += Fraction(response["certificate"]["delta"])
            if (
                Fraction(response["certificate"]["delta"])
                > Fraction(protocol["trajectory_total_tv"]) / row["masks"]
            ):
                errors.append([key, "local certificate exceeds allocation", step])
            mass = Fraction(response["sample_valid_mass"])
            context = sha, tuple(record["input_canvas"])
            if row["method"].startswith("exact_"):
                if context in exact_masses and exact_masses[context] != mass:
                    errors.append([key, "inconsistent exact mass", step])
                exact_masses[context] = mass
            else:
                approximate.append(
                    (context, mass, Fraction(response["certificate"]["upper_tail"]), key, step)
                )
            for p in commits:
                canvas[p] = word[p]
        if row["status"] == "complete":
            if any(t is None for t in canvas) or row["original_token_ids"] != canvas:
                errors.append([key, "incomplete final original IDs"])
            text = adapter.detokenize_bytes(canvas).decode("utf8")
            json.loads(text, parse_constant=reject)
            if row["output"] != text or Fraction(row["observed_local_certificate_sum"]) != delta:
                errors.append([key, "final output/certificate mismatch"])
            if delta > Fraction(protocol["trajectory_total_tv"]):
                errors.append([key, "trajectory allocation exceeded"])
    for group, values in first_heads.items():
        if len(values) != 1:
            errors.append([group, "same initial canvas has different real head"])
    for sha, lower, upper, key, step in approximate:
        if sha in exact_masses:
            mass_checks += 1
            if not lower <= exact_masses[sha] <= lower + upper:
                errors.append([key, "tail certificate violates full mass", step])
    for case, masks, seed, method in index:
        if method != "handoff_numpy":
            continue
        a, b = (
            index[case, masks, seed, method],
            index.get((case, masks, seed, "handoff_full_sparse")),
        )
        if b is None or a["status"] != "complete" or b["status"] != "complete":
            continue

        def signature(row):
            return [
                (
                    s["head_sha256"],
                    s["input_canvas"],
                    s["response"]["sample"],
                    s["response"]["committed"],
                    s["response"]["decisions"],
                )
                for s in row["steps"]
            ]

        if signature(a) != signature(b):
            errors.append([[case, masks, seed], "cursor/full sparse trajectories differ"])
        else:
            matches += 1
    complete = set(index) == keys and not errors and all(r["status"] != "error" for r in rows)
    controls = [m for m in protocol["methods"] if not m.startswith("handoff_")]
    states = []
    for case in capture["selected"]:
        for masks in (4, 8, 16):
            candidate = [
                index.get((case["key"], masks, seed, "handoff_numpy")) for seed in protocol["seeds"]
            ]
            candidate_complete = all(r is not None and r["status"] == "complete" for r in candidate)
            passed, all_controls_complete, comparisons = candidate_complete, True, []
            for method in controls:
                other = [
                    index.get((case["key"], masks, seed, method)) for seed in protocol["seeds"]
                ]
                if candidate_complete and all(
                    r is not None and r["status"] == "complete" for r in other
                ):
                    ratios = {
                        u: [
                            a["actual_warm_total"][u] / b["actual_warm_total"][u]
                            for a, b in zip(candidate, other, strict=True)
                        ]
                        for u in ("wall", "cpu")
                    }
                    strong = all(
                        median(v) <= 0.8 and all(x < 1 for x in v) for v in ratios.values()
                    )
                    passed &= strong
                    comparisons.append(
                        dict(
                            method=method,
                            kind="paired warm full cost",
                            strong=strong,
                            ratios=ratios,
                            median_ratios={u: median(v) for u, v in ratios.items()},
                        )
                    )
                else:
                    all_controls_complete = False
                    # Consistent intrinsic capped failures receive separate capacity credit.
                    capacity = candidate_complete and all(
                        r is not None
                        and r["status"] == "resource_refusal"
                        and r["steps"]
                        and r["steps"][-1]["response"]
                        .get("reason", "")
                        .startswith(("MemoryError:", "CompilationLimit:"))
                        for r in other
                    )
                    passed &= capacity
                    comparisons.append(
                        dict(
                            method=method,
                            kind="explicit-budget capacity"
                            if capacity
                            else "incomplete; no favorable credit",
                            statuses=[None if r is None else r["status"] for r in other],
                        )
                    )
            states.append(
                dict(
                    case=case["key"],
                    masks=masks,
                    scoped_pilot_pass=bool(complete and passed),
                    all_controls_complete=all_controls_complete,
                    strict_timing_pass=bool(complete and passed and all_controls_complete),
                    comparisons=comparisons,
                )
            )
    result = dict(
        records=len(rows),
        planned=len(keys),
        campaign_complete=complete,
        statuses=dict(Counter(r["status"] for r in rows)),
        by_method={
            m: dict(Counter(r["status"] for r in rows if r["method"] == m))
            for m in protocol["methods"]
        },
        new_case_forwards=sum(r["new_forwards"] for r in rows),
        warmup_forwards=meta["warmup_forwards"],
        head_integrity_checks=head_checks,
        distinct_heads=len(heads),
        original_sample_and_fixed_id_checks=fixed_checks,
        exact_mass_certificate_checks=mass_checks,
        literal_cursor_full_sparse_trajectory_matches=matches,
        errors=errors,
        scoped_pilot_states=sum(s["scoped_pilot_pass"] for s in states),
        strict_timing_states=sum(s["strict_timing_pass"] for s in states),
        states=states,
        rows_sha256=digest(directory / "rows.jsonl"),
        metadata_sha256=digest(directory / "metadata.json"),
        scope=(
            "Two-seed pilot on all known documents; no independent corpus, semantics, "
            "native EPIC or publication confirmation. Capacity is not a timing win; "
            "wall-censored successes are not unconditional target-law draws."
        ),
    )
    (directory / "decision.json").write_text(json.dumps(result, indent=2) + "\n")
    (directory / "head-inventory.json").write_text(json.dumps(heads, indent=2) + "\n")
    return result


def reject(_):
    raise ValueError("non-JSON constant")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.input, args.original)
    print(json.dumps({k: v for k, v in result.items() if k != "states"}, indent=2))


if __name__ == "__main__":
    main()
