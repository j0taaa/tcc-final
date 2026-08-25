"""Optional component-level profiling for one exact-commit step.

The profiler is deliberately separate from scientific result diagnostics:
enabling it must not affect solver status, objective, support, witness, or
fallback behavior.  A caller may pass the same profiler through proposal,
support, solver, and decoder boundaries, then serialize one snapshot after the
step is complete.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from math import fsum, isclose, isfinite
from time import monotonic
from types import MappingProxyType


class ProfilingComponent(StrEnum):
    """Disjoint wall-clock components of an exact-commit step."""

    PROPOSAL_POLICY = "proposal_policy"
    SUPPORT_CONSTRUCTION = "support_construction"
    TOKEN_LATTICE_CONSTRUCTION = "token_lattice_construction"
    BYTE_LATTICE_EXPANSION = "byte_lattice_expansion"
    PARSER = "parser"
    BACKTRACKING = "backtracking"
    VALIDATION = "validation"
    COMMIT_UPDATE = "commit_update"


_COMPONENTS = tuple(ProfilingComponent)
_DEFAULT_COUNTERS = {
    "proposal_count": 0,
    "support_slot_count": 0,
    "support_alternative_count": 0,
    "support_max_row_size": 0,
    "support_attempt_count": 0,
    "support_expansion_count": 0,
    "token_lattice_node_count": 0,
    "token_lattice_edge_count": 0,
    "terminal_graph_node_count": 0,
    "terminal_graph_edge_count": 0,
    "normalized_graph_edge_count": 0,
    "chart_entries": 0,
    "commit_count": 0,
}


def _non_negative_finite(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    result = float(value)
    if not isfinite(result) or result < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return result


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


@dataclass(frozen=True, slots=True)
class ProfilingEvent:
    """Immutable JSON-safe snapshot of accumulated component measurements."""

    component_seconds: Mapping[str, float]
    component_invocations: Mapping[str, int]
    counters: Mapping[str, int]
    support_row_sizes: tuple[int, ...]
    measured_component_seconds: float
    unattributed_overhead_seconds: float
    wall_span_seconds: float
    schema_version: str = "mwpc_component_profile_v1"
    event_type: str = "exact_commit_component_profile"

    def __post_init__(self) -> None:
        expected = {component.value for component in _COMPONENTS}
        component_seconds = dict(self.component_seconds)
        invocations = dict(self.component_invocations)
        if set(component_seconds) != expected or set(invocations) != expected:
            raise ValueError("profiling events must contain every component exactly once")
        normalized_seconds = {
            name: _non_negative_finite(value, f"component_seconds[{name!r}]")
            for name, value in component_seconds.items()
        }
        normalized_invocations = {
            name: _non_negative_integer(value, f"component_invocations[{name!r}]")
            for name, value in invocations.items()
        }
        counters = {
            str(name): _non_negative_integer(value, f"counters[{name!r}]")
            for name, value in self.counters.items()
        }
        support_row_sizes = tuple(
            _non_negative_integer(value, f"support_row_sizes[{index}]")
            for index, value in enumerate(self.support_row_sizes)
        )
        measured = _non_negative_finite(
            self.measured_component_seconds,
            "measured_component_seconds",
        )
        overhead = _non_negative_finite(
            self.unattributed_overhead_seconds,
            "unattributed_overhead_seconds",
        )
        wall = _non_negative_finite(self.wall_span_seconds, "wall_span_seconds")
        component_sum = fsum(normalized_seconds.values())
        tolerance = max(1e-12, 1e-9 * max(wall, component_sum, 1.0))
        if not isclose(measured, component_sum, rel_tol=1e-12, abs_tol=tolerance):
            raise ValueError("measured component total does not equal its breakdown")
        if not isclose(measured + overhead, wall, rel_tol=1e-12, abs_tol=tolerance):
            raise ValueError("component time plus overhead does not equal wall span")
        object.__setattr__(self, "component_seconds", MappingProxyType(normalized_seconds))
        object.__setattr__(
            self,
            "component_invocations",
            MappingProxyType(normalized_invocations),
        )
        object.__setattr__(self, "counters", MappingProxyType(counters))
        object.__setattr__(self, "support_row_sizes", support_row_sizes)
        object.__setattr__(self, "measured_component_seconds", measured)
        object.__setattr__(self, "unattributed_overhead_seconds", overhead)
        object.__setattr__(self, "wall_span_seconds", wall)

    @property
    def accounted_total_seconds(self) -> float:
        """Return component time plus explicitly recorded measurement overhead."""

        return self.measured_component_seconds + self.unattributed_overhead_seconds

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable profiling event."""

        return {
            "schema_version": self.schema_version,
            "event_type": self.event_type,
            "timings_seconds": {
                "components": dict(self.component_seconds),
                "measured_component_total": self.measured_component_seconds,
                "unattributed_measurement_overhead": self.unattributed_overhead_seconds,
                "accounted_total": self.accounted_total_seconds,
                "wall_span": self.wall_span_seconds,
            },
            "component_invocations": dict(self.component_invocations),
            "sizes": {
                "counters": dict(self.counters),
                "support_row_sizes": list(self.support_row_sizes),
            },
        }


