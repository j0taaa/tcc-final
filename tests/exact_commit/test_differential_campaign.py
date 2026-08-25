from __future__ import annotations

import json

from mwpc_exact.reference.random_instances import RandomTokenAlignedInstance
from mwpc_research.token_aligned_differential import (
    DifferentialMismatch,
    check_differential_instance,
    run_differential_campaign,
)


def test_normal_differential_campaign_has_complete_agreement() -> None:
    summary = run_differential_campaign(seed_start=0, case_count=32)

    assert summary.failed_cases == 0, summary.to_dict()
    assert summary.passed_cases == 32
    assert sum(summary.status_counts.values()) == 32
    assert set(summary.status_counts) == {"optimal", "infeasible_on_support"}
    assert summary.property_checks["three_way_agreement"] == 32 * 5
    assert summary.property_checks["support_monotonicity"] == 32
    assert summary.property_checks["proposal_removal"] == 32
    assert summary.property_checks["fixed_position"] == 32
    assert summary.property_checks["certificate_validation"] > 0


def test_single_seed_report_records_every_property() -> None:
    from mwpc_exact.reference.random_instances import generate_random_instance

    report = check_differential_instance(generate_random_instance(17))

    assert report.seed == 17
    assert report.property_checks["three_way_agreement"] == 5
    assert report.property_checks["support_monotonicity"] == 1
    assert report.property_checks["proposal_removal"] == 1
    assert report.property_checks["fixed_position"] == 1


def test_campaign_writes_replay_artifacts_for_a_failing_seed(tmp_path) -> None:
    failure_directory = tmp_path / "failures"

    def injected_failure(
        instance: RandomTokenAlignedInstance,
    ):  # return type is unreachable by design
        if instance.seed == 4:
            raise DifferentialMismatch(
                seed=instance.seed,
                property_name="injected_test_failure",
                details="artifact smoke test",
            )
        return check_differential_instance(instance)

    summary = run_differential_campaign(
        seed_start=3,
        case_count=3,
        failure_directory=failure_directory,
        checker=injected_failure,
    )
    summary_path = tmp_path / "summary.json"
    summary.write_json(summary_path)

    assert summary.passed_cases == 2
    assert summary.failed_cases == 1
    failure = summary.failures[0]
    assert failure.seed == 4
    assert failure.fixture_file == "seed-4.json"
    assert failure.failure_file == "seed-4.failure.json"
    assert (failure_directory / "seed-4.json").is_file()
    assert (failure_directory / "seed-4.failure.json").is_file()
    assert json.loads(summary_path.read_text())["failed_cases"] == 1
