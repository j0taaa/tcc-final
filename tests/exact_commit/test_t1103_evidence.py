from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from mwpc_exact.experiments import load_experiment_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q3_finite_slots_v1.toml"
FIXTURE_PATH = REPOSITORY_ROOT / "tests/exact_commit/fixtures/finite_slot_counterexamples.json"
SUMMARY_PATH = REPOSITORY_ROOT / "docs/evidence/t1103-q3-finite-slot-summary.json"
T1103_IMPLEMENTATION_COMMIT = "ac447a8644583052806c66f7b4deb39ac66f9378"


def test_checked_in_t1103_summary_matches_the_pinned_q3_config() -> None:
    config = load_experiment_config(CONFIG_PATH)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    fixture_sha256 = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()

    assert summary["artifact_kind"] == "mwpc_q3_finite_slot_summary"
    assert summary["schema_version"] == 1
    assert summary["case_count"] == summary["passed_cases"] == 2
    assert summary["failed_cases"] == 0
    assert summary["failures"] == []
    assert summary["curated_case_count"] == 2
    assert summary["real_decoder_state_count"] == 0
    assert summary["abstract_accept_count"] == 2
    assert summary["finite_slot_false_positive_count"] == 2
    assert summary["finite_status_counts"] == {
        "infeasible_on_support": 1,
        "optimal": 1,
    }
    assert summary["all_results_support_finite_slot_claim"] is True
    assert math.isfinite(summary["total_runtime_seconds"])
    assert summary["total_runtime_seconds"] >= 0.0
    assert summary["source_fixture"] == {
        "path": "tests/exact_commit/fixtures/finite_slot_counterexamples.json",
        "sha256": fixture_sha256,
    }

    metadata = summary["run_metadata"]
    assert metadata["config_sha256"] == config.config_sha256
    assert metadata["git_commit"] == T1103_IMPLEMENTATION_COMMIT
    assert metadata["git_dirty"] is False
    assert metadata["seed"] == 1103
    assert metadata["source_fixture_sha256"] == fixture_sha256
    assert metadata["real_decoder_states_mined"] is False
    assert metadata["abstract_baseline"] == "ordered_anchor_sigma_star"
    assert metadata["finite_solver"] == ("python_reference_plus_exhaustive_path_enumeration")
    assert metadata["independent_oracle"] == ("complete_finite_eos_lattice_path_enumeration")
    assert metadata["exactness_scope"] == "exact_on_support"
    assert metadata["exactness_guarantee"] == "per_step"
    assert metadata["finite_slots"] is True
    assert metadata["timing_scope"] == ("single_repetition_smoke_not_publication_benchmark")

    cases = {case["case_id"]: case for case in summary["cases"]}
    assert set(cases) == {
        "required_eos_one_slot_infeasible_v1",
        "required_eos_one_slot_lower_empty_v1",
    }
    for case in cases.values():
        assert case["available_physical_slots"] == 1
        assert case["minimum_required_physical_tokens"] == 2
        assert case["slot_shortfall"] == 1
        assert case["abstract_status"] == "accepted"
        assert case["abstract_witness_token_ids"] == [0]
        assert case["claim_supported"] is True

    infeasible = cases["required_eos_one_slot_infeasible_v1"]
    assert infeasible["finite_status"] == "infeasible_on_support"
    assert infeasible["finite_objective_value"] is None
    assert infeasible["finite_witness_token_ids"] is None
    assert infeasible["finite_reason_code"] == (
        "no_grammar_valid_finite_path_under_explicit_support_and_required_eos"
    )

    lower_alternative = cases["required_eos_one_slot_lower_empty_v1"]
    assert lower_alternative["finite_status"] == "optimal"
    assert lower_alternative["finite_objective_value"] == 1.0
    assert lower_alternative["finite_witness_token_ids"] == [1]
    assert lower_alternative["finite_reason_code"] == (
        "abstract_witness_exceeds_canvas_lower_score_finite_path_selected"
    )
