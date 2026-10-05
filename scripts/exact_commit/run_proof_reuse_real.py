#!/usr/bin/env python3
"""Frozen two-sided reuse follow-up; same cohort, scores and exact certificates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from scripts.exact_commit.run_conflict_real import (
    JobTimeout,
    alarm,
    cohort,
    read,
    sha,
    system_data,
    write,
)

from mwpc_exact.budget_bounds import budget_input_fingerprint
from mwpc_exact.budget_proof import fraction_data
from mwpc_exact.conflict_proof import conflict_proof_data, verify_conflict_proof
from mwpc_exact.experiments.metadata import collect_system_metadata
from mwpc_exact.proof_reuse import ProofReuseSolver

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "configs/experiments/m29_proof_reuse_real_v1.json"


def worker(directory, method, repetition):
    config = read(directory / "config.json")
    memory = config["address_space_bytes"]
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    signal.signal(signal.SIGALRM, alarm)
    solver = ProofReuseSolver(use_conflicts=method == "proof_reuse")
    metadata = read(directory / "metadata.json")
    with (directory / f"{method}-r{repetition}.jsonl").open("x") as output:
        for ordinal, (instance, old) in enumerate(cohort(config)):
            state = instance.selection_input
            for budget in config["budgets"]:
                signal.setitimer(signal.ITIMER_REAL, config["timeout_seconds"][method])
                started = perf_counter()
                common = {
                    "instance_id": instance.instance_id,
                    "family": instance.grammar.grammar_id,
                    "reward_profile": instance.metadata["reward_profile"],
                    "input_fingerprint": budget_input_fingerprint(state),
                    "method": method,
                    "repetition": repetition,
                    "max_budget": budget,
                    "git_commit": metadata["git_commit"],
                    "config_sha256": metadata["config_sha256"],
                    "model_revision": instance.metadata["model_revision"],
                    "model_id": old["model_id"],
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
                try:
                    result = solver.solve(state, budget)
                    elapsed = perf_counter() - started
                    expected = next(b for b in old["frontier"] if b["budget"] == budget)
                    if (result.status.value, fraction_data(result.objective_value)) != (
                        expected["status"],
                        expected["objective_value"],
                    ):
                        raise ValueError(
                            "CORRECTNESS GATE: cached result differs from source optimum"
                        )
                    before = perf_counter()
                    proof = conflict_proof_data(state, result)
                    name = f"proofs/{method}-r{repetition}-{instance.instance_id}-b{budget}.json.gz"
                    write(directory / name, proof)
                    serialization = perf_counter() - before
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    before = perf_counter()
                    verify_conflict_proof(proof, expected_input=state)
                    row = {
                        **common,
                        "status": "completed",
                        "solve_seconds": elapsed,
                        "serialization_seconds": serialization,
                        "external_verify_seconds": perf_counter() - before,
                        "proof": name,
                        "batches": [
                            {
                                "budget": budget,
                                "status": result.status.value,
                                "objective_value": fraction_data(result.objective_value),
                                "oracle_calls": result.oracle_calls,
                                "learned_conflicts": result.learned_conflicts,
                                "reused_conflicts": result.reused_conflicts,
                            }
                        ],
                        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    }
                except JobTimeout:
                    row = {
                        **common,
                        "status": "timeout",
                        "batches": [],
                        "solve_seconds": perf_counter() - started,
                    }
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                output.write(json.dumps(row, allow_nan=False) + "\n")
                output.flush()
                print(
                    f"{method} r{repetition} {ordinal + 1}/72 b{budget}: "
                    f"{row['status']} {row['solve_seconds']:.4f}s",
                    flush=True,
                )


def run(config_path, directory, after):
    if after is not None:
        while not (after / "manifest.json").exists():
            time.sleep(15)
    system = collect_system_metadata(ROOT)
    if system.git_dirty is not False:
        raise ValueError("commit producing code/config before execution")
    config = read(config_path)
    if sha(ROOT / config["primary_config"]) != config["primary_config_sha256"]:
        raise ValueError("primary protocol changed")
    cohort(config)
    directory.mkdir(parents=True, exist_ok=False)
    write(directory / "config.json", config)
    write(
        directory / "metadata.json",
        {
            "git_commit": system.git_commit,
            "git_dirty": False,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "config_source": str(config_path.relative_to(ROOT)),
            "config_sha256": sha(config_path),
            "hardware_software": system_data(system),
            "new_model_forwards": 0,
            "comparison_scope": config["comparison_scope"],
            "timing_scope": config["timing_scope"],
            "development_scope": config["development_scope"],
        },
    )
    for method in config["methods"]:
        for repetition in range(config["repetitions"][method]):
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.exact_commit.run_proof_reuse_real",
                    "--worker",
                    method,
                    "--repetition",
                    str(repetition),
                    "--output",
                    str(directory),
                ],
                cwd=ROOT,
                env={**os.environ, **config["thread_environment"], "PYTHONDONTWRITEBYTECODE": "1"},
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--after", type=Path)
    parser.add_argument("--worker")
    parser.add_argument("--repetition", type=int, default=0)
    args = parser.parse_args()
    if args.worker:
        worker(args.output, args.worker, args.repetition)
    else:
        run(args.config.resolve(), args.output.resolve(), args.after)


if __name__ == "__main__":
    main()
