"""Validation and deterministic indexing for weighted terminal DAGs."""

from __future__ import annotations

import heapq
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from mwpc_exact.types import (
    EpsilonEdge,
    GraphEdge,
    TerminalEdge,
    TerminalLabel,
    WeightedTerminalDAG,
)


class GraphValidationError(ValueError):
    """A weighted terminal graph violates the reference-solver contract."""


class GraphCycleError(GraphValidationError):
    """A weighted terminal graph contains a directed cycle."""


@dataclass(frozen=True, slots=True)
class IndexedTerminalDAG:
    """One fully validated graph plus immutable deterministic indices."""

    graph: WeightedTerminalDAG
    topological_order: tuple[int, ...]
    topological_index: Mapping[int, int]
    edge_by_id: Mapping[int, GraphEdge]
    outgoing_edges: Mapping[int, tuple[GraphEdge, ...]]
    incoming_edges: Mapping[int, tuple[GraphEdge, ...]]
    edges_by_label: Mapping[TerminalLabel, tuple[TerminalEdge, ...]]
    edges_by_endpoints: Mapping[tuple[int, int], tuple[GraphEdge, ...]]

    def __post_init__(self) -> None:
        if not isinstance(self.graph, WeightedTerminalDAG):
            raise TypeError("graph must be a WeightedTerminalDAG")


def index_terminal_dag(graph: WeightedTerminalDAG) -> IndexedTerminalDAG:
    """Validate and index a finite acyclic terminal graph.

    Kahn's algorithm uses node IDs as the priority key, making the order
    independent of input edge order. All edge indices use stable edge-ID order
    and retain parallel edges rather than collapsing them.
    """
    if not isinstance(graph, WeightedTerminalDAG):
        raise TypeError("graph must be a WeightedTerminalDAG")

    node_ids = tuple(graph.node_ids)
    node_set = set(node_ids)
    if len(node_set) != len(node_ids):
        raise GraphValidationError("node IDs must be unique")
    if graph.start_node_id not in node_set:
        raise GraphValidationError("start node must reference an existing node")
    if not graph.final_node_ids:
        raise GraphValidationError("at least one final node is required")
    if any(final_id not in node_set for final_id in graph.final_node_ids):
        raise GraphValidationError("final nodes must reference existing nodes")

    edges = tuple(sorted(graph.edges, key=lambda edge: edge.edge_id))
    edge_by_id: dict[int, GraphEdge] = {}
    outgoing: dict[int, list[GraphEdge]] = {node_id: [] for node_id in node_ids}
    incoming: dict[int, list[GraphEdge]] = {node_id: [] for node_id in node_ids}
    by_label: dict[TerminalLabel, list[TerminalEdge]] = {}
    by_endpoints: dict[tuple[int, int], list[GraphEdge]] = {}
    indegree = dict.fromkeys(node_ids, 0)

    for edge in edges:
        if not isinstance(edge, (TerminalEdge, EpsilonEdge)):
            raise TypeError("graph edges must contain only graph edge instances")
        if edge.edge_id in edge_by_id:
            raise GraphValidationError(f"duplicate edge ID: {edge.edge_id}")
        if edge.source_state not in node_set or edge.target_state not in node_set:
            raise GraphValidationError(
                f"edge {edge.edge_id} endpoint does not reference an existing node"
            )
        edge_by_id[edge.edge_id] = edge
        outgoing[edge.source_state].append(edge)
        incoming[edge.target_state].append(edge)
        if isinstance(edge, TerminalEdge):
            by_label.setdefault(edge.terminal_label, []).append(edge)
        by_endpoints.setdefault((edge.source_state, edge.target_state), []).append(edge)
        indegree[edge.target_state] += 1

    ready = [node_id for node_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    topological_order: list[int] = []
    while ready:
        node_id = heapq.heappop(ready)
        topological_order.append(node_id)
        for edge in outgoing[node_id]:
            indegree[edge.target_state] -= 1
            if indegree[edge.target_state] == 0:
                heapq.heappush(ready, edge.target_state)

    if len(topological_order) != len(node_ids):
        cyclic_nodes = tuple(sorted(node_id for node_id, degree in indegree.items() if degree > 0))
        raise GraphCycleError(
            f"weighted terminal graph must be acyclic; cycle involves nodes {cyclic_nodes}"
        )

    order = tuple(topological_order)
    order_index = {node_id: index for index, node_id in enumerate(order)}
    for edge in edges:
        if order_index[edge.source_state] >= order_index[edge.target_state]:
            raise GraphCycleError(f"edge {edge.edge_id} violates the computed topological order")

    return IndexedTerminalDAG(
        graph=graph,
        topological_order=order,
        topological_index=MappingProxyType(order_index),
        edge_by_id=MappingProxyType(edge_by_id),
        outgoing_edges=MappingProxyType(
            {node_id: tuple(node_edges) for node_id, node_edges in outgoing.items()}
        ),
        incoming_edges=MappingProxyType(
            {node_id: tuple(node_edges) for node_id, node_edges in incoming.items()}
        ),
        edges_by_label=MappingProxyType(
            {label: tuple(label_edges) for label, label_edges in by_label.items()}
        ),
        edges_by_endpoints=MappingProxyType(
            {endpoints: tuple(endpoint_edges) for endpoints, endpoint_edges in by_endpoints.items()}
        ),
    )
