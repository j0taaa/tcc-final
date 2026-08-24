from __future__ import annotations

import pytest

from mwpc_exact import EpsilonEdge, SolveStatus, TerminalEdge, WeightedTerminalDAG
from mwpc_exact.reference.dag_parser import EpsilonNormalizationRequired, run_dag_cky
from mwpc_exact.reference.epsilon import normalize_epsilon_edges, solve_cfg_on_epsilon_dag
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.graph import GraphCycleError
from mwpc_exact.reference.graph_oracle import enumerate_best_cfg_path


def single_x_grammar(*, accepts_empty: bool = False) -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(10, "x"),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 10),),
        accepts_empty=accepts_empty,
    )


def test_core_parser_requires_explicit_epsilon_normalization() -> None:
    graph = WeightedTerminalDAG(
        (0, 1, 2),
        0,
        (2,),
        (EpsilonEdge(0, 0, 1), TerminalEdge(1, 1, 2, "x")),
    )

    with pytest.raises(EpsilonNormalizationRequired, match=r"edge_ids=\(0,\)"):
        run_dag_cky(single_x_grammar(), graph)


def test_leading_and_trailing_epsilon_provenance_is_reconstructed_once() -> None:
    graph = WeightedTerminalDAG(
        (0, 1, 2, 3),
        0,
        (3,),
        (
            EpsilonEdge(0, 0, 1, 2, (10,)),
            TerminalEdge(1, 1, 2, "x", 3, matched_proposal_ids=(11,)),
            EpsilonEdge(2, 2, 3, 5, (12,)),
        ),
    )

    result = solve_cfg_on_epsilon_dag(single_x_grammar(), graph)
    oracle = enumerate_best_cfg_path(single_x_grammar(), graph)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == oracle.objective_value == 10.0
    assert result.certificate is not None
    assert result.certificate.witness_graph_edge_ids == (0, 1, 2)
    assert result.certificate.witness_terminal_labels == ("x",)
    assert result.certificate.selected_proposal_ids == (10, 11, 12)


def test_epsilon_chain_between_terminals_is_not_duplicated() -> None:
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "X")),
        terminals=(Terminal(10, "x"),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 1, 10),),
        binary_productions=(BinaryProduction(1, 0, 1, 1),),
    )
    graph = WeightedTerminalDAG(
        (0, 1, 2, 3),
        0,
        (3,),
        (
            TerminalEdge(0, 0, 1, "x", 2),
            EpsilonEdge(1, 1, 2, 5, (20,)),
            TerminalEdge(2, 2, 3, "x", 3),
        ),
    )

    result = solve_cfg_on_epsilon_dag(grammar, graph)

    assert result.objective_value == 10.0
    assert result.certificate is not None
    assert result.certificate.witness_graph_edge_ids == (0, 1, 2)
    assert result.certificate.selected_proposal_ids == (20,)


def test_maximum_epsilon_closure_safely_dominates_lower_weight_path() -> None:
    graph = WeightedTerminalDAG(
        (0, 1, 2),
        0,
        (2,),
        (
            EpsilonEdge(0, 0, 1, 1),
            EpsilonEdge(1, 0, 1, 5),
            TerminalEdge(2, 1, 2, "x", 3),
        ),
    )

    normalization = normalize_epsilon_edges(graph)
    result = solve_cfg_on_epsilon_dag(single_x_grammar(), graph)
    oracle = enumerate_best_cfg_path(single_x_grammar(), graph)

    saturated = [
        edge
        for edge in normalization.normalized_graph.edges
        if edge.source_state == 0 and edge.target_state == 2
    ]
    assert [edge.weight for edge in saturated] == [8.0]
    assert normalization.original_edge_ids_by_normalized_edge_id[saturated[0].edge_id] == (
        1,
        2,
    )
    assert result.objective_value == oracle.objective_value == 8.0


def test_epsilon_only_path_requires_empty_grammar_acceptance() -> None:
    graph = WeightedTerminalDAG(
        (0, 1),
        0,
        (1,),
        (EpsilonEdge(0, 0, 1, 7, (30,)),),
    )

    accepted = solve_cfg_on_epsilon_dag(single_x_grammar(accepts_empty=True), graph)
    rejected = solve_cfg_on_epsilon_dag(single_x_grammar(), graph)
    oracle = enumerate_best_cfg_path(single_x_grammar(accepts_empty=True), graph)

    assert accepted.status is SolveStatus.OPTIMAL
    assert accepted.objective_value == oracle.objective_value == 7.0
    assert accepted.certificate is not None
    assert accepted.certificate.witness_terminal_labels == ()
    assert accepted.certificate.witness_graph_edge_ids == (0,)
    assert rejected.status is SolveStatus.INFEASIBLE_ON_SUPPORT


def test_epsilon_cycle_is_rejected_before_closure() -> None:
    graph = WeightedTerminalDAG(
        (0, 1, 2),
        0,
        (2,),
        (EpsilonEdge(0, 0, 1), EpsilonEdge(1, 1, 0)),
    )

    with pytest.raises(GraphCycleError, match="must be acyclic"):
        normalize_epsilon_edges(graph)
