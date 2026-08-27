#!/usr/bin/env python3
"""Run the configured Q1 exactness experiment and fail on disagreement."""

from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path

from mwpc_exact import ExactBackend
from mwpc_exact.experiments import (
    ExperimentKind,
    canonical_json_sha256,
    capture_run_metadata,
    finalize_run_metadata,
    load_experiment_config,
    save_resolved_config,
)
from mwpc_research.finite_differential import check_finite_lattice_instance
from mwpc_research.q1_correctness import (
    Q1Case,
    Q1CaseFamily,
    configured_q1_cases,
    run_q1_correctness_cases,
    write_q1_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q1_correctness_v1.toml"
EXPECTED_CAMPAIGNS = tuple(family.value for family in Q1CaseFamily)
EXPECTED_SOLVERS = ("exhaustive_oracle", "python_reference", "rust_production")


def _grammar_hashes(cases: Sequence[Q1Case]) -> tuple[str, ...]:
    return tuple(canonical_json_sha256(case.instance.grammar.to_dict()) for case in cases)


def _string_sequence(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence")
    result = tuple(value)
    if not result or not all(isinstance(item, str) and item for item in result):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return result


def _positive_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _configuration_parameters(parameters: Mapping[str, object]) -> tuple[int, str, str]:
    required = {
        "campaigns",
        "solvers",
        "random_case_count",
        "failure_directory",
        "raw_output_root",
    }
    if set(parameters) != required:
        raise ValueError(
            "Q1 parameters must contain exactly: " + ", ".join(sorted(required))
        )
    campaigns = _string_sequence(parameters["campaigns"], "parameters.campaigns")
    solvers = _string_sequence(parameters["solvers"], "parameters.solvers")
    if campaigns != EXPECTED_CAMPAIGNS:
        raise ValueError(f"Q1 campaigns must be {EXPECTED_CAMPAIGNS!r}")
    if solvers != EXPECTED_SOLVERS:
        raise ValueError(f"Q1 solvers must be {EXPECTED_SOLVERS!r}")
    random_case_count = _positive_integer(
        parameters["random_case_count"], "parameters.random_case_count"
    )
    failure_directory = parameters["failure_directory"]
    raw_output_root = parameters["raw_output_root"]
    if not isinstance(failure_directory, str) or not failure_directory.strip():
        raise ValueError("parameters.failure_directory must be a non-empty string")
    if Path(failure_directory).is_absolute() or Path(failure_directory).name != failure_directory:
        raise ValueError("parameters.failure_directory must be one relative directory name")
    if not isinstance(raw_output_root, str) or not raw_output_root.strip():
        raise ValueError("parameters.raw_output_root must be a non-empty string")
    if Path(raw_output_root).is_absolute():
        raise ValueError("parameters.raw_output_root must be relative to the repository")
    return random_case_count, failure_directory, raw_output_root


def _default_run_directory(raw_output_root: str, experiment_id: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return REPOSITORY_ROOT / raw_output_root / f"{experiment_id}-{timestamp}"


def _copy_summary(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as input_file, destination.open("xb") as output_file:
        shutil.copyfileobj(input_file, output_file)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare exhaustive token paths with independent Python and Rust "
            "finite-lattice solvers."
        )
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="optional immutable copy of the computed run summary",
    )
    arguments = parser.parse_args(argv)

    config = load_experiment_config(arguments.config)
    if config.question is not ExperimentKind.CORRECTNESS:
        raise ValueError("Q1 driver requires a correctness experiment configuration")
    if config.repetitions != 1:
        raise ValueError("Q1 correctness currently requires repetitions = 1")
    if len(config.seeds) != 1:
        raise ValueError("Q1 correctness currently requires exactly one seed_start")
    random_case_count, failure_name, raw_output_root = _configuration_parameters(
        config.parameters
    )
    import_module("mwpc_parser_py")

    run_directory = (
        _default_run_directory(raw_output_root, config.experiment_id)
        if arguments.run_directory is None
        else arguments.run_directory
    )
    run_id = run_directory.name
    save_resolved_config(config, run_directory)
    cases = configured_q1_cases(
        seed_start=config.seeds[0],
        random_case_count=random_case_count,
    )
    metadata = capture_run_metadata(
        config,
        run_id=run_id,
        repository_root=REPOSITORY_ROOT,
        grammar_sha256=_grammar_hashes(cases),
        require_rust=True,
        additional={
            "dataset": "synthetic_q1_finite_support",
            "commit_strategy": "exact_mwpc",
            "weight_policy": "nonnegative_integer_proposal_weights",
        },
    )
    result = run_q1_correctness_cases(
        cases,
        checker=lambda instance: check_finite_lattice_instance(
            instance,
            backends=(ExactBackend.PYTHON, ExactBackend.RUST),
            rust_timeout_seconds=config.solver_timeout_seconds,
        ),
        required_solvers=EXPECTED_SOLVERS,
        run_metadata=metadata,
        failure_directory=run_directory / failure_name,
    )
    status_counts = result.summary_dict()["solver_status_counts"]
    if not isinstance(status_counts, Mapping):
        raise TypeError("Q1 summary omitted solver status counts")
    metadata = finalize_run_metadata(
        metadata,
        solver_status_counts=status_counts,
        publication_mode=config.publication_mode,
    )
    result = replace(result, run_metadata=metadata)
    raw_path, summary_path = write_q1_artifacts(result, run_directory)
    if arguments.summary_output is not None:
        _copy_summary(summary_path, arguments.summary_output)
    print(
        json.dumps(
            {
                "run_directory": str(run_directory),
                "raw_cases": str(raw_path),
                "summary": str(summary_path),
                "case_count": len(result.records),
                "failed_cases": result.failed_cases,
                "agreement_rate": result.summary_dict()["agreement_rate"],
            },
            sort_keys=True,
        )
    )
    return 1 if result.failed_cases else 0


if __name__ == "__main__":
    raise SystemExit(main())
