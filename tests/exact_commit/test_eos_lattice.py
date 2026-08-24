from __future__ import annotations

import json
from collections.abc import Iterator

import pytest

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    EOSPolicyViolation,
    EOSState,
    EpsilonEdge,
    Proposal,
    SolveStatus,
    SupportKind,
    SupportPolicy,
    TerminalEdge,
    TokenLattice,
    TokenRole,
    WeightedTerminalDAG,
    build_eos_lattice,
    build_per_position_support,
    build_token_lattice,
)
from mwpc_exact.reference.epsilon import solve_cfg_on_epsilon_dag
from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal, TerminalProduction
from mwpc_exact.reference.graph import index_terminal_dag
from mwpc_exact.types import GraphEdge


def token_lattice(
    *,
    rows: tuple[tuple[int, ...], ...],
    vocabulary_size: int,
    canvas: tuple[int | None, ...] | None = None,
    proposals: tuple[Proposal, ...] = (),
) -> TokenLattice:
    if canvas is None:
        canvas = (None,) * len(rows)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=vocabulary_size),
        explicit_support=dict(enumerate(rows)),
        proposals=proposals,
    )
    return build_token_lattice(support=support, proposals=proposals)


def adapter() -> CompositionalByteLevelAdapter:
    # IDs 2/3 are EOS/EOT controls; ID 4 is an unrelated mask control.
    return CompositionalByteLevelAdapter(emissions=(b"a", b"bc", None, None, None))


def policy(mode: EOSMode) -> EOSPolicy:
    if mode is EOSMode.ABSENT:
        return EOSPolicy(mode=mode)
    return EOSPolicy(mode=mode, termination_token_ids=(2, 3), pad_token_id=2)


def enumerate_graph_paths(graph: WeightedTerminalDAG) -> Iterator[tuple[GraphEdge, ...]]:
    indexed = index_terminal_dag(graph)
    path: list[GraphEdge] = []

    def visit(state: int) -> Iterator[tuple[GraphEdge, ...]]:
        if state in graph.final_node_ids:
            yield tuple(path)
        for edge in indexed.outgoing_edges[state]:
            path.append(edge)
            yield from visit(edge.target_state)
            path.pop()

    yield from visit(graph.start_node_id)


def test_required_automaton_contains_exactly_the_legal_full_slot_paths() -> None:
    lattice = token_lattice(rows=((0, 1, 2, 3, 4),) * 3, vocabulary_size=5)
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )

    paths = tuple(eos_lattice.iter_paths())
    raw_graph_paths = tuple(enumerate_graph_paths(eos_lattice.graph))

    assert eos_lattice.path_count == len(paths) == len(raw_graph_paths) == 14
    assert {path.graph_edge_ids for path in paths} == {
        tuple(edge.edge_id for edge in graph_path) for graph_path in raw_graph_paths
    }
    for path in paths:
        eos_lattice.validate_path(path)
        assert len(path.token_path.token_ids) == 3
        assert path.token_roles.count(TokenRole.EOS) == 1
        eos_index = path.token_roles.index(TokenRole.EOS)
        assert path.eos_position == path.content_endpoint_slot == eos_index
        assert all(role is TokenRole.ORDINARY for role in path.token_roles[:eos_index])
        assert all(role is TokenRole.PAD for role in path.token_roles[eos_index + 1 :])
        assert all(token_id == 2 for token_id in path.token_path.token_ids[eos_index + 1 :])


def test_optional_mode_adds_only_the_all_ordinary_paths() -> None:
    lattice = token_lattice(rows=((0, 1, 2, 3, 4),) * 3, vocabulary_size=5)
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.OPTIONAL),
    )

    paths = tuple(eos_lattice.iter_paths())
    unterminated = tuple(path for path in paths if path.eos_position is None)

    assert eos_lattice.path_count == len(paths) == 22
    assert len(unterminated) == 8
    assert all(path.token_roles == (TokenRole.ORDINARY,) * 3 for path in unterminated)
    assert all(path.content_endpoint_slot == 3 for path in unterminated)


