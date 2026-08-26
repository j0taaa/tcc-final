from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from mwpc_exact.experiments import load_experiment_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q2_heuristic_gap_v1.toml"
SUMMARY_PATH = REPOSITORY_ROOT / "docs/evidence/t1102-q2-heuristic-gap-summary.json"
T1102_IMPLEMENTATION_COMMIT = "a8b4e7c499dbf67c7f33a5110e95b4b02738729d"
EPIC_UPSTREAM_COMMIT = "5b1b31098f34ed3691d2a9f4aae14fdf5839d072"

EXPECTED_CASE_KIND_COUNTS = {
    "canonical": 2,
    "crafted_adversarial": 4,
}
EXPECTED_AGGREGATES = {
    "unit": {
        "exact_mwpc": (7.0, 7, None, None),
        "greedy_exact_feasibility": (5.0, 5, 1, 1.0),
        "epic_regular_cover": (3.0, 3, 1, 2.0),
    },
    "confidence": {
        "exact_mwpc": (4.4, 6, None, None),
        "greedy_exact_feasibility": (4.2, 5, 2, 0.2),
        "epic_regular_cover": (2.4, 3, 1, 1.1),
    },
}
EXPECTED_STATUS_COUNTS = {
    "exact_mwpc": {"optimal": 3},
    "greedy_exact_feasibility": {"feasible_on_support": 3},
    "epic_regular_cover": {"heuristic": 3},
}


def test_checked_in_t1102_summary_matches_the_pinned_q2_config() -> None:
    config = load_experiment_config(CONFIG_PATH)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert summary["artifact_kind"] == "mwpc_q2_heuristic_gap_summary"
    assert summary["schema_version"] == 1
    assert summary["case_count"] == 6
    assert summary["common_instance_count"] == 3
    assert summary["case_kind_counts"] == EXPECTED_CASE_KIND_COUNTS
    assert summary["passed_cases"] == 6
    assert summary["failed_cases"] == 0
    assert summary["failures"] == []

    metadata = summary["run_metadata"]
    assert metadata["config_sha256"] == config.config_sha256
    assert metadata["git_commit"] == T1102_IMPLEMENTATION_COMMIT
    assert metadata["git_dirty"] is False
    assert metadata["epic_upstream_commit"] == EPIC_UPSTREAM_COMMIT
    assert metadata["component_selectors"] == [
        "greedy_exact_feasibility",
        "epic_regular_cover",
        "exact_mwpc",
    ]
    assert metadata["exact_backend"] == "rust"
    assert metadata["exactness_scope"] == "exact_on_support"
    assert metadata["exactness_guarantee"] == "per_step"
    assert metadata["finite_slots"] is True
    assert metadata["epic_exact_shrink"] is True
    assert metadata["epic_minimum_batch_size"] == 2
    assert metadata["timing_scope"] == "single_repetition_smoke_not_publication_benchmark"

    assert set(summary["weight_modes"]) == set(EXPECTED_AGGREGATES)
    for weight_mode, expected_selectors in EXPECTED_AGGREGATES.items():
        mode_summary = summary["weight_modes"][weight_mode]
        assert mode_summary["case_count"] == 3
        assert set(mode_summary["selectors"]) == set(expected_selectors)

        for selector, expected in expected_selectors.items():
            total_score, total_cardinality, equality_count, maximum_gap = expected
            selector_summary = mode_summary["selectors"][selector]
            assert selector_summary["case_count"] == 3
            assert selector_summary["status_counts"] == EXPECTED_STATUS_COUNTS[selector]
            assert selector_summary["total_score"] == pytest.approx(total_score)
            assert selector_summary["total_cardinality"] == total_cardinality
            runtime = selector_summary["total_runtime_seconds"]
            assert math.isfinite(runtime) and runtime >= 0.0

            if equality_count is not None:
                assert selector_summary["equality_count"] == equality_count
                assert selector_summary["equality_rate"] == pytest.approx(equality_count / 3)
                assert selector_summary["maximum_absolute_gap"] == pytest.approx(maximum_gap)

