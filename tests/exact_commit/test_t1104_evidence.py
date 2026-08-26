from __future__ import annotations

import json
from pathlib import Path

from mwpc_exact.experiments import load_experiment_config
from mwpc_research.q4_scaling import Q4_AXES

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q4_scaling_v1.toml"
SUMMARY_PATH = REPOSITORY_ROOT / "docs/evidence/t1104-q4-scaling-summary.json"
T1104_IMPLEMENTATION_COMMIT = "66b8b5d7ef908a40ea94018fbe3502cbc3a1c5c1"


def test_checked_in_t1104_summary_matches_the_pinned_q4_config() -> None:
    config = load_experiment_config(CONFIG_PATH)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert summary["artifact_kind"] == "mwpc_q4_scaling_summary"
    assert summary["schema_version"] == 1
    assert summary["measurement_count"] == 84
    assert summary["plot_ready_runtime_count"] == 84
    assert summary["status_counts"] == {"optimal": 84}
    assert summary["backend_status_counts"] == {
        "python": {"optimal": 42},
        "rust": {"optimal": 42},
    }
    assert set(summary["axis_counts"]) == set(Q4_AXES)
    assert summary["backend_comparison_count"] == 42
    assert summary["backend_mismatch_count"] == 0
    assert summary["backend_mismatches"] == []
    assert summary["failed_row_count"] == 0
    assert summary["censored_count"] == 0
    assert summary["timeout_count"] == 0
    assert summary["timeout_plot_runtime_count"] == 0
    assert summary["censoring_integrity"] is True

    metadata = summary["run_metadata"]
    assert metadata["config_sha256"] == config.config_sha256
    assert metadata["git_commit"] == T1104_IMPLEMENTATION_COMMIT
    assert metadata["git_dirty"] is False
    assert metadata["seeds"] == [1104]
    assert metadata["repetitions"] == 2
    assert metadata["point_count"] == 21
    assert metadata["exactness_scope"] == "exact_on_support"
    assert metadata["exactness_guarantee"] == "per_step"
    assert metadata["finite_slots"] is True
    assert metadata["timeout_enforcement"] == (
        "fresh_subprocess_wall_deadline_for_both_backends_plus_native_rust_deadline"
    )
    assert metadata["timing_scope"] == (
        "component_profiled_cpu_smoke_not_publication_benchmark"
    )
