"""Reproducible Python/Rust/oracle differential checks for terminal DAGs."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import fsum, isclose
from pathlib import Path
from types import MappingProxyType
from typing import NoReturn

from mwpc_exact.reference.dag_parser import (
    reconstruct_dag_certificate,
    run_dag_cky,
    validate_dag_certificate,
)
from mwpc_exact.reference.epsilon import normalize_epsilon_edges
from mwpc_exact.reference.graph import index_terminal_dag
from mwpc_exact.reference.graph_oracle import enumerate_best_cfg_path
from mwpc_exact.rust_solver import RustDagSolveResult, solve_rust_dag
from mwpc_exact.types import SolveStatus, TerminalEdge, WeightedTerminalDAG
from mwpc_research.graph_differential import (
    RandomGraphInstance,
    generate_random_graph_instance,
)


class RustDifferentialMismatch(AssertionError):
    """One deterministic seed violated a cross-language exactness property."""

    def __init__(self, *, seed: int, property_name: str, details: str) -> None:
        self.seed = seed
        self.property_name = property_name
        self.details = details
        super().__init__(f"seed={seed} property={property_name}: {details}")


@dataclass(frozen=True, slots=True)
class RustDifferentialCaseReport:
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
class RustDifferentialFailure:
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
class RustDifferentialCampaignSummary:
    campaign_name: str
    seed_start: int
    case_count: int
    passed_cases: int
    failed_cases: int
    status_counts: Mapping[str, int]
    feature_case_counts: Mapping[str, int]
    property_checks: Mapping[str, int]
    failures: tuple[RustDifferentialFailure, ...]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.campaign_name.strip():
            raise ValueError("campaign_name must be non-empty")
        if self.passed_cases + self.failed_cases != self.case_count:
            raise ValueError("campaign passed/failed counts must equal case_count")
        for field_name in (
            "status_counts",
            "feature_case_counts",
            "property_checks",
            "metadata",
        ):
            object.__setattr__(
                self,
                field_name,
                MappingProxyType(dict(getattr(self, field_name))),
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "campaign": "m5_rust_differential",
            "campaign_name": self.campaign_name,
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


def check_rust_differential_instance(
    instance: RandomGraphInstance,
) -> RustDifferentialCaseReport:
    """Compare Python, Rust, and exhaustive parsing on one normalized instance."""
    if not isinstance(instance, RandomGraphInstance):
        raise TypeError("instance must be a RandomGraphInstance")
    normalized = normalize_epsilon_edges(instance.graph).normalized_graph
    python_solve = run_dag_cky(instance.grammar, normalized)
    rust_solve = solve_rust_dag(instance.grammar, normalized)
    oracle = enumerate_best_cfg_path(instance.grammar, normalized, max_paths=100_000)
    statuses = (python_solve.status, rust_solve.status, oracle.status)
    if len(set(statuses)) != 1:
        _mismatch(
            instance,
            "status_agreement",
            " ".join(
                (
                    f"python={python_solve.status.value}",
                    f"rust={rust_solve.status.value}",
                    f"oracle={oracle.status.value}",
                )
            ),
        )
    checks = {"status_agreement": 1}
    if rust_solve.status is SolveStatus.OPTIMAL:
        python_certificate = reconstruct_dag_certificate(python_solve)
        rust_certificate = rust_solve.certificate
        oracle_certificate = oracle.certificate
        if rust_certificate is None or oracle_certificate is None:
            _mismatch(instance, "certificate_presence", "optimal result omitted certificate")
        assert rust_certificate is not None and oracle_certificate is not None
        objectives = (
            python_certificate.objective_value,
            rust_certificate.objective_value,
            oracle_certificate.objective_value,
        )
        if not all(
            isclose(objective, objectives[0], rel_tol=1e-12, abs_tol=1e-12)
            for objective in objectives[1:]
        ):
            _mismatch(
                instance,
                "objective_agreement",
                f"python={objectives[0]} rust={objectives[1]} oracle={objectives[2]}",
            )
        for backend, certificate in (
            ("python", python_certificate),
            ("rust", rust_certificate),
            ("oracle", oracle_certificate),
        ):
            if not validate_dag_certificate(instance.grammar, normalized, certificate):
                _mismatch(
                    instance,
                    "certificate_validation",
                    f"independent validator rejected {backend} certificate",
                )
        _validate_rust_path_reward(instance, normalized, rust_solve)
        checks.update(
            {
                "objective_agreement": 1,
                "certificate_validation": 3,
                "rust_path_reward": 1,
                "rust_token_provenance": 1,
            }
        )
    else:
        if rust_solve.objective_value is not None or rust_solve.certificate is not None:
            _mismatch(
                instance,
                "nonoptimal_payload",
                "non-optimal Rust result exposed objective or certificate",
            )
        checks["nonoptimal_payload"] = 1
    return RustDifferentialCaseReport(
        seed=instance.seed,
        status=rust_solve.status,
        property_checks=checks,
        features=(*instance.features, "epsilon_normalization_output"),
    )


def run_rust_differential_campaign(
    *,
    campaign_name: str,
    seed_start: int,
    case_count: int,
    failure_directory: str | Path | None = None,
    metadata: Mapping[str, str] | None = None,
    checker: Callable[[RandomGraphInstance], RustDifferentialCaseReport] = (
        check_rust_differential_instance
    ),
) -> RustDifferentialCampaignSummary:
    """Run a replayable seed range and save exact serialized failures."""
    if not isinstance(campaign_name, str) or not campaign_name.strip():
        raise ValueError("campaign_name must be non-empty")
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
    failures: list[RustDifferentialFailure] = []
    for seed in range(seed_start, seed_start + case_count):
        instance = generate_random_graph_instance(seed)
        try:
            report = checker(instance)
        except Exception as error:
            fixture_file: str | None = None
            failure_file: str | None = None
            if failure_path is not None:
                fixture_name = f"seed-{seed}.json"
                failure_name = f"seed-{seed}.failure.json"
                (failure_path / fixture_name).write_text(instance.to_json(), encoding="utf-8")
                (failure_path / failure_name).write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "campaign_name": campaign_name,
                            "seed": seed,
                            "error_type": type(error).__name__,
                            "message": str(error),
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
                RustDifferentialFailure(
                    seed=seed,
                    error_type=type(error).__name__,
                    message=str(error),
                    fixture_file=fixture_file,
                    failure_file=failure_file,
                )
            )
            continue
        passed += 1
        status_counts[report.status.value] = status_counts.get(report.status.value, 0) + 1
        for feature in report.features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
        for property_name, count in report.property_checks.items():
            property_counts[property_name] = property_counts.get(property_name, 0) + count

    return RustDifferentialCampaignSummary(
        campaign_name=campaign_name,
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


def _validate_rust_path_reward(
    instance: RandomGraphInstance,
    normalized_graph: WeightedTerminalDAG,
    rust_solve: RustDagSolveResult,
) -> None:
    certificate = rust_solve.certificate
    assert certificate is not None and rust_solve.objective_value is not None
    indexed = index_terminal_dag(normalized_graph)
    path_edges = tuple(
        indexed.edge_by_id[edge_id] for edge_id in certificate.witness_graph_edge_ids
    )
    reward = fsum(edge.weight for edge in path_edges)
    if not isclose(reward, rust_solve.objective_value, rel_tol=1e-12, abs_tol=1e-12):
        _mismatch(
            instance,
            "rust_path_reward",
            f"certificate={rust_solve.objective_value} recomputed={reward}",
        )
    expected_token_ids = tuple(
        edge.provenance_token_edge_id for edge in path_edges if isinstance(edge, TerminalEdge)
    )
    if rust_solve.witness_token_edge_ids != expected_token_ids:
        _mismatch(
            instance,
            "rust_token_provenance",
            f"certificate={rust_solve.witness_token_edge_ids} expected={expected_token_ids}",
        )


def _mismatch(
    instance: RandomGraphInstance,
    property_name: str,
    details: str,
) -> NoReturn:
    raise RustDifferentialMismatch(
        seed=instance.seed,
        property_name=property_name,
        details=details,
    )


__all__ = [
    "RustDifferentialCampaignSummary",
    "RustDifferentialCaseReport",
    "RustDifferentialMismatch",
    "check_rust_differential_instance",
    "run_rust_differential_campaign",
]
