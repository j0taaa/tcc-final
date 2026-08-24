"""Exhaustive path oracle for tiny weighted terminal DAGs."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum

from mwpc_exact.reference.dag_parser import DagParseCertificate, validate_dag_certificate
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.graph import index_terminal_dag
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.types import SolveStatus, TerminalEdge, WeightedTerminalDAG


class PathEnumerationLimitExceeded(RuntimeError):
    """The explicit oracle encountered more completed paths than allowed."""


@dataclass(frozen=True, slots=True)
class GraphPathOracleResult:
    """Independent exhaustive result over all enumerated graph paths."""

    status: SolveStatus
    objective_value: float | None
    certificate: DagParseCertificate | None
    enumerated_path_count: int

    def __post_init__(self) -> None:
        if self.status not in {
            SolveStatus.OPTIMAL,
            SolveStatus.INFEASIBLE_ON_SUPPORT,
        }:
            raise ValueError("graph path oracle status must be optimal or infeasible")
        if self.enumerated_path_count < 0:
            raise ValueError("enumerated_path_count must be non-negative")
        if self.status is SolveStatus.OPTIMAL:
            if self.objective_value is None or self.certificate is None:
                raise ValueError("optimal oracle result requires a complete certificate")
        elif self.objective_value is not None or self.certificate is not None:
            raise ValueError("infeasible oracle result cannot contain a certificate")


def enumerate_best_cfg_path(
    grammar: CnfGrammar,
    graph: WeightedTerminalDAG,
    *,
    max_paths: int = 100_000,
) -> GraphPathOracleResult:
    """Enumerate tiny graph paths and return the heaviest CFG-accepted path.

    This oracle does not import or inspect the weighted parser chart. Its only
    grammar operation is independent Boolean recognition of a complete path.
    """
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    if isinstance(max_paths, bool) or not isinstance(max_paths, int):
        raise TypeError("max_paths must be an integer")
    if max_paths <= 0:
        raise ValueError("max_paths must be positive")
    indexed = index_terminal_dag(graph)

    completed_paths = 0
    best_score: float | None = None
    best_certificate: DagParseCertificate | None = None
    path: list[TerminalEdge] = []

    def visit(state: int) -> None:
        nonlocal completed_paths, best_score, best_certificate
        if state in graph.final_node_ids:
            if completed_paths >= max_paths:
                raise PathEnumerationLimitExceeded(
                    f"graph path enumeration exceeded max_paths={max_paths}"
                )
            completed_paths += 1
            labels = tuple(edge.terminal_label for edge in path)
            if recognizes_cnf(grammar, labels):
                score = fsum(edge.weight for edge in path)
                selected_ids = tuple(
                    proposal_id
                    for edge in path
                    for proposal_id in edge.matched_proposal_ids
                )
                certificate = DagParseCertificate(
                    objective_value=score,
                    selected_proposal_ids=selected_ids,
                    witness_terminal_labels=labels,
                    witness_graph_edge_ids=tuple(edge.edge_id for edge in path),
                )
                if not validate_dag_certificate(grammar, graph, certificate):
                    raise ValueError(
                        "enumerated path cannot produce a valid certificate; "
                        "check graph proposal provenance"
                    )
                if best_score is None or score > best_score:
                    best_score = score
                    best_certificate = certificate

        for edge in indexed.outgoing_edges[state]:
            path.append(edge)
            visit(edge.target_state)
            path.pop()

    visit(graph.start_node_id)
    if best_certificate is None:
        return GraphPathOracleResult(
            status=SolveStatus.INFEASIBLE_ON_SUPPORT,
            objective_value=None,
            certificate=None,
            enumerated_path_count=completed_paths,
        )
    return GraphPathOracleResult(
        status=SolveStatus.OPTIMAL,
        objective_value=best_score,
        certificate=best_certificate,
        enumerated_path_count=completed_paths,
    )
