"""Explicit epsilon-edge normalization for finite weighted DAGs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import fsum, isclose, isfinite
from types import MappingProxyType

from mwpc_exact.reference.dag_parser import (
    DagParseCertificate,
    DagSolve,
    reconstruct_dag_certificate,
    run_dag_cky,
    validate_dag_certificate,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.graph import index_terminal_dag
from mwpc_exact.types import EpsilonEdge, SolveStatus, TerminalEdge, WeightedTerminalDAG


class EpsilonNormalizationError(ValueError):
    """Epsilon normalization cannot preserve a valid weighted certificate."""


@dataclass(frozen=True, slots=True)
class EpsilonPath:
    """One maximum-weight epsilon-only path between two graph states."""

    source_state: int
    target_state: int
    weight: float
    original_edge_ids: tuple[int, ...]
    matched_proposal_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class EpsilonNormalizationResult:
    """Epsilon-free graph plus exact original-edge provenance."""

    original_graph: WeightedTerminalDAG
    normalized_graph: WeightedTerminalDAG
    original_edge_ids_by_normalized_edge_id: Mapping[int, tuple[int, ...]]
    best_epsilon_only_path: EpsilonPath | None

    def __post_init__(self) -> None:
        if not isinstance(self.original_graph, WeightedTerminalDAG):
            raise TypeError("original_graph must be a WeightedTerminalDAG")
        if not isinstance(self.normalized_graph, WeightedTerminalDAG):
            raise TypeError("normalized_graph must be a WeightedTerminalDAG")
        if any(isinstance(edge, EpsilonEdge) for edge in self.normalized_graph.edges):
            raise ValueError("normalized_graph must not contain epsilon edges")
        provenance = dict(self.original_edge_ids_by_normalized_edge_id)
        if set(provenance) != {edge.edge_id for edge in self.normalized_graph.edges}:
            raise ValueError("every normalized edge requires exactly one provenance path")
        object.__setattr__(
            self,
            "original_edge_ids_by_normalized_edge_id",
            MappingProxyType(provenance),
        )


@dataclass(frozen=True, slots=True)
class EpsilonDagSolveResult:
    """Exact solve whose certificate names edges in the external graph."""

    status: SolveStatus
    objective_value: float | None
    certificate: DagParseCertificate | None
    normalization: EpsilonNormalizationResult
    normalized_solve: DagSolve

    def __post_init__(self) -> None:
        if self.status not in {
            SolveStatus.OPTIMAL,
            SolveStatus.INFEASIBLE_ON_SUPPORT,
        }:
            raise ValueError("epsilon DAG solve must be optimal or infeasible")
        if self.status is SolveStatus.OPTIMAL:
            if self.objective_value is None or self.certificate is None:
                raise ValueError("optimal epsilon DAG solve requires a certificate")
        elif self.objective_value is not None or self.certificate is not None:
            raise ValueError("infeasible epsilon DAG solve cannot contain a certificate")


def normalize_epsilon_edges(graph: WeightedTerminalDAG) -> EpsilonNormalizationResult:
    """Saturate terminal edges with maximum-weight epsilon closures.

    For fixed endpoints an epsilon-only subpath is invisible to both the
    terminal string and all surrounding graph contexts. Consequently only its
    maximum weight is relevant to a max-plus optimum. Equal-weight paths use a
    stable lexicographic edge-ID tie-break, which is not part of the objective.
    """
    indexed = index_terminal_dag(graph)
    order = indexed.topological_order
    closures: dict[tuple[int, int], EpsilonPath] = {}

    for source_index, source in enumerate(order):
        best_from_source: dict[int, EpsilonPath] = {
            source: EpsilonPath(source, source, 0.0, (), ())
        }
        for state in order[source_index:]:
            prefix = best_from_source.get(state)
            if prefix is None:
                continue
            for edge in indexed.outgoing_edges[state]:
                if not isinstance(edge, EpsilonEdge):
                    continue
                candidate_weight = prefix.weight + edge.weight
                if not isfinite(candidate_weight):
                    raise EpsilonNormalizationError(
                        "epsilon closure objective overflowed finite float range"
                    )
                candidate_ids = (*prefix.original_edge_ids, edge.edge_id)
                candidate_proposals = (
                    *prefix.matched_proposal_ids,
                    *edge.matched_proposal_ids,
                )
                candidate = EpsilonPath(
                    source,
                    edge.target_state,
                    candidate_weight,
                    candidate_ids,
                    candidate_proposals,
                )
                current = best_from_source.get(edge.target_state)
                if current is None or _epsilon_path_is_better(candidate, current):
                    best_from_source[edge.target_state] = candidate
        closures.update(
            {(source, target): path for target, path in best_from_source.items()}
        )

    normalized_edges: list[TerminalEdge] = []
    provenance: dict[int, tuple[int, ...]] = {}
    terminal_edges = sorted(
        (edge for edge in graph.edges if isinstance(edge, TerminalEdge)),
        key=lambda edge: edge.edge_id,
    )
    for terminal_edge in terminal_edges:
        prefixes = tuple(
            closures[(source, terminal_edge.source_state)]
            for source in order
            if (source, terminal_edge.source_state) in closures
        )
        suffixes = tuple(
            closures[(terminal_edge.target_state, target)]
            for target in order
            if (terminal_edge.target_state, target) in closures
        )
        for prefix in prefixes:
            for suffix in suffixes:
                original_ids = (
                    *prefix.original_edge_ids,
                    terminal_edge.edge_id,
                    *suffix.original_edge_ids,
                )
                matched_ids = (
                    *prefix.matched_proposal_ids,
                    *terminal_edge.matched_proposal_ids,
                    *suffix.matched_proposal_ids,
                )
                weight = prefix.weight + terminal_edge.weight + suffix.weight
                if not isfinite(weight):
                    raise EpsilonNormalizationError(
                        "saturated terminal edge weight overflowed finite float range"
                    )
                edge_id = len(normalized_edges)
                normalized_edges.append(
                    TerminalEdge(
                        edge_id=edge_id,
                        source_state=prefix.source_state,
                        target_state=suffix.target_state,
                        terminal_label=terminal_edge.terminal_label,
                        weight=weight,
                        provenance_token_edge_id=terminal_edge.provenance_token_edge_id,
                        matched_proposal_ids=matched_ids,
                    )
                )
                provenance[edge_id] = original_ids

    epsilon_only_candidates = tuple(
        closures[(graph.start_node_id, final)]
        for final in graph.final_node_ids
        if (graph.start_node_id, final) in closures
    )
    best_epsilon_only = min(
        epsilon_only_candidates,
        key=lambda path: (-path.weight, path.original_edge_ids, path.target_state),
        default=None,
    )
    normalized = WeightedTerminalDAG(
        node_ids=graph.node_ids,
        start_node_id=graph.start_node_id,
        final_node_ids=graph.final_node_ids,
        edges=tuple(normalized_edges),
    )
    return EpsilonNormalizationResult(
        original_graph=graph,
        normalized_graph=normalized,
        original_edge_ids_by_normalized_edge_id=provenance,
        best_epsilon_only_path=best_epsilon_only,
    )


def solve_cfg_on_epsilon_dag(
    grammar: CnfGrammar,
    graph: WeightedTerminalDAG,
) -> EpsilonDagSolveResult:
    """Normalize epsilon edges, solve exactly, and restore original provenance."""
    normalization = normalize_epsilon_edges(graph)
    normalized_solve = run_dag_cky(grammar, normalization.normalized_graph)
    candidates: list[DagParseCertificate] = []

    if normalized_solve.status is SolveStatus.OPTIMAL:
        normalized_certificate = reconstruct_dag_certificate(normalized_solve)
        candidates.append(_expand_normalized_certificate(normalization, normalized_certificate))

    epsilon_path = normalization.best_epsilon_only_path
    if grammar.accepts_empty and epsilon_path is not None:
        candidates.append(
            DagParseCertificate(
                objective_value=epsilon_path.weight,
                selected_proposal_ids=epsilon_path.matched_proposal_ids,
                witness_terminal_labels=(),
                witness_graph_edge_ids=epsilon_path.original_edge_ids,
            )
        )

    if not candidates:
        return EpsilonDagSolveResult(
            status=SolveStatus.INFEASIBLE_ON_SUPPORT,
            objective_value=None,
            certificate=None,
            normalization=normalization,
            normalized_solve=normalized_solve,
        )
    best = min(
        candidates,
        key=lambda certificate: (
            -certificate.objective_value,
            certificate.witness_graph_edge_ids,
        ),
    )
    if not validate_dag_certificate(grammar, graph, best):
        raise EpsilonNormalizationError("expanded original-graph certificate is invalid")
    return EpsilonDagSolveResult(
        status=SolveStatus.OPTIMAL,
        objective_value=best.objective_value,
        certificate=best,
        normalization=normalization,
        normalized_solve=normalized_solve,
    )


def _expand_normalized_certificate(
    normalization: EpsilonNormalizationResult,
    certificate: DagParseCertificate,
) -> DagParseCertificate:
    original_ids = tuple(
        original_edge_id
        for normalized_edge_id in certificate.witness_graph_edge_ids
        for original_edge_id in normalization.original_edge_ids_by_normalized_edge_id[
            normalized_edge_id
        ]
    )
    edge_by_id = index_terminal_dag(normalization.original_graph).edge_by_id
    original_edges = tuple(edge_by_id[edge_id] for edge_id in original_ids)
    selected_ids = tuple(
        proposal_id
        for edge in original_edges
        for proposal_id in edge.matched_proposal_ids
    )
    objective = fsum(edge.weight for edge in original_edges)
    if not isclose(
        objective,
        certificate.objective_value,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        raise EpsilonNormalizationError(
            "expanded original path weight differs from normalized certificate"
        )
    return DagParseCertificate(
        objective_value=objective,
        selected_proposal_ids=selected_ids,
        witness_terminal_labels=certificate.witness_terminal_labels,
        witness_graph_edge_ids=original_ids,
    )


def _epsilon_path_is_better(candidate: EpsilonPath, current: EpsilonPath) -> bool:
    return candidate.weight > current.weight or (
        candidate.weight == current.weight
        and candidate.original_edge_ids < current.original_edge_ids
    )
