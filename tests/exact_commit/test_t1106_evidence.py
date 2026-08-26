from __future__ import annotations

import json
from pathlib import Path

from mwpc_research.q5_end_to_end import Q5_STRATEGIES

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = REPOSITORY_ROOT / "docs/evidence/t1106-q5-timing-summary.json"


def test_t1106_live_timing_evidence_is_clean_balanced_and_complete() -> None:
    summary = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    metadata = summary["run_metadata"]
    protocol = metadata["timing_protocol"]

    assert summary["benchmark_claim"] is False
    assert summary["measurement_count"] == 32
    assert summary["repetition_count"] == 8
    assert summary["recorded_repetitions"] == list(range(8))
    assert summary["execution_status_counts"] == {"complete": 32}
    assert summary["exact_solver_status_counts"] == {"optimal": 8}
    assert summary["failed_record_count"] == 0
    assert summary["required_contract_failure_count"] == 0
    assert summary["all_required_methods_passed"] is True
    assert metadata["git_commit"] == "83ba41d1a29d84d8147319d33b85c6646d743b8e"
    assert metadata["git_dirty"] is False
    assert metadata["config_path"] == "configs/experiments/q5_timing_v1.toml"
    assert metadata["config_sha256"] == (
        "ef284d1b73d31848bbaa46635339170ed92a7ccaeef9d64b6f43987fb88f8b39"
    )
    assert protocol == {
        "cuda_peak_counters_reset_before_each_measurement": True,
        "cuda_synchronized_before_and_after_each_measurement": True,
        "failed_timeout_and_incomplete_rows_in_runtime_aggregates": False,
        "method_order": "balanced_cyclic_by_repetition",
        "method_specific_runner_setup_inside_measured_region": False,
        "model_load_inside_measured_region": False,
        "quartile_policy": "linear_interpolation_type7",
        "recorded_repetitions_per_strategy": 8,
        "rss_metric": "sampled_process_resident_set_peak_per_call",
        "rss_sample_interval_seconds": 0.001,
        "tokenizer_grammar_and_shared_preprocessing_inside_measured_region": False,
        "warmup_runs_per_strategy": 1,
    }
    assert len(metadata["warmup_records"]) == 4
    assert all(
        record["execution_status"] == "complete"
        for record in metadata["warmup_records"]
    )
    assert metadata["warmup_records"][-1]["solver_status"] == "optimal"
    assert metadata["warmup_records"][-1]["certificate_valid"] is True

    orders = summary["method_order_by_repetition"]
    for strategy in Q5_STRATEGIES:
        positions = [orders[str(repetition)].index(strategy) for repetition in range(8)]
        assert sorted(positions[:4]) == [0, 1, 2, 3]
        assert positions[4:] == positions[:4]

    for strategy in Q5_STRATEGIES:
        method = summary["methods"][strategy]
        assert method["successful_runtime_count"] == 8
        assert method["excluded_runtime_count"] == 0
        assert method["runtime_seconds"]["count"] == 8
        assert method["runtime_seconds"]["median"] > 0.0
        assert method["runtime_seconds"]["iqr"] >= 0.0
        assert method["process_sampled_peak_rss_bytes"]["count"] == 8
        assert method["process_sampled_peak_rss_bytes"]["median"] > 0.0
        assert method["cuda_peak_allocated_bytes"]["count"] == 8
        assert method["cuda_peak_allocated_bytes"]["median"] > 0.0
        assert method["cuda_peak_reserved_bytes"]["median"] >= (
            method["cuda_peak_allocated_bytes"]["median"]
        )

    exact = summary["methods"]["exact"]
    assert exact["solver_status"] == "optimal"
    assert exact["fallback_count"] == 0
    assert exact["support_expansion_count"] == 0
    assert exact["empty_optimal_batch_count"] == 0