class ComponentProfiler:
    """Accumulate optional, non-nested component timings and size counters.

    The default disabled state never reads the supplied clock.  Measurement
    scopes must not overlap: double-counted nested timings would make the
    component sum incomparable with the enclosing wall span.
    """

    __slots__ = (
        "_clock",
        "_component_invocations",
        "_component_seconds",
        "_counters",
        "_enabled",
        "_first_started_at",
        "_last_finished_at",
        "_span_active",
        "_support_row_sizes",
    )

    def __init__(
        self,
        *,
        enabled: bool = False,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a boolean")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._enabled = enabled
        self._clock = clock
        self._component_seconds = {component: 0.0 for component in _COMPONENTS}
        self._component_invocations = {component: 0 for component in _COMPONENTS}
        self._counters = dict(_DEFAULT_COUNTERS)
        self._support_row_sizes: tuple[int, ...] = ()
        self._first_started_at: float | None = None
        self._last_finished_at: float | None = None
        self._span_active = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _read_clock(self) -> float:
        value = self._clock()
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("profiling clock must return a real number")
        result = float(value)
        if not isfinite(result):
            raise ValueError("profiling clock must return a finite value")
        return result

    def _open_span(self) -> float:
        if self._span_active:
            raise RuntimeError("profiling measurement spans must not be nested")
        started_at = self._read_clock()
        if self._last_finished_at is not None and started_at < self._last_finished_at:
            raise RuntimeError("profiling clock moved backwards")
        if self._first_started_at is None:
            self._first_started_at = started_at
        self._span_active = True
        return started_at

    def _close_span(self, started_at: float) -> float:
        finished_at = self._read_clock()
        if finished_at < started_at:
            raise RuntimeError("profiling clock moved backwards")
        self._span_active = False
        self._last_finished_at = finished_at
        return finished_at - started_at

    @contextmanager
    def measure(self, component: ProfilingComponent) -> Iterator[None]:
        """Measure one component; a disabled profiler is a clock-free no-op."""

        if not isinstance(component, ProfilingComponent):
            raise TypeError("component must be a ProfilingComponent")
        if not self._enabled:
            yield
            return
        started_at = self._open_span()
        try:
            yield
        finally:
            elapsed = self._close_span(started_at)
            self._component_seconds[component] += elapsed
            self._component_invocations[component] += 1

    @contextmanager
    def observe_wall_span(self) -> Iterator[None]:
        """Track an externally decomposed operation without double-counting it."""

        if not self._enabled:
            yield
            return
        started_at = self._open_span()
        try:
            yield
        finally:
            self._close_span(started_at)

    def add_duration(self, component: ProfilingComponent, seconds: float) -> None:
        """Add a separately measured duration, such as an in-Rust phase timer."""

        if not self._enabled:
            return
        if not isinstance(component, ProfilingComponent):
            raise TypeError("component must be a ProfilingComponent")
        duration = _non_negative_finite(seconds, "seconds")
        self._component_seconds[component] += duration
        self._component_invocations[component] += 1

    def set_counter(self, name: str, value: int) -> None:
        """Set the latest size/count observation for this step."""

        if not self._enabled:
            return
        if not isinstance(name, str) or not name:
            raise ValueError("counter name must be a non-empty string")
        self._counters[name] = _non_negative_integer(value, f"counter {name!r}")

    def set_support_row_sizes(self, row_sizes: Sequence[int]) -> None:
        """Record the latest represented support width at every physical slot."""

        if not self._enabled:
            return
        self._support_row_sizes = tuple(
            _non_negative_integer(value, f"support row size {index}")
            for index, value in enumerate(row_sizes)
        )

    def snapshot(self) -> ProfilingEvent | None:
        """Freeze the current event, or return ``None`` when profiling is disabled."""

        if not self._enabled:
            return None
        if self._span_active:
            raise RuntimeError("cannot snapshot while a profiling measurement is active")
        first = self._first_started_at
        last = self._last_finished_at
        wall = 0.0 if first is None or last is None else last - first
        measured = fsum(self._component_seconds.values())
        tolerance = max(1e-12, 1e-9 * max(wall, measured, 1.0))
        if measured > wall + tolerance:
            raise RuntimeError("component timings overlap or exceed the measured wall span")
        overhead = max(0.0, wall - measured)
        return ProfilingEvent(
            component_seconds={
                component.value: self._component_seconds[component] for component in _COMPONENTS
            },
            component_invocations={
                component.value: self._component_invocations[component] for component in _COMPONENTS
            },
            counters=dict(sorted(self._counters.items())),
            support_row_sizes=self._support_row_sizes,
            measured_component_seconds=measured,
            unattributed_overhead_seconds=overhead,
            wall_span_seconds=wall,
        )


__all__ = ["ComponentProfiler", "ProfilingComponent", "ProfilingEvent"]
