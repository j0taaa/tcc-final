from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from mwpc_exact.experiments import ExperimentKind, load_experiment_config
from mwpc_exact.types import SolveStatus
from mwpc_research.finite_slot_counterexamples import (
    load_finite_slot_counterexamples,
    replay_finite_slot_counterexample,
)
from mwpc_research.q3_finite_slots import (
    Q3_CASE_IDS,
    run_q3_finite_slot_cases,
    write_q3_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q3_finite_slots_v1.toml"
FIXTURE_PATH = REPOSITORY_ROOT / "tests/exact_commit/fixtures/finite_slot_counterexamples.json"
FIXTURE_RELATIVE = "tests/exact_commit/fixtures/finite_slot_counterexamples.json"


def _run_cases():
    fixture_sha256 = hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest()
    return run_q3_finite_slot_cases(
        load_finite_slot_counterexamples(FIXTURE_PATH),
        run_metadata={"config_sha256": "test-hash"},
        fixture_path=FIXTURE_RELATIVE,
        fixture_sha256=fixture_sha256,
    )


def test_q3_config_freezes_curated_cases_and_both_decision_models() -> None:
    config = load_experiment_config(CONFIG_PATH)

    assert config.question is ExperimentKind.FINITE_SLOTS
    assert config.publication_mode is False
    assert config.exactness_scope == "exact_on_support"
    assert config.finite_slots is True
    assert config.grammar_source == FIXTURE_RELATIVE
    assert config.parameters["case_ids"] == Q3_CASE_IDS
    assert config.parameters["abstract_baseline"] == "ordered_anchor_sigma_star"
    assert config.parameters["finite_solver"] == "python_reference_plus_exhaustive_path_enumeration"
    assert config.parameters["mine_real_decoder_states"] is False


def test_curated_rows_directly_record_the_finite_slot_claim() -> None:
    result = _run_cases()

    assert result.failed_cases == 0
    assert tuple(record.case.case_id for record in result.records) == Q3_CASE_IDS
    assert all(record.claim_supported for record in result.records)
    first, second = result.records
    assert first.report is not None
    assert second.report is not None
    assert first.report.available_physical_slots == 1
    assert first.report.minimum_physical_slots == 2
    assert first.report.finite_status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert first.report.finite_witness_token_ids is None
    assert second.report.available_physical_slots == 1
    assert second.report.minimum_physical_slots == 2
    assert second.report.finite_status is SolveStatus.OPTIMAL
    assert second.report.finite_objective == 1.0 < second.report.abstract_objective == 10.0
    assert second.report.finite_witness_token_ids == (1,)

    summary = result.summary_dict()
    assert summary["case_count"] == summary["passed_cases"] == 2
    assert summary["failed_cases"] == 0
    assert summary["curated_case_count"] == 2
    assert summary["real_decoder_state_count"] == 0
    assert summary["abstract_accept_count"] == 2
    assert summary["finite_slot_false_positive_count"] == 2
    assert summary["finite_status_counts"] == {
        "infeasible_on_support": 1,
        "optimal": 1,
    }
    assert summary["all_results_support_finite_slot_claim"] is True


def test_raw_rows_include_slots_decisions_witnesses_reasons_and_scope(
    tmp_path: Path,
) -> None:
    result = _run_cases()

    raw_path, summary_path = write_q3_artifacts(result, tmp_path)
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert len(rows) == summary["case_count"] == 2
    for row in rows:
        assert row["success"] is True
        assert row["slot_accounting"] == {
            "available_physical_slots": 1,
            "minimum_content_tokens_in_abstract_witness": 1,
            "required_termination_tokens": 1,
            "minimum_required_physical_tokens": 2,
            "slot_shortfall": 1,
        }
        assert row["abstract_decision"]["status"] == "accepted"
        assert row["abstract_decision"]["witness_token_ids"] == [0]
        assert row["finite_decision"]["reason_code"]
        assert row["finite_decision"]["exactness_scope"]["claim"] == "exact_on_support"
        assert row["comparison"]["abstract_witness_fits_finite_canvas"] is False
        assert row["comparison"]["claim_supported"] is True
        assert all(row["independent_validation"].values())
    assert rows[0]["finite_decision"]["status"] == "infeasible_on_support"
    assert rows[0]["finite_decision"]["witness"]["token_ids"] is None
    assert rows[1]["finite_decision"]["status"] == "optimal"
    assert rows[1]["finite_decision"]["witness"]["token_ids"] == [1]

    with pytest.raises(FileExistsError):
        write_q3_artifacts(result, tmp_path)


def test_replay_error_is_not_reported_as_finite_infeasibility() -> None:
    cases = load_finite_slot_counterexamples(FIXTURE_PATH)

    def failing_replay(_case):
        raise TimeoutError("injected distinct timeout")

    result = run_q3_finite_slot_cases(
        cases[:1],
        run_metadata={"test": "timeout"},
        fixture_path=FIXTURE_RELATIVE,
        fixture_sha256=hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(),
        replay=failing_replay,
    )
    row = result.records[0].to_dict(
        run_metadata=result.run_metadata,
        fixture_path=result.fixture_path,
        fixture_sha256=result.fixture_sha256,
    )

    assert result.failed_cases == 1
    assert row["error_type"] == "TimeoutError"
    assert row["finite_decision"] is None
    assert result.summary_dict()["finite_status_counts"] == {}
    assert result.summary_dict()["all_results_support_finite_slot_claim"] is False


def test_replay_for_a_different_case_fails_closed() -> None:
    cases = load_finite_slot_counterexamples(FIXTURE_PATH)
    second_report = replay_finite_slot_counterexample(cases[1])

    result = run_q3_finite_slot_cases(
        cases[:1],
        run_metadata={"test": "wrong-case"},
        fixture_path=FIXTURE_RELATIVE,
        fixture_sha256=hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(),
        replay=lambda _case: second_report,
    )

    assert result.failed_cases == 1
    assert result.records[0].error_type == "AssertionError"
    assert "different case" in (result.records[0].error_message or "")
