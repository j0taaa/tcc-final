#!/usr/bin/env python3
"""Run the configured Q3 abstract-versus-finite-slot experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from mwpc_exact.experiments import (
    ExperimentKind,
    canonical_json_sha256,
    capture_run_metadata,
    finalize_run_metadata,
    load_experiment_config,
    save_resolved_config,
)
from mwpc_research.finite_slot_counterexamples import (
    ABSTRACT_SIGMA_STAR_SEMANTICS,
    load_finite_slot_counterexamples,
)
from mwpc_research.q3_finite_slots import (
    Q3_CASE_IDS,
    run_q3_finite_slot_cases,
    write_q3_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q3_finite_slots_v1.toml"
EXPECTED_ABSTRACT_BASELINE = "ordered_anchor_sigma_star"
EXPECTED_FINITE_SOLVER = "python_reference_plus_exhaustive_path_enumeration"


def _string_sequence(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence")
    items = tuple(value)
    if not items or not all(isinstance(item, str) and item for item in items):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return items


def _relative_path(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field_name} must be repository-relative")
    return value


def _configuration_parameters(
    parameters: Mapping[str, object],
) -> tuple[str, bool, str]:
    required = {
        "case_ids",
        "abstract_baseline",
        "finite_solver",
        "mine_real_decoder_states",
        "raw_output_root",
    }
    if set(parameters) != required:
        raise ValueError("Q3 parameters must contain exactly: " + ", ".join(sorted(required)))
    case_ids = _string_sequence(parameters["case_ids"], "parameters.case_ids")
    if case_ids != Q3_CASE_IDS:
        raise ValueError(f"Q3 case_ids must be {Q3_CASE_IDS!r}")
    if parameters["abstract_baseline"] != EXPECTED_ABSTRACT_BASELINE:
        raise ValueError(f"Q3 abstract_baseline must be {EXPECTED_ABSTRACT_BASELINE!r}")
    if parameters["finite_solver"] != EXPECTED_FINITE_SOLVER:
        raise ValueError(f"Q3 finite_solver must be {EXPECTED_FINITE_SOLVER!r}")
    mine_real = parameters["mine_real_decoder_states"]
    if not isinstance(mine_real, bool) or mine_real:
        raise ValueError("Q3 v1 is a curated-only experiment and must not mine real states")
    raw_output_root = _relative_path(parameters["raw_output_root"], "parameters.raw_output_root")
    return raw_output_root, mine_real, EXPECTED_FINITE_SOLVER


def _default_run_directory(raw_output_root: str, experiment_id: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return REPOSITORY_ROOT / raw_output_root / f"{experiment_id}-{timestamp}"


def _copy_summary(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as input_file, destination.open("xb") as output_file:
        shutil.copyfileobj(input_file, output_file)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare curated abstract Sigma-star witnesses with finite-slot results."
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
    if config.question is not ExperimentKind.FINITE_SLOTS:
        raise ValueError("Q3 driver requires a finite_slots configuration")
    if config.repetitions != 1:
        raise ValueError("Q3 curated experiment requires repetitions = 1")
    if config.seeds != (1103,):
        raise ValueError("Q3 curated experiment requires the frozen seed 1103")
    raw_output_root, mine_real, finite_solver = _configuration_parameters(config.parameters)
    fixture_relative = _relative_path(config.grammar_source, "grammar.source")
    fixture_path = (REPOSITORY_ROOT / fixture_relative).resolve()
    if not fixture_path.is_relative_to(REPOSITORY_ROOT):
        raise ValueError("grammar.source resolves outside the repository")
    fixture_sha256 = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    cases = load_finite_slot_counterexamples(fixture_path)
    if tuple(case.case_id for case in cases) != Q3_CASE_IDS:
        raise ValueError("Q3 fixture cases differ from the configured case_ids")

    run_directory = (
        _default_run_directory(raw_output_root, config.experiment_id)
        if arguments.run_directory is None
        else arguments.run_directory
    )
    save_resolved_config(config, run_directory)
    metadata = capture_run_metadata(
        config,
        run_id=run_directory.name,
        repository_root=REPOSITORY_ROOT,
        grammar_sha256=tuple(canonical_json_sha256(case.grammar.to_dict()) for case in cases),
        require_rust=False,
        additional={
            "dataset": "curated_t703_counterexamples_v1",
            "source_fixture_path": fixture_relative,
            "source_fixture_sha256": fixture_sha256,
            "case_ids": list(Q3_CASE_IDS),
            "real_decoder_states_mined": mine_real,
            "abstract_baseline": EXPECTED_ABSTRACT_BASELINE,
            "abstract_sigma_star_semantics": ABSTRACT_SIGMA_STAR_SEMANTICS,
            "finite_solver": finite_solver,
            "independent_oracle": "complete_finite_eos_lattice_path_enumeration",
            "timeout_enforcement": (
                "post_replay_case_deadline_and_between_case_run_deadline; "
                "tiny_python_reference_replay_is_not_preemptible"
            ),
            "timing_scope": "single_repetition_smoke_not_publication_benchmark",
        },
    )
    result = run_q3_finite_slot_cases(
        cases,
        run_metadata=metadata,
        fixture_path=fixture_relative,
        fixture_sha256=fixture_sha256,
        case_timeout_seconds=config.solver_timeout_seconds,
        run_timeout_seconds=config.run_timeout_seconds,
    )
    summary = result.summary_dict()
    finite_status_counts = summary["finite_status_counts"]
    abstract_accept_count = summary["abstract_accept_count"]
    if not isinstance(finite_status_counts, Mapping) or not isinstance(abstract_accept_count, int):
        raise TypeError("Q3 summary omitted solver status counts")
    metadata = finalize_run_metadata(
        metadata,
        solver_status_counts={
            "abstract_sigma_star": {
                "accept": abstract_accept_count,
                "reject": len(result.records) - abstract_accept_count,
            },
            "finite_exact_on_support": finite_status_counts,
        },
        publication_mode=config.publication_mode,
    )
    result = replace(result, run_metadata=metadata)
    raw_path, summary_path = write_q3_artifacts(result, run_directory)
    if arguments.summary_output is not None:
        _copy_summary(summary_path, arguments.summary_output)
    summary = result.summary_dict()
    print(
        json.dumps(
            {
                "run_directory": str(run_directory),
                "raw_rows": str(raw_path),
                "summary": str(summary_path),
                "case_count": len(result.records),
                "failed_cases": result.failed_cases,
                "finite_slot_false_positive_count": summary["finite_slot_false_positive_count"],
            },
            sort_keys=True,
        )
    )
    return 1 if result.failed_cases else 0


if __name__ == "__main__":
    raise SystemExit(main())
