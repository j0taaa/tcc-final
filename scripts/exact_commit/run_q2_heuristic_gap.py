#!/usr/bin/env python3
"""Run the configured Q2 component-selector optimality-gap experiment."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path

from mwpc_exact import ExactBackend, ProposalWeightMode, replay_benchmark_instance
from mwpc_exact.evaluation.epic_regular_cover import EPIC_UPSTREAM_COMMIT
from mwpc_exact.experiments import (
    ExperimentKind,
    capture_run_metadata,
    finalize_run_metadata,
    load_experiment_config,
    save_resolved_config,
)
from mwpc_research.q2_gap import (
    Q2_CASE_IDS,
    Q2_COMPONENT_SELECTORS,
    Q2WeightedInstance,
    configured_q2_instances,
    run_q2_gap_instances,
    write_q2_artifacts,
)

sys.dont_write_bytecode = True

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q2_heuristic_gap_v1.toml"


def _grammar_hashes(instances: Sequence[Q2WeightedInstance]) -> tuple[str, ...]:
    return tuple(instance.benchmark_instance.grammar.fingerprint for instance in instances)


def _string_sequence(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence")
    items = tuple(value)
    if not items or not all(isinstance(item, str) and item for item in items):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return items


def _positive_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _configuration_parameters(
    parameters: Mapping[str, object],
) -> tuple[tuple[ProposalWeightMode, ...], int, bool, int, str, str]:
    required = {
        "case_ids",
        "selectors",
        "weight_modes",
        "exact_backend",
        "brute_force_max_completions",
        "epic_exact_shrink",
        "epic_minimum_batch_size",
        "failure_directory",
        "raw_output_root",
    }
    if set(parameters) != required:
        raise ValueError("Q2 parameters must contain exactly: " + ", ".join(sorted(required)))
    case_ids = _string_sequence(parameters["case_ids"], "parameters.case_ids")
    selectors = _string_sequence(parameters["selectors"], "parameters.selectors")
    raw_modes = _string_sequence(parameters["weight_modes"], "parameters.weight_modes")
    if case_ids != Q2_CASE_IDS:
        raise ValueError(f"Q2 case_ids must be {Q2_CASE_IDS!r}")
    if selectors != Q2_COMPONENT_SELECTORS:
        raise ValueError(f"Q2 selectors must be {Q2_COMPONENT_SELECTORS!r}")
    try:
        modes = tuple(ProposalWeightMode(mode) for mode in raw_modes)
    except ValueError as error:
        raise ValueError("Q2 weight_modes must contain only unit and confidence") from error
    if modes != (ProposalWeightMode.UNIT, ProposalWeightMode.CONFIDENCE):
        raise ValueError("Q2 must evaluate unit and confidence weighting separately")
    if parameters["exact_backend"] != "rust":
        raise ValueError("Q2 exact_backend must be rust")
    brute_force_limit = _positive_integer(
        parameters["brute_force_max_completions"],
        "parameters.brute_force_max_completions",
    )
    exact_shrink = parameters["epic_exact_shrink"]
    if not isinstance(exact_shrink, bool) or exact_shrink is not True:
        raise ValueError("Q2 requires the pinned EPIC exact-shrink check")
    minimum_batch = _positive_integer(
        parameters["epic_minimum_batch_size"],
        "parameters.epic_minimum_batch_size",
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
        raise ValueError("parameters.raw_output_root must be repository-relative")
    return modes, brute_force_limit, exact_shrink, minimum_batch, failure_directory, raw_output_root


@contextmanager
def _epic_environment(*, exact_shrink: bool, minimum_batch: int) -> Iterator[None]:
    updates = {
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT": "1" if exact_shrink else "0",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH": str(minimum_batch),
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


def _default_run_directory(raw_output_root: str, experiment_id: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return REPOSITORY_ROOT / raw_output_root / f"{experiment_id}-{timestamp}"


def _copy_summary(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as input_file, destination.open("xb") as output_file:
        shutil.copyfileobj(input_file, output_file)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay common synthetic states through Q2 component selectors."
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
    if config.question is not ExperimentKind.HEURISTIC_GAP:
        raise ValueError("Q2 driver requires a heuristic_gap configuration")
    if config.repetitions != 1:
        raise ValueError("Q2 smoke currently requires repetitions = 1")
    if len(config.seeds) != 1:
        raise ValueError("Q2 currently requires exactly one seed_start")
    (
        weight_modes,
        brute_force_limit,
        exact_shrink,
        minimum_batch,
        failure_name,
        raw_output_root,
    ) = _configuration_parameters(config.parameters)
    import_module("mwpc_parser_py")
    import_module("constrained_diffusion.regular_cover")
    import_module("rustformlang.cfg")

    run_directory = (
        _default_run_directory(raw_output_root, config.experiment_id)
        if arguments.run_directory is None
        else arguments.run_directory
    )
    save_resolved_config(config, run_directory)
    instances = configured_q2_instances(
        seed_start=config.seeds[0],
        weight_modes=weight_modes,
    )
    metadata = capture_run_metadata(
        config,
        run_id=run_directory.name,
        repository_root=REPOSITORY_ROOT,
        grammar_sha256=_grammar_hashes(instances),
        require_rust=True,
        additional={
            "dataset": "configured_synthetic_q2_states_v1",
            "component_selectors": list(Q2_COMPONENT_SELECTORS),
            "exact_backend": "rust",
            "epic_upstream_commit": EPIC_UPSTREAM_COMMIT,
            "epic_exact_shrink": exact_shrink,
            "epic_minimum_batch_size": minimum_batch,
            "timing_scope": "single_repetition_smoke_not_publication_benchmark",
        },
    )
    with _epic_environment(exact_shrink=exact_shrink, minimum_batch=minimum_batch):
        result = run_q2_gap_instances(
            instances,
            replay=lambda instance: replay_benchmark_instance(
                instance,
                backend=ExactBackend.RUST,
                selector_timeout_seconds=config.solver_timeout_seconds,
                brute_force_max_completions=brute_force_limit,
            ),
            run_metadata=metadata,
            failure_directory=run_directory / failure_name,
            run_timeout_seconds=config.run_timeout_seconds,
        )
    summary = result.summary_dict()
    weight_summaries = summary["weight_modes"]
    if not isinstance(weight_summaries, Mapping):
        raise TypeError("Q2 summary omitted weight-mode status counts")
    solver_status_counts: dict[str, object] = {}
    for mode, mode_summary in weight_summaries.items():
        if not isinstance(mode, str) or not isinstance(mode_summary, Mapping):
            raise TypeError("Q2 weight-mode summary is malformed")
        selectors = mode_summary.get("selectors")
        if not isinstance(selectors, Mapping):
            raise TypeError("Q2 selector summary is malformed")
        selector_counts: dict[str, object] = {}
        for selector, selector_summary in selectors.items():
            if not isinstance(selector, str) or not isinstance(selector_summary, Mapping):
                raise TypeError("Q2 selector summary is malformed")
            status_counts = selector_summary.get("status_counts")
            if not isinstance(status_counts, Mapping):
                raise TypeError("Q2 selector summary omitted status counts")
            selector_counts[selector] = status_counts
        solver_status_counts[mode] = selector_counts
    metadata = finalize_run_metadata(
        metadata,
        solver_status_counts=solver_status_counts,
        publication_mode=config.publication_mode,
    )
    result = replace(result, run_metadata=metadata)
    raw_path, summary_path = write_q2_artifacts(result, run_directory)
    if arguments.summary_output is not None:
        _copy_summary(summary_path, arguments.summary_output)
    print(
        json.dumps(
            {
                "run_directory": str(run_directory),
                "raw_rows": str(raw_path),
                "summary": str(summary_path),
                "case_count": len(result.records),
                "failed_cases": result.failed_cases,
            },
            sort_keys=True,
        )
    )
    return 1 if result.failed_cases else 0


if __name__ == "__main__":
    raise SystemExit(main())
