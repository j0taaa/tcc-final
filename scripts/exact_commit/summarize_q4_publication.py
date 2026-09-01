#!/usr/bin/env python3
"""Validate, summarize, and pin the publication Q4 scaling campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mwpc_exact.experiments import load_experiment_config
from mwpc_research.q4_scaling import Q4_AXES, ScalingPoint
from mwpc_research.statistical_summaries import summarize_numeric_distribution

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q4_scaling_publication_v1.toml"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "docs/evidence/t1255-q4-publication-summary.json"
DEFAULT_PINNED_RAW = (
    REPOSITORY_ROOT / "docs/artifacts/raw/m125_publication_results_v1/q4-scaling-rows.jsonl"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    _require(bool(rows), "Q4 raw artifact is empty")
    _require(all(isinstance(row, dict) for row in rows), "Q4 raw row is not an object")
    return rows


def _validate_optimal_row(row: dict[str, Any]) -> None:
    _require(row["censored"] is False, "Q4 OPTIMAL row is censored")
    _require(row["censor_reason"] is None, "Q4 OPTIMAL row has a censor reason")
    _require(row["certificate_valid"] is True, "Q4 OPTIMAL certificate is invalid")
    runtime = float(row["successful_runtime_seconds"])
    _require(math.isfinite(runtime) and runtime >= 0.0, "Q4 runtime is invalid")
    point = ScalingPoint.from_dict(row["instance"])
    _require(row["instance_fingerprint"] == point.instance_fingerprint, "Q4 point hash drift")
    witness = tuple(int(value) for value in row["witness_token_ids"])
    terminals = tuple(int(value) for value in row["witness_terminal_labels"])
    graph_edges = tuple(int(value) for value in row["witness_graph_edge_ids"])
    _require(len(witness) == point.slot_count, "Q4 witness has the wrong slot count")
    _require(
        terminals == (ord("a"),) * (point.slot_count * point.token_byte_length),
        "Q4 witness terminal labels do not independently reproduce a+",
    )
    _require(bool(graph_edges), "Q4 OPTIMAL witness omits its graph path")
    proposals = tuple(
        (
            proposal_id,
            proposal_id % point.slot_count,
            (proposal_id // point.slot_count) % point.support_width,
            1.0 + (proposal_id % 7) / 10.0,
        )
        for proposal_id in range(point.proposal_count)
    )
    recomputed_ids = tuple(
        proposal_id
        for proposal_id, position, token_id, _weight in proposals
        if witness[position] == token_id
    )
    recomputed_objective = math.fsum(
        weight
        for proposal_id, _position, _token_id, weight in proposals
        if proposal_id in recomputed_ids
    )
    _require(
        sorted(row["selected_proposal_ids"]) == sorted(recomputed_ids),
        "Q4 selected proposal IDs did not independently reproduce",
    )
    _require(
        math.isclose(
            float(row["objective_value"]),
            recomputed_objective,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ),
        "Q4 objective did not independently reproduce",
    )


def summarize_campaign(config_path: Path, raw_path: Path) -> dict[str, object]:
    config = load_experiment_config(config_path)
    _require(config.publication_mode, "Q4 evidence requires publication mode")
    parameters = config.parameters
    _require(tuple(parameters["backends"]) == ("python", "rust"), "wrong Q4 backends")
    threshold = int(parameters["minimum_repetitions_for_distribution"])
    _require(threshold >= 10, "Q4 distribution threshold is too small")
    _require(config.repetitions >= threshold, "Q4 repetitions are below the threshold")
    _require(
        parameters["graph_size_scale_interpretation"]
        == "compound_support_width_and_token_byte_length",
        "Q4 graph-size interpretation is not compound",
    )
    expected_point_count = sum(
        len(parameters[field])
        for field in (
            "slot_counts",
            "top_k_values",
            "graph_size_scales",
            "grammar_production_counts",
            "token_byte_lengths",
            "proposal_counts",
        )
    )
    rows = _rows(raw_path)
    expected_measurement_count = expected_point_count * config.repetitions * 2
    _require(len(rows) == expected_measurement_count, "wrong Q4 measurement count")
    parameter_by_axis = {
        "slot_count": "slot_counts",
        "top_k": "top_k_values",
        "graph_size_scale": "graph_size_scales",
        "grammar_production_count": "grammar_production_counts",
        "token_byte_length": "token_byte_lengths",
        "proposal_count": "proposal_counts",
    }
    observed_axis_values = {
        axis: sorted({int(row["axis_value"]) for row in rows if row["axis"] == axis})
        for axis in Q4_AXES
    }
    _require(
        all(
            observed_axis_values[axis]
            == [int(value) for value in parameters[parameter_by_axis[axis]]]
            for axis in Q4_AXES
        ),
        "Q4 axis range differs from the publication config",
    )
    metadata = rows[0]["run_metadata"]
    _require(all(row["run_metadata"] == metadata for row in rows), "Q4 metadata drift")
    _require(metadata["git_dirty"] is False, "Q4 campaign used a dirty tree")
    _require(metadata["config_sha256"] == config.config_sha256, "Q4 config hash drift")
    _require(
        metadata["metadata_integrity"]["publication_blockers"] == [],
        "Q4 publication metadata has blockers",
    )

    identities: set[tuple[str, str, int]] = set()
    grouped: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    statuses: Counter[str] = Counter()
    backend_statuses: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        _require(row["artifact_kind"] == "mwpc_q4_scaling_row", "wrong Q4 row kind")
        identity = (str(row["case_id"]), str(row["backend"]), int(row["repetition"]))
        _require(identity not in identities, "duplicate Q4 measurement identity")
        identities.add(identity)
        status = str(row["status"])
        statuses[status] += 1
        backend_statuses[str(row["backend"])][status] += 1
        if status == "optimal":
            _validate_optimal_row(row)
        else:
            _require(row["censored"] is True, "non-OPTIMAL Q4 row is not censored")
            _require(
                row["successful_runtime_seconds"] is None,
                "censored Q4 row exposes a successful runtime",
            )
        grouped[(str(row["case_id"]), str(row["backend"]))].append(row)

    comparison_count = 0
    for case_id in {str(row["case_id"]) for row in rows}:
        for repetition in range(config.repetitions):
            pair = {
                str(row["backend"]): row
                for row in rows
                if row["case_id"] == case_id and row["repetition"] == repetition
            }
            _require(set(pair) == {"python", "rust"}, "Q4 backend pair is incomplete")
            python = pair["python"]
            rust = pair["rust"]
            _require(python["status"] == rust["status"], "Q4 backend status mismatch")
            _require(
                python["instance_fingerprint"] == rust["instance_fingerprint"]
                and python["grammar_sha256"] == rust["grammar_sha256"]
                and python["represented_support_sha256"] == rust["represented_support_sha256"],
                "Q4 backends did not receive the same instance",
            )
            _require(
                python["objective_value"] == rust["objective_value"],
                "Q4 backend objective mismatch",
            )
            comparison_count += 1

    series: list[dict[str, object]] = []
    for (case_id, backend), group in sorted(grouped.items()):
        point = ScalingPoint.from_dict(group[0]["instance"])
        successful = [
            float(row["successful_runtime_seconds"])
            for row in group
            if row["status"] == "optimal" and row["censored"] is False
        ]
        eligible = len(successful) >= threshold
        series.append(
            {
                "case_id": case_id,
                "axis": point.axis,
                "axis_value": point.axis_value,
                "backend": backend,
                "configured_repetitions": config.repetitions,
                "successful_runtime_count": len(successful),
                "censored_count": sum(bool(row["censored"]) for row in group),
                "distribution_status": (
                    "available" if eligible else "withheld_insufficient_repetitions"
                ),
                "runtime_seconds": (
                    summarize_numeric_distribution(successful).to_dict() if eligible else None
                ),
            }
        )

    return {
        "artifact_kind": "mwpc_q4_publication_campaign_summary",
        "schema_version": 1,
        "publication_bundle_id": parameters["publication_bundle_id"],
        "config_path": config_path.relative_to(REPOSITORY_ROOT).as_posix(),
        "config_normalized_sha256": config.config_sha256,
        "config_file_sha256": _sha256(config_path),
        "producing_commit": metadata["git_commit"],
        "raw_source_path": raw_path.relative_to(REPOSITORY_ROOT).as_posix(),
        "raw_sha256": _sha256(raw_path),
        "point_count": expected_point_count,
        "axis_values": observed_axis_values,
        "measurement_count": len(rows),
        "configured_repetitions_per_backend_point": config.repetitions,
        "minimum_repetitions_for_distribution": threshold,
        "status_counts": dict(sorted(statuses.items())),
        "backend_status_counts": {
            backend: dict(sorted(counts.items()))
            for backend, counts in sorted(backend_statuses.items())
        },
        "censored_count": sum(bool(row["censored"]) for row in rows),
        "timeout_count": statuses["timeout"],
        "error_count": statuses["error"],
        "backend_comparison_count": comparison_count,
        "backend_mismatch_count": 0,
        "all_optimal_certificates_independently_rechecked": True,
        "graph_size_scale_interpretation": parameters["graph_size_scale_interpretation"],
        "scaling_series": series,
        "run_metadata": metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--raw-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--pinned-raw-output", type=Path, default=DEFAULT_PINNED_RAW)
    arguments = parser.parse_args()
    config_path = arguments.config.resolve()
    raw_path = arguments.raw_input.resolve()
    summary = summarize_campaign(config_path, raw_path)
    pinned_path = arguments.pinned_raw_output.resolve()
    output_path = arguments.output.resolve()
    _require(not pinned_path.exists(), "refusing to overwrite pinned Q4 raw rows")
    _require(not output_path.exists(), "refusing to overwrite Q4 evidence summary")
    pinned_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(raw_path, pinned_path)
    summary["pinned_raw_path"] = pinned_path.relative_to(REPOSITORY_ROOT).as_posix()
    summary["pinned_raw_sha256"] = _sha256(pinned_path)
    output_path.write_text(
        json.dumps(summary, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(output_path),
                "pinned_raw": str(pinned_path),
                "measurement_count": summary["measurement_count"],
                "censored_count": summary["censored_count"],
                "backend_mismatch_count": summary["backend_mismatch_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
