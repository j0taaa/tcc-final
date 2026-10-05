#!/usr/bin/env python3
"""Same-input exact comparisons with complete, immutable real-state coverage."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
from dataclasses import fields
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from time import perf_counter

from mwpc_exact import ExactBackend
from mwpc_exact.budget_bounds import budget_input_fingerprint, validate_budget_batch
from mwpc_exact.budget_proof import budget_proof_data, fraction_data, verify_budget_proof
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.conflict_certificate import restrict_choices, rewarded_choices
from mwpc_exact.conflict_commit import ConflictCommitSolver
from mwpc_exact.conflict_proof import conflict_proof_data, verify_conflict_proof
from mwpc_exact.evaluation.instance import BenchmarkInstance
from mwpc_exact.evaluation.selection import SelectionStatus, select_exact_mwpc
from mwpc_exact.experiments.metadata import collect_system_metadata

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "configs/experiments/m29_conflict_real_v1.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def system_data(system):
    return {
        field.name: dict(getattr(system, field.name))
        if field.name == "thread_environment"
        else getattr(system, field.name)
        for field in fields(system)
    }


class JobTimeout(Exception):
    pass


def alarm(signum, frame):
    raise JobTimeout


def cohort(config):
    archive = ROOT / config["input_archive"]
    if sha(ROOT / config["cohort_config"]) != config["cohort_config_sha256"]:
        raise ValueError("frozen cohort configuration changed")
    if sha(archive / "manifest.json") != config["input_manifest_sha256"]:
        raise ValueError("source manifest changed")
    manifest = read(archive / "manifest.json")
    originals = []
    expected = {}
    for line in (archive / "rows.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["method"] == "budgeted_rational":
            expected[row["instance_id"]] = row
    for relative in sorted(p for p in manifest if p.startswith("inputs/")):
        path = archive / relative
        if sha(path) != manifest[relative]:
            raise ValueError(f"source input changed: {relative}")
        instance = BenchmarkInstance.from_dict(read(path))
        originals.append((instance, expected[instance.instance_id]))
    if len(originals) != config["expected_inputs"]:
        raise ValueError("incomplete source cohort")
    return originals


def ranked_subsets(state, budget, timeout):
    choices = rewarded_choices(state)
    candidates = []
    for size in range(min(budget, len(choices)) + 1):
        for batch in combinations(range(len(choices)), size):
            if len({choices[j][0][0] for j in batch}) == size:
                candidates.append((sum((choices[j][1] for j in batch), Fraction()), batch))
    candidates.sort(key=lambda row: (-row[0], row[1]))
    calls = 0
    checked_base = False
    for score, ids in candidates:
        batch = tuple(choices[j][0] for j in ids)
        answer = select_exact_mwpc(
            restrict_choices(state, batch), backend=ExactBackend.RUST, timeout_seconds=timeout
        )
        calls += 1
        if answer.status is SelectionStatus.TIMEOUT:
            return {"status": "timeout", "objective_value": None, "oracle_calls": calls}
        if answer.status is SelectionStatus.OPTIMAL:
            checked = validate_budget_batch(
                state,
                budget=budget,
                witness_token_ids=answer.witness_token_ids,
                committed_positions=tuple(p for p, _ in batch),
            )
            if checked.reward != score:
                raise ValueError("enumeration reward differs from original-input reward")
            return {
                "status": "optimal",
                "objective_value": fraction_data(score),
                "witness_token_ids": checked.witness_token_ids,
                "committed_positions": checked.committed_positions,
                "oracle_calls": calls,
            }
        if answer.status is not SelectionStatus.INFEASIBLE_ON_SUPPORT:
            raise ValueError(f"enumerator oracle failed: {answer.status}")
        if not checked_base:
            checked_base = True
            base = select_exact_mwpc(
                restrict_choices(state, ()), backend=ExactBackend.RUST, timeout_seconds=timeout
            )
            calls += 1
            if base.status is SelectionStatus.INFEASIBLE_ON_SUPPORT:
                return {
                    "status": "infeasible_on_support",
                    "objective_value": None,
                    "oracle_calls": calls,
                }
            if base.status is not SelectionStatus.OPTIMAL:
                return {"status": base.status.value, "objective_value": None, "oracle_calls": calls}
    raise AssertionError("feasible base must eventually admit the empty batch")


def worker(directory, method, repetition):
    config = read(directory / "config.json")
    memory = config["address_space_bytes"]
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    if config["pin_first_available_cpu"]:
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    signal.signal(signal.SIGALRM, alarm)
    solver = ConflictCommitSolver()
    provenance = read(directory / "metadata.json")
    output_path = directory / f"{method}-r{repetition}.jsonl"
    with output_path.open("x") as output:
        for i, (instance, source_row) in enumerate(cohort(config)):
            state = instance.selection_input
            common = {
                "instance_id": instance.instance_id,
                "family": instance.grammar.grammar_id,
                "reward_profile": instance.metadata["reward_profile"],
                "input_fingerprint": budget_input_fingerprint(state),
                "method": method,
                "repetition": repetition,
                "git_commit": provenance["git_commit"],
                "config_sha256": provenance["config_sha256"],
                "model_revision": instance.metadata["model_revision"],
                "tokenizer_revision": instance.metadata["tokenizer_revision"],
                "seed": instance.metadata["source_seed"],
                "grammar_sha256": hashlib.sha256(
                    json.dumps(state.grammar.to_dict(), sort_keys=True).encode()
                ).hexdigest(),
                "support_sha256": state.support.fingerprint,
                "exactness_scope": state.support.exactness_scope.to_dict(),
                "cpu_affinity": sorted(os.sched_getaffinity(0)),
                "metadata_file": "metadata.json",
            }
            budgets = [max(config["budgets"])] if method == "resource_dp" else config["budgets"]
            for budget in budgets:
                signal.setitimer(signal.ITIMER_REAL, config["timeout_seconds"][method])
                started = perf_counter()
                try:
                    proofs = []
                    if method == "resource_dp":
                        results = budgeted_commit_frontier(state, budget)
                        elapsed = perf_counter() - started
                        proofs = [budget_proof_data(state, results)]
                        rows = [
                            {
                                "budget": r.budget,
                                "status": r.status.value,
                                "objective_value": fraction_data(r.objective_value),
                            }
                            for r in results
                        ]
                    elif method == "ranked_subsets":
                        rows = [
                            {
                                "budget": budget,
                                **ranked_subsets(state, budget, config["timeout_seconds"][method]),
                            }
                        ]
                        elapsed = perf_counter() - started
                    else:
                        engine = ConflictCommitSolver() if method == "conflict_cold" else solver
                        result = engine.solve(
                            state, budget, timeout_seconds=config["timeout_seconds"][method]
                        )
                        elapsed = perf_counter() - started
                        rows = [
                            {
                                "budget": budget,
                                "status": result.status.value,
                                "objective_value": fraction_data(result.objective_value),
                                "oracle_calls": result.oracle_calls,
                                "learned_conflicts": result.learned_conflicts,
                                "reused_conflicts": result.reused_conflicts,
                            }
                        ]
                        if result.certificate is not None:
                            proofs = [conflict_proof_data(state, result)]
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    expected_rows = source_row["frontier"]
                    for row in rows:
                        expected = next(r for r in expected_rows if r["budget"] == row["budget"])
                        if row["status"] not in ("timeout", "error") and (
                            row["status"] != expected["status"]
                            or row["objective_value"] != expected["objective_value"]
                        ):
                            raise ValueError("CORRECTNESS GATE: new exact result differs from M28")
                    proof_path = None
                    check_seconds = 0.0
                    if proofs:
                        proof_name = f"{method}-r{repetition}-{instance.instance_id}-b{budget}"
                        proof_path = f"proofs/{proof_name}.json.gz"
                        write(directory / proof_path, proofs[0])
                        before = perf_counter()
                        if method == "resource_dp":
                            verify_budget_proof(proofs[0], expected_input=state)
                        else:
                            verify_conflict_proof(proofs[0], expected_input=state)
                        check_seconds = perf_counter() - before
                    record = {
                        **common,
                        "max_budget": budget,
                        "solve_seconds": elapsed,
                        "external_verify_seconds": check_seconds,
                        "proof": proof_path,
                        "batches": rows,
                        "status": "completed",
                        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    }
                except JobTimeout:
                    record = {
                        **common,
                        "max_budget": budget,
                        "status": "timeout",
                        "solve_seconds": perf_counter() - started,
                        "batches": [],
                    }
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                output.write(json.dumps(record, allow_nan=False) + "\n")
                output.flush()
                print(
                    f"{method} r{repetition} {i + 1}/72 b{budget}: {record['status']} "
                    f"{record['solve_seconds']:.4f}s",
                    flush=True,
                )


def run(config_path, directory):
    config = read(config_path)
    system = collect_system_metadata(ROOT)
    if system.git_dirty is not False:
        raise ValueError("commit code/config before archive-producing execution")
    cohort(config)
    directory.mkdir(parents=True, exist_ok=False)
    write(directory / "config.json", config)
    write(
        directory / "metadata.json",
        {
            "git_commit": system.git_commit,
            "git_dirty": system.git_dirty,
            "config_source": str(config_path.relative_to(ROOT)),
            "config_sha256": sha(config_path),
            "hardware_software": system_data(system),
            "new_model_forwards": 0,
            "comparison_scope": config["comparison_scope"],
            "timing_scope": config["timing_scope"],
        },
    )
    for method in config["methods"]:
        for repetition in range(config["repetitions"][method]):
            environment = {
                **os.environ,
                **config["thread_environment"],
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    method,
                    "--repetition",
                    str(repetition),
                    "--output",
                    str(directory),
                ],
                env=environment,
                check=True,
            )
    write(
        directory / "manifest.json",
        {
            str(p.relative_to(directory)): sha(p)
            for p in sorted(directory.rglob("*"))
            if p.is_file()
        },
    )


def verify(directory):
    manifest = read(directory / "manifest.json")
    for relative, expected_hash in manifest.items():
        if sha(directory / relative) != expected_hash:
            raise ValueError(f"archive hash mismatch: {relative}")
    inputs = {
        instance.instance_id: (instance.selection_input, old)
        for instance, old in cohort(read(directory / "config.json"))
    }
    count = 0
    for path in sorted(directory.glob("*-r*.jsonl")):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            state, old = inputs[row["instance_id"]]
            if row["input_fingerprint"] != budget_input_fingerprint(state):
                raise ValueError("foreign input in result")
            for batch in row["batches"]:
                if batch["status"] in ("timeout", "error"):
                    continue
                expected = next(b for b in old["frontier"] if b["budget"] == batch["budget"])
                if (batch["status"], batch["objective_value"]) != (
                    expected["status"],
                    expected["objective_value"],
                ):
                    raise ValueError("archived exact comparison failed")
                if "witness_token_ids" in batch:
                    checked = validate_budget_batch(
                        state,
                        budget=batch["budget"],
                        witness_token_ids=batch["witness_token_ids"],
                        committed_positions=batch["committed_positions"],
                    )
                    if fraction_data(checked.reward) != batch["objective_value"]:
                        raise ValueError("invalid baseline batch")
            if row.get("proof"):
                proof = read(directory / row["proof"])
                if row["method"] == "resource_dp":
                    verify_budget_proof(proof, expected_input=state)
                else:
                    verify_conflict_proof(proof, expected_input=state)
                count += 1
    print(json.dumps({"verified_proofs": count, "status": "PASS"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker")
    parser.add_argument("--repetition", type=int, default=0)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        verify(args.verify)
    elif args.worker:
        worker(args.output, args.worker, args.repetition)
    else:
        run(args.config.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
