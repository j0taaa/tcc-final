from __future__ import annotations

import json
from importlib.util import find_spec

import pytest

import mwpc_exact.selection as selection_module
from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    ExactCommitResult,
    Proposal,
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
    SolveStatus,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    recompute_witness_selection,
    select_exact,
    select_serial,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)

ADAPTER = CompositionalByteLevelAdapter((b"a", b"b"))
NO_EOS = EOSPolicy(EOSMode.ABSENT)
requires_rust = pytest.mark.skipif(
    find_spec("mwpc_parser_py") is None,
    reason="build the production binding with `make bootstrap-rust-parser`",
)


def same_pair_grammar() -> CnfGrammar:
    """Accept exactly ``aa`` and ``bb``."""

    return CnfGrammar(
        nonterminals=(
            Nonterminal(0, "S"),
            Nonterminal(1, "A"),
            Nonterminal(2, "B"),
        ),
        terminals=(Terminal(0, ord("a")), Terminal(1, ord("b"))),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 1, 0),
            TerminalProduction(1, 2, 1),
        ),
        binary_productions=(
            BinaryProduction(2, 0, 1, 1),
            BinaryProduction(3, 0, 2, 2),
        ),
    )


def one_a_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, ord("a")),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )


def frozen_input(
    proposals: tuple[Proposal, ...],
    *,
    canvas: tuple[int | None, ...] = (None, None),
    rows: tuple[tuple[int, ...], ...] = ((0, 1), (0, 1)),
) -> SelectionInput:
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=ADAPTER.vocabulary_size,
            pruning_description="T1000 deterministic common-selector fixture",
        ),
        explicit_support=dict(enumerate(rows)),
        proposals=proposals,
    )
    return SelectionInput(
        grammar=same_pair_grammar(),
        canvas=canvas,
        proposals=proposals,
        support=support,
        tokenizer_adapter=ADAPTER,
        eos_policy=NO_EOS,
    )


def test_same_frozen_input_runs_serial_and_exact_without_overstating_serial() -> None:
    selection_input = frozen_input(
        (
            Proposal(0, position=0, token_id=0, weight=1.0),
            Proposal(1, position=1, token_id=1, weight=10.0),
        )
    )

    serial = select_serial(selection_input, backend=ExactBackend.PYTHON)
    exact = select_exact(selection_input, backend=ExactBackend.PYTHON)

    assert serial.selector is SelectorKind.SERIAL
    assert serial.status is SelectionStatus.FEASIBLE_ON_SUPPORT
    assert serial.status is not SelectionStatus.OPTIMAL
    assert serial.selected_proposal_ids == (0,)
    assert serial.score == 1.0
    assert serial.witness_token_ids == (0, 0)
    assert serial.witness_available
    assert serial.diagnostics["optimization_guarantee"] == "none_order_greedy"

    assert exact.selector is SelectorKind.EXACT
    assert exact.status is SelectionStatus.OPTIMAL
    assert exact.selected_proposal_ids == (1,)
    assert exact.score == 10.0
    assert exact.witness_token_ids == (1, 1)
    assert exact.witness_graph_edge_ids
    assert exact.diagnostics["optimization_guarantee"] == "exact_on_support"

    assert serial.exactness_scope == exact.exactness_scope
    assert exact.exactness_scope == selection_input.support.exactness_scope
    assert serial.runtime_seconds >= 0.0
    assert exact.runtime_seconds >= 0.0
    json.dumps(serial.to_dict())
    json.dumps(exact.to_dict())


@requires_rust
def test_same_common_input_runs_through_production_rust_backend() -> None:
    selection_input = frozen_input(
        (
            Proposal(0, position=0, token_id=0, weight=1.0),
            Proposal(1, position=1, token_id=1, weight=10.0),
        )
    )

    serial = select_serial(selection_input, backend=ExactBackend.RUST)
    exact = select_exact(selection_input, backend=ExactBackend.RUST)

    assert serial.status is SelectionStatus.FEASIBLE_ON_SUPPORT
    assert serial.selected_proposal_ids == (0,)
    assert exact.status is SelectionStatus.OPTIMAL
    assert exact.selected_proposal_ids == (1,)


def test_same_input_contract_preserves_required_eos_and_pad_slots() -> None:
    adapter = CompositionalByteLevelAdapter((b"a", None, None))
    eos_policy = EOSPolicy(
        EOSMode.REQUIRED,
        termination_token_ids=(2,),
        pad_token_id=1,
    )
    canvas = (None, None, None)
    proposals = (
        Proposal(0, position=0, token_id=0, weight=3.0),
        Proposal(1, position=1, token_id=2, weight=2.0),
        Proposal(2, position=2, token_id=1, weight=1.0),
    )
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=adapter.vocabulary_size,
            required_special_token_ids=(1, 2),
        ),
        explicit_support={0: (0, 1, 2), 1: (0, 1, 2), 2: (0, 1, 2)},
        proposals=proposals,
    )
    selection_input = SelectionInput(
        grammar=one_a_grammar(),
        canvas=canvas,
        proposals=proposals,
        support=support,
        tokenizer_adapter=adapter,
        eos_policy=eos_policy,
    )

    serial = select_serial(selection_input, backend=ExactBackend.PYTHON)
    exact = select_exact(selection_input, backend=ExactBackend.PYTHON)

    for result in (serial, exact):
        assert result.selected_proposal_ids == (0, 1, 2)
        assert result.score == 6.0
        assert result.witness_token_ids == (0, 2, 1)
        assert result.witness_eos_position == 1
        assert result.witness_content_endpoint_slot == 1


