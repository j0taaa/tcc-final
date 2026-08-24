"""Reproducible differential checks for weighted terminal/epsilon DAGs."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import fsum, isclose
from pathlib import Path
from random import Random
from types import MappingProxyType
from typing import NoReturn

from mwpc_exact.reference.dag_parser import validate_dag_certificate
from mwpc_exact.reference.epsilon import (
    EpsilonNormalizationResult,
    solve_cfg_on_epsilon_dag,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.reference.graph import index_terminal_dag
from mwpc_exact.reference.graph_oracle import enumerate_best_cfg_path
from mwpc_exact.types import EpsilonEdge, SolveStatus, TerminalEdge, WeightedTerminalDAG

GRAPH_GENERATOR_SCHEMA_VERSION = 1


class GraphDifferentialMismatch(AssertionError):
    """One deterministic graph seed violated an exactness property."""

    def __init__(self, *, seed: int, property_name: str, details: str) -> None:
        self.seed = seed
        self.property_name = property_name
        self.details = details
        super().__init__(f"seed={seed} property={property_name}: {details}")


@dataclass(frozen=True, slots=True)
class RandomGraphInstance:
    """One deterministic tiny graph/grammar intersection."""

    seed: int
    grammar_kind: str
    grammar: CnfGrammar
    graph: WeightedTerminalDAG
    features: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": GRAPH_GENERATOR_SCHEMA_VERSION,
            "seed": self.seed,
            "grammar_kind": self.grammar_kind,
            "grammar": self.grammar.to_dict(),
            "graph": {
                "node_ids": list(self.graph.node_ids),
                "start_node_id": self.graph.start_node_id,
                "final_node_ids": list(self.graph.final_node_ids),
                "edges": [_edge_to_dict(edge) for edge in self.graph.edges],
            },
            "features": list(self.features),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True, slots=True)
class GraphDifferentialCaseReport:
    seed: int
    status: SolveStatus
    property_checks: Mapping[str, int]
    features: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "property_checks",
            MappingProxyType(dict(self.property_checks)),
        )


@dataclass(frozen=True, slots=True)
class GraphDifferentialFailure:
    seed: int
    error_type: str
    message: str
    fixture_file: str | None
    failure_file: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "error_type": self.error_type,
            "message": self.message,
            "fixture_file": self.fixture_file,
            "failure_file": self.failure_file,
        }


@dataclass(frozen=True, slots=True)
class GraphDifferentialCampaignSummary:
    seed_start: int
    case_count: int
    passed_cases: int
    failed_cases: int
    status_counts: Mapping[str, int]
    feature_case_counts: Mapping[str, int]
    property_checks: Mapping[str, int]
    failures: tuple[GraphDifferentialFailure, ...]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        if self.passed_cases + self.failed_cases != self.case_count:
            raise ValueError("campaign passed/failed counts must equal case_count")
        for field_name in ("status_counts", "feature_case_counts", "property_checks", "metadata"):
            object.__setattr__(self, field_name, MappingProxyType(dict(getattr(self, field_name))))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "campaign": "m4_graph_differential",
            "seed_start": self.seed_start,
            "case_count": self.case_count,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "status_counts": dict(self.status_counts),
            "feature_case_counts": dict(self.feature_case_counts),
            "property_checks": dict(self.property_checks),
            "failures": [failure.to_dict() for failure in self.failures],
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    def write_json(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_json(), encoding="utf-8")


def generate_random_graph_instance(seed: int) -> RandomGraphInstance:
    """Generate a tiny acyclic graph with mandatory M4 stress features."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    rng = Random(seed)
    node_count = 4 + rng.randrange(2)
    topological_nodes = tuple(rng.sample(range(10, 90), node_count))
    edges: list[TerminalEdge | EpsilonEdge] = []

    def add_epsilon(source_index: int, target_index: int) -> None:
        edge_id = len(edges)
        edges.append(
            EpsilonEdge(
                edge_id=edge_id,
                source_state=topological_nodes[source_index],
                target_state=topological_nodes[target_index],
                weight=rng.randint(0, 9),
                matched_proposal_ids=(edge_id,),
            )
        )

    def add_terminal(source_index: int, target_index: int, label: str) -> None:
        edge_id = len(edges)
        edges.append(
            TerminalEdge(
                edge_id=edge_id,
                source_state=topological_nodes[source_index],
                target_state=topological_nodes[target_index],
                terminal_label=label,
                weight=rng.randint(0, 9),
                provenance_token_edge_id=10_000 + edge_id,
                matched_proposal_ids=(edge_id,),
            )
        )

    # Every generated case contains a two-edge epsilon chain and two parallel
    # arcs that emit the same terminal through distinct token provenance IDs.
    add_epsilon(0, 1)
    add_epsilon(1, 2)
    parallel_label = rng.choice(("x", "y"))
    add_terminal(2, 3, parallel_label)
    add_terminal(2, 3, parallel_label)

    for source_index in range(node_count - 1):
        for target_index in range(source_index + 1, node_count):
            for _ in range(rng.randrange(3)):
                if rng.random() < 0.3:
                    add_epsilon(source_index, target_index)
                else:
                    add_terminal(source_index, target_index, rng.choice(("x", "y")))

    final_indices: tuple[int, ...]
    if seed % 2 == 0:
        final_indices = (2, node_count - 1)
    else:
        final_indices = (node_count - 1,)
    final_ids = tuple(dict.fromkeys(topological_nodes[index] for index in final_indices))
    graph = WeightedTerminalDAG(
        node_ids=tuple(reversed(topological_nodes)),
        start_node_id=topological_nodes[0],
        final_node_ids=final_ids,
        edges=tuple(reversed(edges)) if seed % 3 == 0 else tuple(edges),
    )
    grammar_kind, grammar = _grammar_for_seed(seed)
    features = [
        "epsilon_chain",
        "integer_edge_rewards",
        "parallel_edges",
        "same_terminal_distinct_token_provenance",
    ]
    if len(final_ids) > 1:
        features.append("multiple_final_states")
    if grammar_kind == "unrepresented_terminal":
        features.append("forced_infeasible_intersection")
    return RandomGraphInstance(seed, grammar_kind, grammar, graph, tuple(features))


