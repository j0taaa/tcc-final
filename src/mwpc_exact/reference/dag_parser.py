"""Max-plus CFG intersection with a finite weighted terminal DAG."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import fsum, isclose, isfinite
from types import MappingProxyType
from typing import TypeAlias

from mwpc_exact.reference.grammar import CnfGrammar, TerminalProduction
from mwpc_exact.reference.graph import IndexedTerminalDAG, index_terminal_dag
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.types import SolveStatus, TerminalLabel, WeightedTerminalDAG


@dataclass(frozen=True, slots=True)
class DagTerminalBackpointer:
    """A terminal production paired with one concrete graph edge."""

    production_id: int
    terminal_id: int
    edge_id: int


@dataclass(frozen=True, slots=True)
class DagBinaryBackpointer:
    """A binary production and the graph state joining its children."""

    production_id: int
    intermediate_state: int
    left_nonterminal_id: int
    right_nonterminal_id: int


DagBackpointer: TypeAlias = DagTerminalBackpointer | DagBinaryBackpointer
DagChartKey: TypeAlias = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class DagChartEntry:
    """Best known weight and reconstructible decision for one chart key."""

    score: float
    backpointer: DagBackpointer

    def __post_init__(self) -> None:
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise TypeError("chart score must be a real number")
        score = float(self.score)
        if not isfinite(score) or score < 0:
            raise ValueError("chart score must be finite and non-negative")
        if not isinstance(
            self.backpointer,
            (DagTerminalBackpointer, DagBinaryBackpointer),
        ):
            raise TypeError("invalid DAG chart backpointer")
        object.__setattr__(self, "score", score)


@dataclass(frozen=True, slots=True)
class DagChart:
    """Immutable sparse chart over graph endpoint pairs."""

    grammar: CnfGrammar
    indexed_graph: IndexedTerminalDAG
    entries: Mapping[DagChartKey, DagChartEntry]

    def __post_init__(self) -> None:
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        if not isinstance(self.indexed_graph, IndexedTerminalDAG):
            raise TypeError("indexed_graph must be an IndexedTerminalDAG")
        entries = dict(self.entries)
        nonterminal_ids = {item.symbol_id for item in self.grammar.nonterminals}
        nodes = set(self.indexed_graph.graph.node_ids)
        order = self.indexed_graph.topological_index
        for key, entry in entries.items():
            if (
                not isinstance(key, tuple)
                or len(key) != 3
                or any(isinstance(item, bool) or not isinstance(item, int) for item in key)
            ):
                raise TypeError("chart keys must be (nonterminal, source, target) integers")
            nonterminal_id, source, target = key
            if nonterminal_id not in nonterminal_ids:
                raise ValueError("chart key references an unknown nonterminal")
            if source not in nodes or target not in nodes:
                raise ValueError("chart key references an unknown graph state")
            if order[source] >= order[target]:
                raise ValueError("DAG chart entries must span forward in topological order")
            if not isinstance(entry, DagChartEntry):
                raise TypeError("chart values must be DagChartEntry instances")
        object.__setattr__(self, "entries", MappingProxyType(entries))

    def entry(self, nonterminal_id: int, source: int, target: int) -> DagChartEntry | None:
        """Look up one sparse chart entry."""
        return self.entries.get((nonterminal_id, source, target))


@dataclass(frozen=True, slots=True)
class DagSolve:
    """Internal parser outcome before certificate reconstruction."""

    status: SolveStatus
    chart: DagChart
    final_node_id: int | None

    def __post_init__(self) -> None:
        if self.status not in {
            SolveStatus.OPTIMAL,
            SolveStatus.INFEASIBLE_ON_SUPPORT,
        }:
            raise ValueError("DAG solve must be OPTIMAL or INFEASIBLE_ON_SUPPORT")
        if not isinstance(self.chart, DagChart):
            raise TypeError("chart must be a DagChart")
        if self.status is SolveStatus.OPTIMAL:
            if self.final_node_id not in self.chart.indexed_graph.graph.final_node_ids:
                raise ValueError("optimal DAG solve requires a graph final node")
        elif self.final_node_id is not None:
            raise ValueError("infeasible DAG solve cannot select a final node")


@dataclass(frozen=True, slots=True)
class DagParseCertificate:
    """Parser-local certificate over a generic terminal graph.

    Token IDs are intentionally absent: only a later token-lattice boundary can
    recover them from token-edge provenance without inventing information.
    """

    objective_value: float
    selected_proposal_ids: tuple[int, ...]
    witness_terminal_labels: tuple[TerminalLabel, ...]
    witness_graph_edge_ids: tuple[int, ...]


class DagCertificateReconstructionError(ValueError):
    """A DAG chart does not reconstruct to its recorded objective."""


def run_dag_cky(grammar: CnfGrammar, graph: WeightedTerminalDAG) -> DagSolve:
    """Run exact max-plus CFG parsing over every path represented by ``graph``."""
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    indexed = index_terminal_dag(graph)
    labels = grammar.terminal_labels
    terminal_id_by_label = {label: terminal_id for terminal_id, label in labels.items()}
    entries: dict[DagChartKey, DagChartEntry] = {}

    productions_by_terminal: dict[int, list[TerminalProduction]] = {}
    for production in sorted(grammar.terminal_productions, key=lambda item: item.production_id):
        productions_by_terminal.setdefault(production.terminal_id, []).append(production)

    for edge in sorted(graph.edges, key=lambda item: item.edge_id):
        terminal_id = terminal_id_by_label.get(edge.terminal_label)
        if terminal_id is None:
            continue
        for terminal_production in productions_by_terminal.get(terminal_id, ()):
            _stable_update(
                entries,
                (terminal_production.head_id, edge.source_state, edge.target_state),
                edge.weight,
                DagTerminalBackpointer(
                    production_id=terminal_production.production_id,
                    terminal_id=terminal_id,
                    edge_id=edge.edge_id,
                ),
            )

    order = indexed.topological_order
    binary_productions = sorted(grammar.binary_productions, key=lambda item: item.production_id)
    for width in range(1, len(order)):
        for source_index in range(0, len(order) - width):
            target_index = source_index + width
            source = order[source_index]
            target = order[target_index]
            for binary_production in binary_productions:
                for middle_index in range(source_index + 1, target_index):
                    middle = order[middle_index]
                    left = entries.get((binary_production.left_id, source, middle))
                    if left is None:
                        continue
                    right = entries.get((binary_production.right_id, middle, target))
                    if right is None:
                        continue
                    candidate = left.score + right.score
                    if not isfinite(candidate):
                        raise ValueError("DAG objective overflowed finite float range")
                    _stable_update(
                        entries,
                        (binary_production.head_id, source, target),
                        candidate,
                        DagBinaryBackpointer(
                            production_id=binary_production.production_id,
                            intermediate_state=middle,
                            left_nonterminal_id=binary_production.left_id,
                            right_nonterminal_id=binary_production.right_id,
                        ),
                    )

    chart = DagChart(grammar, indexed, entries)
    start = graph.start_node_id
    best_final: int | None = None
    best_score: float | None = None
    for final in sorted(
        graph.final_node_ids,
        key=lambda node_id: (indexed.topological_index[node_id], node_id),
    ):
        if final == start and grammar.accepts_empty:
            candidate = 0.0
        else:
            root = chart.entry(grammar.start_nonterminal_id, start, final)
            if root is None:
                continue
            candidate = root.score
        if best_score is None or candidate > best_score:
            best_score = candidate
            best_final = final

    if best_final is None:
        return DagSolve(SolveStatus.INFEASIBLE_ON_SUPPORT, chart, None)
    return DagSolve(SolveStatus.OPTIMAL, chart, best_final)


def reconstruct_dag_certificate(solve: DagSolve) -> DagParseCertificate:
    """Reconstruct a graph path and independently re-sum its edge weights."""
    if not isinstance(solve, DagSolve):
        raise TypeError("solve must be a DagSolve")
    if solve.status is not SolveStatus.OPTIMAL or solve.final_node_id is None:
        raise DagCertificateReconstructionError("cannot reconstruct an infeasible DAG solve")

    graph = solve.chart.indexed_graph.graph
    if solve.final_node_id == graph.start_node_id:
        if not solve.chart.grammar.accepts_empty:
            raise DagCertificateReconstructionError("empty path requires empty grammar acceptance")
        return DagParseCertificate(0.0, (), (), ())

    terminal_productions = {
        production.production_id: production
        for production in solve.chart.grammar.terminal_productions
    }
    binary_productions = {
        production.production_id: production
        for production in solve.chart.grammar.binary_productions
    }
    edge_by_id = solve.chart.indexed_graph.edge_by_id
    labels = solve.chart.grammar.terminal_labels
    path_edges: list[int] = []
    path_labels: list[TerminalLabel] = []
    selected_ids: list[int] = []

    def visit(nonterminal_id: int, source: int, target: int) -> float:
        entry = solve.chart.entry(nonterminal_id, source, target)
        if entry is None:
            raise DagCertificateReconstructionError(
                f"missing chart entry ({nonterminal_id}, {source}, {target})"
            )
        pointer = entry.backpointer
        if isinstance(pointer, DagTerminalBackpointer):
            terminal_production = terminal_productions.get(pointer.production_id)
            edge = edge_by_id.get(pointer.edge_id)
            if terminal_production is None or edge is None:
                raise DagCertificateReconstructionError(
                    "terminal backpointer references an unknown production or edge"
                )
            if (
                terminal_production.head_id != nonterminal_id
                or terminal_production.terminal_id != pointer.terminal_id
                or edge.source_state != source
                or edge.target_state != target
                or labels[pointer.terminal_id] != edge.terminal_label
            ):
                raise DagCertificateReconstructionError(
                    "terminal backpointer does not match its chart key"
                )
            if not isclose(entry.score, edge.weight, rel_tol=1e-12, abs_tol=1e-12):
                raise DagCertificateReconstructionError(
                    "terminal chart score does not equal its edge weight"
                )
            path_edges.append(edge.edge_id)
            path_labels.append(edge.terminal_label)
            selected_ids.extend(edge.matched_proposal_ids)
            return edge.weight

        binary_production = binary_productions.get(pointer.production_id)
        if binary_production is None:
            raise DagCertificateReconstructionError("unknown binary production")
        middle = pointer.intermediate_state
        order = solve.chart.indexed_graph.topological_index
        if not order[source] < order[middle] < order[target]:
            raise DagCertificateReconstructionError("binary intermediate state is outside span")
        if (
            binary_production.head_id != nonterminal_id
            or binary_production.left_id != pointer.left_nonterminal_id
            or binary_production.right_id != pointer.right_nonterminal_id
        ):
            raise DagCertificateReconstructionError(
                "binary backpointer does not match its production"
            )
        left = visit(pointer.left_nonterminal_id, source, middle)
        right = visit(pointer.right_nonterminal_id, middle, target)
        score = left + right
        if not isfinite(score) or not isclose(
            entry.score, score, rel_tol=1e-12, abs_tol=1e-12
        ):
            raise DagCertificateReconstructionError(
                "binary chart score does not equal its child-score sum"
            )
        return score

    root_score = visit(
        solve.chart.grammar.start_nonterminal_id,
        graph.start_node_id,
        solve.final_node_id,
    )
    if len(set(path_edges)) != len(path_edges):
        raise DagCertificateReconstructionError("reconstructed path repeats an edge")
    if len(set(selected_ids)) != len(selected_ids):
        raise DagCertificateReconstructionError(
            "reconstructed path repeats a matched proposal ID"
        )
    objective = fsum(edge_by_id[edge_id].weight for edge_id in path_edges)
    if not isclose(objective, root_score, rel_tol=1e-12, abs_tol=1e-12):
        raise DagCertificateReconstructionError(
            "recomputed path objective does not equal the root chart score"
        )
    certificate = DagParseCertificate(
        objective_value=objective,
        selected_proposal_ids=tuple(selected_ids),
        witness_terminal_labels=tuple(path_labels),
        witness_graph_edge_ids=tuple(path_edges),
    )
    if not validate_dag_certificate(solve.chart.grammar, graph, certificate):
        raise DagCertificateReconstructionError("independent certificate validation failed")
    return certificate


def validate_dag_certificate(
    grammar: CnfGrammar,
    graph: WeightedTerminalDAG,
    certificate: DagParseCertificate,
) -> bool:
    """Validate a parser-local certificate without reading its chart."""
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    indexed = index_terminal_dag(graph)
    if not isinstance(certificate, DagParseCertificate):
        raise TypeError("certificate must be a DagParseCertificate")
    if len(certificate.witness_terminal_labels) != len(
        certificate.witness_graph_edge_ids
    ):
        return False

    current = graph.start_node_id
    labels: list[TerminalLabel] = []
    selected_ids: list[int] = []
    weights: list[float] = []
    for edge_id, claimed_label in zip(
        certificate.witness_graph_edge_ids,
        certificate.witness_terminal_labels,
        strict=True,
    ):
        edge = indexed.edge_by_id.get(edge_id)
        if edge is None or edge.source_state != current or edge.terminal_label != claimed_label:
            return False
        current = edge.target_state
        labels.append(edge.terminal_label)
        selected_ids.extend(edge.matched_proposal_ids)
        weights.append(edge.weight)
    if current not in graph.final_node_ids:
        return False
    if tuple(selected_ids) != certificate.selected_proposal_ids:
        return False
    if len(set(selected_ids)) != len(selected_ids):
        return False
    if not isclose(
        fsum(weights), certificate.objective_value, rel_tol=1e-12, abs_tol=1e-12
    ):
        return False
    return recognizes_cnf(grammar, tuple(labels))


def _stable_update(
    entries: dict[DagChartKey, DagChartEntry],
    key: DagChartKey,
    candidate_score: float,
    backpointer: DagBackpointer,
) -> None:
    existing = entries.get(key)
    if existing is None or candidate_score > existing.score:
        entries[key] = DagChartEntry(candidate_score, backpointer)
