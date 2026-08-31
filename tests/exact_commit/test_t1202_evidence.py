from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from mwpc_research.statistical_artifacts import (
    STATISTICAL_INTERPRETATION,
    STATISTICAL_SUMMARY_KIND,
    build_statistical_artifact,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/analysis/t1202_statistics_v1.toml"
RAW_PATH = REPOSITORY_ROOT / "docs/artifacts/raw/t1202_statistics_v1/statistical-observations.jsonl"
SUMMARY_PATH = (
    REPOSITORY_ROOT / "docs/artifacts/processed/t1202_statistics_v1/statistical-summary.json"
)
RAW_SHA256 = "2f91b80894b45cf9ea7b816d59e7daa95a87bf1dab40dd8ab04ceb36b8c215a9"
SUMMARY_SHA256 = "40b236f2e5988eca6ccdbe9aa2cb22b5df4cda087dfea34bade4f19f6e34a776"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_t1202_summary_is_pinned_computed_and_unit_explicit() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert _sha256(RAW_PATH) == RAW_SHA256
    assert _sha256(SUMMARY_PATH) == SUMMARY_SHA256
    assert summary["artifact_kind"] == STATISTICAL_SUMMARY_KIND
    assert summary["benchmark_claim"] is False
    assert summary["interpretation"] == STATISTICAL_INTERPRETATION
    assert summary["source"] == {
        "path": "docs/artifacts/raw/t1202_statistics_v1/statistical-observations.jsonl",
        "row_count": 6,
        "sha256": RAW_SHA256,
    }

    agreement = summary["agreement"]
    assert agreement["event_count"] == 4
    assert agreement["observation_count"] == 6
    assert agreement["rate"] == pytest.approx(2 / 3)
    assert agreement["confidence_interval_method"] == "wilson_score"
    assert agreement["confidence_interval_lower"] < agreement["rate"]
    assert agreement["confidence_interval_upper"] > agreement["rate"]

    gap = summary["gap"]
    assert gap["equality"]["rate"] == pytest.approx(1 / 3)
    assert gap["absolute_gap"]["count"] == 6
    assert gap["relative_gap"]["count"] == 5
    assert gap["zero_optimum_count"] == 1
    assert gap["relative_gap_undefined_count"] == 1
    assert gap["relative_gap_zero_optimum_policy"] == "undefined_and_excluded"

    runtime = summary["runtime"]
    assert runtime["baseline_runtime_seconds"]["median"] == 1.5
    assert runtime["candidate_runtime_seconds"]["median"] == 2.5
    assert runtime["median_runtime_ratio"] == pytest.approx(5 / 3)
    assert runtime["normalized_median_overhead"] == pytest.approx(2 / 3)
    assert runtime["baseline_median_zero"] is False

    per_step = summary["operational_rates"]["per_step"]
    per_generation = summary["operational_rates"]["per_generation"]
    assert per_step["analysis_unit"] == "optimizer_step"
    assert per_step["observation_count"] == 6
    assert per_step["fallback"]["rate"] == pytest.approx(1 / 6)
    assert per_step["timeout"]["rate"] == pytest.approx(1 / 6)
    assert per_step["support_expansion"]["rate"] == pytest.approx(2 / 6)
    assert per_generation["analysis_unit"] == "generation"
    assert per_generation["observation_count"] == 3
    assert per_generation["fallback"]["rate"] == pytest.approx(1 / 3)
    assert per_generation["timeout"]["rate"] == pytest.approx(1 / 3)
    assert per_generation["support_expansion"]["rate"] == pytest.approx(2 / 3)

    verified = build_statistical_artifact(
        CONFIG_PATH,
        repository_root=REPOSITORY_ROOT,
        verify_existing=True,
    )
    assert verified.source_sha256 == RAW_SHA256
    assert verified.output_sha256 == SUMMARY_SHA256
    assert verified.verified_existing is True
