from __future__ import annotations

import json

import pytest

pytest.importorskip("mwpc_parser_py")

from mwpc_exact.types import SolveStatus
from mwpc_research.graph_differential import (
    generate_random_graph_instance,
)
from mwpc_research.rust_differential import (
    check_rust_differential_instance,
    run_rust_differential_campaign,
)


def test_small_python_rust_oracle_campaign_has_full_agreement() -> None:
    summary = run_rust_differential_campaign(
        campaign_name="unit",
        seed_start=0,
        case_count=50,
    )

    assert summary.passed_cases == 50
    assert summary.failed_cases == 0
    assert summary.property_checks["status_agreement"] == 50
    assert sum(summary.status_counts.values()) == 50


def test_case_report_uses_normalized_epsilon_graph() -> None:
    report = check_rust_differential_instance(generate_random_graph_instance(3))

    assert report.status in {SolveStatus.OPTIMAL, SolveStatus.INFEASIBLE_ON_SUPPORT}
    assert "epsilon_normalization_output" in report.features


def test_campaign_serializes_exact_instance_and_failure_metadata(tmp_path) -> None:
    def fail(_instance):
        raise AssertionError("injected deterministic mismatch")

    summary = run_rust_differential_campaign(
        campaign_name="failure-test",
        seed_start=17,
        case_count=1,
        failure_directory=tmp_path,
        checker=fail,
    )

    assert summary.failed_cases == 1
    fixture = json.loads((tmp_path / "seed-17.json").read_text(encoding="utf-8"))
    failure = json.loads(
        (tmp_path / "seed-17.failure.json").read_text(encoding="utf-8")
    )
    assert fixture["seed"] == failure["seed"] == 17
    assert failure["fixture_file"] == "seed-17.json"
