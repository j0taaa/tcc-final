from __future__ import annotations

import json
import math
from pathlib import Path

from mwpc_exact.experiments import load_experiment_config
from mwpc_research.q5_end_to_end import Q5_STRATEGIES

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q5_end_to_end_v1.toml"
SUMMARY_PATH = REPOSITORY_ROOT / "docs/evidence/t1105-q5-end-to-end-summary.json"
T1105_IMPLEMENTATION_COMMIT = "c8587d26c02879fdc0996dd3db31038864d7a536"


def test_checked_in_t1105_summary_matches_the_pinned_q5_config() -> None:
    config = load_experiment_config(CONFIG_PATH)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert summary["artifact_kind"] == "mwpc_q5_end_to_end_summary"
    assert summary["schema_version"] == 1
    assert summary["benchmark_claim"] is False
    assert summary["measurement_count"] == 4
    assert summary["strategies"] == list(Q5_STRATEGIES)
    assert summary["paired_input_verified"] is True
    assert summary["execution_status_counts"] == {"complete": 4}
    assert summary["exact_solver_status_counts"] == {"optimal": 1}
    assert summary["failed_record_count"] == 0
    assert summary["required_contract_failure_count"] == 0
    assert summary["all_required_methods_passed"] is True
    assert summary["syntactic_valid_count"] == 4
    assert summary["functional_success_count"] == 4
    assert summary["fallback_count"] == 3
    assert summary["support_expansion_count"] == 0
    assert summary["empty_optimal_batch_count"] == 0
    assert summary["timing_interpretation"] == (
        "single ordered smoke; ratios are diagnostic and not a publication benchmark"
    )

    methods = summary["methods"]
    assert set(methods) == set(Q5_STRATEGIES)
    for strategy, method in methods.items():
        assert method["execution_status"] == "complete"
        assert method["syntactic_valid"] is True
        assert method["functional_success"] is True
        assert method["configured_diffusion_steps"] == 1
        assert method["model_forward_count"] == 1
        assert math.isfinite(method["elapsed_seconds"])
        assert method["elapsed_seconds"] > 0.0
        assert method["process_high_water_rss_bytes"] > 0
        assert method["cuda_peak_allocated_bytes"] > 0
        assert method["cuda_peak_reserved_bytes"] >= method["cuda_peak_allocated_bytes"]
        if strategy == "exact":
            assert method["solver_status"] == "optimal"
            assert method["commit_batch_sizes"] == [4]
            assert method["average_commit_batch_size"] == 4.0
            assert method["fallback_count"] == 0
            assert method["support_expansion_count"] == 0
            assert method["empty_optimal_batch_count"] == 0
        else:
            assert method["solver_status"] is None
            assert method["commit_batch_sizes"] == [1, 1, 1]
            assert method["average_commit_batch_size"] == 1.0
            assert method["support_expansion_count"] is None
            assert method["empty_optimal_batch_count"] is None
    assert methods["epic"]["fallback_count"] == 3

    ratios = summary["diagnostic_exact_runtime_ratio"]
    assert set(ratios) == {"unconstrained", "serial", "epic"}
    assert all(math.isfinite(value) and value > 0.0 for value in ratios.values())

    metadata = summary["run_metadata"]
    assert metadata["git_commit"] == T1105_IMPLEMENTATION_COMMIT
    assert metadata["git_dirty"] is False
    assert metadata["config_path"] == "configs/experiments/q5_end_to_end_v1.toml"
    assert metadata["config_sha256"] == config.config_sha256
    assert metadata["benchmark_claim"] is False
    assert metadata["publication_mode"] is False
    assert metadata["comparison_fingerprint"] == summary["comparison_fingerprint"]
    assert metadata["comparison_contract"]["model_revision"] == config.model_revision
    assert metadata["comparison_contract"]["tokenizer_revision"] == (
        config.tokenizer_revision
    )
    assert metadata["comparison_contract"]["steps"] == 1
    assert metadata["comparison_contract"]["seed"] == 904
    assert metadata["exactness_scope"] == "exact_on_support"
    assert metadata["exactness_guarantee"] == "per_step"
    assert metadata["model"]["resolved_revision"] == config.model_revision
    assert metadata["hardware"]["gpu_name"]
    assert metadata["timing_scope"] == (
        "single_fixed_order_cuda_smoke_without_warmup; "
        "model/tokenizer/grammar setup excluded"
    )
