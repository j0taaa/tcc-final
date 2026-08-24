from __future__ import annotations

from mwpc_exact import Proposal, SolveStatus, TerminalEdge, WeightedTerminalDAG
from mwpc_exact.reference.dag_parser import (
    DagBinaryBackpointer,
    reconstruct_dag_certificate,
    run_dag_cky,
    validate_dag_certificate,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.lexical import build_lexical_rewards
from mwpc_exact.reference.token_aligned import build_token_aligned_support_graph, run_cky


def pair_grammar(*, ambiguous: bool = False) -> CnfGrammar:
    nonterminals = [Nonterminal(0, "S"), Nonterminal(1, "A"), Nonterminal(2, "B")]
    terminal_productions = [TerminalProduction(2, 1, 10), TerminalProduction(3, 2, 20)]
    binary_productions = [BinaryProduction(1, 0, 1, 2)]
    if ambiguous:
        nonterminals.extend((Nonterminal(3, "C"), Nonterminal(4, "D")))
        terminal_productions.extend((TerminalProduction(5, 3, 10), TerminalProduction(6, 4, 20)))
        binary_productions.append(BinaryProduction(4, 0, 3, 4))
    return CnfGrammar(
        nonterminals=tuple(nonterminals),
        terminals=(Terminal(10, "x"), Terminal(20, "y")),
        start_nonterminal_id=0,
        terminal_productions=tuple(terminal_productions),
        binary_productions=tuple(binary_productions),
    )


def test_string_chain_dag_equals_token_aligned_cky() -> None:
    grammar = pair_grammar()
    proposals = (Proposal(4, 0, 100, 2), Proposal(5, 1, 200, 7))
    lexical = build_lexical_rewards(
        grammar=grammar,
        canvas=(None, None),
        proposals=proposals,
        terminal_token_ids={10: 100, 20: 200},
    )
    graph = build_token_aligned_support_graph(grammar, lexical)

    token_solve = run_cky(grammar, lexical)
    graph_solve = run_dag_cky(grammar, graph)
    certificate = reconstruct_dag_certificate(graph_solve)

    assert token_solve.chart.root_entry is not None
    assert certificate.objective_value == token_solve.chart.root_entry.score == 9.0
    assert certificate.witness_terminal_labels == ("x", "y")
    assert certificate.selected_proposal_ids == (4, 5)
    assert validate_dag_certificate(grammar, graph, certificate)


def test_parallel_paths_choose_maximum_edge_score() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(10, "x"),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 10),),
    )
    graph = WeightedTerminalDAG(
        node_ids=(0, 1),
        start_node_id=0,
        final_node_ids=(1,),
        edges=(
            TerminalEdge(8, 0, 1, "x", 2, matched_proposal_ids=(2,)),
            TerminalEdge(3, 0, 1, "x", 5, matched_proposal_ids=(7,)),
        ),
    )

    certificate = reconstruct_dag_certificate(run_dag_cky(grammar, graph))

    assert certificate.objective_value == 5.0
    assert certificate.witness_graph_edge_ids == (3,)
    assert certificate.selected_proposal_ids == (7,)


def test_ambiguous_grammar_does_not_sum_derivations() -> None:
    grammar = pair_grammar(ambiguous=True)
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 2),
        start_node_id=0,
        final_node_ids=(2,),
        edges=(TerminalEdge(0, 0, 1, "x", 3), TerminalEdge(1, 1, 2, "y", 4)),
    )

    solve = run_dag_cky(grammar, graph)
    certificate = reconstruct_dag_certificate(solve)

    assert certificate.objective_value == 7.0
    root = solve.chart.entry(0, 0, 2)
    assert root is not None
    assert isinstance(root.backpointer, DagBinaryBackpointer)
    assert root.backpointer.production_id == 1


def test_multiple_finals_choose_best_grammar_valid_path() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(10, "x"),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 10),),
    )
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 2, 3),
        start_node_id=0,
        final_node_ids=(1, 2, 3),
        edges=(TerminalEdge(0, 0, 1, "x", 2), TerminalEdge(1, 0, 2, "x", 9)),
    )

    solve = run_dag_cky(grammar, graph)

    assert solve.status is SolveStatus.OPTIMAL
    assert solve.final_node_id == 2
    assert reconstruct_dag_certificate(solve).objective_value == 9.0


def test_infeasible_intersection_has_distinct_status() -> None:
    grammar = pair_grammar()
    graph = WeightedTerminalDAG(
        node_ids=(0, 1),
        start_node_id=0,
        final_node_ids=(1,),
        edges=(TerminalEdge(0, 0, 1, "x", 100),),
    )

    solve = run_dag_cky(grammar, graph)

    assert solve.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert solve.final_node_id is None


def test_empty_path_is_explicit_when_start_is_final_and_grammar_accepts_empty() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(),
        start_nonterminal_id=0,
        accepts_empty=True,
    )
    graph = WeightedTerminalDAG(node_ids=(5,), start_node_id=5, final_node_ids=(5,))

    solve = run_dag_cky(grammar, graph)
    certificate = reconstruct_dag_certificate(solve)

    assert solve.status is SolveStatus.OPTIMAL
    assert certificate == type(certificate)(0.0, (), (), ())
    assert validate_dag_certificate(grammar, graph, certificate)
