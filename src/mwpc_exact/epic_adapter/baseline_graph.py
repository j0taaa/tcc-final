"""Safe parent-side calls into EPIC's boolean graph feasibility baseline.

This module is baseline-only. The exact MWPC solver must expose explicit
statuses and must not reuse a boolean API that maps timeout to emptiness.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

GraphT = TypeVar("GraphT", contravariant=True)


class NormalizedGraphCFG(Protocol[GraphT]):
    def is_graph_intersection_empty(self, graph: GraphT, timeout: float) -> bool: ...


class NormalizableGraphCFG(Protocol[GraphT]):
    def to_normal_form(self) -> NormalizedGraphCFG[GraphT]: ...


def baseline_graph_intersection_is_empty(
    cfg: NormalizableGraphCFG[GraphT], graph: GraphT, timeout_seconds: float
) -> bool:
    """Call EPIC's graph checker after avoiding its raw-CFG OnceCell deadlock."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    normalized = cfg.to_normal_form()
    return normalized.is_graph_intersection_empty(graph, timeout_seconds)
