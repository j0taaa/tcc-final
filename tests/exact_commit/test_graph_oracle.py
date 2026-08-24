from __future__ import annotations

import random

import pytest

from mwpc_exact import SolveStatus, TerminalEdge, WeightedTerminalDAG
from mwpc_exact.reference.dag_parser import reconstruct_dag_certificate, run_dag_cky
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.graph_oracle import (
    PathEnumerationLimitExceeded,
    enumerate_best_cfg_path,
)


def nonempty_xy_grammar() -> CnfGrammar:
    # S -> S S | x | y accepts every non-empty x/y string. Ambiguous parses
    # remain irrelevant to a path's edge-weight objective.
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(10, "x"), Terminal(20, "y")),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(1, 0, 10), TerminalProduction(2, 0, 20)),
        binary_productions=(BinaryProduction(3, 0, 0, 0),),
    )


def random_tiny_dag(seed: int) -> WeightedTerminalDAG:
    rng = random.Random(seed)
    node_count = rng.randint(2, 5)
    edges: list[TerminalEdge] = []
    edge_id = 0
    for source in range(node_count - 1):
        for target in range(source + 1, node_count):
            parallel_count = rng.randrange(3) if rng.random() < 0.65 else 0
            for _ in range(parallel_count):
                edges.append(
                    TerminalEdge(
                        edge_id=edge_id,
                        source_state=source,
                        target_state=target,
                        terminal_label=rng.choice(("x", "y", "z")),
                        weight=rng.randint(0, 9),
                        matched_proposal_ids=(edge_id,),
                    )
                )
                edge_id += 1
    finals = tuple(
        node_id for node_id in range(1, node_count) if rng.random() < 0.5
    ) or (node_count - 1,)
    return WeightedTerminalDAG(tuple(range(node_count)), 0, finals, tuple(edges))


def test_oracle_sums_each_path_edge_once() -> None:
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 2),
        start_node_id=0,
        final_node_ids=(2,),
        edges=(TerminalEdge(0, 0, 1, "x", 4), TerminalEdge(1, 1, 2, "y", 7)),
    )

    result = enumerate_best_cfg_path(nonempty_xy_grammar(), graph)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 11.0
    assert result.enumerated_path_count == 1
    assert result.certificate is not None
    assert result.certificate.witness_graph_edge_ids == (0, 1)


def test_oracle_distinguishes_no_final_path_from_grammar_infeasibility() -> None:
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 2),
        start_node_id=0,
        final_node_ids=(2,),
        edges=(TerminalEdge(0, 0, 1, "x", 4),),
    )

    result = enumerate_best_cfg_path(nonempty_xy_grammar(), graph)

    assert result.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert result.enumerated_path_count == 0


def test_oracle_path_limit_is_not_reported_as_infeasible() -> None:
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 2),
        start_node_id=0,
        final_node_ids=(2,),
        edges=tuple(
            [TerminalEdge(edge_id, 0, 1, "x") for edge_id in range(4)]
            + [TerminalEdge(edge_id, 1, 2, "y") for edge_id in range(4, 8)]
        ),
    )

    with pytest.raises(PathEnumerationLimitExceeded, match="max_paths=3"):
        enumerate_best_cfg_path(nonempty_xy_grammar(), graph, max_paths=3)


def test_graph_parser_agrees_with_path_oracle_on_250_recorded_seeds() -> None:
    grammar = nonempty_xy_grammar()
    for seed in range(250):
        graph = random_tiny_dag(seed)
        parser = run_dag_cky(grammar, graph)
        oracle = enumerate_best_cfg_path(grammar, graph, max_paths=10_000)
        assert parser.status is oracle.status, f"status mismatch at seed={seed}"
        if parser.status is SolveStatus.OPTIMAL:
            parser_certificate = reconstruct_dag_certificate(parser)
            assert parser_certificate.objective_value == oracle.objective_value, (
                f"objective mismatch at seed={seed}"
            )
