from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mwpc_exact.types import SolveStatus
from mwpc_research.finite_slot_counterexamples import (
    ABSTRACT_SIGMA_STAR_SEMANTICS,
    load_finite_slot_counterexamples,
    replay_finite_slot_counterexample,
    summarize_finite_slot_counterexamples,
)

FIXTURE_DIRECTORY = Path(__file__).with_name("fixtures")
CORPUS_PATH = FIXTURE_DIRECTORY / "finite_slot_counterexamples.json"
DOCUMENTATION_PATH = FIXTURE_DIRECTORY / "finite_slot_counterexamples.md"
EVIDENCE_PATH = Path(__file__).parents[2] / "docs/evidence/t703-finite-slot-counterexamples.json"


def test_versioned_sigma_star_cases_replay_against_finite_solver_and_enumeration() -> None:
    cases = load_finite_slot_counterexamples(CORPUS_PATH)
    reports = tuple(replay_finite_slot_counterexample(case) for case in cases)
    summary = summarize_finite_slot_counterexamples(reports)

    assert tuple(case.case_id for case in cases) == (
        "required_eos_one_slot_infeasible_v1",
        "required_eos_one_slot_lower_empty_v1",
    )
    assert summary["abstract_sigma_star_semantics"] == ABSTRACT_SIGMA_STAR_SEMANTICS
    assert summary["case_count"] == 2
    assert summary["all_abstract_sigma_star_accepted"] is True
    assert summary["all_slot_shortfalls_positive"] is True
    assert summary["finite_status_counts"] == {
        "infeasible_on_support": 1,
        "optimal": 1,
    }
    assert tuple(report.finite_status for report in reports) == (
        SolveStatus.INFEASIBLE_ON_SUPPORT,
        SolveStatus.OPTIMAL,
    )
    assert reports[1].finite_objective == 1.0 < reports[1].abstract_objective == 10.0
    assert reports[1].finite_selected_proposal_ids == (21,)
    assert reports[1].finite_witness_token_ids == (1,)
    assert reports[1].finite_witness_terminal_labels == ()
    assert reports[1].finite_witness_graph_edge_ids is not None
    assert len(reports[1].finite_witness_graph_edge_ids) == 1
    assert reports[1].finite_witness_token_roles == ("eos",)
    assert reports[1].finite_witness_eos_position == 0
    assert reports[1].finite_witness_content_endpoint_slot == 0
    assert reports[1].finite_exactness_scope.kind.value == "explicit"
    assert reports[1].finite_exactness_scope.included_special_tokens == (1,)


def test_first_case_is_the_documented_minimal_required_eos_counterexample() -> None:
    (minimal, _) = load_finite_slot_counterexamples(CORPUS_PATH)
    report = replay_finite_slot_counterexample(minimal)

    assert len(minimal.canvas) == 1
    assert len(minimal.abstract_witness_token_ids) == 1
    assert minimal.grammar.accepts_empty is False
    assert report.abstract_terminal_labels == (ord("a"),)
    assert report.available_physical_slots == 1
    assert report.minimum_physical_slots == 2
    assert report.slot_shortfall == 1
    assert report.finite_status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert report.finite_objective is None
    assert report.finite_witness_token_ids is None


def test_human_explanation_names_every_case_and_scopes_the_claim() -> None:
    cases = load_finite_slot_counterexamples(CORPUS_PATH)
    documentation = DOCUMENTATION_PATH.read_text(encoding="utf-8")

    for case in cases:
        assert f"`{case.case_id}`" in documentation
    normalized = " ".join(documentation.split())
    assert "This abstraction is useful only as the false-positive side" in normalized
    assert "finite result is always reported as `exact_on_support`" in normalized
    assert "not a timeout" in normalized


def test_committed_evidence_is_the_deterministic_fixture_replay() -> None:
    fixture_bytes = CORPUS_PATH.read_bytes()
    cases = load_finite_slot_counterexamples(CORPUS_PATH)
    reports = tuple(replay_finite_slot_counterexample(case) for case in cases)
    expected = {
        **summarize_finite_slot_counterexamples(reports),
        "fixture_path": "tests/exact_commit/fixtures/finite_slot_counterexamples.json",
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
    }

    actual: object = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    assert actual == expected
