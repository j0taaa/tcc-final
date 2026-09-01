#!/usr/bin/env python3
"""Replay Q2 selectors over the shared real LLaDA snapshot corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from mwpc_exact.experiments import (
    capture_run_metadata,
    default_processed_directory,
    finalize_run_metadata,
    load_experiment_config,
    save_resolved_config,
)
from mwpc_research.q2_real_gap import (
    Q2_REAL_ROW_KIND,
    Q2_REAL_SCHEMA_VERSION,
    Q2_REAL_SELECTORS,
    load_snapshot_jsonl,
    replay_real_snapshot,
    summarize_real_rows,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q2_real_state_publication_v2.toml"
RAW_FILENAME = "q2-real-gap-rows.jsonl"
SUMMARY_FILENAME = "q2-real-gap-summary.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


@contextmanager
def _epic_environment() -> Iterator[None]:
    updates = {
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT": "1",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH": "2",
    }
    previous = {name: os.environ.get(name) for name in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--processed-directory", type=Path)
    arguments = parser.parse_args()
    config_path = arguments.config.resolve()
    config = load_experiment_config(config_path)
    _require(config.publication_mode, "real Q2 replay requires publication mode")
    parameters = config.parameters
    expected_fields = {
        "snapshot_capture_config",
        "snapshot_jsonl",
        "task_ids",
        "snapshots_per_task_seed",
        "expected_snapshot_count",
        "selectors",
        "weight_modes",
        "exact_backend",
        "independent_validation",
        "maximum_support_combinations_for_baseline_validation",
        "require_common_snapshot_hash",
        "publication_bundle_id",
        "raw_output_root",
    }
    _require(set(parameters) == expected_fields, "unexpected real Q2 replay parameters")
    _require(tuple(parameters["selectors"]) == Q2_REAL_SELECTORS, "wrong Q2 selectors")
    _require(parameters["weight_modes"] == ("confidence",), "wrong Q2 weight mode")
    _require(parameters["exact_backend"] == "rust", "real Q2 replay requires Rust")
    snapshot_path = REPOSITORY_ROOT / str(parameters["snapshot_jsonl"])
    instances = load_snapshot_jsonl(snapshot_path)
    _require(
        len(instances) == int(parameters["expected_snapshot_count"]),
        "real Q2 snapshot count differs from config",
    )
    tasks = Counter(str(instance.metadata["task_id"]) for instance in instances)
    seeds = Counter(int(instance.metadata["seed"]) for instance in instances)
    per_pair = int(parameters["snapshots_per_task_seed"])
    task_ids = tuple(str(task) for task in parameters["task_ids"])
    _require(
        tasks == Counter({task: per_pair * len(config.seeds) for task in task_ids}),
        "real Q2 task coverage differs from config",
    )
    _require(
        seeds == Counter({seed: per_pair * len(task_ids) for seed in config.seeds}),
        "real Q2 seed coverage differs from config",
    )
    run_directory = (
        REPOSITORY_ROOT / str(parameters["raw_output_root"])
        if arguments.run_directory is None
        else arguments.run_directory.resolve()
    )
    processed_directory = (
        default_processed_directory(run_directory, REPOSITORY_ROOT)
        if arguments.processed_directory is None
        else arguments.processed_directory.resolve()
    )
    raw_path = run_directory / RAW_FILENAME
    summary_path = processed_directory / SUMMARY_FILENAME
    _require(not raw_path.exists(), "refusing to overwrite real Q2 raw rows")
    _require(not summary_path.exists(), "refusing to overwrite real Q2 summary")
    save_resolved_config(config, run_directory)
    metadata = capture_run_metadata(
        config,
        run_id=run_directory.name,
        repository_root=REPOSITORY_ROOT,
        grammar_sha256=tuple(instance.grammar.fingerprint for instance in instances),
        require_rust=True,
        additional={
            "dataset": "saved_real_llada_selector_states_v2",
            "snapshot_jsonl": snapshot_path.relative_to(REPOSITORY_ROOT).as_posix(),
            "snapshot_jsonl_sha256": _sha256(snapshot_path),
            "snapshot_count": len(instances),
            "component_selectors": list(Q2_REAL_SELECTORS),
            "publication_bundle_id": parameters["publication_bundle_id"],
            "synthetic_rows_included": False,
        },
    )
    rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    with _epic_environment():
        for instance in instances:
            try:
                row = replay_real_snapshot(
                    instance,
                    timeout_seconds=config.solver_timeout_seconds,
                    maximum_support_combinations=int(
                        parameters["maximum_support_combinations_for_baseline_validation"]
                    ),
                )
                row["success"] = True
            except Exception as error:
                row = {
                    "artifact_kind": Q2_REAL_ROW_KIND,
                    "schema_version": Q2_REAL_SCHEMA_VERSION,
                    "snapshot_id": instance.instance_id,
                    "snapshot_sha256": instance.fingerprint,
                    "source": instance.to_dict()["metadata"],
                    "success": False,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
                failures.append(row)
            rows.append(row)
    successful = [row for row in rows if row["success"] is True]
    selector_statuses = {
        name: dict(
            sorted(
                Counter(
                    str(row["selector_results"][name]["status"])  # type: ignore[index]
                    for row in successful
                ).items()
            )
        )
        for name in Q2_REAL_SELECTORS
    }
    metadata = finalize_run_metadata(
        metadata,
        solver_status_counts={
            "selectors": selector_statuses,
            "replay": {"complete": len(successful), "error": len(failures)},
        },
        publication_mode=True,
    )
    for row in rows:
        row["run_metadata"] = metadata
    run_directory.mkdir(parents=True, exist_ok=True)
    processed_directory.mkdir(parents=True, exist_ok=True)
    with raw_path.open("x", encoding="utf-8") as output:
        for row in rows:
            output.write(
                json.dumps(row, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n"
            )
    summary = (
        summarize_real_rows(successful)
        if successful
        else {
            "artifact_kind": "mwpc_q2_real_state_gap_summary",
            "schema_version": 1,
            "snapshot_count": 0,
        }
    )
    summary.update(
        {
            "configured_snapshot_count": len(instances),
            "failure_count": len(failures),
            "failures": failures,
            "run_metadata": metadata,
            "raw_sha256": _sha256(raw_path),
        }
    )
    summary_path.write_text(
        json.dumps(summary, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "raw_path": str(raw_path),
                "summary_path": str(summary_path),
                "snapshot_count": len(instances),
                "successful_count": len(successful),
                "failure_count": len(failures),
            },
            sort_keys=True,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