def test_absent_mode_preserves_the_completed_ordinary_lattice_contract() -> None:
    lattice = token_lattice(rows=((0, 1), (0, 1)), vocabulary_size=2)
    byte_adapter = CompositionalByteLevelAdapter(emissions=(b"a", b"bc"))
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=byte_adapter,
        policy=EOSPolicy(EOSMode.ABSENT),
    )

    paths = tuple(eos_lattice.iter_paths())

    assert eos_lattice.path_count == lattice.path_count == len(paths) == 4
    assert all(path.eos_position is None for path in paths)
    assert tuple(path.emitted_bytes for path in paths) == (
        b"aa",
        b"abc",
        b"bca",
        b"bcbc",
    )
    assert eos_lattice.graph.edges == eos_lattice.normalized_graph.edges
    assert not any(isinstance(edge, EpsilonEdge) for edge in eos_lattice.graph.edges)


def test_invalid_ordinary_token_after_eos_has_no_product_graph_path() -> None:
    lattice = token_lattice(
        rows=((2,), (0,), (2,)),
        vocabulary_size=5,
        canvas=(2, 0, 2),
    )
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )
    token_path = next(lattice.iter_paths())

    assert eos_lattice.path_count == 0
    assert tuple(eos_lattice.iter_paths()) == ()
    assert tuple(enumerate_graph_paths(eos_lattice.graph)) == ()
    assert tuple(enumerate_graph_paths(eos_lattice.normalized_graph)) == ()
    with pytest.raises(EOSPolicyViolation, match="at slot 1"):
        eos_lattice.expand_path(token_path)


def test_eos_pad_alias_has_state_dependent_roles_and_eot_cannot_pad() -> None:
    lattice = token_lattice(rows=((2, 3), (2, 3)), vocabulary_size=5)
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )

    alias_arcs = tuple(arc for arc in eos_lattice.arcs if arc.token_id == 2)
    eot_arcs = tuple(arc for arc in eos_lattice.arcs if arc.token_id == 3)
    paths = tuple(eos_lattice.iter_paths())

    assert {(arc.role, arc.source_eos_state, arc.target_eos_state) for arc in alias_arcs} == {
        (TokenRole.EOS, EOSState.BEFORE_EOS, EOSState.AFTER_EOS),
        (TokenRole.PAD, EOSState.AFTER_EOS, EOSState.AFTER_EOS),
    }
    assert {arc.role for arc in eot_arcs} == {TokenRole.EOS}
    assert tuple(path.token_path.token_ids for path in paths) == ((2, 2), (3, 2))


def test_distinct_pad_is_illegal_before_eos_and_only_pad_is_legal_after() -> None:
    lattice = token_lattice(rows=((2, 3), (0, 2, 3)), vocabulary_size=5)
    distinct_policy = EOSPolicy(
        mode=EOSMode.REQUIRED,
        termination_token_ids=(2,),
        pad_token_id=3,
    )
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=distinct_policy,
    )

    (path,) = tuple(eos_lattice.iter_paths())

    assert path.token_path.token_ids == (2, 3)
    assert path.token_roles == (TokenRole.EOS, TokenRole.PAD)


def test_eos_and_pad_keep_their_own_weight_and_duplicate_proposal_provenance() -> None:
    proposals = (
        Proposal(10, position=0, token_id=2, weight=7),
        Proposal(11, position=1, token_id=2, weight=5),
        Proposal(12, position=2, token_id=2, weight=2),
        Proposal(13, position=2, token_id=2, weight=3),
    )
    lattice = token_lattice(
        rows=((2,), (2,), (2,)),
        vocabulary_size=5,
        proposals=proposals,
    )
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )

    (path,) = tuple(eos_lattice.iter_paths())
    edges = tuple(eos_lattice.graph.edges[edge_id] for edge_id in path.graph_edge_ids)

    assert path.token_path.token_ids == (2, 2, 2)
    assert path.token_roles == (TokenRole.EOS, TokenRole.PAD, TokenRole.PAD)
    assert path.emitted_bytes == b""
    assert path.objective_value == 17.0
    assert path.matched_proposal_ids == (10, 11, 12, 13)
    assert tuple(edge.weight for edge in edges) == (7.0, 5.0, 5.0)
    assert tuple(edge.matched_proposal_ids for edge in edges) == (
        (10,),
        (11,),
        (12, 13),
    )
    assert all(isinstance(edge, EpsilonEdge) for edge in edges)


