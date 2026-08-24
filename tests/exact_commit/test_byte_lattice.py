from __future__ import annotations

import json
from dataclasses import replace
from math import fsum

import pytest

from mwpc_exact import (
    BYTE_LEVEL_ALPHABET,
    ByteLatticePath,
    CompositionalByteLevelAdapter,
    Proposal,
    SupportKind,
    SupportPolicy,
    TokenArc,
    TokenLattice,
    UnsupportedTokenError,
    build_byte_lattice,
    build_per_position_support,
    build_token_lattice,
)
from mwpc_exact.reference.graph import index_terminal_dag
from mwpc_exact.types import TerminalEdge, WeightedTerminalDAG


def token_lattice(
    *,
    canvas: tuple[int | None, ...],
    rows: tuple[tuple[int, ...], ...],
    vocabulary_size: int,
    proposals: tuple[Proposal, ...] = (),
) -> TokenLattice:
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=vocabulary_size,
        ),
        explicit_support=dict(enumerate(rows)),
        proposals=proposals,
    )
    return build_token_lattice(support=support, proposals=proposals)


def enumerate_graph_paths(graph: WeightedTerminalDAG) -> tuple[tuple[TerminalEdge, ...], ...]:
    indexed = index_terminal_dag(graph)
    completed: list[tuple[TerminalEdge, ...]] = []
    path: list[TerminalEdge] = []

    def visit(state: int) -> None:
        if state in graph.final_node_ids:
            completed.append(tuple(path))
        for edge in indexed.outgoing_edges[state]:
            assert isinstance(edge, TerminalEdge)
            path.append(edge)
            visit(edge.target_state)
            path.pop()

    visit(graph.start_node_id)
    return tuple(completed)


def test_multi_byte_choice_expands_to_private_chain_with_stable_ids() -> None:
    lattice = token_lattice(
        canvas=(None,),
        rows=((0, 1),),
        vocabulary_size=2,
        proposals=(Proposal(7, position=0, token_id=1, weight=4),),
    )
    adapter = CompositionalByteLevelAdapter(emissions=(b"A", "👩".encode()))

    byte_lattice = build_byte_lattice(token_lattice=lattice, adapter=adapter)

    assert byte_lattice.graph.node_ids == (0, 1, 2, 3, 4)
    assert byte_lattice.terminal_edge_ids_by_token_edge == ((0,), (1, 2, 3, 4))
    assert tuple(
        (edge.source_state, edge.target_state, edge.terminal_label)
        for edge in byte_lattice.terminal_edges_for_token(1)
    ) == ((0, 2, 0xF0), (2, 3, 0x9F), (3, 4, 0x91), (4, 1, 0xA9))
    for edge in byte_lattice.terminal_edges_for_token(1):
        assert edge.provenance_token_edge_id == 1
    assert tuple(edge.weight for edge in byte_lattice.terminal_edges_for_token(1)) == (
        4.0,
        0.0,
        0.0,
        0.0,
    )
    assert tuple(
        edge.matched_proposal_ids for edge in byte_lattice.terminal_edges_for_token(1)
    ) == ((7,), (), (), ())
    assert index_terminal_dag(byte_lattice.graph).topological_order[0] == 0


def test_every_graph_path_matches_one_token_path_and_full_raw_detokenization() -> None:
    lattice = token_lattice(
        canvas=(None, None, 4),
        rows=((0, 1), (2, 3), (4,)),
        vocabulary_size=5,
    )
    adapter = CompositionalByteLevelAdapter(
        emissions=(b"a", bytes.fromhex("f09f91"), bytes.fromhex("a9"), b" bc", b"!")
    )
    byte_lattice = build_byte_lattice(token_lattice=lattice, adapter=adapter)

    expanded_paths = tuple(byte_lattice.iter_paths())
    graph_paths = enumerate_graph_paths(byte_lattice.graph)

    assert len(expanded_paths) == lattice.path_count == len(graph_paths) == 4
    assert {path.graph_edge_ids for path in expanded_paths} == {
        tuple(edge.edge_id for edge in path) for path in graph_paths
    }
    for path in expanded_paths:
        byte_lattice.validate_path(path)
        assert path.emitted_bytes == adapter.detokenize_bytes(path.token_path.token_ids)
        assert path.terminal_labels == tuple(path.emitted_bytes)


def test_reward_is_attached_once_and_independent_of_token_byte_length() -> None:
    proposals = (
        Proposal(3, position=0, token_id=0, weight=7),
        Proposal(8, position=0, token_id=1, weight=7),
    )
    lattice = token_lattice(
        canvas=(None,),
        rows=((0, 1),),
        vocabulary_size=2,
        proposals=proposals,
    )
    adapter = CompositionalByteLevelAdapter(emissions=(b"x", b"a much longer token"))
    byte_lattice = build_byte_lattice(token_lattice=lattice, adapter=adapter)

    for path in byte_lattice.iter_paths():
        edges = tuple(byte_lattice.graph.edges[edge_id] for edge_id in path.graph_edge_ids)
        assert fsum(edge.weight for edge in edges) == 7.0
        assert sum(bool(edge.matched_proposal_ids) for edge in edges) == 1
        assert path.objective_value == 7.0


