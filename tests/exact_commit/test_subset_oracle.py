from __future__ import annotations

import pytest

from mwpc_exact import ExactnessScope, Proposal, SolveStatus, SupportKind
from mwpc_exact.reference.brute_force import (
    SearchSpaceLimitExceeded,
    exhaustive_completion_oracle,
    exhaustive_subset_oracle,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.token_aligned import solve_token_aligned


def branching_grammar() -> CnfGrammar:
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
SCOPE = ExactnessScope(
    kind=SupportKind.EXPLICIT,
    vocabulary_size=64,
    pruning_description="four-token subset-oracle fixture",
)


@pytest.mark.parametrize(
    ("proposals", "canvas", "expected_status", "expected_objective"),
    [
        (
            (Proposal(1, 0, 10, 2), Proposal(2, 1, 20, 3)),
            (None, None),
            SolveStatus.OPTIMAL,
            5.0,
        ),
        (
            (Proposal(1, 0, 10, 4), Proposal(2, 1, 40, 5)),
            (None, None),
            SolveStatus.OPTIMAL,
            5.0,
        ),
        (
            (
                Proposal(1, 0, 30, 0.99),
                Proposal(2, 0, 10, 0.80),
                Proposal(3, 1, 20, 0.79),
            ),
            (None, None),
            SolveStatus.OPTIMAL,
            1.59,
        ),
        (
            (Proposal(1, 0, 10, 2), Proposal(2, 0, 30, 2)),
            (None, None),
            SolveStatus.OPTIMAL,
            2.0,
        ),
        ((), (10, 40), SolveStatus.INFEASIBLE_ON_SUPPORT, None),
        (
            (
                Proposal(7, 0, 10, 2),
                Proposal(8, 0, 10, 3),
                Proposal(9, 1, 20, 1),
            ),
            (None, None),
            SolveStatus.OPTIMAL,
            6.0,
        ),
    ],
)
def test_completion_subset_and_cky_agree_on_canonical_fixtures(
    proposals: tuple[Proposal, ...],
    canvas: tuple[int | None, ...],
    expected_status: SolveStatus,
    expected_objective: float | None,
) -> None:
    grammar = branching_grammar()
    completion = exhaustive_completion_oracle(
        grammar=grammar,
        per_position_support=SUPPORT,
        canvas=canvas,
        proposals=proposals,
        terminal_labels_by_token_id=LABELS,
    )
    subset = exhaustive_subset_oracle(
        grammar=grammar,
        per_position_support=SUPPORT,
        canvas=canvas,
        proposals=proposals,
        terminal_labels_by_token_id=LABELS,
    )
    cky = solve_token_aligned(
        grammar=grammar,
        canvas=canvas,
        proposals=proposals,
        exactness_scope=SCOPE,
        terminal_token_ids={10: 10, 20: 20, 30: 30, 40: 40},
    )

    assert completion.status is subset.status is cky.status is expected_status
    if expected_objective is None:
        assert completion.objective_value is subset.objective_value is cky.objective_value is None
    else:
        assert completion.objective_value == pytest.approx(expected_objective)
        assert subset.objective_value == pytest.approx(expected_objective)
        assert cky.objective_value == pytest.approx(expected_objective)


def test_subset_oracle_preserves_a_compatibility_witness_and_duplicate_ids() -> None:
    result = exhaustive_subset_oracle(
        grammar=branching_grammar(),
        per_position_support=SUPPORT,
        canvas=(None, None),
        proposals=(
            Proposal(7, 0, 10, 2),
            Proposal(8, 0, 10, 3),
            Proposal(9, 1, 40, 4),
        ),
        terminal_labels_by_token_id=LABELS,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 5.0
    assert result.selected_proposal_ids == (7, 8)
    assert result.witness_token_ids == (10, 20)
    assert result.witness_terminal_labels == ("x", "y")


def test_subset_oracle_has_an_explicit_subset_count_guard() -> None:
    proposals = tuple(Proposal(index, 0, 10, 1) for index in range(5))

    with pytest.raises(SearchSpaceLimitExceeded, match="32 exceeds maximum 31"):
        exhaustive_subset_oracle(
            grammar=branching_grammar(),
            per_position_support=SUPPORT,
            canvas=(None, None),
            proposals=proposals,
            terminal_labels_by_token_id=LABELS,
            max_subsets=31,
        )
