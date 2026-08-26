from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

from mwpc_research.finite_differential import (
    FINITE_LATTICE_GENERATOR_SCHEMA_VERSION,
    finite_grammar_family_sha256,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/exact_commit/m6_finite_lattice_differential.toml"
T606_IMPLEMENTATION_COMMIT = "8d951f0777e4c22f8be286bd559ab3467be69fa0"

EXPECTED_CAMPAIGN_RESULTS = {
    "normal": {
        "status_counts": {"infeasible_on_support": 233, "optimal": 267},
        "total_enumerated_token_paths": 8201,
        "total_grammar_valid_paths": 3639,
    },
    "extended": {
        "status_counts": {"infeasible_on_support": 920, "optimal": 1080},
        "total_enumerated_token_paths": 34195,
        "total_grammar_valid_paths": 16234,
    },
}

ALWAYS_PRESENT_FEATURES = {
    "explicit_represented_support",
    "integer_proposal_weights",
    "multi_byte_token",
    "multiple_proposals_same_choice",
    "same_bytes_distinct_token_ids",
    "variable_byte_lengths",
    "zero_weight_proposal",
}


def test_checked_in_m6_summaries_match_the_immutable_campaign_config() -> None:
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
        assert summary["campaign"] == "m6_finite_lattice_differential"
        assert summary["campaign_name"] == campaign_name
        assert summary["seed_start"] == campaign["seed_start"]
        assert summary["case_count"] == case_count
        assert summary["passed_cases"] == case_count
        assert summary["failed_cases"] == 0
        assert summary["failures"] == []
        assert summary["status_counts"] == expected["status_counts"]
        assert sum(summary["status_counts"].values()) == case_count
        assert summary["total_enumerated_token_paths"] == expected["total_enumerated_token_paths"]
        assert summary["total_grammar_valid_paths"] == expected["total_grammar_valid_paths"]

        feature_counts = summary["feature_case_counts"]
        for feature in ALWAYS_PRESENT_FEATURES:
            assert feature_counts[feature] == case_count
        assert feature_counts["fixed_position"] == case_count // 2
        assert feature_counts["forced_infeasible_intersection"] == case_count // 4

        checks = summary["property_checks"]
        path_count = summary["total_enumerated_token_paths"]
        assert checks["status_agreement"] == case_count
        assert checks["exactness_scope"] == 2 * case_count
        assert checks["certificate_validation"] + checks["nonoptimal_payload"] == (2 * case_count)
        for check_name in (
            "byte_expansion_path_validation",
            "byte_expansion_provenance",
            "byte_expansion_score",
        ):
            assert checks[check_name] == path_count

        metadata = summary["metadata"]
        assert metadata["git_commit"] == T606_IMPLEMENTATION_COMMIT
        assert metadata["config_path"] == str(CONFIG_PATH.relative_to(REPOSITORY_ROOT))
        assert metadata["config_sha256"] == config_sha256
        assert metadata["generator_schema_version"] == str(FINITE_LATTICE_GENERATOR_SCHEMA_VERSION)
        assert metadata["grammar_family_sha256"] == finite_grammar_family_sha256()
        assert metadata["support_policy"] == "explicit_per_position_token_rows"
        assert metadata["exactness_scope"] == "exact_on_support"
        assert metadata["finite_slot_policy"] == "one_ordinary_token_per_physical_slot_no_eos_pad"