def test_original_graph_paths_reconstruct_every_physical_token_id() -> None:
    lattice = token_lattice(rows=((0, 2, 3), (0, 1, 2), (1, 2)), vocabulary_size=5)
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )

    reconstructed = tuple(
        eos_lattice.reconstruct_original_path(edge.edge_id for edge in graph_path)
        for graph_path in enumerate_graph_paths(eos_lattice.graph)
    )

    assert {path.graph_edge_ids for path in reconstructed} == {
        path.graph_edge_ids for path in eos_lattice.iter_paths()
    }
    assert all(len(path.token_path.token_ids) == lattice.slot_count for path in reconstructed)


def test_normalized_terminal_paths_expand_back_to_full_slots_without_epsilon_duplication() -> None:
    lattice = token_lattice(rows=((0,), (1,), (2,), (2,)), vocabulary_size=5)
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )

    normalized_paths = tuple(enumerate_graph_paths(eos_lattice.normalized_graph))
    reconstructed = tuple(
        eos_lattice.reconstruct_normalized_path(edge.edge_id for edge in graph_path)
        for graph_path in normalized_paths
    )

    assert normalized_paths
    assert {path.token_path.token_ids for path in reconstructed} == {(0, 1, 2, 2)}
    assert all(len(path.token_path.token_ids) == 4 for path in reconstructed)
    assert all(path.graph_edge_ids.count(path.graph_edge_ids[-1]) == 1 for path in reconstructed)
    assert all(path.emitted_bytes == b"abc" for path in reconstructed)


def test_cfg_solve_expands_normalization_to_a_reconstructible_full_slot_witness() -> None:
    proposals = (
        Proposal(30, position=0, token_id=0, weight=2),
        Proposal(31, position=1, token_id=2, weight=3),
        Proposal(32, position=2, token_id=2, weight=5),
    )
    lattice = token_lattice(
        rows=((0,), (2,), (2,)),
        vocabulary_size=5,
        proposals=proposals,
    )
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )
    grammar = CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, ord("a")),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )

    result = solve_cfg_on_epsilon_dag(grammar, eos_lattice.graph)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 10.0
    assert result.certificate is not None
    path = eos_lattice.reconstruct_original_path(result.certificate.witness_graph_edge_ids)
    assert path.token_path.token_ids == (0, 2, 2)
    assert path.matched_proposal_ids == (30, 31, 32)
    assert path.terminal_labels == (ord("a"),)


def test_epsilon_only_normalization_reconstructs_eos_and_every_pad_slot() -> None:
    proposals = (
        Proposal(20, position=0, token_id=2, weight=4),
        Proposal(21, position=0, token_id=3, weight=9),
        Proposal(22, position=1, token_id=2, weight=2),
        Proposal(23, position=2, token_id=2, weight=1),
    )
    lattice = token_lattice(
        rows=((2, 3), (2,), (2,)),
        vocabulary_size=5,
        proposals=proposals,
    )
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )

    path = eos_lattice.reconstruct_epsilon_only_path()

    assert eos_lattice.normalized_graph.edges == ()
    assert path.token_path.token_ids == (3, 2, 2)
    assert path.token_roles == (TokenRole.EOS, TokenRole.PAD, TokenRole.PAD)
    assert path.objective_value == 12.0
    assert path.matched_proposal_ids == (21, 22, 23)
    assert path.eos_position == path.content_endpoint_slot == 0
    assert len(path.graph_edge_ids) == lattice.slot_count


