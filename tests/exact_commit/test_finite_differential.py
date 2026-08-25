from __future__ import annotations

import json
from importlib import import_module

import pytest

from mwpc_exact import ExactBackend, SolveStatus
from mwpc_research.finite_differential import (
    FiniteLatticeDifferentialMismatch,
    RandomFiniteLatticeInstance,
    check_finite_lattice_instance,
    generate_random_finite_lattice_instance,
    run_finite_lattice_campaign,
)


def _rust_binding_available() -> bool:
    try:
        import_module("mwpc_parser_py")
    except ImportError:
        return False
    return True


requires_rust_binding = pytest.mark.skipif(
    not _rust_binding_available(),
    reason="build the production binding with `make bootstrap-rust-parser`",
)


def _python_checker(instance: RandomFiniteLatticeInstance):
    return check_finite_lattice_instance(instance, backends=(ExactBackend.PYTHON,))


def test_seed_is_deterministic_and_fixture_round_trips() -> None:
    instance = generate_random_finite_lattice_instance(1729)

    assert instance == generate_random_finite_lattice_instance(1729)
    assert RandomFiniteLatticeInstance.from_json(instance.to_json()) == instance
    json.loads(instance.to_json())


def test_fixture_can_be_written_and_replayed_offline(tmp_path) -> None:
    instance = generate_random_finite_lattice_instance(41)
    fixture_path = tmp_path / "seed-41.json"

    instance.write_json(fixture_path)

    assert RandomFiniteLatticeInstance.read_json(fixture_path) == instance


def test_generator_forces_tokenizer_and_provenance_stressors() -> None:
    for seed in (0, 1):
        instance = generate_random_finite_lattice_instance(seed)
        features = set(instance.features)

        assert instance.emissions[0] == instance.emissions[1]
        assert {0, 1, 2} <= set(instance.support_rows[0])
        assert len(instance.emissions[0]) == 1
        assert len(instance.emissions[2]) > 1
        assert {
            "multi_byte_token",
            "same_bytes_distinct_token_ids",
            "variable_byte_lengths",
            "multiple_proposals_same_choice",
            "zero_weight_proposal",
        } <= features
    assert "fixed_position" in generate_random_finite_lattice_instance(0).features
    assert "fixed_position" not in generate_random_finite_lattice_instance(1).features


def test_python_solver_matches_exhaustive_token_paths_over_seed_campaign() -> None:
    summary = run_finite_lattice_campaign(
        campaign_name="python-unit",
        seed_start=0,
        case_count=64,
        checker=_python_checker,
    )

    assert summary.failed_cases == 0, summary.to_dict()
    assert summary.passed_cases == 64
    assert set(summary.status_counts) == {
        SolveStatus.OPTIMAL.value,
        SolveStatus.INFEASIBLE_ON_SUPPORT.value,
    }
    assert summary.property_checks["status_agreement"] == 64
    assert summary.property_checks["byte_expansion_score"] > 64
    assert summary.property_checks["byte_expansion_provenance"] > 64
    assert summary.property_checks["certificate_validation"] > 0
    assert summary.feature_case_counts["multi_byte_token"] == 64
    assert summary.feature_case_counts["same_bytes_distinct_token_ids"] == 64
    assert summary.feature_case_counts["fixed_position"] == 32
    assert summary.feature_case_counts["forced_infeasible_intersection"] == 16


@requires_rust_binding
def test_python_rust_and_oracle_agree_over_seed_campaign() -> None:
    summary = run_finite_lattice_campaign(
        campaign_name="cross-language-unit",
        seed_start=1000,
        case_count=50,
    )

    assert summary.passed_cases == 50
    assert summary.failed_cases == 0, summary.to_dict()
    assert summary.property_checks["status_agreement"] == 50
    assert summary.property_checks["exactness_scope"] == 100
    assert summary.property_checks["certificate_validation"] > 0


def test_campaign_saves_exact_replay_fixture_and_failure_metadata(tmp_path) -> None:
    def fail(instance: RandomFiniteLatticeInstance):
        raise FiniteLatticeDifferentialMismatch(
            seed=instance.seed,
            property_name="injected_test_failure",
            details="failure serialization smoke test",
        )

    summary = run_finite_lattice_campaign(
        campaign_name="failure-test",
        seed_start=17,
        case_count=1,
        failure_directory=tmp_path,
        checker=fail,
    )

    assert summary.failed_cases == 1
    fixture_path = tmp_path / "seed-17.json"
    failure_path = tmp_path / "seed-17.failure.json"
    fixture = RandomFiniteLatticeInstance.read_json(fixture_path)
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    assert fixture.seed == failure["seed"] == 17
    assert failure["fixture_file"] == fixture_path.name
