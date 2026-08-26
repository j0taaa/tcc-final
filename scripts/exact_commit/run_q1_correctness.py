#!/usr/bin/env python3
"""Run the configured Q1 exactness experiment and fail on disagreement."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from importlib import import_module
from importlib.metadata import version
from pathlib import Path

from mwpc_exact import ExactBackend
from mwpc_exact.experiments import (
    ExperimentConfig,
    ExperimentKind,
    load_experiment_config,
    save_resolved_config,
)
from mwpc_research.finite_differential import check_finite_lattice_instance
from mwpc_research.q1_correctness import (
    Q1CaseFamily,
    configured_q1_cases,
    run_q1_correctness_cases,
    write_q1_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q1_correctness_v1.toml"
EXPECTED_CAMPAIGNS = tuple(family.value for family in Q1CaseFamily)
EXPECTED_SOLVERS = ("exhaustive_oracle", "python_reference", "rust_production")


def _command_output(command: Sequence[str]) -> str:
    return subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


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


def _run_metadata(
    *, config_hash: str, run_id: str, config: ExperimentConfig
) -> dict[str, object]:
    git_status = _command_output(["git", "status", "--porcelain"])
    return {
        "run_id": run_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_commit": _command_output(["git", "rev-parse", "HEAD"]),
        "git_dirty": bool(git_status),
        "config_sha256": config_hash,
        "exactness_scope": config.exactness_scope,
        "exactness_guarantee": config.exactness_guarantee,
        "support_policy": config.support_policy,
        "support_top_k": config.support_top_k,
        "support_k_max": config.support_k_max,
        "finite_slots": config.finite_slots,
        "model_id": config.model_id,
        "model_revision": config.model_revision,
        "tokenizer_id": config.tokenizer_id,
        "tokenizer_revision": config.tokenizer_revision,
        "grammar_hash_policy": config.grammar_hash_policy,
        "dataset": "synthetic_q1_finite_support",
        "commit_strategy": "exact_mwpc",
        "weight_policy": "nonnegative_integer_proposal_weights",
        "solver_timeout_seconds": config.solver_timeout_seconds,
        "run_timeout_seconds": config.run_timeout_seconds,
        "hardware": {
            "device": config.device,
            "dtype": config.dtype,
            "cpu_threads": config.cpu_threads,
            "cuda_device": config.cuda_device,
            "synchronize_cuda": config.synchronize_cuda,
            "machine": platform.machine() or "unknown",
            "processor": platform.processor() or "unknown",
        },
        "software_versions": {
            "python": platform.python_version(),
            "mwpc_exact": version("mwpc-exact"),
            "mwpc_parser_py": version("mwpc-parser-py"),
            "rust": _command_output(["rustc", "--version"]),
            "platform": platform.platform(),
        },
    }


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
    metadata = _run_metadata(
        config_hash=config.config_sha256,
        run_id=run_id,
        config=config,
    )
    cases = configured_q1_cases(
        seed_start=config.seeds[0],
        random_case_count=random_case_count,
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
