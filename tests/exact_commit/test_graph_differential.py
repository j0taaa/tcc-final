from __future__ import annotations

import json

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from mwpc_exact.reference.graph_differential import (
    GraphDifferentialMismatch,
    RandomGraphInstance,
    check_graph_differential_instance,
    generate_random_graph_instance,
    run_graph_differential_campaign,
)


def test_generated_graph_has_required_parallel_epsilon_and_provenance_features() -> None:
    instance = generate_random_graph_instance(19)

    assert {
        "epsilon_chain",
        "integer_edge_rewards",
        "parallel_edges",
        "same_terminal_distinct_token_provenance",
    } <= set(instance.features)
    assert instance.to_json() == generate_random_graph_instance(19).to_json()
    json.loads(instance.to_json())


@settings(
    max_examples=50,
    derandomize=True,
    database=None,
    deadline=None,
    suppress_health_check=(HealthCheck.too_slow,),
)
@given(seed=st.integers(min_value=0, max_value=100_000))
def test_graph_solver_matches_path_oracle_property(seed: int) -> None:
    report = check_graph_differential_instance(generate_random_graph_instance(seed))

    assert report.property_checks["status_agreement"] == 1
    assert report.property_checks["objective_agreement"] == 1
    assert report.property_checks["normalized_edge_validation"] > 0


def test_configured_smoke_campaign_has_complete_agreement_and_coverage() -> None:
    summary = run_graph_differential_campaign(seed_start=0, case_count=100)

    assert summary.failed_cases == 0, summary.to_dict()
    assert summary.passed_cases == 100
    assert set(summary.status_counts) == {"optimal", "infeasible_on_support"}
    assert summary.property_checks["status_agreement"] == 100
    assert summary.property_checks["objective_agreement"] == 100
    assert summary.property_checks["certificate_validation"] > 0
    assert summary.property_checks["normalized_edge_validation"] > 0
    assert summary.feature_case_counts["epsilon_chain"] == 100
    assert summary.feature_case_counts["parallel_edges"] == 100
    assert summary.feature_case_counts["same_terminal_distinct_token_provenance"] == 100
    assert summary.feature_case_counts["multiple_final_states"] == 50
    assert summary.feature_case_counts["forced_infeasible_intersection"] == 20


def test_campaign_persists_replayable_failure(tmp_path) -> None:
    def injected_failure(instance: RandomGraphInstance):
        if instance.seed == 8:
            raise GraphDifferentialMismatch(
                seed=8,
                property_name="injected_test_failure",
                details="artifact smoke test",
            )
        return check_graph_differential_instance(instance)

    failure_directory = tmp_path / "failures"
    summary = run_graph_differential_campaign(
        seed_start=7,
        case_count=3,
        failure_directory=failure_directory,
        checker=injected_failure,
    )

    assert summary.passed_cases == 2
    assert summary.failed_cases == 1
    failure = summary.failures[0]
    assert failure.seed == 8
    assert failure.fixture_file == "seed-8.json"
    assert failure.failure_file == "seed-8.failure.json"
    assert (failure_directory / "seed-8.json").is_file()
    assert (failure_directory / "seed-8.failure.json").is_file()
