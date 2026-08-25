"""Finite-slot product lattice for explicit EOS/PAD semantics.

The ordinary byte lattice remains unchanged.  This module composes the same
finite token choices with the two-state automaton frozen by ADR 0007, then
normalizes the resulting weighted epsilon edges for the CFG parser while
retaining enough provenance to reconstruct every physical token slot.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import pairwise
from math import fsum, isfinite

from mwpc_exact.eos_policy import (
    EOSMode,
    EOSPolicy,
    EOSPolicyViolation,
    EOSState,
    TokenRole,
    _id_tuple,
    _non_negative_id,
)
from mwpc_exact.reference.epsilon import (
    EpsilonNormalizationResult,
    normalize_epsilon_edges,
)
from mwpc_exact.token_lattice import TokenChoice, TokenLattice, TokenLatticePath
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import EpsilonEdge, GraphEdge, TerminalEdge, WeightedTerminalDAG


@dataclass(frozen=True, slots=True)
class EOSArc:
    """One token choice in one legal automaton state and role."""

    arc_id: int
    token_edge_id: int
    position: int
    token_id: int
    role: TokenRole
    source_eos_state: EOSState
    target_eos_state: EOSState
    source_node_id: int
    target_node_id: int
    emitted_bytes: bytes
    weight: float
    matched_proposal_ids: tuple[int, ...]
    graph_edge_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "arc_id",
            "token_edge_id",
            "position",
            "token_id",
            "source_node_id",
            "target_node_id",
        ):
            _non_negative_id(getattr(self, field_name), field_name)
        if not isinstance(self.role, TokenRole):
            raise TypeError("role must be a TokenRole")
        if not isinstance(self.source_eos_state, EOSState) or not isinstance(
            self.target_eos_state, EOSState
        ):
            raise TypeError("source_eos_state and target_eos_state must be EOSState values")
        if not isinstance(self.emitted_bytes, bytes):
            raise TypeError("emitted_bytes must be bytes")
        graph_edge_ids = _id_tuple(self.graph_edge_ids, "graph_edge_ids", unique=True)
        if not graph_edge_ids:
            raise ValueError("every EOS-product arc must contain at least one graph edge")
        object.__setattr__(self, "graph_edge_ids", graph_edge_ids)


@dataclass(frozen=True, slots=True)
class EOSLatticePath:
    """One legal full-slot token path and its grammar-visible byte witness."""

    token_path: TokenLatticePath
    token_roles: tuple[TokenRole, ...]
    graph_edge_ids: tuple[int, ...]
    emitted_bytes: bytes
    eos_position: int | None
    content_endpoint_slot: int

    def __post_init__(self) -> None:
        if not isinstance(self.token_path, TokenLatticePath):
            raise TypeError("token_path must be a TokenLatticePath")
        roles = tuple(self.token_roles)
        if not all(isinstance(role, TokenRole) for role in roles):
            raise TypeError("token_roles must contain only TokenRole values")
        if len(roles) != len(self.token_path.token_ids):
            raise ValueError("token_roles must contain exactly one role per physical token")
        graph_edge_ids = _id_tuple(self.graph_edge_ids, "graph_edge_ids", unique=True)
        if not isinstance(self.emitted_bytes, bytes):
            raise TypeError("emitted_bytes must be bytes")
        if self.eos_position is not None:
            _non_negative_id(self.eos_position, "eos_position")
        _non_negative_id(self.content_endpoint_slot, "content_endpoint_slot")
        object.__setattr__(self, "token_roles", roles)
        object.__setattr__(self, "graph_edge_ids", graph_edge_ids)

    @property
    def terminal_labels(self) -> tuple[int, ...]:
        return tuple(self.emitted_bytes)

    @property
    def objective_value(self) -> float:
        return self.token_path.objective_value

    @property
    def matched_proposal_ids(self) -> tuple[int, ...]:
        return self.token_path.matched_proposal_ids

    def to_dict(self) -> dict[str, object]:
        return {
            "token_path": self.token_path.to_dict(),
            "token_roles": [role.value for role in self.token_roles],
            "graph_edge_ids": list(self.graph_edge_ids),
            "terminal_labels": list(self.terminal_labels),
            "emitted_bytes_hex": self.emitted_bytes.hex(),
            "eos_position": self.eos_position,
            "content_endpoint_slot": self.content_endpoint_slot,
        }


@dataclass(frozen=True, slots=True)
class EOSLattice:
    """Token/byte lattice composed with the finite-slot EOS automaton."""

    token_lattice: TokenLattice
    adapter: CompositionalByteLevelAdapter
    policy: EOSPolicy
    arcs: tuple[EOSArc, ...]
    graph: WeightedTerminalDAG
    normalization: EpsilonNormalizationResult

    def __post_init__(self) -> None:
        if not isinstance(self.token_lattice, TokenLattice):
            raise TypeError("token_lattice must be a TokenLattice")
        if not isinstance(self.adapter, CompositionalByteLevelAdapter):
            raise TypeError("adapter must be a CompositionalByteLevelAdapter")
        if not isinstance(self.policy, EOSPolicy):
            raise TypeError("policy must be an EOSPolicy")
        expected_vocabulary_size = (
            self.token_lattice.support.exactness_scope.vocabulary_size
        )
        if self.adapter.vocabulary_size != expected_vocabulary_size:
            raise ValueError(
                "tokenizer adapter and exactness scope must have equal vocabulary sizes"
            )
        self._validate_policy_vocabulary()

        arcs = tuple(self.arcs)
        if not all(isinstance(arc, EOSArc) for arc in arcs):
            raise TypeError("arcs must contain only EOSArc instances")
        if tuple(arc.arc_id for arc in arcs) != tuple(range(len(arcs))):
            raise ValueError("EOS arc IDs must be contiguous in canonical order")
        if not isinstance(self.graph, WeightedTerminalDAG):
            raise TypeError("graph must be a WeightedTerminalDAG")
        if not isinstance(self.normalization, EpsilonNormalizationResult):
            raise TypeError("normalization must be an EpsilonNormalizationResult")
        if self.normalization.original_graph != self.graph:
            raise ValueError("epsilon normalization must refer to the EOS product graph")

        expected_start = self.node_id(0, EOSState.BEFORE_EOS)
        if self.graph.start_node_id != expected_start:
            raise ValueError("EOS graph must start in BEFORE_EOS at boundary zero")
        if self.graph.final_node_ids != self._expected_final_node_ids():
            raise ValueError("EOS graph final nodes do not match the configured EOS mode")

        expected_transitions = tuple(
            transition
            for choice in self.token_lattice.choices
            for transition in self._transitions_for_choice(choice)
        )
        actual_transitions = tuple(
            (
                arc.token_edge_id,
                arc.role,
                arc.source_eos_state,
                arc.target_eos_state,
            )
            for arc in arcs
        )
        if actual_transitions != expected_transitions:
            raise ValueError("EOS arcs must contain exactly the configured legal transitions")

        edge_by_id = {edge.edge_id: edge for edge in self.graph.edges}
        flattened_edge_ids = tuple(edge_id for arc in arcs for edge_id in arc.graph_edge_ids)
        if flattened_edge_ids != tuple(range(len(self.graph.edges))):
            raise ValueError("EOS arcs must partition graph edges in canonical edge-ID order")
        observed_intermediate_nodes: list[int] = []
        for arc in arcs:
            choice = self.token_lattice.choices[arc.token_edge_id]
            self._validate_arc_metadata(arc, choice)
            edges = tuple(edge_by_id[edge_id] for edge_id in arc.graph_edge_ids)
            self._validate_arc_edges(arc, edges)
            observed_intermediate_nodes.extend(edge.target_state for edge in edges[:-1])

        state_node_count = 2 * (self.token_lattice.slot_count + 1)
        expected_intermediate_nodes = tuple(
            range(state_node_count, state_node_count + len(observed_intermediate_nodes))
        )
        if tuple(observed_intermediate_nodes) != expected_intermediate_nodes:
            raise ValueError("ordinary token byte paths must use private canonical nodes")
        if self.graph.node_ids != tuple(range(state_node_count + len(observed_intermediate_nodes))):
            raise ValueError("EOS graph nodes must be exactly state and private byte nodes")

        object.__setattr__(self, "arcs", arcs)

    def _validate_policy_vocabulary(self) -> None:
        vocabulary_size = self.adapter.vocabulary_size
        for token_id in self.policy.termination_token_ids:
            if token_id >= vocabulary_size:
                raise ValueError("termination token IDs must belong to the tokenizer vocabulary")
        if self.policy.pad_token_id is not None and self.policy.pad_token_id >= vocabulary_size:
            raise ValueError("PAD token ID must belong to the tokenizer vocabulary")

    def _expected_final_node_ids(self) -> tuple[int, ...]:
        boundary = self.token_lattice.slot_count
        before = self.node_id(boundary, EOSState.BEFORE_EOS)
        after = self.node_id(boundary, EOSState.AFTER_EOS)
        if self.policy.mode is EOSMode.REQUIRED:
            return (after,)
        if self.policy.mode is EOSMode.OPTIONAL:
            return (before, after)
        return (before,)

    def _transitions_for_choice(
        self, choice: TokenChoice
    ) -> tuple[tuple[int, TokenRole, EOSState, EOSState], ...]:
        transitions: list[tuple[int, TokenRole, EOSState, EOSState]] = []
        special_mode = self.policy.mode is not EOSMode.ABSENT
        if special_mode and choice.token_id in self.policy.termination_token_ids:
            transitions.append(
                (
                    choice.token_edge_id,
                    TokenRole.EOS,
                    EOSState.BEFORE_EOS,
                    EOSState.AFTER_EOS,
                )
            )
        if special_mode and choice.token_id == self.policy.pad_token_id:
            transitions.append(
                (
                    choice.token_edge_id,
                    TokenRole.PAD,
                    EOSState.AFTER_EOS,
                    EOSState.AFTER_EOS,
                )
            )
        is_special = special_mode and (
            choice.token_id in self.policy.termination_token_ids
            or choice.token_id == self.policy.pad_token_id
        )
        if not is_special and self.adapter.emissions[choice.token_id] is not None:
            transitions.insert(
                0,
                (
                    choice.token_edge_id,
                    TokenRole.ORDINARY,
                    EOSState.BEFORE_EOS,
                    EOSState.BEFORE_EOS,
                ),
            )
        return tuple(transitions)

    def _validate_arc_metadata(self, arc: EOSArc, choice: TokenChoice) -> None:
        expected_emission = (
            self.adapter.token_bytes(choice.token_id)
            if arc.role is TokenRole.ORDINARY
            else b""
        )
        if (
            arc.position != choice.position
            or arc.token_id != choice.token_id
            or arc.source_node_id != self.node_id(choice.position, arc.source_eos_state)
            or arc.target_node_id != self.node_id(choice.position + 1, arc.target_eos_state)
            or arc.emitted_bytes != expected_emission
            or arc.weight != choice.weight
            or arc.matched_proposal_ids != choice.matched_proposal_ids
        ):
            raise ValueError("EOS arc metadata must exactly preserve its token choice and role")

    @staticmethod
    def _validate_arc_edges(arc: EOSArc, edges: tuple[GraphEdge, ...]) -> None:
        if not edges or edges[0].source_state != arc.source_node_id:
            raise ValueError("EOS arc graph edges must start at the arc source node")
        if edges[-1].target_state != arc.target_node_id:
            raise ValueError("EOS arc graph edges must end at the arc target node")
        if any(left.target_state != right.source_state for left, right in pairwise(edges)):
            raise ValueError("EOS arc graph edges must form one connected path")

        if arc.role is TokenRole.ORDINARY:
            if len(edges) != len(arc.emitted_bytes) or not all(
                isinstance(edge, TerminalEdge) for edge in edges
            ):
                raise ValueError("ordinary arcs require exactly one terminal edge per byte")
            terminal_edges = tuple(edge for edge in edges if isinstance(edge, TerminalEdge))
            if tuple(edge.terminal_label for edge in terminal_edges) != tuple(arc.emitted_bytes):
                raise ValueError("ordinary arc labels must equal its raw token bytes")
            if any(edge.provenance_token_edge_id != arc.token_edge_id for edge in terminal_edges):
                raise ValueError("ordinary edges must retain token-edge identity")
        elif len(edges) != 1 or not isinstance(edges[0], EpsilonEdge):
            raise ValueError("EOS and PAD arcs require exactly one epsilon edge")

        first, *suffix = edges
        if first.weight != arc.weight or first.matched_proposal_ids != arc.matched_proposal_ids:
            raise ValueError("the first graph edge must carry all token reward and provenance")
        if any(edge.weight != 0.0 or edge.matched_proposal_ids for edge in suffix):
            raise ValueError("only the first graph edge may carry reward or proposals")

    def node_id(self, boundary: int, state: EOSState) -> int:
        """Return the canonical product-state node for one physical boundary."""

        boundary = _non_negative_id(boundary, "boundary")
        if boundary > self.token_lattice.slot_count:
            raise ValueError("boundary is outside the finite token lattice")
        if not isinstance(state, EOSState):
            raise TypeError("state must be an EOSState")
        return 2 * boundary + (1 if state is EOSState.AFTER_EOS else 0)

    @property
    def normalized_graph(self) -> WeightedTerminalDAG:
        """Return the epsilon-free graph consumed by the core CFG parser."""

        return self.normalization.normalized_graph

    @property
    def path_count(self) -> int:
        """Count complete legal token paths without constructing certificates."""

        before_count = 1
        after_count = 0
        arcs_by_position = tuple(
            tuple(arc for arc in self.arcs if arc.position == position)
            for position in range(self.token_lattice.slot_count)
        )
        for arcs in arcs_by_position:
            next_before = sum(
                before_count
                for arc in arcs
                if arc.source_eos_state is EOSState.BEFORE_EOS
                and arc.target_eos_state is EOSState.BEFORE_EOS
            )
            next_after = sum(
                before_count
                for arc in arcs
                if arc.source_eos_state is EOSState.BEFORE_EOS
                and arc.target_eos_state is EOSState.AFTER_EOS
            ) + sum(
                after_count
                for arc in arcs
                if arc.source_eos_state is EOSState.AFTER_EOS
                and arc.target_eos_state is EOSState.AFTER_EOS
            )
            before_count, after_count = next_before, next_after
        if self.policy.mode is EOSMode.REQUIRED:
            return after_count
        if self.policy.mode is EOSMode.OPTIONAL:
            return before_count + after_count
        return before_count

    def _arc_for_choice(self, token_edge_id: int, state: EOSState) -> EOSArc | None:
        return next(
            (
                arc
                for arc in self.arcs
                if arc.token_edge_id == token_edge_id and arc.source_eos_state is state
            ),
            None,
        )

    def expand_path(self, token_path: TokenLatticePath) -> EOSLatticePath:
        """Apply the EOS policy to a full token path and expand its graph witness."""

        self.token_lattice.validate_path(token_path)
        state = EOSState.BEFORE_EOS
        selected_arcs: list[EOSArc] = []
        for position, token_edge_id in enumerate(token_path.token_edge_ids):
            arc = self._arc_for_choice(token_edge_id, state)
            if arc is None:
                raise EOSPolicyViolation(
                    f"token path violates the {self.policy.mode.value} EOS policy at slot "
                    f"{position}"
                )
            selected_arcs.append(arc)
            state = arc.target_eos_state
        final_node_id = self.node_id(self.token_lattice.slot_count, state)
        if final_node_id not in self.graph.final_node_ids:
            raise EOSPolicyViolation(
                f"token path ends in non-accepting {state.value} state for "
                f"{self.policy.mode.value} EOS mode"
            )

        eos_position = next(
            (arc.position for arc in selected_arcs if arc.role is TokenRole.EOS),
            None,
        )
        return EOSLatticePath(
            token_path=token_path,
            token_roles=tuple(arc.role for arc in selected_arcs),
            graph_edge_ids=tuple(
                edge_id for arc in selected_arcs for edge_id in arc.graph_edge_ids
            ),
            emitted_bytes=b"".join(arc.emitted_bytes for arc in selected_arcs),
            eos_position=eos_position,
            content_endpoint_slot=(
                self.token_lattice.slot_count if eos_position is None else eos_position
            ),
        )

    def iter_paths(self) -> Iterator[EOSLatticePath]:
        """Enumerate legal full-slot paths for tiny fixtures and exhaustive oracles."""

        for token_path in self.token_lattice.iter_paths():
            try:
                yield self.expand_path(token_path)
            except EOSPolicyViolation:
                continue

    def reconstruct_original_path(self, graph_edge_ids: Iterable[int]) -> EOSLatticePath:
        """Reconstruct all physical token IDs from one complete original-graph path."""

        edge_ids = _id_tuple(graph_edge_ids, "graph_edge_ids", unique=True)
        first_edge_to_arc = {arc.graph_edge_ids[0]: arc for arc in self.arcs}
        selected_arcs: list[EOSArc] = []
        offset = 0
        while offset < len(edge_ids):
            arc = first_edge_to_arc.get(edge_ids[offset])
            if arc is None:
                raise ValueError(f"graph edge {edge_ids[offset]} does not begin an EOS arc")
            end = offset + len(arc.graph_edge_ids)
            if edge_ids[offset:end] != arc.graph_edge_ids:
                raise ValueError("graph path does not preserve a complete token arc")
            selected_arcs.append(arc)
            offset = end

        choices = tuple(self.token_lattice.choices[arc.token_edge_id] for arc in selected_arcs)
        try:
            objective = fsum(choice.weight for choice in choices)
        except OverflowError as exc:
            raise ValueError("reconstructed token objective must remain finite") from exc
        if not isfinite(objective):
            raise ValueError("reconstructed token objective must remain finite")
        token_path = TokenLatticePath(
            token_edge_ids=tuple(choice.token_edge_id for choice in choices),
            token_ids=tuple(choice.token_id for choice in choices),
            objective_value=objective,
            matched_proposal_ids=tuple(
                proposal_id for choice in choices for proposal_id in choice.matched_proposal_ids
            ),
        )
        path = self.expand_path(token_path)
        if path.graph_edge_ids != edge_ids:
            raise ValueError("graph edges do not form the canonical complete EOS path")
        return path

    def reconstruct_normalized_path(
        self, normalized_graph_edge_ids: Iterable[int]
    ) -> EOSLatticePath:
        """Expand one complete normalized parser path to its full-slot token witness."""

        normalized_ids = _id_tuple(
            normalized_graph_edge_ids,
            "normalized_graph_edge_ids",
            unique=True,
        )
        provenance = self.normalization.original_edge_ids_by_normalized_edge_id
        unknown = tuple(edge_id for edge_id in normalized_ids if edge_id not in provenance)
        if unknown:
            raise ValueError(f"unknown normalized graph edge IDs: {unknown}")
        return self.reconstruct_original_path(
            original_edge_id
            for normalized_edge_id in normalized_ids
            for original_edge_id in provenance[normalized_edge_id]
        )

    def reconstruct_epsilon_only_path(self) -> EOSLatticePath:
        """Reconstruct the maximum-weight all-special path recorded by normalization."""

        epsilon_path = self.normalization.best_epsilon_only_path
        if epsilon_path is None:
            raise ValueError("the EOS lattice has no complete epsilon-only path")
        return self.reconstruct_original_path(epsilon_path.original_edge_ids)

    def validate_path(self, path: EOSLatticePath) -> None:
        """Independently verify graph, score, proposal, and full-slot metadata."""

        if not isinstance(path, EOSLatticePath):
            raise TypeError("path must be an EOSLatticePath")
        expected = self.expand_path(path.token_path)
        if path != expected:
            raise ValueError("EOS path metadata does not match its token-edge expansion")
        edge_by_id = {edge.edge_id: edge for edge in self.graph.edges}
        edges = tuple(edge_by_id[edge_id] for edge_id in path.graph_edge_ids)
        if edges:
            if edges[0].source_state != self.graph.start_node_id:
                raise ValueError("complete EOS path must start at the graph start node")
            if edges[-1].target_state not in self.graph.final_node_ids:
                raise ValueError("complete EOS path must end at a graph final node")
            if any(left.target_state != right.source_state for left, right in pairwise(edges)):
                raise ValueError("complete EOS path graph edges must be connected")
        elif self.graph.start_node_id not in self.graph.final_node_ids:
            raise ValueError("an empty EOS path is valid only when start is final")
        terminal_labels = tuple(
            edge.terminal_label for edge in edges if isinstance(edge, TerminalEdge)
        )
        if terminal_labels != path.terminal_labels:
            raise ValueError("EOS path terminal labels do not match its ordinary token bytes")
        try:
            objective = fsum(edge.weight for edge in edges)
        except OverflowError as exc:
            raise ValueError("EOS path graph objective must remain finite") from exc
        if not isfinite(objective) or objective != path.objective_value:
            raise ValueError("EOS path graph objective does not match its token objective")
        proposals = tuple(
            proposal_id for edge in edges for proposal_id in edge.matched_proposal_ids
        )
        if proposals != path.matched_proposal_ids:
            raise ValueError("EOS path proposal provenance does not match its token path")

    @property
    def diagnostics(self) -> dict[str, object]:
        return {
            "eos_mode": self.policy.mode.value,
            "termination_token_ids": list(self.policy.termination_token_ids),
            "pad_token_id": self.policy.pad_token_id,
            "physical_slot_count": self.token_lattice.slot_count,
            "legal_token_path_count": self.path_count,
            "product_arc_count": len(self.arcs),
            "original_graph_node_count": len(self.graph.node_ids),
            "original_graph_edge_count": len(self.graph.edges),
            "normalized_graph_edge_count": len(self.normalized_graph.edges),
            "epsilon_edge_count": sum(
                isinstance(edge, EpsilonEdge) for edge in self.graph.edges
            ),
            "special_reward_attachment": "own_epsilon_edge",
            "physical_slot_policy": "all_slots_consumed",
            "represented_support_sha256": self.token_lattice.support.fingerprint,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "policy": self.policy.to_dict(),
            "token_lattice": self.token_lattice.to_dict(),
            "arcs": [
                {
                    "arc_id": arc.arc_id,
                    "token_edge_id": arc.token_edge_id,
                    "position": arc.position,
                    "token_id": arc.token_id,
                    "role": arc.role.value,
                    "source_eos_state": arc.source_eos_state.value,
                    "target_eos_state": arc.target_eos_state.value,
                    "source_node_id": arc.source_node_id,
                    "target_node_id": arc.target_node_id,
                    "emitted_bytes_hex": arc.emitted_bytes.hex(),
                    "weight": arc.weight,
                    "matched_proposal_ids": list(arc.matched_proposal_ids),
                    "graph_edge_ids": list(arc.graph_edge_ids),
                }
                for arc in self.arcs
            ],
            "epsilon_provenance": {
                str(edge_id): list(original_ids)
                for edge_id, original_ids in sorted(
                    self.normalization.original_edge_ids_by_normalized_edge_id.items()
                )
            },
            "diagnostics": self.diagnostics,
        }


def build_eos_lattice(
    *,
    token_lattice: TokenLattice,
    adapter: CompositionalByteLevelAdapter,
    policy: EOSPolicy,
) -> EOSLattice:
    """Compose finite token choices with EOS state and normalize epsilon edges."""

    if not isinstance(token_lattice, TokenLattice):
        raise TypeError("token_lattice must be a TokenLattice")
    if not isinstance(adapter, CompositionalByteLevelAdapter):
        raise TypeError("adapter must be a CompositionalByteLevelAdapter")
    if not isinstance(policy, EOSPolicy):
        raise TypeError("policy must be an EOSPolicy")
    vocabulary_size = token_lattice.support.exactness_scope.vocabulary_size
    if adapter.vocabulary_size != vocabulary_size:
        raise ValueError("tokenizer adapter and exactness scope must have equal vocabulary sizes")
    for token_id in (*policy.termination_token_ids,):
        if token_id >= vocabulary_size:
            raise ValueError("termination token IDs must belong to the tokenizer vocabulary")
    if policy.pad_token_id is not None and policy.pad_token_id >= vocabulary_size:
        raise ValueError("PAD token ID must belong to the tokenizer vocabulary")

    state_node_count = 2 * (token_lattice.slot_count + 1)
    next_node_id = state_node_count
    arcs: list[EOSArc] = []
    edges: list[GraphEdge] = []

    def product_node(boundary: int, state: EOSState) -> int:
        return 2 * boundary + (1 if state is EOSState.AFTER_EOS else 0)

    for choice in token_lattice.choices:
        transitions: list[tuple[TokenRole, EOSState, EOSState, bytes]] = []
        special_mode = policy.mode is not EOSMode.ABSENT
        if special_mode and choice.token_id in policy.termination_token_ids:
            transitions.append(
                (TokenRole.EOS, EOSState.BEFORE_EOS, EOSState.AFTER_EOS, b"")
            )
        if special_mode and choice.token_id == policy.pad_token_id:
            transitions.append(
                (TokenRole.PAD, EOSState.AFTER_EOS, EOSState.AFTER_EOS, b"")
            )
        is_special = special_mode and (
            choice.token_id in policy.termination_token_ids
            or choice.token_id == policy.pad_token_id
        )
        if not is_special and adapter.emissions[choice.token_id] is not None:
            transitions.insert(
                0,
                (
                    TokenRole.ORDINARY,
                    EOSState.BEFORE_EOS,
                    EOSState.BEFORE_EOS,
                    adapter.token_bytes(choice.token_id),
                ),
            )

        for role, source_state, target_state, emission in transitions:
            source_node_id = product_node(choice.position, source_state)
            target_node_id = product_node(choice.position + 1, target_state)
            graph_edge_ids: list[int] = []
            cursor = source_node_id
            if role is TokenRole.ORDINARY:
                for offset, byte_value in enumerate(emission):
                    is_last = offset == len(emission) - 1
                    next_state = target_node_id if is_last else next_node_id
                    if not is_last:
                        next_node_id += 1
                    edge_id = len(edges)
                    graph_edge_ids.append(edge_id)
                    edges.append(
                        TerminalEdge(
                            edge_id=edge_id,
                            source_state=cursor,
                            target_state=next_state,
                            terminal_label=byte_value,
                            weight=choice.weight if offset == 0 else 0.0,
                            provenance_token_edge_id=choice.token_edge_id,
                            matched_proposal_ids=(
                                choice.matched_proposal_ids if offset == 0 else ()
                            ),
                        )
                    )
                    cursor = next_state
            else:
                edge_id = len(edges)
                graph_edge_ids.append(edge_id)
                edges.append(
                    EpsilonEdge(
                        edge_id=edge_id,
                        source_state=source_node_id,
                        target_state=target_node_id,
                        weight=choice.weight,
                        matched_proposal_ids=choice.matched_proposal_ids,
                    )
                )
            arcs.append(
                EOSArc(
                    arc_id=len(arcs),
                    token_edge_id=choice.token_edge_id,
                    position=choice.position,
                    token_id=choice.token_id,
                    role=role,
                    source_eos_state=source_state,
                    target_eos_state=target_state,
                    source_node_id=source_node_id,
                    target_node_id=target_node_id,
                    emitted_bytes=emission,
                    weight=choice.weight,
                    matched_proposal_ids=choice.matched_proposal_ids,
                    graph_edge_ids=tuple(graph_edge_ids),
                )
            )

    final_boundary = token_lattice.slot_count
    before_final = product_node(final_boundary, EOSState.BEFORE_EOS)
    after_final = product_node(final_boundary, EOSState.AFTER_EOS)
    final_node_ids: tuple[int, ...]
    if policy.mode is EOSMode.REQUIRED:
        final_node_ids = (after_final,)
    elif policy.mode is EOSMode.OPTIONAL:
        final_node_ids = (before_final, after_final)
    else:
        final_node_ids = (before_final,)
    graph = WeightedTerminalDAG(
        node_ids=tuple(range(next_node_id)),
        start_node_id=product_node(0, EOSState.BEFORE_EOS),
        final_node_ids=final_node_ids,
        edges=tuple(edges),
    )
    return EOSLattice(
        token_lattice=token_lattice,
        adapter=adapter,
        policy=policy,
        arcs=tuple(arcs),
        graph=graph,
        normalization=normalize_epsilon_edges(graph),
    )
