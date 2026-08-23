from __future__ import annotations

from math import inf

import pytest

from mwpc_exact import Proposal
from mwpc_exact.reference.grammar import (
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.lexical import build_lexical_rewards


def alternatives_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(10, "alpha"), Terminal(20, "beta"), Terminal(30, "gamma")),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(1, 0, 10),
            TerminalProduction(2, 0, 20),
            TerminalProduction(3, 0, 30),
        ),
    )


TOKEN_IDS = {10: 101, 20: 202, 30: 303}


def test_unfixed_alternatives_get_duplicate_sum_or_zero_reward() -> None:
    table = build_lexical_rewards(
        grammar=alternatives_grammar(),
        canvas=(None,),
        proposals=(
            Proposal(7, 0, 101, 2),
            Proposal(8, 0, 101, 3),
            Proposal(9, 0, 202, 1),
        ),
        terminal_token_ids=TOKEN_IDS,
    )

    assert table.reward(0, 10).score == 5.0
    assert table.reward(0, 10).matched_proposal_ids == (7, 8)
    assert table.reward(0, 20).score == 1.0
    assert table.reward(0, 20).matched_proposal_ids == (9,)
    assert table.reward(0, 30).score == 0.0
    assert table.reward(0, 30).matched_proposal_ids == ()


def test_fixed_position_sets_every_conflicting_terminal_to_negative_infinity() -> None:
    table = build_lexical_rewards(
        grammar=alternatives_grammar(),
        canvas=(202,),
        proposals=(Proposal(1, 0, 101, 100), Proposal(2, 0, 202, 4)),
        terminal_token_ids=TOKEN_IDS,
    )

    assert table.reward(0, 10).score == -inf
    assert table.reward(0, 10).matched_proposal_ids == ()
    assert table.reward(0, 20).score == 4.0
    assert table.reward(0, 20).matched_proposal_ids == (2,)
    assert table.reward(0, 30).score == -inf


def test_zero_weight_proposal_does_not_enter_positive_certificate_ids() -> None:
    table = build_lexical_rewards(
        grammar=alternatives_grammar(),
        canvas=(None,),
        proposals=(Proposal(4, 0, 303, 0),),
        terminal_token_ids=TOKEN_IDS,
    )

    assert table.reward(0, 30).score == 0.0
    assert table.reward(0, 30).matched_proposal_ids == ()


def test_fixed_token_outside_grammar_support_makes_entire_row_infeasible() -> None:
    table = build_lexical_rewards(
        grammar=alternatives_grammar(),
        canvas=(999,),
        proposals=(),
        terminal_token_ids=TOKEN_IDS,
    )

    assert all(cell.score == -inf for cell in table.rows[0].values())


def test_string_terminal_labels_require_explicit_token_alignment() -> None:
    with pytest.raises(ValueError, match="terminal_token_ids is required"):
        build_lexical_rewards(
            grammar=alternatives_grammar(),
            canvas=(None,),
            proposals=(),
        )


def test_alignment_must_cover_each_terminal_exactly_once() -> None:
    with pytest.raises(ValueError, match="cover exactly"):
        build_lexical_rewards(
            grammar=alternatives_grammar(),
            canvas=(None,),
            proposals=(),
            terminal_token_ids={10: 101, 20: 202},
        )
    with pytest.raises(ValueError, match="must be unique"):
        build_lexical_rewards(
            grammar=alternatives_grammar(),
            canvas=(None,),
            proposals=(),
            terminal_token_ids={10: 101, 20: 101, 30: 303},
        )


def test_out_of_canvas_proposal_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside the finite canvas"):
        build_lexical_rewards(
            grammar=alternatives_grammar(),
            canvas=(None,),
            proposals=(Proposal(1, 1, 101, 1),),
            terminal_token_ids=TOKEN_IDS,
        )


def test_empty_terminal_support_builds_an_infeasible_row_for_epsilon_only_grammar() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(),
        start_nonterminal_id=0,
        accepts_empty=True,
    )

    table = build_lexical_rewards(
        grammar=grammar,
        canvas=(None,),
        proposals=(),
    )

    assert table.slot_count == 1
    assert dict(table.rows[0]) == {}


def test_explicit_per_position_support_sets_absent_grammar_tokens_to_negative_infinity() -> None:
    table = build_lexical_rewards(
        grammar=alternatives_grammar(),
        canvas=(None,),
        proposals=(Proposal(1, 0, 101, 100),),
        terminal_token_ids=TOKEN_IDS,
        per_position_support=((303,),),
    )

    assert table.reward(0, 10).score == -inf
    assert table.reward(0, 20).score == -inf
    assert table.reward(0, 30).score == 0.0
