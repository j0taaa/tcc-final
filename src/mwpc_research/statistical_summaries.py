"""Deterministic, model-independent statistical summaries for MWPC experiments."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import fsum, isclose, isfinite, sqrt
from statistics import NormalDist

from mwpc_research.robust_timing import QUARTILE_POLICY, summarize_distribution

DEFAULT_CONFIDENCE_LEVEL = 0.95
PROPORTION_INTERVAL_METHOD = "wilson_score"
RELATIVE_GAP_ZERO_OPTIMUM_POLICY = "undefined_and_excluded"
NORMALIZED_OVERHEAD_POLICY = "(candidate_median-baseline_median)/baseline_median"


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _non_negative_finite(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    result = float(value)
    if not isfinite(result) or result < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return result


def _confidence_level(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("confidence_level must be a real number")
    result = float(value)
    if not isfinite(result) or not 0.0 < result < 1.0:
        raise ValueError("confidence_level must be finite and strictly between zero and one")
    return result


def _analysis_unit(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("analysis_unit must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class ProportionSummary:
    """One binary-event rate with a two-sided Wilson score interval."""

    event_count: int
    observation_count: int
    rate: float | None
    confidence_interval_lower: float | None
    confidence_interval_upper: float | None
    confidence_level: float
    analysis_unit: str

    def to_dict(self) -> dict[str, int | float | str | None]:
        return {
            "event_count": self.event_count,
            "observation_count": self.observation_count,
            "rate": self.rate,
            "confidence_interval_lower": self.confidence_interval_lower,
            "confidence_interval_upper": self.confidence_interval_upper,
            "confidence_level": self.confidence_level,
            "confidence_interval_method": PROPORTION_INTERVAL_METHOD,
            "analysis_unit": self.analysis_unit,
        }


def summarize_proportion(
    event_count: int,
    observation_count: int,
    *,
    analysis_unit: str,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
) -> ProportionSummary:
    """Compute a rate and Wilson interval without a normal approximation at the edges."""

    events = _non_negative_integer(event_count, "event_count")
    observations = _non_negative_integer(observation_count, "observation_count")
    if events > observations:
        raise ValueError("event_count cannot exceed observation_count")
    confidence = _confidence_level(confidence_level)
    unit = _analysis_unit(analysis_unit)
    if observations == 0:
        return ProportionSummary(events, observations, None, None, None, confidence, unit)

    rate = events / observations
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    z_squared = z * z
    denominator = 1.0 + z_squared / observations
    center = (rate + z_squared / (2.0 * observations)) / denominator
    half_width = (
        z
        * sqrt(rate * (1.0 - rate) / observations + z_squared / (4.0 * observations * observations))
        / denominator
    )
    return ProportionSummary(
        event_count=events,
        observation_count=observations,
        rate=rate,
        confidence_interval_lower=(0.0 if events == 0 else max(0.0, center - half_width)),
        confidence_interval_upper=(
            1.0 if events == observations else min(1.0, center + half_width)
        ),
        confidence_level=confidence,
        analysis_unit=unit,
    )


@dataclass(frozen=True, slots=True)
class NumericDistributionSummary:
    """A non-negative distribution with mean and type-7 quartiles."""

    count: int
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float
    iqr: float
    mean: float

    def to_dict(self) -> dict[str, int | float | str]:
        return {
            "count": self.count,
            "minimum": self.minimum,
            "q1": self.q1,
            "median": self.median,
            "q3": self.q3,
            "maximum": self.maximum,
            "iqr": self.iqr,
            "mean": self.mean,
            "quartile_policy": QUARTILE_POLICY,
        }


def summarize_numeric_distribution(
    values: Sequence[int | float],
) -> NumericDistributionSummary:
    """Summarize one non-empty sequence using unrounded finite observations."""

    normalized = tuple(
        _non_negative_finite(value, f"values[{index}]") for index, value in enumerate(values)
    )
    robust = summarize_distribution(normalized)
    return NumericDistributionSummary(
        count=robust.count,
        minimum=robust.minimum,
        q1=robust.q1,
        median=robust.median,
        q3=robust.q3,
        maximum=robust.maximum,
        iqr=robust.iqr,
        mean=fsum(normalized) / len(normalized),
    )


@dataclass(frozen=True, slots=True)
class GapSummary:
    """Exact-minus-comparator score gaps with explicit zero-optimum semantics."""

    comparison_count: int
    equality: ProportionSummary
    absolute_gap: NumericDistributionSummary | None
    relative_gap: NumericDistributionSummary | None
    zero_optimum_count: int
    relative_gap_defined_count: int
    relative_gap_undefined_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "comparison_count": self.comparison_count,
            "equality": self.equality.to_dict(),
            "absolute_gap": (None if self.absolute_gap is None else self.absolute_gap.to_dict()),
            "relative_gap": (None if self.relative_gap is None else self.relative_gap.to_dict()),
            "zero_optimum_count": self.zero_optimum_count,
            "relative_gap_defined_count": self.relative_gap_defined_count,
            "relative_gap_undefined_count": self.relative_gap_undefined_count,
            "relative_gap_zero_optimum_policy": RELATIVE_GAP_ZERO_OPTIMUM_POLICY,
        }


def summarize_gaps(
    exact_scores: Sequence[int | float],
    comparator_scores: Sequence[int | float],
    *,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
    relative_tolerance: float = 1e-12,
    absolute_tolerance: float = 1e-12,
) -> GapSummary:
    """Summarize paired exact/comparator scores without dividing by a zero optimum."""

    exact = tuple(
        _non_negative_finite(value, f"exact_scores[{index}]")
        for index, value in enumerate(exact_scores)
    )
    comparator = tuple(
        _non_negative_finite(value, f"comparator_scores[{index}]")
        for index, value in enumerate(comparator_scores)
    )
    if len(exact) != len(comparator):
        raise ValueError("exact_scores and comparator_scores must have equal lengths")
    rel_tol = _non_negative_finite(relative_tolerance, "relative_tolerance")
    abs_tol = _non_negative_finite(absolute_tolerance, "absolute_tolerance")

    absolute_gaps: list[float] = []
    relative_gaps: list[float] = []
    equality_count = 0
    zero_optimum_count = 0
    for index, (optimum, observed) in enumerate(zip(exact, comparator, strict=True)):
        if observed > optimum and not isclose(
            observed,
            optimum,
            rel_tol=rel_tol,
            abs_tol=abs_tol,
        ):
            raise ValueError(f"comparator_scores[{index}] exceeds the exact optimum")
        equal = isclose(observed, optimum, rel_tol=rel_tol, abs_tol=abs_tol)
        equality_count += equal
        gap = 0.0 if equal else optimum - observed
        absolute_gaps.append(gap)
        if optimum == 0.0:
            zero_optimum_count += 1
        else:
            relative_gaps.append(gap / optimum)

    count = len(exact)
    return GapSummary(
        comparison_count=count,
        equality=summarize_proportion(
            equality_count,
            count,
            analysis_unit="paired_score_comparison",
            confidence_level=confidence_level,
        ),
        absolute_gap=(None if not absolute_gaps else summarize_numeric_distribution(absolute_gaps)),
        relative_gap=(None if not relative_gaps else summarize_numeric_distribution(relative_gaps)),
        zero_optimum_count=zero_optimum_count,
        relative_gap_defined_count=len(relative_gaps),
        relative_gap_undefined_count=zero_optimum_count,
    )


@dataclass(frozen=True, slots=True)
class RuntimeComparisonSummary:
    """Robust runtime summaries and normalized median overhead."""

    candidate: NumericDistributionSummary | None
    baseline: NumericDistributionSummary | None
    median_runtime_ratio: float | None
    normalized_median_overhead: float | None
    baseline_median_zero: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_runtime_seconds": (
                None if self.candidate is None else self.candidate.to_dict()
            ),
            "baseline_runtime_seconds": (
                None if self.baseline is None else self.baseline.to_dict()
            ),
            "median_runtime_ratio": self.median_runtime_ratio,
            "normalized_median_overhead": self.normalized_median_overhead,
            "normalized_overhead_policy": NORMALIZED_OVERHEAD_POLICY,
            "baseline_median_zero": self.baseline_median_zero,
        }


def summarize_runtime_comparison(
    candidate_runtime_seconds: Sequence[int | float],
    baseline_runtime_seconds: Sequence[int | float],
) -> RuntimeComparisonSummary:
    """Compare median runtimes; a zero baseline leaves both ratios undefined."""

    candidate = (
        None
        if not candidate_runtime_seconds
        else summarize_numeric_distribution(candidate_runtime_seconds)
    )
    baseline = (
        None
        if not baseline_runtime_seconds
        else summarize_numeric_distribution(baseline_runtime_seconds)
    )
    baseline_zero = baseline is not None and baseline.median == 0.0
    ratio = (
        None
        if candidate is None or baseline is None or baseline_zero
        else candidate.median / baseline.median
    )
    return RuntimeComparisonSummary(
        candidate=candidate,
        baseline=baseline,
        median_runtime_ratio=ratio,
        normalized_median_overhead=None if ratio is None else ratio - 1.0,
        baseline_median_zero=baseline_zero,
    )


@dataclass(frozen=True, slots=True)
class OperationalEvent:
    """Binary operational outcomes for exactly one declared analysis unit."""

    fallback_used: bool
    timed_out: bool
    support_expanded: bool

    def __post_init__(self) -> None:
        for field_name in ("fallback_used", "timed_out", "support_expanded"):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a boolean")


@dataclass(frozen=True, slots=True)
class OperationalRateSummary:
    """Fallback, timeout, and expansion rates for one non-mixed unit."""

    analysis_unit: str
    observation_count: int
    fallback: ProportionSummary
    timeout: ProportionSummary
    support_expansion: ProportionSummary

    def to_dict(self) -> dict[str, object]:
        return {
            "analysis_unit": self.analysis_unit,
            "observation_count": self.observation_count,
            "fallback": self.fallback.to_dict(),
            "timeout": self.timeout.to_dict(),
            "support_expansion": self.support_expansion.to_dict(),
        }


def summarize_operational_rates(
    events: Sequence[OperationalEvent],
    *,
    analysis_unit: str,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
) -> OperationalRateSummary:
    """Compute three rates while retaining their explicit step/generation unit."""

    unit = _analysis_unit(analysis_unit)
    normalized = tuple(events)
    if not all(isinstance(event, OperationalEvent) for event in normalized):
        raise TypeError("events must contain OperationalEvent values")
    count = len(normalized)
    return OperationalRateSummary(
        analysis_unit=unit,
        observation_count=count,
        fallback=summarize_proportion(
            sum(event.fallback_used for event in normalized),
            count,
            analysis_unit=unit,
            confidence_level=confidence_level,
        ),
        timeout=summarize_proportion(
            sum(event.timed_out for event in normalized),
            count,
            analysis_unit=unit,
            confidence_level=confidence_level,
        ),
        support_expansion=summarize_proportion(
            sum(event.support_expanded for event in normalized),
            count,
            analysis_unit=unit,
            confidence_level=confidence_level,
        ),
    )


__all__ = [
    "DEFAULT_CONFIDENCE_LEVEL",
    "NORMALIZED_OVERHEAD_POLICY",
    "PROPORTION_INTERVAL_METHOD",
    "RELATIVE_GAP_ZERO_OPTIMUM_POLICY",
    "GapSummary",
    "NumericDistributionSummary",
    "OperationalEvent",
    "OperationalRateSummary",
    "ProportionSummary",
    "RuntimeComparisonSummary",
    "summarize_gaps",
    "summarize_numeric_distribution",
    "summarize_operational_rates",
    "summarize_proportion",
    "summarize_runtime_comparison",
]
