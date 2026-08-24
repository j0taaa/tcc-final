"""Validated Python boundary for the independent Rust CFG-on-DAG solver."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module
from math import isfinite
from types import MappingProxyType
from typing import Protocol, cast

from mwpc_exact.reference.dag_parser import DagParseCertificate
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.types import SolveStatus, TerminalLabel, WeightedTerminalDAG


class RustBindingUnavailable(ImportError):
    """The release binding has not been built in the active environment."""


class _RustBinding(Protocol):
    def solve(
        self,
        grammar: object,
        graph: object,
        *,
        timeout_seconds: float | None,
        deadline_check_interval: int,
        deterministic_work_limit: int | None,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class RustDagSolveResult:
    """Parser-local Rust result with an optional independently checkable certificate."""

    status: SolveStatus
    objective_value: float | None
    certificate: DagParseCertificate | None
    witness_token_edge_ids: tuple[int | None, ...]
    diagnostics: Mapping[str, int | float]

    def __post_init__(self) -> None:
        if not isinstance(self.status, SolveStatus):
            raise TypeError("status must be a SolveStatus")
        if self.status is SolveStatus.OPTIMAL:
            if self.objective_value is None or self.certificate is None:
                raise ValueError("OPTIMAL Rust result requires an objective and certificate")
            if len(self.witness_token_edge_ids) != len(self.certificate.witness_graph_edge_ids):
                raise ValueError("token provenance must align with witness graph edges")
        elif self.objective_value is not None or self.certificate is not None:
            raise ValueError("non-OPTIMAL Rust result cannot expose a partial certificate")
        object.__setattr__(self, "diagnostics", MappingProxyType(dict(self.diagnostics)))


def _binding() -> _RustBinding:
    try:
        return cast("_RustBinding", import_module("mwpc_parser_py"))
    except ImportError as error:
        raise RustBindingUnavailable(
            "mwpc_parser_py is unavailable; rebuild it with `make bootstrap-rust-parser`"
        ) from error


def _tuple_of_ids(value: object, field_name: str, *, require_unique: bool) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, list):
        raise TypeError(f"Rust {field_name} must be a list")
    result: list[int] = []
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise TypeError(f"Rust {field_name}[{index}] must be a non-negative integer")
        result.append(item)
    if require_unique and len(set(result)) != len(result):
        raise ValueError(f"Rust {field_name} must not contain duplicates")
    return tuple(result)


def _tuple_of_labels(value: object) -> tuple[TerminalLabel, ...]:
    if not isinstance(value, list):
        raise TypeError("Rust witness_terminal_labels must be a list")
    labels: list[TerminalLabel] = []
    for index, label in enumerate(value):
        if isinstance(label, bool) or not isinstance(label, (int, str)):
            raise TypeError(f"Rust witness_terminal_labels[{index}] has invalid type")
        if isinstance(label, int) and not 0 <= label <= 255:
            raise ValueError(f"Rust witness_terminal_labels[{index}] is not a byte")
        if isinstance(label, str) and not label:
            raise ValueError(f"Rust witness_terminal_labels[{index}] is empty")
        labels.append(label)
    return tuple(labels)


def _tuple_of_optional_ids(value: object) -> tuple[int | None, ...]:
    if not isinstance(value, list):
        raise TypeError("Rust witness_token_edge_ids must be a list")
    result: list[int | None] = []
    for index, item in enumerate(value):
        if item is None:
            result.append(None)
        elif isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise TypeError(
                f"Rust witness_token_edge_ids[{index}] must be a non-negative integer or None"
            )
        else:
            result.append(item)
    return tuple(result)


def _diagnostics(value: object) -> Mapping[str, int | float]:
    if not isinstance(value, Mapping):
        raise TypeError("Rust diagnostics must be a mapping")
    result: dict[str, int | float] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise TypeError("Rust diagnostics keys must be strings")
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError(f"Rust diagnostic {key!r} must be numeric")
        if isinstance(item, float) and not isfinite(item):
            raise ValueError(f"Rust diagnostic {key!r} must be finite")
        result[key] = item
    return result


def solve_rust_dag(
    grammar: CnfGrammar,
    graph: WeightedTerminalDAG,
    *,
    timeout_seconds: float | None = None,
    deadline_check_interval: int = 1_024,
    deterministic_work_limit: int | None = None,
) -> RustDagSolveResult:
    """Solve one validated epsilon-free graph using the Rust production parser."""
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    if not isinstance(graph, WeightedTerminalDAG):
        raise TypeError("graph must be a WeightedTerminalDAG")
    if timeout_seconds is not None:
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
            raise TypeError("timeout_seconds must be a real number or None")
        timeout_seconds = float(timeout_seconds)
        if not isfinite(timeout_seconds) or timeout_seconds < 0.0:
            raise ValueError("timeout_seconds must be finite and non-negative")
    if (
        isinstance(deadline_check_interval, bool)
        or not isinstance(deadline_check_interval, int)
        or deadline_check_interval <= 0
    ):
        raise ValueError("deadline_check_interval must be a positive integer")
    if deterministic_work_limit is not None and (
        isinstance(deterministic_work_limit, bool)
        or not isinstance(deterministic_work_limit, int)
        or deterministic_work_limit < 0
    ):
        raise ValueError("deterministic_work_limit must be a non-negative integer or None")
    raw_object = _binding().solve(
        grammar,
        graph,
        timeout_seconds=timeout_seconds,
        deadline_check_interval=deadline_check_interval,
        deterministic_work_limit=deterministic_work_limit,
    )
    if not isinstance(raw_object, Mapping):
        raise TypeError("Rust solve result must be a mapping")
    raw = cast("Mapping[str, object]", raw_object)
    status = raw.get("status")
    if not isinstance(status, SolveStatus):
        raise TypeError("Rust status must be the Python SolveStatus enum")
    objective_raw = raw.get("objective_value")
    if objective_raw is None:
        objective = None
    elif isinstance(objective_raw, bool) or not isinstance(objective_raw, (int, float)):
        raise TypeError("Rust objective_value must be a real number or None")
    else:
        objective = float(objective_raw)
        if not isfinite(objective) or objective < 0.0:
            raise ValueError("Rust objective_value must be finite and non-negative")

    selected = _tuple_of_ids(
        raw.get("selected_proposal_ids"),
        "selected_proposal_ids",
        require_unique=False,
    )
    labels = _tuple_of_labels(raw.get("witness_terminal_labels"))
    edge_ids = _tuple_of_ids(
        raw.get("witness_graph_edge_ids"),
        "witness_graph_edge_ids",
        require_unique=True,
    )
    token_edge_ids = _tuple_of_optional_ids(raw.get("witness_token_edge_ids"))
    certificate = None
    if status is SolveStatus.OPTIMAL:
        if objective is None:
            raise ValueError("OPTIMAL Rust result omitted objective_value")
        certificate = DagParseCertificate(objective, selected, labels, edge_ids)
    elif selected or labels or edge_ids or token_edge_ids:
        raise ValueError("non-OPTIMAL Rust result exposed partial witness data")
    return RustDagSolveResult(
        status=status,
        objective_value=objective,
        certificate=certificate,
        witness_token_edge_ids=token_edge_ids,
        diagnostics=_diagnostics(raw.get("diagnostics")),
    )


__all__ = ["RustBindingUnavailable", "RustDagSolveResult", "solve_rust_dag"]