def test_identical_and_shared_prefix_emissions_remain_distinct_token_paths() -> None:
    lattice = token_lattice(
        canvas=(None,),
        rows=((0, 1, 2),),
        vocabulary_size=3,
    )
    adapter = CompositionalByteLevelAdapter(emissions=(b"ab", b"ab", b"ac"))

    byte_lattice = build_byte_lattice(token_lattice=lattice, adapter=adapter)
    paths = tuple(byte_lattice.iter_paths())

    assert tuple(path.token_path.token_ids for path in paths) == ((0,), (1,), (2,))
    assert tuple(path.emitted_bytes for path in paths) == (b"ab", b"ab", b"ac")
    assert len({path.graph_edge_ids for path in paths}) == 3
    first_edges = tuple(byte_lattice.terminal_edges_for_token(token_id)[0] for token_id in range(3))
    assert tuple(edge.terminal_label for edge in first_edges) == (ord("a"),) * 3
    assert len({edge.target_state for edge in first_edges}) == 3
    assert tuple(edge.provenance_token_edge_id for edge in first_edges) == (0, 1, 2)


def test_raw_byte_fallback_value_is_preserved_without_unicode_rendering() -> None:
    lattice = token_lattice(canvas=(None,), rows=((0,),), vocabulary_size=1)
    adapter = CompositionalByteLevelAdapter.from_token_pieces((BYTE_LEVEL_ALPHABET[0xFF],))

    byte_lattice = build_byte_lattice(token_lattice=lattice, adapter=adapter)
    (path,) = tuple(byte_lattice.iter_paths())

    assert path.emitted_bytes == b"\xff"
    assert path.terminal_labels == (255,)
    assert byte_lattice.graph.edges[0].terminal_label == 255


def test_unsupported_special_token_is_rejected_before_expansion() -> None:
    lattice = token_lattice(canvas=(None,), rows=((1,),), vocabulary_size=2)
    adapter = CompositionalByteLevelAdapter(emissions=(b"a", None))

    with pytest.raises(UnsupportedTokenError, match="token ID 1"):
        build_byte_lattice(token_lattice=lattice, adapter=adapter)


def test_adapter_and_exactness_scope_vocabulary_must_match() -> None:
    lattice = token_lattice(canvas=(None,), rows=((0,),), vocabulary_size=2)
    adapter = CompositionalByteLevelAdapter(emissions=(b"a",))

    with pytest.raises(ValueError, match="equal vocabulary sizes"):
        build_byte_lattice(token_lattice=lattice, adapter=adapter)


def test_empty_canvas_expands_to_single_empty_start_final_path() -> None:
    lattice = token_lattice(canvas=(), rows=(), vocabulary_size=1)
    adapter = CompositionalByteLevelAdapter(emissions=(b"unused",))

    byte_lattice = build_byte_lattice(token_lattice=lattice, adapter=adapter)

    assert byte_lattice.graph.node_ids == (0,)
    assert byte_lattice.graph.start_node_id == 0
    assert byte_lattice.graph.final_node_ids == (0,)
    assert byte_lattice.graph.edges == ()
    assert byte_lattice.terminal_edge_ids_by_token_edge == ()
    assert tuple(byte_lattice.iter_paths()) == (
        ByteLatticePath(
            token_path=next(lattice.iter_paths()),
            graph_edge_ids=(),
            emitted_bytes=b"",
        ),
    )
    byte_lattice.validate_path(next(byte_lattice.iter_paths()))


def test_validation_rejects_duplicated_reward_on_suffix_byte() -> None:
    lattice = token_lattice(
        canvas=(None,),
        rows=((0,),),
        vocabulary_size=1,
        proposals=(Proposal(2, position=0, token_id=0, weight=5),),
    )
    byte_lattice = build_byte_lattice(
        token_lattice=lattice,
        adapter=CompositionalByteLevelAdapter(emissions=(b"ab",)),
    )
    suffix = byte_lattice.graph.edges[1]
    assert isinstance(suffix, TerminalEdge)
    bad_graph = replace(
        byte_lattice.graph,
        edges=(
            byte_lattice.graph.edges[0],
            replace(suffix, weight=5, matched_proposal_ids=(2,)),
        ),
    )

    with pytest.raises(ValueError, match="only the first byte edge"):
        replace(byte_lattice, graph=bad_graph)


def test_empty_token_arc_is_rejected_explicitly() -> None:
    with pytest.raises(ValueError, match="empty token emissions"):
        TokenArc(
            token_edge_id=0,
            slot=0,
            token_id=0,
            source_boundary=0,
            target_boundary=1,
            emitted_bytes=b"",
        )


def test_serialization_records_exact_bytes_graph_and_expansion_policies() -> None:
    lattice = token_lattice(canvas=(None,), rows=((0,),), vocabulary_size=1)
    byte_lattice = build_byte_lattice(
        token_lattice=lattice,
        adapter=CompositionalByteLevelAdapter(emissions=(b"\x00\xff",)),
    )

    serialized = json.loads(json.dumps(byte_lattice.to_dict()))

    assert serialized["token_arcs"][0]["emitted_bytes_hex"] == "00ff"
    assert serialized["terminal_graph"]["edges"][0]["terminal_label"] == 0
    assert serialized["terminal_graph"]["edges"][1]["terminal_label"] == 255
    assert serialized["terminal_edge_ids_by_token_edge"] == [[0, 1]]
    assert serialized["diagnostics"]["reward_attachment"] == "first_byte_edge_only"
    assert serialized["diagnostics"]["prefix_sharing"] is False
