"""Model-independent timing, memory, and robust-summary helpers.

Preparation belongs outside :func:`measure_call`.  The measured callable must
contain only the work whose runtime is being compared.  Accelerator callbacks
keep this module independent of torch and make the synchronization boundaries
unit-testable on CPU-only machines.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import isfinite
from threading import Event, Thread
from time import perf_counter
from typing import Generic, TypeVar

_T = TypeVar("_T")

QUARTILE_POLICY = "linear_interpolation_type7"


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


def _quantile(sorted_values: tuple[float, ...], probability: float) -> float:
    if not sorted_values:
        raise ValueError("a distribution requires at least one value")
    position = probability * (len(sorted_values) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = position - lower_index
    return sorted_values[lower_index] + fraction * (
        sorted_values[upper_index] - sorted_values[lower_index]
    )


@dataclass(frozen=True, slots=True)
class DistributionSummary:
    """Deterministic median/IQR summary using type-7 linear interpolation."""

    count: int
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float
    iqr: float

    def to_dict(self) -> dict[str, int | float | str]:
        return {
            "count": self.count,
            "minimum": self.minimum,
            "q1": self.q1,
            "median": self.median,
            "q3": self.q3,
            "maximum": self.maximum,
            "iqr": self.iqr,
            "quartile_policy": QUARTILE_POLICY,
        }


def summarize_distribution(values: Sequence[int | float]) -> DistributionSummary:
    """Summarize one non-empty sequence without rounding stored measurements."""

    normalized = tuple(
        sorted(
            _non_negative_finite(value, f"values[{index}]") for index, value in enumerate(values)
        )
    )
    if not normalized:
        raise ValueError("a distribution requires at least one value")
    q1 = _quantile(normalized, 0.25)
    median = _quantile(normalized, 0.5)
    q3 = _quantile(normalized, 0.75)
    return DistributionSummary(
        count=len(normalized),
        minimum=normalized[0],
        q1=q1,
        median=median,
        q3=q3,
        maximum=normalized[-1],
        iqr=q3 - q1,
    )


def cyclic_method_order(methods: Sequence[str], repetition: int) -> tuple[str, ...]:
    """Rotate a fixed method tuple so repeated runs have balanced positions."""

    normalized = tuple(methods)
    if not normalized or len(set(normalized)) != len(normalized):
        raise ValueError("methods must be a non-empty sequence of unique names")
    index = _non_negative_integer(repetition, "repetition") % len(normalized)
    return normalized[index:] + normalized[:index]


@dataclass(frozen=True, slots=True)
class CallMeasurement(Generic[_T]):
    """One measured call, including per-call memory observations."""

    value: _T | None
    error: Exception | None
    elapsed_seconds: float
    process_rss_before_bytes: int
    process_rss_after_bytes: int
    process_sampled_peak_rss_bytes: int
    process_rss_sample_count: int
    accelerator_peak_allocated_bytes: int
    accelerator_peak_reserved_bytes: int


class _PeakRssSampler:
    """Sample process RSS while a short measured call is active."""

    def __init__(self, reader: Callable[[], int], interval_seconds: float) -> None:
        if not callable(reader):
            raise TypeError("RSS reader must be callable")
        self._reader = reader
        self._interval = _non_negative_finite(interval_seconds, "RSS sample interval")
        if self._interval == 0.0:
            raise ValueError("RSS sample interval must be positive")
        self._started = Event()
        self._stop = Event()
        self._ready = Event()
        self._peak = 0
        self._sample_count = 0
        self._thread = Thread(target=self._sample, name="mwpc-rss-sampler", daemon=True)

    def _read(self) -> None:
        value = self._reader()
        normalized = _non_negative_integer(value, "process RSS")
        self._peak = max(self._peak, normalized)
        self._sample_count += 1

    def _sample(self) -> None:
        self._ready.set()
        self._started.wait()
        while not self._stop.wait(self._interval):
            self._read()

    def launch(self) -> None:
        self._thread.start()
        self._ready.wait()

    def begin(self, initial_rss_bytes: int) -> None:
        normalized = _non_negative_integer(initial_rss_bytes, "initial process RSS")
        self._peak = normalized
        self._sample_count = 1
        self._started.set()

    def finish(self, final_rss_bytes: int) -> tuple[int, int]:
        normalized = _non_negative_integer(final_rss_bytes, "final process RSS")
        self._peak = max(self._peak, normalized)
        self._sample_count += 1
        self._stop.set()
        self._thread.join()
        return self._peak, self._sample_count


def measure_call(
    run: Callable[[], _T],
    *,
    synchronize_accelerator: Callable[[], None],
    reset_accelerator_peak: Callable[[], None],
    read_accelerator_peak: Callable[[], tuple[int, int]],
    read_process_rss: Callable[[], int],
    maximum_elapsed_seconds: float,
    rss_sample_interval_seconds: float,
    clock: Callable[[], float] = perf_counter,
) -> CallMeasurement[_T]:
    """Measure a prepared call with synchronized accelerator boundaries.

    The RSS sampler thread, CUDA synchronization, peak-counter reset, and RSS
    snapshots are intentionally outside the elapsed interval.  Exceptions are
    preserved as statuses for the caller rather than converted to values.
    """

    if not callable(run) or not callable(clock):
        raise TypeError("run and clock must be callable")
    budget = _non_negative_finite(maximum_elapsed_seconds, "maximum elapsed seconds")
    sampler = _PeakRssSampler(read_process_rss, rss_sample_interval_seconds)
    sampler.launch()
    synchronize_accelerator()
    reset_accelerator_peak()
    rss_before = _non_negative_integer(read_process_rss(), "process RSS before")
    sampler.begin(rss_before)
    start = float(clock())
    if not isfinite(start):
        raise ValueError("measurement clock must return finite values")
    value: _T | None = None
    error: Exception | None = None
    try:
        if budget == 0.0:
            raise TimeoutError("run deadline expired before the measured call started")
        value = run()
        synchronize_accelerator()
    except Exception as caught:
        error = caught
        try:
            synchronize_accelerator()
        except Exception:
            pass
    end = float(clock())
    if not isfinite(end) or end < start:
        raise ValueError("measurement clock must be finite and monotonic")
    elapsed = end - start
    if error is None and elapsed > budget:
        value = None
        error = TimeoutError("measured call completed after the configured run deadline")
    rss_after = _non_negative_integer(read_process_rss(), "process RSS after")
    rss_peak, rss_sample_count = sampler.finish(rss_after)
    accelerator_allocated, accelerator_reserved = read_accelerator_peak()
    allocated = _non_negative_integer(accelerator_allocated, "accelerator allocated peak")
    reserved = _non_negative_integer(accelerator_reserved, "accelerator reserved peak")
    if reserved < allocated:
        raise ValueError("accelerator reserved peak cannot be below allocated peak")
    return CallMeasurement(
        value=value,
        error=error,
        elapsed_seconds=elapsed,
        process_rss_before_bytes=rss_before,
        process_rss_after_bytes=rss_after,
        process_sampled_peak_rss_bytes=rss_peak,
        process_rss_sample_count=rss_sample_count,
        accelerator_peak_allocated_bytes=allocated,
        accelerator_peak_reserved_bytes=reserved,
    )


__all__ = [
    "QUARTILE_POLICY",
    "CallMeasurement",
    "DistributionSummary",
    "cyclic_method_order",
    "measure_call",
    "summarize_distribution",
]
