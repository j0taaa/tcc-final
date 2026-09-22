#!/usr/bin/env python3
"""Bounded recursive scaling or replay of immutable pre-commit model snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path
from statistics import median
from time import perf_counter

from mwpc_exact import BenchmarkInstance, ComponentProfiler, ExactBackend, solve_exact_commit
from mwpc_exact.evaluation.selection import (
    recompute_witness_selection,
    select_greedy_exact_feasibility,
)
from mwpc_exact.experiments import capture_run_metadata, load_experiment_config
from mwpc_exact.experiments.metadata import canonical_json_sha256
from mwpc_research.live_evidence import snapshot_instance
from mwpc_research.recursive_scaling import scaling_instance
from mwpc_research.recursive_tasks import check_syntax, recursive_grammar

ROOT = Path(__file__).resolve().parents[2]


def dump(path, value):
    with path.open("x") as output:
        json.dump(value, output, allow_nan=False, sort_keys=True)
        output.write("\n")


def child(job_path, result_path, timeout, memory_mib):
    resource.setrlimit(resource.RLIMIT_AS, (memory_mib * 1024**2,) * 2)
    job = json.loads(job_path.read_text())
    instance = BenchmarkInstance.from_dict(job["instance"])
    state = instance.selection_input
    profiler = ComponentProfiler(enabled=True)
    started = perf_counter()
    try:
        if job["method"] == "greedy_exact_feasibility":
            result = select_greedy_exact_feasibility(
                state,
                backend=ExactBackend.RUST,
                total_timeout_seconds=timeout,
            )
            status, score = result.status.value, result.score
        else:
            result = solve_exact_commit(
                state.grammar,
                canvas=state.canvas,
                support=state.support,
                proposals=state.proposals,
                tokenizer_adapter=state.tokenizer_adapter,
                eos_policy=state.eos_policy,
                backend=ExactBackend.RUST,
                timeout_seconds=timeout,
                profiler=profiler,
            )
            status, score = result.status.value, result.objective_value
        elapsed = perf_counter() - started
        valid = None
        if status in {"optimal", "feasible_on_support"}:
            selected, recomputed = recompute_witness_selection(state, result.witness_token_ids)
            if set(selected) != set(result.selected_proposal_ids) or recomputed != score:
                raise RuntimeError("independent witness scoring disagrees")
            valid = check_syntax(
                instance.grammar.grammar_id, bytes(result.witness_terminal_labels)
            ).syntax_valid
            if not valid:
                raise RuntimeError("independent syntax check rejected an optimal certificate")
        row = {
            "status": status,
            "score": score,
            "runtime_seconds": elapsed,
            "result": result.to_dict(),
            "independent_syntax": valid,
            "profile": profiler.snapshot().to_dict(),
        }
    except Exception as error:
        row = {
            "status": "error",
            "score": None,
            "runtime_seconds": perf_counter() - started,
            "error": f"{type(error).__name__}: {error}",
        }
    row["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    dump(result_path, row)


def summarize(rows):
    """Pair repetitions inside each state; never count repetitions as new states."""
    paired = defaultdict(dict)
    groups = defaultdict(list)
    for row in rows:
        paired[row["instance"]["instance_id"], row["repetition"]][row["method"]] = row
    for pair in paired.values():
        if set(pair) != {"rust_exact", "greedy_exact_feasibility"}:
            continue
        exact, greedy = pair["rust_exact"], pair["greedy_exact_feasibility"]
        metadata = exact["instance"]["metadata"]
        if "proposal_budget" not in metadata:
            continue
        groups[metadata["width"], metadata["proposal_budget"]].append((exact, greedy))
    comparisons = []
    for (width, budget), pairs in sorted(groups.items()):
        states = defaultdict(list)
        gaps = []
        for exact, greedy in pairs:
            if exact["status"] == "optimal" and greedy["status"] == "feasible_on_support":
                states[exact["instance"]["instance_id"]].append(
                    greedy["runtime_seconds"] / exact["runtime_seconds"]
                )
                gaps.append(exact["score"] - greedy["score"])
        comparisons.append(
            {
                "width": width,
                "proposal_budget": budget,
                "states": len({e["instance"]["instance_id"] for e, _ in pairs}),
                "paired_feasible_states": len(states),
                "paired_feasible_repetitions": len(gaps),
                "exact_statuses": dict(Counter(e["status"] for e, _ in pairs)),
                "greedy_statuses": dict(Counter(g["status"] for _, g in pairs)),
                "median_state_speedup": median(median(times) for times in states.values())
                if states
                else None,
                "exact_faster_states": sum(median(times) > 1 for times in states.values()),
                "positive_gap_repetitions": sum(gap > 1e-12 for gap in gaps),
                "negative_gap_repetitions": sum(gap < -1e-12 for gap in gaps),
                "maximum_score_gap": max(gaps) if gaps else None,
            }
        )
    return {
        "rows": len(rows),
        "solver_status_counts": dict(Counter(row["status"] for row in rows)),
        "analysis_unit": "snapshot; K/budget/method/repetition are repeated measures",
        "timing_scope": "selection including lattice, parsing and certificate; excludes model",
        "comparisons": comparisons,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--analyze-directory", type=Path)
    parser.add_argument("--child-job", type=Path)
    parser.add_argument("--child-result", type=Path)
    parser.add_argument("--timeout", type=float, default=1)
    parser.add_argument("--memory-mib", type=int, default=2048)
    args = parser.parse_args()
    if args.analyze_directory:
        from scripts.exact_commit.build_review_results import verified_rows

        print(json.dumps(summarize(verified_rows(args.analyze_directory)), indent=2))
        return
    if args.child_job:
        child(args.child_job, args.child_result, args.timeout, args.memory_mib)
        return
    config = load_experiment_config(args.config)
    directory = args.run_directory
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "jobs").mkdir()
    (directory / "results").mkdir()
    metadata = capture_run_metadata(
        config,
        run_id=directory.name,
        repository_root=ROOT,
        require_rust=True,
        grammar_sha256=[
            canonical_json_sha256(recursive_grammar(f).to_dict())
            for f in ("brackets", "arithmetic", "nested_json")
        ],
    )
    if metadata["git_dirty"]:
        raise RuntimeError("freeze source and config before measurement")
    dump(directory / "metadata.json", metadata)
    (directory / "config.toml").write_bytes(args.config.read_bytes())
    parameters = config.parameters
    instances = []
    inputs = {}
    if parameters["study"] == "scaling":
        for slots, width, depth in product(
            parameters["slot_counts"],
            parameters["widths"],
            parameters["fixed_depths"],
        ):
            instances.append(scaling_instance(slots, width, depth))
    else:
        snapshot_root = ROOT / str(parameters["snapshot_directory"])
        paths = sorted(snapshot_root.glob("*.json"))
        if len(paths) != parameters["expected_snapshots"]:
            raise ValueError("snapshot count differs from frozen configuration")
        for path in paths:
            inputs[path.relative_to(ROOT).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            snapshot = json.loads(path.read_text())
            for width, budget in product(
                parameters["widths"], parameters.get("proposal_budgets", [None])
            ):
                instances.append(snapshot_instance(snapshot, width, budget))
    dump(directory / "input-hashes.json", inputs)
    jobs = []
    for instance in instances:
        for repetition in range(config.repetitions):
            methods = list(parameters["methods"])
            if repetition % 2:
                methods.reverse()
            for method in methods:
                jobs.append(
                    {
                        "job_id": f"{instance.instance_id}-r{repetition}-{method}",
                        "instance": instance.to_dict(),
                        "method": method,
                        "repetition": repetition,
                    }
                )
    dump(directory / "jobs.json", jobs)
    began = perf_counter()
    rows = []
    for index, job in enumerate(jobs):
        job_path = directory / "jobs" / f"{index}.json"
        result_path = directory / "results" / f"{index}.json"
        dump(job_path, job)
        remaining = config.run_timeout_seconds - (perf_counter() - began)
        if remaining <= 0:
            result = {"status": "not_run_run_budget", "score": None, "runtime_seconds": None}
        else:
            limit = min(float(parameters["process_timeout_seconds"]), remaining)
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "scripts.exact_commit.run_review_offline",
                        "--child-job",
                        str(job_path),
                        "--child-result",
                        str(result_path),
                        "--timeout",
                        str(config.solver_timeout_seconds),
                        "--memory-mib",
                        str(parameters["max_address_space_mib"]),
                    ],
                    cwd=ROOT,
                    timeout=limit,
                    capture_output=True,
                    text=True,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )
                result = (
                    json.loads(result_path.read_text())
                    if result_path.exists()
                    else {
                        "status": "error",
                        "score": None,
                        "runtime_seconds": None,
                        "worker_exit_code": process.returncode,
                        "stderr": process.stderr[-2000:],
                    }
                )
            except subprocess.TimeoutExpired:
                result = {
                    "status": "timeout",
                    "score": None,
                    "runtime_seconds": None,
                    "censoring_seconds": limit,
                    "timeout_phase": "process",
                }
        row = {**job, **result, "run_metadata": metadata}
        rows.append(row)
        with (directory / "rows.jsonl").open("a") as output:
            output.write(json.dumps(row, allow_nan=False) + "\n")
        if (index + 1) % 12 == 0:
            print(json.dumps({"completed": index + 1, "total": len(jobs)}), flush=True)
    dump(
        directory / "summary.json",
        summarize(rows),
    )
    if any(row["status"] == "error" for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
