from __future__ import annotations

from mwpc_exact import Proposal, SolveStatus
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.lexical import build_lexical_rewards
from mwpc_exact.reference.token_aligned import (
    BinaryBackpointer,
    EmptyBackpointer,
    TerminalBackpointer,
    run_cky,
)


def choice_pair_grammar() -> CnfGrammar:
    # S -> A B; A -> x | y; B -> u | v.
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A"), Nonterminal(2, "B")),
        terminals=(
            Terminal(10, "x"),
            Terminal(20, "y"),
            Terminal(30, "u"),
            Terminal(40, "v"),
        ),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(2, 1, 10),
            TerminalProduction(3, 1, 20),
            TerminalProduction(4, 2, 30),
            TerminalProduction(5, 2, 40),
        ),
        binary_productions=(BinaryProduction(1, 0, 1, 2),),
    )


TOKEN_IDS = {10: 100, 20: 200, 30: 300, 40: 400}


def test_cky_hand_computed_max_plus_score() -> None:
    lexical = build_lexical_rewards(
        grammar=choice_pair_grammar(),
        canvas=(None, None),
        proposals=(
            Proposal(1, 0, 100, 2),
            Proposal(2, 0, 200, 3),
            Proposal(3, 1, 300, 5),
            Proposal(4, 1, 400, 1),
        ),
        terminal_token_ids=TOKEN_IDS,
    )

    result = run_cky(choice_pair_grammar(), lexical)

    assert result.status is SolveStatus.OPTIMAL
    assert result.chart.root_entry is not None
    assert result.chart.root_entry.score == 8.0  # y (3) followed by u (5)
    assert result.chart.entry(1, 0, 1) is not None
    assert result.chart.entry(2, 1, 2) is not None


def test_ambiguous_derivations_do_not_double_count_reward() -> None:
    # S -> A B and S -> C D both derive x u. Max-plus chooses one parse, not 2x reward.
    grammar = CnfGrammar(
        nonterminals=(
            Nonterminal(0, "S"),
            Nonterminal(1, "A"),
            Nonterminal(2, "B"),
            Nonterminal(3, "C"),
            Nonterminal(4, "D"),
        ),
        terminals=(Terminal(10, "x"), Terminal(30, "u")),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(10, 1, 10),
            TerminalProduction(11, 2, 30),
            TerminalProduction(12, 3, 10),
            TerminalProduction(13, 4, 30),
        ),
        binary_productions=(
            BinaryProduction(1, 0, 1, 2),
            BinaryProduction(2, 0, 3, 4),
        ),
    )
    lexical = build_lexical_rewards(
        grammar=grammar,
        canvas=(None, None),
        proposals=(Proposal(1, 0, 100, 2), Proposal(2, 1, 300, 5)),
        terminal_token_ids={10: 100, 30: 300},
    )

    result = run_cky(grammar, lexical)

    assert result.chart.root_entry is not None
    assert result.chart.root_entry.score == 7.0
    root_pointer = result.chart.root_entry.backpointer
    assert isinstance(root_pointer, BinaryBackpointer)
    assert root_pointer.production_id == 1


def test_fixed_position_forces_compatible_terminal() -> None:
    grammar = choice_pair_grammar()
    lexical = build_lexical_rewards(
        grammar=grammar,
        canvas=(100, None),
        proposals=(
            Proposal(1, 0, 200, 100),
            Proposal(2, 0, 100, 1),
            Proposal(3, 1, 300, 2),
        ),
        terminal_token_ids=TOKEN_IDS,
    )

    result = run_cky(grammar, lexical)

    assert result.chart.root_entry is not None
    assert result.chart.root_entry.score == 3.0
    left = result.chart.entry(1, 0, 1)
    assert left is not None
    assert left.backpointer == TerminalBackpointer(2, 10)


def test_infeasible_fixed_canvas_is_explicit() -> None:
    grammar = choice_pair_grammar()
    lexical = build_lexical_rewards(
        grammar=grammar,
        canvas=(999, None),
        proposals=(),
        terminal_token_ids=TOKEN_IDS,
    )

    result = run_cky(grammar, lexical)

    assert result.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert result.chart.root_entry is None


def test_equal_score_terminal_tie_keeps_lowest_production_id() -> None:
    grammar = choice_pair_grammar()
    lexical = build_lexical_rewards(
        grammar=grammar,
        canvas=(None, None),
        proposals=(),
        terminal_token_ids=TOKEN_IDS,
    )

    result = run_cky(grammar, lexical)

    left = result.chart.entry(1, 0, 1)
    assert left is not None
    assert left.score == 0.0
    assert left.backpointer == TerminalBackpointer(2, 10)


def test_empty_acceptance_is_an_explicit_zero_width_chart_entry() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(),
        start_nonterminal_id=0,
        accepts_empty=True,
    )
    lexical = build_lexical_rewards(grammar=grammar, canvas=(), proposals=())

    result = run_cky(grammar, lexical)

    assert result.status is SolveStatus.OPTIMAL
    assert result.chart.root_entry is not None
    assert result.chart.root_entry.score == 0.0
    assert isinstance(result.chart.root_entry.backpointer, EmptyBackpointer)


def test_nonempty_canvas_is_infeasible_for_epsilon_only_grammar() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(),
        start_nonterminal_id=0,
        accepts_empty=True,
    )
    lexical = build_lexical_rewards(grammar=grammar, canvas=(None,), proposals=())

    result = run_cky(grammar, lexical)

    assert result.status is SolveStatus.INFEASIBLE_ON_SUPPORT
