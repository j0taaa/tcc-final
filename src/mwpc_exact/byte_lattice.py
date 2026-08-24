"""Exact expansion of finite token choices into private raw-byte paths."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import pairwise
from math import fsum, isfinite
from typing import cast

from mwpc_exact.token_lattice import TokenLattice, TokenLatticePath
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import TerminalEdge, TokenArc, WeightedTerminalDAG


def _non_negative_id(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _id_tuple(value: object, field_name: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of integer IDs")
    result = tuple(_non_negative_id(item, f"{field_name} item") for item in value)
    if len(set(result)) != len(result):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


@dataclass(frozen=True, slots=True)
class ByteLatticePath:
    """One complete token path and its exact expanded graph-edge witness."""

    token_path: TokenLatticePath
    graph_edge_ids: tuple[int, ...]
    emitted_bytes: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.token_path, TokenLatticePath):
            raise TypeError("token_path must be a TokenLatticePath")
        graph_edge_ids = _id_tuple(self.graph_edge_ids, "graph_edge_ids")
        if not isinstance(self.emitted_bytes, (bytes, bytearray)):
            raise TypeError("emitted_bytes must be bytes")
        emitted_bytes = bytes(self.emitted_bytes)
        if len(graph_edge_ids) != len(emitted_bytes):
            raise ValueError("graph_edge_ids must contain exactly one edge per emitted byte")
        object.__setattr__(self, "graph_edge_ids", graph_edge_ids)
        object.__setattr__(self, "emitted_bytes", emitted_bytes)

    @property
    def terminal_labels(self) -> tuple[int, ...]:
        """Return raw bytes as integer terminal labels in ``[0, 255]``."""

        return tuple(self.emitted_bytes)

    @property
    def objective_value(self) -> float:
        return self.token_path.objective_value

    @property
    def matched_proposal_ids(self) -> tuple[int, ...]:
        return self.token_path.matched_proposal_ids

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible byte-path metadata."""

        return {
            "token_path": self.token_path.to_dict(),
            "graph_edge_ids": list(self.graph_edge_ids),
            "terminal_labels": list(self.terminal_labels),
            "emitted_bytes_hex": self.emitted_bytes.hex(),
        }


