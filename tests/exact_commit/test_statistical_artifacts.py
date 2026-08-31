from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from mwpc_research.statistical_artifacts import (
    STATISTICAL_INTERPRETATION,
    STATISTICAL_OBSERVATION_KIND,
    STATISTICAL_SUMMARY_KIND,
    build_statistical_artifact,
    load_statistical_observations,
    summarize_statistical_observations,
)


def _event(
    *,
    fallback: bool = False,
    timeout: bool = False,
    expansion: bool = False,
) -> dict[str, bool]:
    return {
        "fallback_used": fallback,
        "timed_out": timeout,
        "support_expanded": expansion,
    }


def _row(
    observation_id: str,
    generation_id: str,
    *,
    agreement: bool,
    exact_score: float,
    comparator_score: float,
    baseline_runtime: float,
    candidate_runtime: float,
    step_events: dict[str, bool],
    generation_events: dict[str, bool],
) -> dict[str, object]:
    return {
        "artifact_kind": STATISTICAL_OBSERVATION_KIND,
        "schema_version": 1,
        "observation_id": observation_id,
        "generation_id": generation_id,
        "agreement": agreement,
        "exact_score": exact_score,
        "comparator_score": comparator_score,
        "baseline_runtime_seconds": baseline_runtime,
        "candidate_runtime_seconds": candidate_runtime,
        "step_events": step_events,
        "generation_events": generation_events,
    }


def _write_repository(root: Path) -> tuple[Path, Path]:
    generation_zero = _event(fallback=True, expansion=True)
    rows = (
        _row(
            "step-0",
            "generation-0",
            agreement=True,
            exact_score=0.0,
            comparator_score=0.0,
            baseline_runtime=0.0,
            candidate_runtime=2.0,
            step_events=_event(fallback=True),
            generation_events=generation_zero,
        ),
        _row(
            "step-1",
            "generation-0",
            agreement=False,
            exact_score=2.0,
            comparator_score=1.0,
            baseline_runtime=1.0,
            candidate_runtime=2.0,
            step_events=_event(expansion=True),
            generation_events=generation_zero,
        ),
        _row(
            "step-2",
            "generation-1",
            agreement=True,
            exact_score=4.0,
            comparator_score=4.0,
            baseline_runtime=2.0,
            candidate_runtime=4.0,
            step_events=_event(timeout=True),
            generation_events=_event(timeout=True),
        ),
    )
    input_path = root / "raw/statistical-observations.jsonl"
    input_path.parent.mkdir(parents=True)
    payload = b"".join(
        (json.dumps(row, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n").encode(
            "utf-8"
        )
        for row in rows
    )
    input_path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    config_path = root / "configs/statistics.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "\n".join(
            (
                "schema_version = 1",
                'artifact_id = "statistics_test_v1"',
                'input_jsonl = "raw/statistical-observations.jsonl"',
                f'expected_sha256 = "{digest}"',
                'output_json = "processed/statistical-summary.json"',
                "confidence_level = 0.95",
                "",
            )
        ),
        encoding="utf-8",
    )
    return config_path, input_path


def test_build_and_verify_statistical_artifact_from_pinned_raw_rows(tmp_path: Path) -> None:
    config_path, _ = _write_repository(tmp_path)

    created = build_statistical_artifact(config_path, repository_root=tmp_path)
    summary = json.loads(created.output_path.read_text(encoding="utf-8"))

    assert summary["artifact_kind"] == STATISTICAL_SUMMARY_KIND
    assert summary["benchmark_claim"] is False
    assert summary["interpretation"] == STATISTICAL_INTERPRETATION
    assert summary["observation_count"] == 3
    assert summary["generation_count"] == 2
    assert summary["agreement"]["rate"] == pytest.approx(2 / 3)
    assert summary["gap"]["zero_optimum_count"] == 1
    assert summary["gap"]["relative_gap_defined_count"] == 2
    assert summary["runtime"]["median_runtime_ratio"] == 2.0
    assert summary["runtime"]["normalized_median_overhead"] == 1.0
    assert summary["operational_rates"]["per_step"]["fallback"]["rate"] == (pytest.approx(1 / 3))
    assert summary["operational_rates"]["per_generation"]["fallback"]["rate"] == 0.5

    verified = build_statistical_artifact(
        config_path,
        repository_root=tmp_path,
        verify_existing=True,
    )
    assert verified.verified_existing is True
    assert verified.output_sha256 == created.output_sha256

    created.output_path.write_text("edited\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs from raw input"):
        build_statistical_artifact(
            config_path,
            repository_root=tmp_path,
            verify_existing=True,
        )


def test_statistical_artifact_rejects_changed_raw_hash(tmp_path: Path) -> None:
    config_path, input_path = _write_repository(tmp_path)
    input_path.write_text(
        json.dumps(
            _row(
                "changed",
                "generation-0",
                agreement=True,
                exact_score=1.0,
                comparator_score=1.0,
                baseline_runtime=1.0,
                candidate_runtime=1.0,
                step_events=_event(),
                generation_events=_event(),
            ),
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="hash mismatch"):
        build_statistical_artifact(config_path, repository_root=tmp_path)


def test_statistical_artifact_keeps_raw_and_processed_directories_separate(
    tmp_path: Path,
) -> None:
    config_path, _ = _write_repository(tmp_path)
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'output_json = "processed/statistical-summary.json"',
            'output_json = "raw/derived/statistical-summary.json"',
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be non-nested"):
        build_statistical_artifact(config_path, repository_root=tmp_path)


def test_statistical_rows_require_consistent_generation_flags(tmp_path: Path) -> None:
    _, input_path = _write_repository(tmp_path)
    rows = [json.loads(line) for line in input_path.read_text().splitlines()]
    rows[1]["generation_events"]["timed_out"] = True
    input_path.write_text(
        "".join(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="agree within each generation"):
        load_statistical_observations(input_path)


def test_statistical_rows_reject_boolean_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "invalid.jsonl"
    row = _row(
        "step-0",
        "generation-0",
        agreement=True,
        exact_score=1.0,
        comparator_score=1.0,
        baseline_runtime=1.0,
        candidate_runtime=1.0,
        step_events=_event(),
        generation_events=_event(),
    )
    row["schema_version"] = True
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(TypeError, match="schema_version must be an integer"):
        load_statistical_observations(path)


def test_direct_statistical_summary_rejects_duplicate_observation_ids(
    tmp_path: Path,
) -> None:
    _, input_path = _write_repository(tmp_path)
    observations = load_statistical_observations(input_path)

    with pytest.raises(ValueError, match="IDs must be unique"):
        summarize_statistical_observations((observations[0], observations[0]))
