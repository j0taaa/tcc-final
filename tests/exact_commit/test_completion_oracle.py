from __future__ import annotations

import pytest

from mwpc_exact import Proposal, SolveStatus
from mwpc_exact.reference.brute_force import (
    SearchSpaceLimitExceeded,
    exhaustive_completion_oracle,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
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


SUPPORT = ((10, 30), (20, 40))
LABELS = {10: "x", 20: "y", 30: "z", 40: "w"}


def test_completion_oracle_matches_hand_computed_joint_incompatibility() -> None:
    # x@0 and w@1 cannot coexist; w is heavier, so z w scores 5 instead of 4.
    result = exhaustive_completion_oracle(
        grammar=branching_grammar(),
        per_position_support=SUPPORT,
        canvas=(None, None),
        proposals=(Proposal(1, 0, 10, 4), Proposal(2, 1, 40, 5)),
        terminal_labels_by_token_id=LABELS,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 5.0
    assert result.optima[0].witness_token_ids == (30, 40)
    assert result.optima[0].selected_proposal_ids == (2,)
    assert result.search_space_size == 4
    assert result.grammar_valid_completions == 2


def test_completion_oracle_returns_all_optima_in_support_order() -> None:
    result = exhaustive_completion_oracle(
        grammar=branching_grammar(),
        per_position_support=SUPPORT,
        canvas=(None, None),
        proposals=(Proposal(1, 0, 10, 2), Proposal(2, 0, 30, 2)),
        terminal_labels_by_token_id=LABELS,
        return_all_optima=True,
    )

    assert result.objective_value == 2.0
    assert tuple(item.witness_token_ids for item in result.optima) == (
        (10, 20),
        (30, 40),
    )


def test_completion_oracle_filters_fixed_position_violations() -> None:
    result = exhaustive_completion_oracle(
        grammar=branching_grammar(),
        per_position_support=SUPPORT,
        canvas=(10, None),
        proposals=(Proposal(1, 0, 30, 100), Proposal(2, 1, 20, 3)),
        terminal_labels_by_token_id=LABELS,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 3.0
    assert result.optima[0].witness_token_ids == (10, 20)
    assert result.fixed_compatible_completions == 2


def test_completion_oracle_reports_infeasible_fixed_canvas() -> None:
    result = exhaustive_completion_oracle(
        grammar=branching_grammar(),
        per_position_support=SUPPORT,
        canvas=(10, 40),
        proposals=(),
        terminal_labels_by_token_id=LABELS,
    )

    assert result.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert result.objective_value is None
    assert result.optima == ()
    assert result.fixed_compatible_completions == 1
    assert result.grammar_valid_completions == 0


def test_completion_oracle_preserves_duplicate_positive_proposal_ids() -> None:
    result = exhaustive_completion_oracle(
        grammar=branching_grammar(),
        per_position_support=SUPPORT,
        canvas=(None, None),
        proposals=(Proposal(7, 0, 10, 2), Proposal(8, 0, 10, 3)),
        terminal_labels_by_token_id=LABELS,
    )

    assert result.objective_value == 5.0
    assert result.optima[0].selected_proposal_ids == (7, 8)


def test_completion_oracle_search_guard_is_explicit_before_enumeration() -> None:
    with pytest.raises(SearchSpaceLimitExceeded, match="16 exceeds maximum 15") as error:
        exhaustive_completion_oracle(
            grammar=branching_grammar(),
            per_position_support=((10, 20, 30, 40),) * 2,
            canvas=(None, None),
            proposals=(),
            terminal_labels_by_token_id=LABELS,
            max_completions=15,
        )

    assert error.value.search_space_size == 16
    assert error.value.maximum == 15


def test_completion_oracle_rejects_duplicate_support_choices() -> None:
    with pytest.raises(ValueError, match="duplicate token IDs"):
        exhaustive_completion_oracle(
            grammar=branching_grammar(),
            per_position_support=((10, 10), (20,)),
            canvas=(None, None),
            proposals=(),
            terminal_labels_by_token_id=LABELS,
        )