@dataclass(frozen=True, slots=True)
class ByteLattice:
    """A terminal DAG obtained by expanding every token choice independently."""

    token_lattice: TokenLattice
    token_arcs: tuple[TokenArc, ...]
    graph: WeightedTerminalDAG
    terminal_edge_ids_by_token_edge: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.token_lattice, TokenLattice):
            raise TypeError("token_lattice must be a TokenLattice")
        token_arcs = tuple(self.token_arcs)
        if not all(isinstance(arc, TokenArc) for arc in token_arcs):
            raise TypeError("token_arcs must contain only TokenArc instances")
        if len(token_arcs) != len(self.token_lattice.choices):
            raise ValueError("there must be exactly one byte-bearing arc per token choice")
        for choice, arc in zip(self.token_lattice.choices, token_arcs, strict=True):
            if (
                arc.token_edge_id != choice.token_edge_id
                or arc.slot != choice.position
                or arc.token_id != choice.token_id
                or arc.source_boundary != choice.source_boundary
                or arc.target_boundary != choice.target_boundary
                or arc.weight != choice.weight
                or arc.matched_proposal_ids != choice.matched_proposal_ids
            ):
                raise ValueError("token arc metadata must exactly preserve its token choice")
            if not arc.emitted_bytes:
                raise ValueError("empty token emissions are unsupported")

        if not isinstance(self.graph, WeightedTerminalDAG):
            raise TypeError("graph must be a WeightedTerminalDAG")
        if self.graph.start_node_id != self.token_lattice.start_boundary:
            raise ValueError("byte graph start must equal the token-lattice start boundary")
        if self.graph.final_node_ids != (self.token_lattice.final_boundary,):
            raise ValueError("byte graph must have exactly the token-lattice final boundary")
        if not all(isinstance(edge, TerminalEdge) for edge in self.graph.edges):
            raise ValueError("ordinary byte expansion must contain only terminal edges")
        terminal_edges = cast(tuple[TerminalEdge, ...], self.graph.edges)

        raw_edge_rows = tuple(self.terminal_edge_ids_by_token_edge)
        if len(raw_edge_rows) != len(token_arcs):
            raise ValueError("terminal edge rows must align one-to-one with token arcs")
        edge_rows = tuple(
            _id_tuple(row, f"terminal edge row {token_edge_id}")
            for token_edge_id, row in enumerate(raw_edge_rows)
        )
        if any(not row for row in edge_rows):
            raise ValueError("every token arc must expand to at least one terminal edge")
        flattened_edge_ids = tuple(edge_id for row in edge_rows for edge_id in row)
        if flattened_edge_ids != tuple(range(len(flattened_edge_ids))):
            raise ValueError("terminal edge IDs must be contiguous in canonical expansion order")
        if tuple(edge.edge_id for edge in terminal_edges) != flattened_edge_ids:
            raise ValueError("terminal edge rows must cover the graph exactly in edge-ID order")
        edge_by_id = {edge.edge_id: edge for edge in terminal_edges}

        physical_boundaries = set(self.token_lattice.boundary_ids)
        observed_intermediate_states: list[int] = []
        for arc, edge_ids in zip(token_arcs, edge_rows, strict=True):
            if len(edge_ids) != len(arc.emitted_bytes):
                raise ValueError("a token arc must have exactly one terminal edge per byte")
            edges = tuple(edge_by_id[edge_id] for edge_id in edge_ids)
            cursor = arc.source_boundary
            for offset, (byte_value, edge) in enumerate(zip(arc.emitted_bytes, edges, strict=True)):
                if edge.source_state != cursor:
                    raise ValueError("terminal edges for a token must form one connected path")
                if edge.terminal_label != byte_value:
                    raise ValueError("terminal edge labels must exactly equal token raw bytes")
                if edge.provenance_token_edge_id != arc.token_edge_id:
                    raise ValueError("every expanded byte edge must retain token-edge identity")
                if offset == 0:
                    if (
                        edge.weight != arc.weight
                        or edge.matched_proposal_ids != arc.matched_proposal_ids
                    ):
                        raise ValueError(
                            "the first byte edge must carry all token reward and provenance"
                        )
                elif edge.weight != 0.0 or edge.matched_proposal_ids:
                    raise ValueError("only the first byte edge may carry reward or proposals")
                cursor = edge.target_state
            if cursor != arc.target_boundary:
                raise ValueError("a token byte path must end at its target physical boundary")
            intermediate_states = tuple(edge.target_state for edge in edges[:-1])
            if any(state in physical_boundaries for state in intermediate_states):
                raise ValueError("token byte paths cannot use physical boundaries internally")
            observed_intermediate_states.extend(intermediate_states)

        if len(set(observed_intermediate_states)) != len(observed_intermediate_states):
            raise ValueError("token byte paths must not share intermediate states")
        expected_intermediate_states = tuple(
            range(
                len(self.token_lattice.boundary_ids),
                len(self.token_lattice.boundary_ids) + len(observed_intermediate_states),
            )
        )
        if tuple(observed_intermediate_states) != expected_intermediate_states:
            raise ValueError("intermediate state IDs must follow canonical token/byte order")
        expected_node_ids = tuple(
            range(len(self.token_lattice.boundary_ids) + len(observed_intermediate_states))
        )
        if self.graph.node_ids != expected_node_ids:
            raise ValueError(
                "byte graph nodes must be exactly the physical and intermediate states"
            )

        object.__setattr__(self, "token_arcs", token_arcs)
        object.__setattr__(self, "terminal_edge_ids_by_token_edge", edge_rows)

    @property
    def terminal_edges(self) -> tuple[TerminalEdge, ...]:
        """Return the graph edges narrowed by the byte-lattice invariant."""

        return cast(tuple[TerminalEdge, ...], self.graph.edges)

    def terminal_edges_for_token(self, token_edge_id: int) -> tuple[TerminalEdge, ...]:
        """Return one token choice's private byte path in emission order."""

        token_edge_id = _non_negative_id(token_edge_id, "token_edge_id")
        if token_edge_id >= len(self.token_arcs):
            raise ValueError(f"unknown token edge ID: {token_edge_id}")
        edge_by_id = {edge.edge_id: edge for edge in self.terminal_edges}
        return tuple(
            edge_by_id[edge_id] for edge_id in self.terminal_edge_ids_by_token_edge[token_edge_id]
        )

    def expand_path(self, token_path: TokenLatticePath) -> ByteLatticePath:
        """Expand one independently validated complete token path to graph edges."""

        self.token_lattice.validate_path(token_path)
        graph_edge_ids = tuple(
            edge_id
            for token_edge_id in token_path.token_edge_ids
            for edge_id in self.terminal_edge_ids_by_token_edge[token_edge_id]
        )
        emitted_bytes = b"".join(
            self.token_arcs[token_edge_id].emitted_bytes
            for token_edge_id in token_path.token_edge_ids
        )
        return ByteLatticePath(
            token_path=token_path,
            graph_edge_ids=graph_edge_ids,
            emitted_bytes=emitted_bytes,
        )

    def iter_paths(self) -> Iterator[ByteLatticePath]:
        """Enumerate expanded paths for tiny correctness fixtures and oracles."""

        for token_path in self.token_lattice.iter_paths():
            yield self.expand_path(token_path)

    def validate_path(self, path: ByteLatticePath) -> None:
        """Independently validate token, byte, edge, score, and proposal metadata."""

        if not isinstance(path, ByteLatticePath):
            raise TypeError("path must be a ByteLatticePath")
        expected = self.expand_path(path.token_path)
        if path != expected:
            raise ValueError("byte path metadata does not match its token-edge expansion")
        edge_by_id = {edge.edge_id: edge for edge in self.terminal_edges}
        edges = tuple(edge_by_id[edge_id] for edge_id in path.graph_edge_ids)
        if path.graph_edge_ids:
            if edges[0].source_state != self.graph.start_node_id:
                raise ValueError("complete byte path must start at the graph start node")
            if edges[-1].target_state not in self.graph.final_node_ids:
                raise ValueError("complete byte path must end at a graph final node")
            if any(left.target_state != right.source_state for left, right in pairwise(edges)):
                raise ValueError("complete byte path graph edges must be connected")
        elif self.graph.start_node_id not in self.graph.final_node_ids:
            raise ValueError("an empty byte path is valid only when start is final")
        if tuple(edge.terminal_label for edge in edges) != path.terminal_labels:
            raise ValueError("byte path terminal labels do not match its emitted bytes")
        try:
            recomputed_objective = fsum(edge.weight for edge in edges)
        except OverflowError as exc:
            raise ValueError("byte path edge weights must have a finite sum") from exc
        if not isfinite(recomputed_objective) or recomputed_objective != path.objective_value:
            raise ValueError("byte path edge weights do not match its token objective")
        selected = tuple(proposal_id for edge in edges for proposal_id in edge.matched_proposal_ids)
        if selected != path.matched_proposal_ids:
            raise ValueError("byte path proposal provenance does not match its token path")

    @property
    def diagnostics(self) -> dict[str, object]:
        """Return machine-readable byte-expansion diagnostics."""

        return {
            "token_choice_count": len(self.token_arcs),
            "terminal_node_count": len(self.graph.node_ids),
            "terminal_edge_count": len(self.terminal_edges),
            "token_emission_lengths": [len(arc.emitted_bytes) for arc in self.token_arcs],
            "reward_attachment": "first_byte_edge_only",
            "token_edge_provenance": "every_byte_edge",
            "prefix_sharing": False,
            "empty_emission_policy": "unsupported",
            "special_token_policy": "unsupported_by_ordinary_byte_adapter",
            "represented_support_sha256": self.token_lattice.support.fingerprint,
        }

    def to_dict(self) -> dict[str, object]:
        """Serialize exact token emissions, terminal graph, and diagnostics."""

        return {
            "token_lattice": self.token_lattice.to_dict(),
            "token_arcs": [
                {
                    "token_edge_id": arc.token_edge_id,
                    "slot": arc.slot,
                    "token_id": arc.token_id,
                    "source_boundary": arc.source_boundary,
                    "target_boundary": arc.target_boundary,
                    "emitted_bytes_hex": arc.emitted_bytes.hex(),
                    "weight": arc.weight,
                    "matched_proposal_ids": list(arc.matched_proposal_ids),
                }
                for arc in self.token_arcs
            ],
            "terminal_graph": {
                "node_ids": list(self.graph.node_ids),
                "start_node_id": self.graph.start_node_id,
                "final_node_ids": list(self.graph.final_node_ids),
                "edges": [
                    {
                        "edge_id": edge.edge_id,
                        "source_state": edge.source_state,
                        "target_state": edge.target_state,
                        "terminal_label": edge.terminal_label,
                        "weight": edge.weight,
                        "provenance_token_edge_id": edge.provenance_token_edge_id,
                        "matched_proposal_ids": list(edge.matched_proposal_ids),
                    }
                    for edge in self.terminal_edges
                ],
            },
            "terminal_edge_ids_by_token_edge": [
                list(row) for row in self.terminal_edge_ids_by_token_edge
            ],
            "diagnostics": self.diagnostics,
        }


