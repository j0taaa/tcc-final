from __future__ import annotations

import pytest

from mwpc_exact import TerminalEdge, WeightedTerminalDAG
from mwpc_exact.reference.graph import GraphCycleError, index_terminal_dag


def edge(edge_id: int, source: int, target: int, label: str, weight: int = 0) -> TerminalEdge:
    return TerminalEdge(edge_id, source, target, label, weight)


def test_index_includes_disconnected_nodes_in_deterministic_order() -> None:
    graph = WeightedTerminalDAG(
        node_ids=(50, 10, 30, 20),
        start_node_id=10,
        final_node_ids=(30,),
        edges=(edge(7, 10, 30, "a"), edge(8, 50, 20, "b")),
    )

    indexed = index_terminal_dag(graph)

    assert indexed.topological_order == (10, 30, 50, 20)
    assert indexed.topological_index == {10: 0, 30: 1, 50: 2, 20: 3}
    assert indexed.outgoing_edges[30] == ()
    assert indexed.incoming_edges[50] == ()


def test_index_preserves_multiple_finals_and_parallel_edges() -> None:
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 2),
        start_node_id=0,
        final_node_ids=(2, 1),
        edges=(
            edge(9, 0, 1, "x", 2),
            edge(3, 0, 1, "x", 5),
            edge(4, 0, 1, "y", 1),
            edge(7, 1, 2, "z", 3),
        ),
    )

    indexed = index_terminal_dag(graph)

    assert graph.final_node_ids == (2, 1)
    assert tuple(item.edge_id for item in indexed.edges_by_endpoints[(0, 1)]) == (3, 4, 9)
    assert tuple(item.edge_id for item in indexed.edges_by_label["x"]) == (3, 9)
    assert tuple(item.edge_id for item in indexed.outgoing_edges[0]) == (3, 4, 9)
    assert indexed.edge_by_id[7].target_state == 2


def test_topological_order_is_independent_of_edge_input_order() -> None:
    edges = (edge(5, 0, 2, "a"), edge(4, 0, 1, "b"), edge(6, 1, 3, "c"))
    first = WeightedTerminalDAG((3, 2, 1, 0), 0, (3,), edges)
    second = WeightedTerminalDAG((0, 1, 2, 3), 0, (3,), tuple(reversed(edges)))

    assert index_terminal_dag(first).topological_order == (0, 1, 2, 3)
    assert index_terminal_dag(second).topological_order == (0, 1, 2, 3)


def test_cycle_is_rejected_even_when_disconnected_from_start() -> None:
    graph = WeightedTerminalDAG(
        node_ids=(0, 1, 10, 11),
        start_node_id=0,
        final_node_ids=(1,),
        edges=(edge(0, 0, 1, "a"), edge(1, 10, 11, "b"), edge(2, 11, 10, "c")),
    )

    with pytest.raises(GraphCycleError, match=r"cycle involves nodes \(10, 11\)"):
        index_terminal_dag(graph)


def test_index_rejects_non_graph_input() -> None:
    with pytest.raises(TypeError, match="WeightedTerminalDAG"):
        index_terminal_dag(object())  # type: ignore[arg-type]
