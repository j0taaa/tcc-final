from __future__ import annotations

import json
import math
from pathlib import Path

from mwpc_exact.experiments import load_experiment_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q1_correctness_v1.toml"
SUMMARY_PATH = REPOSITORY_ROOT / "docs/evidence/t1101-q1-correctness-summary.json"
T1101_IMPLEMENTATION_COMMIT = "bd6b4455102f3b1a7603de8096b3380d4733b13e"

EXPECTED_FAMILY_COUNTS = {
    "canonical": 5,
    "exhaustive": 144,
    "randomized": 100,
}
EXPECTED_STATUS_COUNTS = {
    "infeasible_on_support": 82,
    "optimal": 167,
}
EXPECTED_SOLVERS = {
    "exhaustive_oracle",
    "python_reference",
    "rust_production",
}


def test_checked_in_t1101_summary_matches_the_pinned_q1_config() -> None:
    config = load_experiment_config(CONFIG_PATH)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    case_count = sum(EXPECTED_FAMILY_COUNTS.values())

    assert summary["artifact_kind"] == "mwpc_q1_correctness_summary"
    assert summary["schema_version"] == 1
    assert summary["case_count"] == case_count
    assert summary["passed_cases"] == case_count
    assert summary["failed_cases"] == 0
    assert summary["agreement_rate"] == 1.0
    assert summary["failures"] == []
    assert summary["status_counts"] == EXPECTED_STATUS_COUNTS
    assert sum(summary["status_counts"].values()) == case_count

    assert set(summary["families"]) == set(EXPECTED_FAMILY_COUNTS)
    for family, expected_count in EXPECTED_FAMILY_COUNTS.items():
        assert summary["families"][family] == {
            "case_count": expected_count,
            "passed_cases": expected_count,
            "failed_cases": 0,
        }
        assert summary["seed_ranges"][family]["count"] == expected_count

    assert set(summary["solver_status_counts"]) == EXPECTED_SOLVERS
    for solver in EXPECTED_SOLVERS:
        assert summary["solver_status_counts"][solver] == EXPECTED_STATUS_COUNTS

    timings = summary["timing_totals_seconds"]
    assert EXPECTED_SOLVERS <= set(timings)
    assert all(math.isfinite(value) and value >= 0.0 for value in timings.values())

    metadata = summary["run_metadata"]
    assert metadata["config_sha256"] == config.config_sha256
    assert metadata["git_commit"] == T1101_IMPLEMENTATION_COMMIT
    assert metadata["git_dirty"] is False
    assert metadata["exactness_scope"] == "exact_on_support"
    assert metadata["exactness_guarantee"] == "per_step"
    assert metadata["finite_slots"] is True
    assert metadata["support_k_max"] == 6
    assert metadata["solver_timeout_seconds"] == 5.0