def build_byte_lattice(
    *,
    token_lattice: TokenLattice,
    adapter: CompositionalByteLevelAdapter,
) -> ByteLattice:
    """Expand every represented token choice through the audited raw-byte adapter."""

    if not isinstance(token_lattice, TokenLattice):
        raise TypeError("token_lattice must be a TokenLattice")
    if not isinstance(adapter, CompositionalByteLevelAdapter):
        raise TypeError("adapter must be a CompositionalByteLevelAdapter")
    expected_vocabulary_size = token_lattice.support.exactness_scope.vocabulary_size
    if adapter.vocabulary_size != expected_vocabulary_size:
        raise ValueError(
            "tokenizer adapter and exactness scope must have equal vocabulary sizes "
            f"({adapter.vocabulary_size} != {expected_vocabulary_size})"
        )

    emissions = tuple(adapter.token_bytes(choice.token_id) for choice in token_lattice.choices)
    if any(not emission for emission in emissions):
        raise ValueError("empty token emissions are unsupported")
    token_arcs = tuple(
        TokenArc(
            token_edge_id=choice.token_edge_id,
            slot=choice.position,
            token_id=choice.token_id,
            source_boundary=choice.source_boundary,
            target_boundary=choice.target_boundary,
            emitted_bytes=emission,
            weight=choice.weight,
            matched_proposal_ids=choice.matched_proposal_ids,
        )
        for choice, emission in zip(token_lattice.choices, emissions, strict=True)
    )

    next_node_id = len(token_lattice.boundary_ids)
    terminal_edges: list[TerminalEdge] = []
    edge_rows: list[tuple[int, ...]] = []
    for arc in token_arcs:
        source_state = arc.source_boundary
        token_edge_ids: list[int] = []
        for offset, byte_value in enumerate(arc.emitted_bytes):
            is_last = offset == len(arc.emitted_bytes) - 1
            target_state = arc.target_boundary if is_last else next_node_id
            if not is_last:
                next_node_id += 1
            edge_id = len(terminal_edges)
            token_edge_ids.append(edge_id)
            terminal_edges.append(
                TerminalEdge(
                    edge_id=edge_id,
                    source_state=source_state,
                    target_state=target_state,
                    terminal_label=byte_value,
                    weight=arc.weight if offset == 0 else 0.0,
                    provenance_token_edge_id=arc.token_edge_id,
                    matched_proposal_ids=(arc.matched_proposal_ids if offset == 0 else ()),
                )
            )
            source_state = target_state
        edge_rows.append(tuple(token_edge_ids))

    graph = WeightedTerminalDAG(
        node_ids=tuple(range(next_node_id)),
        start_node_id=token_lattice.start_boundary,
        final_node_ids=(token_lattice.final_boundary,),
        edges=tuple(terminal_edges),
    )
    return ByteLattice(
        token_lattice=token_lattice,
        token_arcs=token_arcs,
        graph=graph,
        terminal_edge_ids_by_token_edge=tuple(edge_rows),
    )
