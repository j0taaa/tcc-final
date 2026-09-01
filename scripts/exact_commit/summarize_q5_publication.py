#!/usr/bin/env python3
"""Validate and summarize the six-run Q5 publication campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from mwpc_exact.experiments import load_experiment_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q5_structured_publication_v4.toml"
DEFAULT_RESULTS_ROOT = REPOSITORY_ROOT / "results/raw/q5_structured_publication_v4"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "docs/evidence/t1253-q5-publication-summary.json"
STRATEGIES = ("unconstrained", "serial", "epic", "exact")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    _require(bool(rows), f"empty Q5 raw artifact: {path}")
    _require(all(isinstance(row, dict) for row in rows), f"non-object Q5 row: {path}")
    return rows


def _validate_exact_row(row: dict[str, Any]) -> int:
    exact = row["exact_solver"]
    _require(exact["status"] == "optimal", "Q5 exact row is not OPTIMAL")
    _require(exact["certificate_valid"] is True, "Q5 exact certificate is invalid")
    _require(exact["exactness_scope"]["claim"] == "exact_on_support", "wrong scope")
    outcomes = row["diagnostics"]["optimizer_outcomes"]
    _require(bool(outcomes), "Q5 exact row has no optimizer outcomes")
    _require(
        row["diagnostics"]["all_optimal_certificates_independently_valid"] is True,
        "Q5 exact row did not validate every optimizer outcome",
    )
    for outcome in outcomes:
        solver = outcome["decoder_step"]["solver_result"]
        _require(solver["status"] == "optimal", "Q5 optimizer step is not OPTIMAL")
        validation = solver["diagnostics"]["certificate_validation"]
        _require(validation["is_valid"] is True, "Q5 optimizer certificate failed")
        _require(validation["issues"] == [], "Q5 optimizer certificate has issues")
        _require(
            solver["objective_value"] == validation["recomputed_objective"],
            "Q5 optimizer objective was not independently reproduced",
        )
        _require(
            sorted(solver["selected_proposal_ids"])
            == sorted(validation["recomputed_selected_proposal_ids"]),
            "Q5 optimizer selected IDs were not independently reproduced",
        )
        _require(bool(solver["witness_graph_edge_ids"]), "Q5 optimizer witness has no path")
    return len(outcomes)


def summarize_campaign(config_path: Path, results_root: Path) -> dict[str, object]:
    config = load_experiment_config(config_path)
    _require(config.publication_mode, "Q5 campaign config must enable publication mode")
    manifest_path = REPOSITORY_ROOT / str(config.parameters["task_manifest"])
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    tasks = tuple(str(row["task_id"]) for row in manifest["tasks"])
    seeds = config.seeds
    expected_rows_per_run = config.repetitions * len(STRATEGIES)
    run_summaries: list[dict[str, object]] = []
    producing_commits: set[str] = set()
    total_optimizer_steps = 0

    for task_id in tasks:
        for seed in seeds:
            raw_path = results_root / f"{task_id}-seed{seed}" / "q5-end-to-end-rows.jsonl"
            rows = _load_jsonl(raw_path)
            _require(len(rows) == expected_rows_per_run, f"wrong Q5 row count: {raw_path}")
            strategies = Counter(str(row["strategy"]) for row in rows)
            _require(
                strategies == Counter({name: config.repetitions for name in STRATEGIES}),
                f"wrong Q5 strategy counts: {raw_path}",
            )
            fingerprints = {str(row["comparison_fingerprint"]) for row in rows}
            _require(len(fingerprints) == 1, f"unpaired Q5 input: {raw_path}")
            metadata = rows[0]["run_metadata"]
            _require(all(row["run_metadata"] == metadata for row in rows), "metadata drift")
            _require(metadata["git_dirty"] is False, "Q5 publication run used a dirty tree")
            _require(metadata["benchmark_claim"] is True, "Q5 run lacks benchmark claim")
            _require(metadata["metadata_integrity"]["publication_blockers"] == [], "blockers")
            _require(metadata["selected_task_id"] == task_id, "Q5 task identity mismatch")
            _require(metadata["selected_seed"] == seed, "Q5 seed identity mismatch")
            _require(
                metadata["config_sha256"] == config.config_sha256,
                "Q5 config hash mismatch",
            )
            producing_commits.add(str(metadata["git_commit"]))

            for row in rows:
                _require(row["execution_status"] == "complete", "incomplete Q5 generation")
                if row["strategy"] != "unconstrained":
                    _require(row["syntactic_valid"] is True, "invalid constrained Q5 output")
                    _require(row["functional_success"] is True, "wrong constrained Q5 output")
                if row["strategy"] == "exact":
                    total_optimizer_steps += _validate_exact_row(row)

            epic_rows = [row for row in rows if row["strategy"] == "epic"]
            selector_calls = sum(
                int(row["diagnostics"]["regular_cover_selector_calls"]) for row in epic_rows
            )
            batch_sizes = [
                int(value)
                for row in epic_rows
                for value in row["diagnostics"]["regular_cover_batch_sizes"]
            ]
            _require(selector_calls > 0, "Q5 EPIC selector was never called")
            _require(max(batch_sizes, default=0) > 1, "Q5 EPIC never committed a parallel batch")
            run_summaries.append(
                {
                    "task_id": task_id,
                    "seed": seed,
                    "comparison_fingerprint": next(iter(fingerprints)),
                    "raw_path": raw_path.relative_to(REPOSITORY_ROOT).as_posix(),
                    "raw_sha256": _sha256(raw_path),
                    "row_count": len(rows),
                    "epic_regular_cover_selector_calls": selector_calls,
                    "epic_max_batch_size": max(batch_sizes),
                    "median_runtime_seconds_by_strategy": {
                        strategy: median(
                            float(row["resources"]["elapsed_seconds"])
                            for row in rows
                            if row["strategy"] == strategy
                        )
                        for strategy in STRATEGIES
                    },
                }
            )

    _require(len(producing_commits) == 1, "Q5 campaign spans multiple code commits")
    return {
        "artifact_kind": "mwpc_q5_publication_campaign_summary",
        "schema_version": 1,
        "publication_bundle_id": config.parameters["publication_bundle_id"],
        "config_path": config_path.relative_to(REPOSITORY_ROOT).as_posix(),
        "config_normalized_sha256": config.config_sha256,
        "config_file_sha256": _sha256(config_path),
        "task_manifest_path": manifest_path.relative_to(REPOSITORY_ROOT).as_posix(),
        "task_manifest_sha256": _sha256(manifest_path),
        "producing_commit": next(iter(producing_commits)),
        "tasks": list(tasks),
        "seeds": list(seeds),
        "repetitions_per_strategy_task_seed": config.repetitions,
        "measured_row_count": len(run_summaries) * expected_rows_per_run,
        "exact_optimizer_step_count": total_optimizer_steps,
        "contract_failure_count": 0,
        "all_constrained_outputs_independently_valid": True,
        "all_exact_optimizer_certificates_independently_valid": True,
        "epic_parallel_commit_observed_in_every_task_seed": True,
        "runs": run_summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    summary = summarize_campaign(arguments.config.resolve(), arguments.results_root.resolve())
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(summary, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(arguments.output), **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