def test_final_slot_eos_is_legal_without_a_pad_suffix() -> None:
    lattice = token_lattice(rows=((0,), (3,)), vocabulary_size=5)
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )

    (path,) = tuple(eos_lattice.iter_paths())

    assert path.token_path.token_ids == (0, 3)
    assert path.token_roles == (TokenRole.ORDINARY, TokenRole.EOS)
    assert path.eos_position == path.content_endpoint_slot == 1
    assert path.emitted_bytes == b"a"


def test_empty_canvas_acceptance_follows_mode_without_inventing_a_token() -> None:
    lattice = token_lattice(rows=(), vocabulary_size=5)

    absent = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.ABSENT),
    )
    optional = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.OPTIONAL),
    )
    required = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )

    assert absent.path_count == optional.path_count == 1
    assert required.path_count == 0
    assert next(absent.iter_paths()).token_path.token_ids == ()
    assert next(optional.iter_paths()).token_path.token_ids == ()
    assert tuple(required.iter_paths()) == ()
    with pytest.raises(ValueError, match="no complete epsilon-only path"):
        required.reconstruct_epsilon_only_path()


@pytest.mark.parametrize("mode", (EOSMode.REQUIRED, EOSMode.OPTIONAL))
def test_configured_special_ids_must_belong_to_the_vocabulary(mode: EOSMode) -> None:
    lattice = token_lattice(rows=((0,),), vocabulary_size=2)
    byte_adapter = CompositionalByteLevelAdapter(emissions=(b"a", None))

    with pytest.raises(ValueError, match="termination token IDs"):
        build_eos_lattice(
            token_lattice=lattice,
            adapter=byte_adapter,
            policy=EOSPolicy(mode, termination_token_ids=(2,), pad_token_id=1),
        )
    with pytest.raises(ValueError, match="PAD token ID"):
        build_eos_lattice(
            token_lattice=lattice,
            adapter=byte_adapter,
            policy=EOSPolicy(mode, termination_token_ids=(1,), pad_token_id=2),
        )


def test_policy_requires_an_explicit_and_unambiguous_profile() -> None:
    with pytest.raises(TypeError, match="EOSMode"):
        EOSPolicy("required")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot configure"):
        EOSPolicy(EOSMode.ABSENT, termination_token_ids=(2,), pad_token_id=2)
    with pytest.raises(ValueError, match="require termination and PAD"):
        EOSPolicy(EOSMode.REQUIRED)
    with pytest.raises(ValueError, match="duplicates"):
        EOSPolicy(EOSMode.REQUIRED, termination_token_ids=(2, 2), pad_token_id=2)


def test_serialization_records_policy_epsilon_provenance_and_slot_contract() -> None:
    lattice = token_lattice(rows=((0,), (2,), (2,)), vocabulary_size=5)
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.REQUIRED),
    )

    serialized = json.loads(json.dumps(eos_lattice.to_dict()))

    assert serialized["policy"] == {
        "mode": "required",
        "termination_token_ids": [2, 3],
        "pad_token_id": 2,
    }
    assert serialized["arcs"][-1]["role"] == "pad"
    assert serialized["diagnostics"]["physical_slot_policy"] == "all_slots_consumed"
    assert serialized["diagnostics"]["special_reward_attachment"] == "own_epsilon_edge"
    assert serialized["epsilon_provenance"]


def test_normalized_graph_contains_only_terminals() -> None:
    lattice = token_lattice(rows=((0, 2), (0, 2)), vocabulary_size=5)
    eos_lattice = build_eos_lattice(
        token_lattice=lattice,
        adapter=adapter(),
        policy=policy(EOSMode.OPTIONAL),
    )

    assert any(isinstance(edge, EpsilonEdge) for edge in eos_lattice.graph.edges)
    assert all(isinstance(edge, TerminalEdge) for edge in eos_lattice.normalized_graph.edges)