def test_serial_consumes_saved_proposal_order_without_sorting_by_id_or_weight() -> None:
    low_then_high = frozen_input(
        (
            Proposal(20, position=0, token_id=0, weight=1.0),
            Proposal(10, position=1, token_id=1, weight=10.0),
        )
    )
    high_then_low = frozen_input(tuple(reversed(low_then_high.proposals)))

    first = select_serial(low_then_high, backend=ExactBackend.PYTHON)
    second = select_serial(high_then_low, backend=ExactBackend.PYTHON)

    assert first.selected_proposal_ids == (20,)
    assert first.witness_token_ids == (0, 0)
    assert first.diagnostics["proposal_order"] == (20, 10)
    assert tuple(decision["outcome"] for decision in first.diagnostics["decisions"]) == (
        "accepted",
        "rejected",
    )

    assert second.selected_proposal_ids == (10,)
    assert second.witness_token_ids == (1, 1)
    assert second.diagnostics["proposal_order"] == (10, 20)


def test_serial_preserves_duplicate_choice_provenance_and_zero_weight_contract() -> None:
    selection_input = frozen_input(
        (
            Proposal(5, position=0, token_id=0, weight=1.0),
            Proposal(6, position=0, token_id=0, weight=2.0),
            Proposal(7, position=1, token_id=0, weight=0.0),
        )
    )

    result = select_serial(selection_input, backend=ExactBackend.PYTHON)

    assert result.status is SelectionStatus.FEASIBLE_ON_SUPPORT
    assert result.witness_token_ids == (0, 0)
    assert result.selected_proposal_ids == (5, 6)
    assert result.score == 3.0
    assert result.diagnostics["accepted_proposal_ids"] == (5, 6, 7)
    assert result.diagnostics["feasibility_call_count"] == 3
    assert result.diagnostics["decisions"][1]["reason"] == "already_fixed_match"


def test_unrepresented_proposal_is_rejected_without_claiming_infeasibility() -> None:
    selection_input = frozen_input(
        (Proposal(4, position=0, token_id=1, weight=50.0),),
        rows=((0,), (0, 1)),
    )

    serial = select_serial(selection_input, backend=ExactBackend.PYTHON)
    exact = select_exact(selection_input, backend=ExactBackend.PYTHON)

    assert serial.status is SelectionStatus.FEASIBLE_ON_SUPPORT
    assert serial.score == 0.0
    assert serial.selected_proposal_ids == ()
    assert serial.diagnostics["decisions"][0]["reason"] == "unrepresented_on_support"
    assert serial.diagnostics["feasibility_call_count"] == 1
    assert exact.status is SelectionStatus.OPTIMAL
    assert exact.score == 0.0
    assert exact.selected_proposal_ids == ()


def test_infeasible_saved_support_has_no_score_or_witness_for_either_selector() -> None:
    selection_input = frozen_input((), rows=((0,), (1,)))

    serial = select_serial(selection_input, backend=ExactBackend.PYTHON)
    exact = select_exact(selection_input, backend=ExactBackend.PYTHON)

    assert serial.status is SelectionStatus.INFEASIBLE_ON_SUPPORT
    assert exact.status is SelectionStatus.INFEASIBLE_ON_SUPPORT
    for result in (serial, exact):
        assert result.score is None
        assert result.selected_proposal_ids == ()
        assert not result.witness_available


def test_timeout_is_preserved_and_never_converted_to_infeasible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection_input = frozen_input((Proposal(0, 0, 0, 1.0),))

    def timed_out(*args: object, **kwargs: object) -> ExactCommitResult:
        del args, kwargs
        return ExactCommitResult(
            status=SolveStatus.TIMEOUT,
            exactness_scope=selection_input.support.exactness_scope,
            diagnostics={"fixture": "deterministic_timeout"},
        )

    monkeypatch.setattr(selection_module, "solve_exact_commit", timed_out)

    serial = select_serial(selection_input, backend=ExactBackend.PYTHON)
    exact = select_exact(selection_input, backend=ExactBackend.PYTHON)

    assert serial.status is SelectionStatus.TIMEOUT
    assert exact.status is SelectionStatus.TIMEOUT
    assert serial.status is not SelectionStatus.INFEASIBLE_ON_SUPPORT
    assert exact.status is not SelectionStatus.INFEASIBLE_ON_SUPPORT
    assert serial.score is exact.score is None


def test_score_recomputation_checks_fixed_canvas_and_saved_support() -> None:
    selection_input = frozen_input(
        (Proposal(0, position=1, token_id=0, weight=2.5),),
        canvas=(0, None),
        rows=((0,), (0, 1)),
    )

    assert recompute_witness_selection(selection_input, (0, 0)) == ((0,), 2.5)
    with pytest.raises(ValueError, match="fixed canvas position 0"):
        recompute_witness_selection(selection_input, (1, 1))


def test_common_result_rejects_certificates_on_inconclusive_status() -> None:
    scope = frozen_input(()).support.exactness_scope

    with pytest.raises(ValueError, match="cannot expose a score or witness"):
        SelectionResult(
            selector=SelectorKind.SERIAL,
            status=SelectionStatus.TIMEOUT,
            exactness_scope=scope,
            runtime_seconds=0.1,
            score=0.0,
            witness_token_ids=(0, 0),
        )
