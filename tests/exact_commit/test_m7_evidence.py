from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

from mwpc_exact.eos_differential import (
    EOS_DIFFERENTIAL_GENERATOR_SCHEMA_VERSION,
    eos_finite_slot_grammar_family_sha256,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/exact_commit/m7_eos_finite_slot_differential.toml"
T704_IMPLEMENTATION_COMMIT = "5cb148efb36c6fd5f224ea6faf7778fff3691a0a"

EXPECTED_CAMPAIGN_RESULTS = {
    "normal": {
        "status_counts": {"infeasible_on_support": 72, "optimal": 428},
        "total_enumerated_token_paths": 51902,
        "total_legal_eos_paths": 4010,
        "total_grammar_valid_paths": 654,
        "witness_eos_position_counts": {
            "absent_optional": 72,
            "final_slot": 118,
            "first_slot": 111,
            "middle_slot": 127,
        },
    },
    "extended": {
        "status_counts": {"infeasible_on_support": 286, "optimal": 1714},
        "total_enumerated_token_paths": 196290,
        "total_legal_eos_paths": 16262,
        "total_grammar_valid_paths": 2631,
        "witness_eos_position_counts": {
            "absent_optional": 285,
            "final_slot": 458,
            "first_slot": 495,
            "middle_slot": 476,
        },
    },
}

ALWAYS_PRESENT_FEATURES = {
    "explicit_represented_support",
    "integer_proposal_weights",
    "multiple_proposals_same_choice",
    "random_support_rows",
    "zero_weight_proposal",
}


def test_checked_in_m7_summaries_match_the_immutable_campaign_config() -> None:
    config_bytes = CONFIG_PATH.read_bytes()
    config = tomllib.loads(config_bytes.decode("utf-8"))
    config_sha256 = hashlib.sha256(config_bytes).hexdigest()

    assert config["schema_version"] == 1
    assert {campaign["name"] for campaign in config["campaigns"]} == set(EXPECTED_CAMPAIGN_RESULTS)

    for campaign in config["campaigns"]:
        campaign_name = campaign["name"]
        case_count = campaign["case_count"]
        summary_path = REPOSITORY_ROOT / campaign["summary"]
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        expected = EXPECTED_CAMPAIGN_RESULTS[campaign_name]

        assert summary["schema_version"] == 1
        assert summary["campaign"] == "m7_eos_finite_slot_differential"
        assert summary["campaign_name"] == campaign_name
        assert summary["seed_start"] == campaign["seed_start"]
        assert summary["case_count"] == case_count
        assert summary["passed_cases"] == case_count
        assert summary["failed_cases"] == 0
        assert summary["failures"] == []
        for field_name, expected_value in expected.items():
            assert summary[field_name] == expected_value
        assert sum(summary["status_counts"].values()) == case_count
        assert (
            sum(summary["witness_eos_position_counts"].values())
            == summary["status_counts"]["optimal"]
        )

        feature_counts = summary["feature_case_counts"]
        for feature in ALWAYS_PRESENT_FEATURES:
            assert feature_counts[feature] == case_count
        assert feature_counts["mode_required"] + feature_counts["mode_optional"] == case_count
        assert (
            feature_counts["target_eos_absent"]
            + feature_counts["target_eos_first_slot"]
            + feature_counts["target_eos_middle_slot"]
            + feature_counts["target_eos_final_slot"]
            == case_count
        )
        assert (
            feature_counts["eos_pad_alias_termination"]
            + feature_counts["alternate_eot_termination"]
            + feature_counts["target_eos_absent"]
            == case_count
        )
        assert feature_counts["fixed_position"] > 0
        assert feature_counts["fixed_ordinary"] > 0
        assert feature_counts["fixed_eos"] > 0
        assert feature_counts["fixed_pad"] > 0
        assert feature_counts["pad_suffix"] > 0

        checks = summary["property_checks"]
        optimal_count = summary["status_counts"]["optimal"]
        infeasible_count = summary["status_counts"]["infeasible_on_support"]
        assert checks["status_agreement"] == case_count
        assert checks["legal_path_set_agreement"] == case_count
        assert checks["certificate_validation"] == optimal_count
        assert checks["exact_slot_consumption"] == optimal_count
        assert checks["objective_agreement"] == optimal_count
        assert checks["optimal_witness_membership"] == optimal_count
        assert checks["nonoptimal_payload"] == infeasible_count
        assert checks["lattice_path_validation"] == summary["total_legal_eos_paths"]
        assert checks["lattice_path_metadata"] == summary["total_legal_eos_paths"]

        metadata = summary["metadata"]
        assert metadata["git_commit"] == T704_IMPLEMENTATION_COMMIT
        assert metadata["config_path"] == str(CONFIG_PATH.relative_to(REPOSITORY_ROOT))
        assert metadata["config_sha256"] == config_sha256
        assert metadata["generator_schema_version"] == str(
            EOS_DIFFERENTIAL_GENERATOR_SCHEMA_VERSION
        )
        assert metadata["grammar_family_sha256"] == eos_finite_slot_grammar_family_sha256()
        assert metadata["exactness_scope"] == "exact_on_support"
        assert metadata["oracle"] == (
            "direct_cartesian_token_rows_with_independent_eos_interpreter"
        )
        assert metadata["finite_slot_policy"] == (
            "all_physical_slots_consumed_under_configured_eos_pad"
        )
