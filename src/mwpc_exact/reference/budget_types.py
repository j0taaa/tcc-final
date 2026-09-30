"""Exact-arithmetic contracts for the separate budgeted-batch objective."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite

from mwpc_exact.types import SolveStatus, TerminalLabel


def rational_reward(value: int | float | Fraction) -> Fraction:
    """Interpret floats as their exact binary rational value, without rounding sums."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise TypeError("reward must be an integer, finite float or Fraction")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("reward must be finite")
    result = Fraction(value)
    if result < 0:
        raise ValueError("reward must be non-negative")
    return result


def nonnegative_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True)
class ResourceArc:
    """One original DAG arc, optionally consuming budget; None emits epsilon."""

    arc_id: int
    source: int
    target: int
    label: TerminalLabel | None
    reward: Fraction
    cost: int = 0

    def __post_init__(self) -> None:
        for name in ("arc_id", "source", "target", "cost"):
            nonnegative_integer(getattr(self, name), name)
        if self.label is not None and (
            isinstance(self.label, bool)
            or not isinstance(self.label, (int, str))
            or (isinstance(self.label, int) and not 0 <= self.label <= 255)
            or self.label == ""
        ):
            raise ValueError("label must be a byte, nonempty string or None")
        object.__setattr__(self, "reward", rational_reward(self.reward))


@dataclass(frozen=True)
class ResourceDAG:
    """Explicit finite graph with caller-supplied, validated topological order."""

    nodes: tuple[int, ...]
    start: int
    finals: tuple[int, ...]
    arcs: tuple[ResourceArc, ...]
    support_description: str = "exact_on_support: explicit finite resource DAG"

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "finals", tuple(self.finals))
        object.__setattr__(self, "arcs", tuple(self.arcs))
        if not all(isinstance(arc, ResourceArc) for arc in self.arcs):
            raise TypeError("arcs must contain ResourceArc values")
        if not self.nodes or len(set(self.nodes)) != len(self.nodes):
            raise ValueError("nodes must be nonempty and unique")
        for node in self.nodes:
            nonnegative_integer(node, "node")
        nonnegative_integer(self.start, "start")
        for final in self.finals:
            nonnegative_integer(final, "final")
        rank = {node: i for i, node in enumerate(self.nodes)}
        if self.start not in rank or any(f not in rank for f in self.finals):
            raise ValueError("start/finals must belong to nodes")
        if len(set(self.finals)) != len(self.finals):
            raise ValueError("final nodes must be unique")
        if len({arc.arc_id for arc in self.arcs}) != len(self.arcs):
            raise ValueError("arc IDs must be unique")
        for arc in self.arcs:
            if arc.source not in rank or arc.target not in rank:
                raise ValueError("arc endpoint missing from nodes")
            if rank[arc.source] >= rank[arc.target]:
                raise ValueError("arcs must strictly advance in topological order")
        if not isinstance(self.support_description, str) or not self.support_description.strip():
            raise ValueError("an explicit support description is required")


EpsilonKey = tuple[int, int, int]
ChartKey = tuple[int, int, int, int]


@dataclass(frozen=True)
class BudgetCertificate:
    """Upper potentials; omitted cells mean minus infinity, never zero."""

    max_budget: int
    epsilon_bounds: tuple[tuple[int, int, int, Fraction], ...]
    grammar_bounds: tuple[tuple[int, int, int, int, Fraction], ...]

    def __post_init__(self) -> None:
        nonnegative_integer(self.max_budget, "max_budget")
        for rows, width in ((self.epsilon_bounds, 4), (self.grammar_bounds, 5)):
            for row in rows:
                if len(row) != width:
                    raise ValueError("invalid potential row width")
                for key in row[:-1]:
                    if not isinstance(key, int) or isinstance(key, bool) or key < 0:
                        raise ValueError("potential keys must be non-negative integers")
                if not isinstance(row[-1], Fraction) or row[-1] < 0:
                    raise ValueError("potentials must be non-negative exact Fractions")


@dataclass(frozen=True)
class BudgetPathResult:
    status: SolveStatus
    budget: int
    objective_value: Fraction | None
    witness_arc_ids: tuple[int, ...] | None
    witness_terminal_labels: tuple[TerminalLabel, ...] | None
    consumed_budget: int | None
    certificate: BudgetCertificate
    exactness_scope: str


@dataclass(frozen=True)
class BudgetCertificateReport:
    accepted: bool
    errors: tuple[str, ...]
