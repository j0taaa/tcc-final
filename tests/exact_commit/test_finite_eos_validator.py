from __future__ import annotations

from dataclasses import replace

import pytest

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    EpsilonEdge,
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
from mwpc_exact.types import GraphEdge

SCOPE = ExactnessScope(
    kind=SupportKind.EXPLICIT,
    vocabulary_size=5,
    included_special_tokens=(2, 3, 4),
    pruning_description="finite EOS validator fixture",
)
ADAPTER = CompositionalByteLevelAdapter((b"a", b"bc", None, None, None))
REQUIRED = EOSPolicy(
    mode=EOSMode.REQUIRED,
    termination_token_ids=(2, 3),
    pad_token_id=2,
)
OPTIONAL = EOSPolicy(
    mode=EOSMode.OPTIONAL,
    termination_token_ids=(2, 3),
    pad_token_id=2,
)


def path_graph(labels: tuple[int | None, ...]) -> WeightedTerminalDAG:
    edges: list[GraphEdge] = []
    for edge_id, label in enumerate(labels):
        if label is None:
            edges.append(EpsilonEdge(edge_id, edge_id, edge_id + 1))
        else:
            edges.append(TerminalEdge(edge_id, edge_id, edge_id + 1, label))
    return WeightedTerminalDAG(
        node_ids=tuple(range(len(labels) + 1)),
        start_node_id=0,
        final_node_ids=(len(labels),),
        edges=tuple(edges),
    )


def result_for(
    *,
    token_ids: tuple[int, ...],
    terminal_labels: tuple[int, ...],
    graph: WeightedTerminalDAG,
    eos_position: int | None,
    content_endpoint: int,
    proposals: tuple[Proposal, ...] = (),
) -> ExactCommitResult:
    matched = tuple(
        proposal
        for proposal in proposals
        if proposal.weight > 0
        and proposal.position < len(token_ids)
        and token_ids[proposal.position] == proposal.token_id
    )
    return ExactCommitResult(
        status=SolveStatus.OPTIMAL,
        exactness_scope=SCOPE,
        objective_value=sum(proposal.weight for proposal in matched),
        selected_proposal_ids=tuple(proposal.proposal_id for proposal in matched),
        witness_token_ids=token_ids,
        witness_terminal_labels=terminal_labels,
        witness_graph_edge_ids=tuple(edge.edge_id for edge in graph.edges),
        witness_eos_position=eos_position,
        witness_content_endpoint_slot=content_endpoint,
    )


def validate(
    result: ExactCommitResult,
    *,
    graph: WeightedTerminalDAG,
    canvas: tuple[int | None, ...],
    policy: EOSPolicy = REQUIRED,
    proposals: tuple[Proposal, ...] = (),
):
    return validate_exact_commit_certificate(
        result,
        expected_scope=SCOPE,
        canvas=canvas,
        proposals=proposals,
        graph=graph,
        grammar_recognizer=lambda _labels: True,
        support_validator=lambda tokens: all(token_id < 10 for token_id in tokens),
        eos_policy=policy,
        eos_adapter=ADAPTER,
    )


def codes(report) -> set[ValidationCode]:
    return {issue.code for issue in report.issues}


def issue(report, code: ValidationCode):
    return next(item for item in report.issues if item.code is code)


def test_structured_validator_accepts_eot_eos_canonical_pad_and_epsilon_edges() -> None:
    proposals = (
        Proposal(10, 1, 3, 2),
        Proposal(11, 2, 2, 3),
    )
    graph = path_graph((ord("a"), None, None))
    result = result_for(
        token_ids=(0, 3, 2),
        terminal_labels=(ord("a"),),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
        proposals=proposals,
    )

    report = validate(
        result,
        graph=graph,
        canvas=(None, 3, None),
        proposals=proposals,
    )

    assert report.is_valid
    assert report.issues == ()
    assert report.skipped_checks == ()
    assert report.recomputed_objective == 5.0
    assert report.recomputed_selected_proposal_ids == (10, 11)


def test_epsilon_only_eos_at_slot_zero_is_a_valid_public_certificate() -> None:
    graph = path_graph((None, None))
    result = result_for(
        token_ids=(3, 2),
        terminal_labels=(),
        graph=graph,
        eos_position=0,
        content_endpoint=0,
    )

    report = validate(result, graph=graph, canvas=(None, None))

    assert report.is_valid
    assert result.witness_terminal_labels == ()
    assert len(result.witness_graph_edge_ids) == 2
    assert ExactCommitResult.from_dict(result.to_dict()) == result


