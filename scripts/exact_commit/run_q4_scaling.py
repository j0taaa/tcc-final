#!/usr/bin/env python3
"""Run the configured Q4 exact-backend scaling experiment."""

from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from mwpc_exact.backend import ExactBackend
from mwpc_exact.experiments import (
    ExperimentKind,
    capture_run_metadata,
    finalize_run_metadata,
    load_experiment_config,
    save_resolved_config,
)
from mwpc_research.q4_scaling import (
    make_scaling_points,
    run_q4_scaling,
    scaling_point_grammar_sha256,
    write_q4_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q4_scaling_v1.toml"


def _positive_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _integer_sequence(value: object, field_name: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence")
    result = tuple(_positive_integer(item, f"{field_name} item") for item in value)
    if not result or len(set(result)) != len(result):
        raise ValueError(f"{field_name} must be non-empty and unique")
    return result


def _backends(value: object) -> tuple[ExactBackend, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("parameters.backends must be a finite sequence")
    result = tuple(ExactBackend(str(item)) for item in value)
    if set(result) != set(ExactBackend) or len(result) != len(ExactBackend):
        raise ValueError("Q4 requires exactly the Python and Rust backends")
    return result


def _relative_path(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field_name} must be repository-relative")
    return value


@dataclass(frozen=True, slots=True)
class Q4Parameters:
    backends: tuple[ExactBackend, ...]
    slot_counts: tuple[int, ...]
    top_k_values: tuple[int, ...]
    graph_size_scales: tuple[int, ...]
    grammar_production_counts: tuple[int, ...]
    token_byte_lengths: tuple[int, ...]
    proposal_counts: tuple[int, ...]
    baseline_slot_count: int
    baseline_top_k: int
    baseline_grammar_production_count: int
    baseline_token_byte_length: int
    baseline_proposal_count: int
    vocabulary_size: int
    address_space_limit_bytes: int
    raw_output_root: str


def _configuration_parameters(parameters: Mapping[str, object]) -> Q4Parameters:
    required = {
        "backends",
        "slot_counts",
        "top_k_values",
        "graph_size_scales",
        "grammar_production_counts",
        "token_byte_lengths",
        "proposal_counts",
        "baseline_slot_count",
        "baseline_top_k",
        "baseline_grammar_production_count",
        "baseline_token_byte_length",
        "baseline_proposal_count",
        "vocabulary_size",
        "max_address_space_mib",
        "record_chart_size",
        "record_graph_size",
        "raw_output_root",
    }
    if set(parameters) != required:
        raise ValueError("Q4 parameters must contain exactly: " + ", ".join(sorted(required)))
    for flag in ("record_chart_size", "record_graph_size"):
        if parameters[flag] is not True:
            raise ValueError(f"parameters.{flag} must be true")
    return Q4Parameters(
        backends=_backends(parameters["backends"]),
        slot_counts=_integer_sequence(parameters["slot_counts"], "parameters.slot_counts"),
        top_k_values=_integer_sequence(
            parameters["top_k_values"], "parameters.top_k_values"
        ),
        graph_size_scales=_integer_sequence(
            parameters["graph_size_scales"], "parameters.graph_size_scales"
        ),
        grammar_production_counts=_integer_sequence(
            parameters["grammar_production_counts"],
            "parameters.grammar_production_counts",
        ),
        token_byte_lengths=_integer_sequence(
            parameters["token_byte_lengths"], "parameters.token_byte_lengths"
        ),
        proposal_counts=_integer_sequence(
            parameters["proposal_counts"], "parameters.proposal_counts"
        ),
        baseline_slot_count=_positive_integer(
            parameters["baseline_slot_count"], "parameters.baseline_slot_count"
        ),
        baseline_top_k=_positive_integer(
            parameters["baseline_top_k"], "parameters.baseline_top_k"
        ),
        baseline_grammar_production_count=_positive_integer(
            parameters["baseline_grammar_production_count"],
            "parameters.baseline_grammar_production_count",
        ),
        baseline_token_byte_length=_positive_integer(
            parameters["baseline_token_byte_length"],
            "parameters.baseline_token_byte_length",
        ),
        baseline_proposal_count=_positive_integer(
            parameters["baseline_proposal_count"], "parameters.baseline_proposal_count"
        ),
        vocabulary_size=_positive_integer(
            parameters["vocabulary_size"], "parameters.vocabulary_size"
        ),
        address_space_limit_bytes=_positive_integer(
            parameters["max_address_space_mib"], "parameters.max_address_space_mib"
        )
        * 1024
        * 1024,
        raw_output_root=_relative_path(
            parameters["raw_output_root"], "parameters.raw_output_root"
        ),
    )


def _default_run_directory(raw_output_root: str, experiment_id: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return REPOSITORY_ROOT / raw_output_root / f"{experiment_id}-{timestamp}"


def _copy_summary(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as input_file, destination.open("xb") as output_file:
        shutil.copyfileobj(input_file, output_file)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure exact-commit scaling with explicit censoring."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--summary-output", type=Path)
    arguments = parser.parse_args(argv)

    config = load_experiment_config(arguments.config)
    if config.question is not ExperimentKind.SCALING:
        raise ValueError("Q4 driver requires a scaling configuration")
    if config.publication_mode:
        raise ValueError("Q4 v1 is a diagnostic smoke, not publication mode")
    if len(config.seeds) != 1:
        raise ValueError("Q4 v1 requires exactly one base seed")
    if config.cpu_threads != 1:
        raise ValueError("Q4 v1 worker isolation requires hardware.cpu_threads = 1")
    parameters = _configuration_parameters(config.parameters)
    if config.support_top_k != parameters.baseline_top_k:
        raise ValueError("support.top_k must equal parameters.baseline_top_k")
    maximum_width = max((*parameters.top_k_values, *parameters.graph_size_scales))
    if config.support_k_max != maximum_width:
        raise ValueError("support.k_max must equal the largest configured support width")
    points = make_scaling_points(
        seed=config.seeds[0],
        vocabulary_size=parameters.vocabulary_size,
        baseline_slot_count=parameters.baseline_slot_count,
        baseline_top_k=parameters.baseline_top_k,
        baseline_grammar_production_count=parameters.baseline_grammar_production_count,
        baseline_token_byte_length=parameters.baseline_token_byte_length,
        baseline_proposal_count=parameters.baseline_proposal_count,
        slot_counts=parameters.slot_counts,
        top_k_values=parameters.top_k_values,
        graph_size_scales=parameters.graph_size_scales,
        grammar_production_counts=parameters.grammar_production_counts,
        token_byte_lengths=parameters.token_byte_lengths,
        proposal_counts=parameters.proposal_counts,
    )
    run_directory = (
        _default_run_directory(parameters.raw_output_root, config.experiment_id)
        if arguments.run_directory is None
        else arguments.run_directory
    )
    save_resolved_config(config, run_directory)
    metadata = capture_run_metadata(
        config,
        run_id=run_directory.name,
        repository_root=REPOSITORY_ROOT,
        grammar_sha256=tuple(scaling_point_grammar_sha256(point) for point in points),
        require_rust=True,
        additional={
            "point_count": len(points),
            "timeout_enforcement": (
                "fresh_subprocess_wall_deadline_for_both_backends_plus_native_rust_deadline"
            ),
            "timing_scope": "component_profiled_cpu_smoke_not_publication_benchmark",
        },
    )
    result = run_q4_scaling(
        points,
        backends=parameters.backends,
        repetitions=config.repetitions,
        solver_timeout_seconds=config.solver_timeout_seconds,
        run_timeout_seconds=config.run_timeout_seconds,
        address_space_limit_bytes=parameters.address_space_limit_bytes,
        run_metadata=metadata,
    )
    summary = result.summary_dict()
    backend_status_counts = summary["backend_status_counts"]
    if not isinstance(backend_status_counts, Mapping):
        raise TypeError("Q4 summary omitted backend status counts")
    metadata = finalize_run_metadata(
        metadata,
        solver_status_counts=backend_status_counts,
        publication_mode=config.publication_mode,
    )
    result = replace(result, run_metadata=metadata)
    raw_path, plot_path, summary_path = write_q4_artifacts(result, run_directory)
    if arguments.summary_output is not None:
        _copy_summary(summary_path, arguments.summary_output)
    summary = result.summary_dict()
    print(
        json.dumps(
            {
                "run_directory": str(run_directory),
                "raw_rows": str(raw_path),
                "plot_rows": str(plot_path),
                "summary": str(summary_path),
                "measurement_count": len(result.measurements),
                "censored_count": summary["censored_count"],
                "failed_row_count": result.failed_rows,
                "backend_mismatch_count": summary["backend_mismatch_count"],
            },
            sort_keys=True,
        )
    )
    return 1 if result.failed_rows or summary["backend_mismatch_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
