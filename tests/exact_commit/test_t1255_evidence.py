from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.exact_commit.summarize_q4_publication import summarize_campaign

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q4_scaling_publication_v1.toml"
RAW_PATH = (
    REPOSITORY_ROOT
    / "docs/artifacts/raw/m125_publication_results_v1/q4-scaling-rows.jsonl"
)
SUMMARY_PATH = REPOSITORY_ROOT / "docs/evidence/t1255-q4-publication-summary.json"
DIAGNOSTIC_RESULTS_PATH = (
    REPOSITORY_ROOT
    / "docs/artifacts/processed/t1203_final_results_v1/final-results.json"
)
DIAGNOSTIC_FIGURE_PATH = (
    REPOSITORY_ROOT / "paper/generated/t1203_final_results_v1/runtime-scaling.svg"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_t1255_publication_scaling_rows_are_complete_paired_and_revalidated() -> None:
    checked = summarize_campaign(CONFIG_PATH, RAW_PATH)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert _sha256(RAW_PATH) == (
        "63abf6a974bdd74f20b34f7f80e9c3d646a30f9385f359a76a4747c86f8eef51"
    )
    assert _sha256(SUMMARY_PATH) == (
        "8570ee64c462a8139302867be56a8abc3c7f116cbb589f363a4c29807b5505f1"
    )
    for result in (checked, summary):
        assert result["producing_commit"] == (
            "a4ea377570d730a32000cf376f29ff500da84a3b"
        )
        assert result["point_count"] == 27
        assert result["measurement_count"] == 540
        assert result["configured_repetitions_per_backend_point"] == 10
        assert result["minimum_repetitions_for_distribution"] == 10
        assert result["status_counts"] == {"optimal": 540}
        assert result["backend_status_counts"] == {
            "python": {"optimal": 270},
            "rust": {"optimal": 270},
        }
        assert result["censored_count"] == 0
        assert result["timeout_count"] == 0
        assert result["error_count"] == 0
        assert result["backend_comparison_count"] == 270
        assert result["backend_mismatch_count"] == 0
        assert result["all_optimal_certificates_independently_rechecked"] is True
        assert result["graph_size_scale_interpretation"] == (
            "compound_support_width_and_token_byte_length"
        )
        assert len(result["scaling_series"]) == 54
        assert all(
            row["successful_runtime_count"] == 10
            and row["censored_count"] == 0
            and row["distribution_status"] == "available"
            and row["runtime_seconds"]["count"] == 10
            for row in result["scaling_series"]
        )

    assert summary["pinned_raw_sha256"] == _sha256(RAW_PATH)
    assert summary["axis_values"] == {
        "grammar_production_count": [4, 8, 16, 32],
        "graph_size_scale": [1, 2, 4, 8],
        "proposal_count": [1, 2, 4, 8, 16],
        "slot_count": [1, 2, 4, 8, 16],
        "token_byte_length": [1, 2, 4, 8],
        "top_k": [1, 2, 4, 8, 16],
    }


def test_t1255_old_two_repetition_smoke_withholds_scaling_distributions() -> None:
    results = json.loads(DIAGNOSTIC_RESULTS_PATH.read_text(encoding="utf-8"))
    runtime = results["runtime_breakdown"]
    figure = DIAGNOSTIC_FIGURE_PATH.read_text(encoding="utf-8")

    assert runtime["interpretation"] == (
        "component_profiled_cpu_smoke_not_publication_benchmark"
    )
    assert runtime["minimum_repetitions_for_distribution"] == 10
    assert runtime["withheld_scaling_point_count"] == 42
    assert all(
        point["runtime_seconds"] is None
        and point["distribution_status"] == "withheld_insufficient_repetitions"
        for series in runtime["scaling_series"]
        for point in series["points"]
    )
    assert "Median/IQR curves withheld" in figure
    assert "graph_size_scale is compound" in figure