def test_validator_rejects_wrong_physical_slot_count() -> None:
    graph = path_graph((ord("a"), None))
    result = result_for(
        token_ids=(0, 3),
        terminal_labels=(ord("a"),),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
    )

    report = validate(result, graph=graph, canvas=(None, None, None))

    assert ValidationCode.SLOT_COUNT_MISMATCH in codes(report)
    mismatch = issue(report, ValidationCode.SLOT_COUNT_MISMATCH)
    assert mismatch.context == {"expected_slots": 3, "actual_slots": 2}


def test_validator_rejects_ordinary_token_after_eos_with_exact_position() -> None:
    graph = path_graph((ord("a"), None, None))
    result = result_for(
        token_ids=(0, 3, 0),
        terminal_labels=(ord("a"),),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
    )

    report = validate(result, graph=graph, canvas=(None, None, None))

    rejected = issue(report, ValidationCode.EOS_TOKEN_AFTER_TERMINATION)
    assert rejected.message == "only the canonical PAD token is legal after EOS"
    assert rejected.context == {
        "position": 2,
        "eos_position": 1,
        "expected_pad_token_id": 2,
        "actual_token_id": 0,
    }


def test_validator_rejects_eot_as_padding_after_an_eos_alias() -> None:
    graph = path_graph((None, None, None))
    result = result_for(
        token_ids=(2, 3, 2),
        terminal_labels=(),
        graph=graph,
        eos_position=0,
        content_endpoint=0,
    )

    report = validate(result, graph=graph, canvas=(None, None, None))

    assert ValidationCode.EOS_TOKEN_AFTER_TERMINATION in codes(report)
    assert issue(report, ValidationCode.EOS_TOKEN_AFTER_TERMINATION).context["position"] == 1


def test_validator_rejects_required_witness_without_termination() -> None:
    graph = path_graph((ord("a"), ord("b"), ord("c")))
    result = result_for(
        token_ids=(0, 1),
        terminal_labels=(ord("a"), ord("b"), ord("c")),
        graph=graph,
        eos_position=None,
        content_endpoint=2,
    )

    report = validate(result, graph=graph, canvas=(None, None))

    missing = issue(report, ValidationCode.EOS_REQUIRED_MISSING)
    assert missing.context["termination_token_ids"] == [2, 3]
    assert missing.context["physical_slot_count"] == 2


def test_validator_rejects_pad_before_eos_when_pad_has_a_distinct_id() -> None:
    distinct_pad_policy = EOSPolicy(
        EOSMode.REQUIRED,
        termination_token_ids=(3,),
        pad_token_id=4,
    )
    graph = path_graph((None, None, None))
    result = result_for(
        token_ids=(4, 3, 4),
        terminal_labels=(),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
    )

    report = validate(
        result,
        graph=graph,
        canvas=(None, None, None),
        policy=distinct_pad_policy,
    )

    rejected = issue(report, ValidationCode.EOS_PAD_BEFORE_TERMINATION)
    assert rejected.context == {"position": 0, "pad_token_id": 4}


def test_validator_rejects_mask_or_other_unsupported_control_before_eos() -> None:
    graph = path_graph((None, None, None))
    result = result_for(
        token_ids=(4, 3, 2),
        terminal_labels=(),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
    )

    report = validate(result, graph=graph, canvas=(None, None, None))

    rejected = issue(report, ValidationCode.EOS_UNSUPPORTED_CONTROL)
    assert rejected.context == {"position": 0, "token_id": 4, "eos_mode": "required"}


def test_validator_rejects_token_outside_policy_tokenizer_vocabulary() -> None:
    graph = path_graph((None, None, None))
    result = result_for(
        token_ids=(9, 3, 2),
        terminal_labels=(),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
    )

    report = validate(result, graph=graph, canvas=(None, None, None))

    rejected = issue(report, ValidationCode.EOS_TOKEN_ID_OUT_OF_RANGE)
    assert rejected.context == {"position": 0, "token_id": 9, "vocabulary_size": 5}


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("witness_eos_position", 0, ValidationCode.EOS_POSITION_MISMATCH),
        (
            "witness_content_endpoint_slot",
            2,
            ValidationCode.CONTENT_ENDPOINT_MISMATCH,
        ),
    ],
)
def test_validator_recomputes_reported_eos_metadata(
    field: str,
    value: int,
    expected_code: ValidationCode,
) -> None:
    graph = path_graph((ord("a"), None, None))
    result = result_for(
        token_ids=(0, 3, 2),
        terminal_labels=(ord("a"),),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
    )

    report = validate(
        replace(result, **{field: value}),
        graph=graph,
        canvas=(None, None, None),
    )

    assert expected_code in codes(report)