def check_graph_differential_instance(
    instance: RandomGraphInstance,
) -> GraphDifferentialCaseReport:
    """Compare normalized parsing to direct enumeration and validate certificates."""
    if not isinstance(instance, RandomGraphInstance):
        raise TypeError("instance must be a RandomGraphInstance")
    solver = solve_cfg_on_epsilon_dag(instance.grammar, instance.graph)
    oracle = enumerate_best_cfg_path(instance.grammar, instance.graph, max_paths=100_000)
    checks: dict[str, int] = {}
    if solver.status is not oracle.status:
        _mismatch(
            instance,
            "status_agreement",
            f"solver={solver.status.value} oracle={oracle.status.value}",
        )
    checks["status_agreement"] = 1

    normalized_edge_checks = _validate_normalization(instance, solver.normalization)
    checks["normalized_edge_validation"] = normalized_edge_checks
    if solver.status is SolveStatus.OPTIMAL:
        if solver.objective_value is None or oracle.objective_value is None:
            _mismatch(instance, "objective_agreement", "optimal result omitted objective")
        if not isclose(
            solver.objective_value,
            oracle.objective_value,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            _mismatch(
                instance,
                "objective_agreement",
                f"solver={solver.objective_value} oracle={oracle.objective_value}",
            )
        assert solver.certificate is not None and oracle.certificate is not None
        if not validate_dag_certificate(instance.grammar, instance.graph, solver.certificate):
            _mismatch(instance, "solver_certificate", "independent validator rejected")
        if not validate_dag_certificate(instance.grammar, instance.graph, oracle.certificate):
            _mismatch(instance, "oracle_certificate", "independent validator rejected")
        checks["certificate_validation"] = 2
    elif solver.objective_value is not None or oracle.objective_value is not None:
        _mismatch(instance, "objective_agreement", "infeasible result exposed objective")
    checks["objective_agreement"] = 1
    return GraphDifferentialCaseReport(
        seed=instance.seed,
        status=solver.status,
        property_checks=checks,
        features=instance.features,
    )


def run_graph_differential_campaign(
    *,
    seed_start: int,
    case_count: int,
    failure_directory: str | Path | None = None,
    metadata: Mapping[str, str] | None = None,
    checker: Callable[[RandomGraphInstance], GraphDifferentialCaseReport] = (
        check_graph_differential_instance
    ),
) -> GraphDifferentialCampaignSummary:
    """Run and summarize a replayable contiguous seed range."""
    if isinstance(seed_start, bool) or not isinstance(seed_start, int) or seed_start < 0:
        raise ValueError("seed_start must be a non-negative integer")
    if isinstance(case_count, bool) or not isinstance(case_count, int) or case_count <= 0:
        raise ValueError("case_count must be a positive integer")
    failure_path = None if failure_directory is None else Path(failure_directory)
    if failure_path is not None:
        failure_path.mkdir(parents=True, exist_ok=True)

    passed = 0
    status_counts: dict[str, int] = {}
    feature_counts: dict[str, int] = {}
    property_counts: dict[str, int] = {}
    failures: list[GraphDifferentialFailure] = []
    for seed in range(seed_start, seed_start + case_count):
        instance = generate_random_graph_instance(seed)
        try:
            report = checker(instance)
        except Exception as exc:
            fixture_file: str | None = None
            failure_file: str | None = None
            if failure_path is not None:
                fixture_name = f"seed-{seed}.json"
                failure_name = f"seed-{seed}.failure.json"
                (failure_path / fixture_name).write_text(
                    instance.to_json(), encoding="utf-8"
                )
                (failure_path / failure_name).write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "seed": seed,
                            "error_type": type(exc).__name__,
                            "message": str(exc),
                            "fixture_file": fixture_name,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                fixture_file = fixture_name
                failure_file = failure_name
            failures.append(
                GraphDifferentialFailure(
                    seed,
                    type(exc).__name__,
                    str(exc),
                    fixture_file,
                    failure_file,
                )
            )
            continue
        passed += 1
        status_counts[report.status.value] = status_counts.get(report.status.value, 0) + 1
        for feature in report.features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        for name, count in report.property_checks.items():
            property_counts[name] = property_counts.get(name, 0) + count

    return GraphDifferentialCampaignSummary(
        seed_start=seed_start,
        case_count=case_count,
        passed_cases=passed,
        failed_cases=len(failures),
        status_counts=status_counts,
        feature_case_counts=feature_counts,
        property_checks=property_counts,
        failures=tuple(failures),
        metadata={} if metadata is None else metadata,
    )


def _grammar_for_seed(seed: int) -> tuple[str, CnfGrammar]:
    terminals = (Terminal(10, "x"), Terminal(20, "y"), Terminal(30, "z"))
    if seed % 5 == 0:
        return (
            "unrepresented_terminal",
            CnfGrammar(
                nonterminals=(Nonterminal(0, "S"),),
                terminals=terminals,
                start_nonterminal_id=0,
                terminal_productions=(TerminalProduction(0, 0, 30),),
            ),
        )
    if seed % 5 == 1:
        return (
            "any_nonempty_xy",
            CnfGrammar(
                nonterminals=(Nonterminal(0, "S"),),
                terminals=terminals,
                start_nonterminal_id=0,
                terminal_productions=(
                    TerminalProduction(0, 0, 10),
                    TerminalProduction(1, 0, 20),
                ),
                binary_productions=(BinaryProduction(2, 0, 0, 0),),
            ),
        )
    if seed % 5 == 2:
        return (
            "exactly_two_xy",
            CnfGrammar(
                nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A")),
                terminals=terminals,
                start_nonterminal_id=0,
                terminal_productions=(
                    TerminalProduction(0, 1, 10),
                    TerminalProduction(1, 1, 20),
                ),
                binary_productions=(BinaryProduction(2, 0, 1, 1),),
            ),
        )
    if seed % 5 == 3:
        return (
            "ordered_xy",
            CnfGrammar(
                nonterminals=(
                    Nonterminal(0, "S"),
                    Nonterminal(1, "X"),
                    Nonterminal(2, "Y"),
                ),
                terminals=terminals,
                start_nonterminal_id=0,
                terminal_productions=(
                    TerminalProduction(0, 1, 10),
                    TerminalProduction(1, 2, 20),
                ),
                binary_productions=(BinaryProduction(2, 0, 1, 2),),
            ),
        )
    return (
        "empty_or_x",
        CnfGrammar(
            nonterminals=(Nonterminal(0, "S"),),
            terminals=terminals,
            start_nonterminal_id=0,
            terminal_productions=(TerminalProduction(0, 0, 10),),
            accepts_empty=True,
        ),
    )


def _validate_normalization(
    instance: RandomGraphInstance,
    normalization: EpsilonNormalizationResult,
) -> int:
    original_edges = index_terminal_dag(instance.graph).edge_by_id
    checked = 0
    for normalized_edge in normalization.normalized_graph.edges:
        assert isinstance(normalized_edge, TerminalEdge)
        original_ids = normalization.original_edge_ids_by_normalized_edge_id[
            normalized_edge.edge_id
        ]
        if len(set(original_ids)) != len(original_ids):
            _mismatch(instance, "normalization_provenance", "original edge repeated")
        current = normalized_edge.source_state
        terminals: list[TerminalEdge] = []
        selected_ids: list[int] = []
        weights: list[float] = []
        for edge_id in original_ids:
            edge = original_edges[edge_id]
            if edge.source_state != current:
                _mismatch(instance, "normalization_provenance", "path is discontinuous")
            current = edge.target_state
            if isinstance(edge, TerminalEdge):
                terminals.append(edge)
            selected_ids.extend(edge.matched_proposal_ids)
            weights.append(edge.weight)
        if current != normalized_edge.target_state or len(terminals) != 1:
            _mismatch(instance, "normalization_provenance", "endpoint or terminal count")
        if terminals[0].terminal_label != normalized_edge.terminal_label:
            _mismatch(instance, "normalization_provenance", "terminal label changed")
        if terminals[0].provenance_token_edge_id != normalized_edge.provenance_token_edge_id:
            _mismatch(instance, "normalization_provenance", "token provenance changed")
        if tuple(selected_ids) != normalized_edge.matched_proposal_ids:
            _mismatch(instance, "normalization_provenance", "proposal provenance changed")
        if not isclose(
            fsum(weights), normalized_edge.weight, rel_tol=1e-12, abs_tol=1e-12
        ):
            _mismatch(instance, "normalization_provenance", "edge weight changed")
        checked += 1
    return checked


def _edge_to_dict(edge: TerminalEdge | EpsilonEdge) -> dict[str, object]:
    common: dict[str, object] = {
        "edge_id": edge.edge_id,
        "source_state": edge.source_state,
        "target_state": edge.target_state,
        "weight": edge.weight,
        "matched_proposal_ids": list(edge.matched_proposal_ids),
    }
    if isinstance(edge, EpsilonEdge):
        return {"kind": "epsilon", **common}
    return {
        "kind": "terminal",
        **common,
        "terminal_label": edge.terminal_label,
        "provenance_token_edge_id": edge.provenance_token_edge_id,
    }


def _mismatch(
    instance: RandomGraphInstance,
    property_name: str,
    details: str,
) -> NoReturn:
    raise GraphDifferentialMismatch(
        seed=instance.seed,
        property_name=property_name,
        details=details,
    )
