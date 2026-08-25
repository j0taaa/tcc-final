from __future__ import annotations

from pathlib import Path

from mwpc_exact import SolveStatus
from mwpc_research.regressions import (
    load_regression_fixtures,
    verify_regression_fixture,
)

REGRESSION_DIRECTORY = Path(__file__).with_name("regressions")


def test_every_offline_regression_fixture_passes_full_differential_replay() -> None:
    fixtures = load_regression_fixtures(REGRESSION_DIRECTORY)

    reports = tuple(verify_regression_fixture(fixture) for fixture in fixtures)

    assert reports
    assert tuple(report.seed for report in reports) == tuple(
        fixture.instance.seed for fixture in fixtures
    )


def test_explicit_support_escape_regression_is_minimal_and_corrected() -> None:
    fixture = load_regression_fixtures(REGRESSION_DIRECTORY)[0]

    assert fixture.regression_id == "explicit-per-position-support-escape"
    assert fixture.expected_status is SolveStatus.OPTIMAL
    assert fixture.expected_objective == 0.0
    assert fixture.expected_selected_proposal_ids == ()
    assert fixture.instance.per_position_support == ((2,), (1, 3))