def test_validator_recomputes_effective_terminal_sequence_before_eos() -> None:
    graph = path_graph((ord("x"), None, None))
    result = result_for(
        token_ids=(0, 3, 2),
        terminal_labels=(ord("x"),),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
    )

    report = validate(result, graph=graph, canvas=(None, None, None))

    rejected = issue(report, ValidationCode.EFFECTIVE_TERMINAL_SEQUENCE_MISMATCH)
    assert rejected.context["expected_terminal_labels"] == [ord("a")]
    assert rejected.context["actual_terminal_labels"] == [ord("x")]
    assert rejected.context["content_endpoint_slot"] == 1


def test_validator_preserves_fixed_special_token_positions() -> None:
    graph = path_graph((ord("a"), None, None))
    result = result_for(
        token_ids=(0, 2, 2),
        terminal_labels=(ord("a"),),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
    )

    report = validate(result, graph=graph, canvas=(None, 3, None))

    rejected = issue(report, ValidationCode.FIXED_POSITION_MISMATCH)
    assert rejected.context == {
        "position": 1,
        "expected_token_id": 3,
        "actual_token_id": 2,
    }


def test_optional_policy_accepts_no_eos_and_uses_all_slots_as_content() -> None:
    graph = path_graph((ord("a"), ord("b"), ord("c")))
    result = result_for(
        token_ids=(0, 1),
        terminal_labels=(ord("a"), ord("b"), ord("c")),
        graph=graph,
        eos_position=None,
        content_endpoint=2,
    )

    report = validate(
        result,
        graph=graph,
        canvas=(None, None),
        policy=OPTIONAL,
    )

    assert report.is_valid


def test_absent_policy_accepts_only_ordinary_tokens() -> None:
    graph = path_graph((ord("a"), ord("b"), ord("c")))
    ordinary = result_for(
        token_ids=(0, 1),
        terminal_labels=(ord("a"), ord("b"), ord("c")),
        graph=graph,
        eos_position=None,
        content_endpoint=2,
    )
    absent = EOSPolicy(EOSMode.ABSENT)

    accepted = validate(
        ordinary,
        graph=graph,
        canvas=(None, None),
        policy=absent,
    )

    assert accepted.is_valid

    control_graph = path_graph((None,))
    control = result_for(
        token_ids=(3,),
        terminal_labels=(),
        graph=control_graph,
        eos_position=None,
        content_endpoint=1,
    )
    rejected = validate(
        control,
        graph=control_graph,
        canvas=(None,),
        policy=absent,
    )
    assert ValidationCode.EOS_UNSUPPORTED_CONTROL in codes(rejected)


def test_graph_validation_counts_labels_only_on_terminal_edges() -> None:
    graph = path_graph((ord("a"), None, None))
    valid = result_for(
        token_ids=(0, 3, 2),
        terminal_labels=(ord("a"),),
        graph=graph,
        eos_position=1,
        content_endpoint=1,
    )

    missing = validate(
        replace(valid, witness_terminal_labels=()),
        graph=graph,
        canvas=(None, None, None),
    )
    extra = validate(
        replace(valid, witness_terminal_labels=(ord("a"), ord("x"))),
        graph=graph,
        canvas=(None, None, None),
    )

    assert ValidationCode.TERMINAL_LABEL_MISMATCH in codes(missing)
    assert ValidationCode.TERMINAL_LABEL_MISMATCH in codes(extra)


def test_structured_policy_configuration_is_explicit_and_consistent() -> None:
    graph = path_graph((None,))
    result = result_for(
        token_ids=(2,),
        terminal_labels=(),
        graph=graph,
        eos_position=0,
        content_endpoint=0,
    )
    common = {
        "result": result,
        "expected_scope": SCOPE,
        "canvas": (None,),
        "proposals": (),
        "graph": graph,
        "grammar_recognizer": lambda _labels: True,
    }

    with pytest.raises(ValueError, match="supplied together"):
        validate_exact_commit_certificate(**common, eos_policy=REQUIRED)
    with pytest.raises(ValueError, match="mutually exclusive"):
        validate_exact_commit_certificate(
            **common,
            eos_policy=REQUIRED,
            eos_adapter=ADAPTER,
            eos_validator=lambda _tokens: True,
        )

    wrong_adapter = CompositionalByteLevelAdapter((b"a", None))
    with pytest.raises(ValueError, match="equal vocabularies"):
        validate_exact_commit_certificate(
            **common,
            eos_policy=REQUIRED,
            eos_adapter=wrong_adapter,
        )
