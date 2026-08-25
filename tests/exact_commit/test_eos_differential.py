from __future__ import annotations

import json

from mwpc_exact.types import SolveStatus
from mwpc_research.eos_differential import (
    EOSFiniteSlotCaseReport,
    EOSFiniteSlotDifferentialMismatch,
    RandomEOSFiniteSlotInstance,
    check_eos_finite_slot_instance,
    generate_random_eos_finite_slot_instance,
    run_eos_finite_slot_campaign,
)


def test_seed_is_deterministic_and_fixture_round_trips() -> None:
    instance = generate_random_eos_finite_slot_instance(1729)

    assert instance == generate_random_eos_finite_slot_instance(1729)
    assert RandomEOSFiniteSlotInstance.from_json(instance.to_json()) == instance
    json.loads(instance.to_json())


def test_fixture_can_be_written_and_replayed_offline(tmp_path) -> None:
    instance = generate_random_eos_finite_slot_instance(41)
    fixture_path = tmp_path / "seed-41.json"

    instance.write_json(fixture_path)

    assert RandomEOSFiniteSlotInstance.read_json(fixture_path) == instance
    check_eos_finite_slot_instance(RandomEOSFiniteSlotInstance.read_json(fixture_path))


def test_generator_covers_eos_pad_fixed_and_support_dimensions() -> None:
    instances = tuple(generate_random_eos_finite_slot_instance(seed) for seed in range(100))
    features = {feature for instance in instances for feature in instance.features}

    assert {
        "mode_required",
        "mode_optional",
        "target_eos_absent",
        "target_eos_first_slot",
        "target_eos_middle_slot",
        "target_eos_final_slot",
        "pad_suffix",
        "eos_pad_alias_termination",
        "alternate_eot_termination",
        "fixed_ordinary",
        "fixed_eos",
        "fixed_pad",
        "random_support_rows",
        "forced_infeasible_intersection",
    } <= features
    assert all(len(instance.canvas) == len(instance.target_token_ids) for instance in instances)
    assert all(
        token_id in instance.support_rows[position]
        for instance in instances
        for position, token_id in enumerate(instance.target_token_ids)
    )


def test_seed_zero_regression_does_not_require_selected_proposal_tuple_order() -> None:
    # Positive proposal IDs for slot zero are deliberately non-contiguous in
    # collection order. Selected-set membership is guaranteed; tuple order is not.
    instance = generate_random_eos_finite_slot_instance(0)

    report = check_eos_finite_slot_instance(instance)

    assert report.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert report.property_checks["legal_path_set_agreement"] == 1
    assert report.property_checks["lattice_path_metadata"] > 0


def test_solver_and_independent_enumerator_agree_over_seed_campaign() -> None:
    summary = run_eos_finite_slot_campaign(
        campaign_name="unit",
        seed_start=0,
        case_count=128,
    )

    assert summary.failed_cases == 0, summary.to_dict()
    assert summary.passed_cases == 128
    assert set(summary.status_counts) == {
        SolveStatus.OPTIMAL.value,
        SolveStatus.INFEASIBLE_ON_SUPPORT.value,
    }
    assert summary.property_checks["status_agreement"] == 128
    assert summary.property_checks["legal_path_set_agreement"] == 128
    assert summary.property_checks["certificate_validation"] == summary.status_counts["optimal"]
    assert summary.property_checks["exact_slot_consumption"] == summary.status_counts["optimal"]
    assert (
        summary.property_checks["nonoptimal_payload"]
        == summary.status_counts["infeasible_on_support"]
    )
    assert set(summary.witness_eos_position_counts) == {
        "absent_optional",
        "first_slot",
        "middle_slot",
        "final_slot",
    }
    assert summary.feature_case_counts["explicit_represented_support"] == 128
    assert summary.feature_case_counts["fixed_position"] > 0
    assert summary.feature_case_counts["fixed_pad"] > 0


def test_campaign_saves_exact_replay_fixture_and_failure_metadata(tmp_path) -> None:
    def fail(instance: RandomEOSFiniteSlotInstance) -> EOSFiniteSlotCaseReport:
        raise EOSFiniteSlotDifferentialMismatch(
            seed=instance.seed,
            property_name="injected_test_failure",
            details="failure serialization smoke test",
        )

    summary = run_eos_finite_slot_campaign(
        campaign_name="failure-test",
        seed_start=17,
        case_count=1,
        failure_directory=tmp_path,
        checker=fail,
    )

    assert summary.failed_cases == 1
    fixture_path = tmp_path / "seed-17.json"
    failure_path = tmp_path / "seed-17.failure.json"
    fixture = RandomEOSFiniteSlotInstance.read_json(fixture_path)
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    assert fixture.seed == failure["seed"] == 17
    assert failure["fixture_file"] == fixture_path.name
