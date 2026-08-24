from __future__ import annotations

import json
from dataclasses import replace

import pytest

from mwpc_exact import (
    ExactCommitResult,
    ExactnessScope,
    Proposal,
    SolveStatus,
    SupportKind,
    TerminalEdge,
    ValidationCode,
    WeightedTerminalDAG,
    validate_exact_commit_certificate,
)


@pytest.fixture
def certificate_case() -> tuple[
    ExactCommitResult,
    ExactnessScope,
    tuple[int | None, ...],
    tuple[Proposal, ...],
    WeightedTerminalDAG,
]:
    scope = ExactnessScope(
        kind=SupportKind.EXPLICIT,
        vocabulary_size=128,
        included_special_tokens=(0, 127),
        pruning_description="validator fixture",
    )
    proposals = (
        Proposal(0, position=0, token_id=10, weight=1),
        Proposal(1, position=0, token_id=11, weight=2),
        Proposal(2, position=1, token_id=20, weight=0),
    )
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 2),
        start_node_id=0,
        final_node_ids=(2,),
        edges=(
            TerminalEdge(edge_id=0, source_state=0, target_state=1, terminal_label="a"),
            TerminalEdge(edge_id=1, source_state=1, target_state=2, terminal_label="b"),
        ),
    )
    result = ExactCommitResult(
        status=SolveStatus.OPTIMAL,
        exactness_scope=scope,
        objective_value=1,
        selected_proposal_ids=(0,),
        witness_token_ids=(10, 20),
        witness_terminal_labels=("a", "b"),
        witness_graph_edge_ids=(0, 1),
    )
    return result, scope, (None, 20), proposals, graph


def validation_codes(report) -> set[ValidationCode]:
    return {issue.code for issue in report.issues}


def validate_case(
    result: ExactCommitResult,
    scope: ExactnessScope,
    canvas: tuple[int | None, ...],
    proposals: tuple[Proposal, ...],
    graph: WeightedTerminalDAG,
):
    return validate_exact_commit_certificate(
        result,
        expected_scope=scope,
        canvas=canvas,
        proposals=proposals,
        graph=graph,
        grammar_recognizer=lambda labels: labels == ("a", "b"),
        tokenizer_validator=lambda tokens, labels: (tokens, labels)
        == ((10, 20), ("a", "b")),
        support_validator=lambda tokens: tokens == (10, 20),
        eos_validator=lambda tokens: len(tokens) == 2,
    )


def test_independent_validator_accepts_complete_certificate(certificate_case) -> None:
    report = validate_case(*certificate_case)

    assert report.is_valid
    assert report.issues == ()
    assert report.skipped_checks == ()
    assert report.recomputed_objective == 1.0
    assert report.recomputed_selected_proposal_ids == (0,)
    json.dumps(report.to_dict())


def test_validator_detects_corrupted_witness_token(certificate_case) -> None:
    result, scope, canvas, proposals, graph = certificate_case
    corrupted = replace(result, witness_token_ids=(10, 21))

    report = validate_case(corrupted, scope, canvas, proposals, graph)

    assert ValidationCode.FIXED_POSITION_MISMATCH in validation_codes(report)


def test_validator_detects_corrupted_slot_count(certificate_case) -> None:
    result, scope, canvas, proposals, graph = certificate_case
    corrupted = replace(result, witness_token_ids=(10,))

    report = validate_case(corrupted, scope, canvas, proposals, graph)

    assert ValidationCode.SLOT_COUNT_MISMATCH in validation_codes(report)


def test_validator_detects_corrupted_objective(certificate_case) -> None:
    result, scope, canvas, proposals, graph = certificate_case
    corrupted = replace(result, objective_value=2.0)

    report = validate_case(corrupted, scope, canvas, proposals, graph)

    assert ValidationCode.OBJECTIVE_MISMATCH in validation_codes(report)


def test_validator_detects_corrupted_selected_proposal_ids(certificate_case) -> None:
    result, scope, canvas, proposals, graph = certificate_case
    corrupted = replace(result, selected_proposal_ids=(99,))

    report = validate_case(corrupted, scope, canvas, proposals, graph)

    assert ValidationCode.SELECTED_PROPOSALS_MISMATCH in validation_codes(report)


def test_validator_compares_selected_proposal_multiplicity(certificate_case) -> None:
    result, scope, canvas, proposals, graph = certificate_case
    corrupted = replace(result, selected_proposal_ids=(0, 0))

    report = validate_case(corrupted, scope, canvas, proposals, graph)

    assert ValidationCode.SELECTED_PROPOSALS_MISMATCH in validation_codes(report)


def test_validator_detects_corrupted_graph_path(certificate_case) -> None:
    result, scope, canvas, proposals, graph = certificate_case
    corrupted = replace(
        result,
        witness_terminal_labels=("b", "a"),
        witness_graph_edge_ids=(1, 0),
    )

    report = validate_case(corrupted, scope, canvas, proposals, graph)

    assert ValidationCode.EDGE_CONTINUITY in validation_codes(report)


def test_validator_detects_scope_mismatch(certificate_case) -> None:
    result, _, canvas, proposals, graph = certificate_case
    other_scope = ExactnessScope(
        kind=SupportKind.TOP_K,
        vocabulary_size=128,
        top_k=8,
    )

    report = validate_case(result, other_scope, canvas, proposals, graph)

    assert ValidationCode.SCOPE_MISMATCH in validation_codes(report)


def test_validator_requires_all_injected_checks_for_validity(certificate_case) -> None:
    result, scope, canvas, proposals, graph = certificate_case

    report = validate_exact_commit_certificate(
        result,
        expected_scope=scope,
        canvas=canvas,
        proposals=proposals,
        graph=graph,
        grammar_recognizer=lambda labels: labels == ("a", "b"),
    )

    assert not report.is_valid
    assert report.skipped_checks == ("tokenizer", "eos")


@pytest.mark.parametrize(
    ("validator_name", "expected_code"),
    [
        ("grammar", ValidationCode.GRAMMAR_REJECTED),
        ("tokenizer", ValidationCode.TOKENIZER_REJECTED),
        ("support", ValidationCode.SUPPORT_REJECTED),
        ("eos", ValidationCode.EOS_REJECTED),
    ],
)
def test_validator_reports_injected_rejection(
    certificate_case, validator_name: str, expected_code: ValidationCode
) -> None:
    result, scope, canvas, proposals, graph = certificate_case
    validators = {
        "grammar_recognizer": lambda labels: True,
        "tokenizer_validator": lambda tokens, labels: True,
        "support_validator": lambda tokens: True,
        "eos_validator": lambda tokens: True,
    }
    validators[
        {
            "grammar": "grammar_recognizer",
            "tokenizer": "tokenizer_validator",
            "support": "support_validator",
            "eos": "eos_validator",
        }[validator_name]
    ] = lambda *args: False

    report = validate_exact_commit_certificate(
        result,
        expected_scope=scope,
        canvas=canvas,
        proposals=proposals,
        graph=graph,
        **validators,  # type: ignore[arg-type]
    )

    assert expected_code in validation_codes(report)
