from __future__ import annotations

import pytest

from mwpc_exact import ExactnessScope, Proposal, SolveStatus, SupportKind
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.reference.token_aligned import solve_token_aligned

TOKEN_IDS = {10: 10, 20: 20, 30: 30, 40: 40}
SCOPE = ExactnessScope(
    kind=SupportKind.EXPLICIT,
    vocabulary_size=64,
    pruning_description="canonical x/y/z/w token fixture",
)


def branching_grammar() -> CnfGrammar:
    # Language: {x y, z w}.
    return CnfGrammar(
        nonterminals=(
            Nonterminal(0, "S"),
            Nonterminal(1, "X"),
            Nonterminal(2, "Y"),
            Nonterminal(3, "Z"),
            Nonterminal(4, "W"),
        ),
        terminals=(
            Terminal(10, "x"),
            Terminal(20, "y"),
            Terminal(30, "z"),
            Terminal(40, "w"),
        ),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(10, 1, 10),
            TerminalProduction(20, 2, 20),
            TerminalProduction(30, 3, 30),
            TerminalProduction(40, 4, 40),
        ),
        binary_productions=(
            BinaryProduction(1, 0, 1, 2),
            BinaryProduction(2, 0, 3, 4),
        ),
    )


def solve(proposals: tuple[Proposal, ...], canvas: tuple[int | None, ...] = (None, None)):
    return solve_token_aligned(
        grammar=branching_grammar(),
        canvas=canvas,
        proposals=proposals,
        exactness_scope=SCOPE,
        terminal_token_ids=TOKEN_IDS,
    )


def test_all_proposals_are_compatible() -> None:
    # x y satisfies both proposals: 2 + 3 = 5.
    result = solve((Proposal(1, 0, 10, 2), Proposal(2, 1, 20, 3)))

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 5.0
    assert result.selected_proposal_ids == (1, 2)
    assert result.witness_token_ids == (10, 20)


def test_individually_compatible_proposals_can_be_jointly_incompatible() -> None:
    # x extends as x y and w extends as z w, but x w is outside the language.
    assert recognizes_cnf(branching_grammar(), ("x", "y"))
    assert recognizes_cnf(branching_grammar(), ("z", "w"))
    assert not recognizes_cnf(branching_grammar(), ("x", "w"))

    result = solve((Proposal(1, 0, 10, 4), Proposal(2, 1, 40, 5)))

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 5.0
    assert result.selected_proposal_ids == (2,)
    assert result.witness_token_ids == (30, 40)


def test_greedy_confidence_order_is_suboptimal() -> None:
    proposals = (
        Proposal(1, 0, 30, 0.99, model_confidence=0.99),
        Proposal(2, 0, 10, 0.80, model_confidence=0.80),
        Proposal(3, 1, 20, 0.79, model_confidence=0.79),
    )
    # Greedy takes z first and then must emit unproposed w: 0.99 < 0.80 + 0.79.
    assert max(proposals, key=lambda item: item.model_confidence or 0).proposal_id == 1

    result = solve(proposals)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == pytest.approx(1.59)
    assert result.selected_proposal_ids == (2, 3)
    assert result.witness_token_ids == (10, 20)


def test_several_optimum_witnesses_do_not_require_identical_tie_choice() -> None:
    # Both x y and z w match one weight-2 proposal, so both objectives are 2.
    result = solve((Proposal(1, 0, 10, 2), Proposal(2, 0, 30, 2)))

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 2.0
    assert result.witness_token_ids in {(10, 20), (30, 40)}
    assert result.selected_proposal_ids in {(1,), (2,)}


def test_infeasible_fixed_canvas_has_no_certified_objective() -> None:
    # x w crosses the two grammar branches and has no completion on this support.
    result = solve((), canvas=(10, 40))

    assert result.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert result.objective_value is None
    assert result.selected_proposal_ids == ()
    assert result.witness_token_ids == ()


def test_duplicate_matching_proposals_keep_both_stable_ids() -> None:
    # Distinct x proposals both match the witness: 2 + 3 + 1 = 6.
    result = solve(
        (
            Proposal(7, 0, 10, 2),
            Proposal(8, 0, 10, 3),
            Proposal(9, 1, 20, 1),
        )
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 6.0
    assert result.selected_proposal_ids == (7, 8, 9)
    assert result.witness_token_ids == (10, 20)
