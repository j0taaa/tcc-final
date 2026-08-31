from __future__ import annotations

from math import inf, nan

import pytest

from mwpc_research.statistical_summaries import (
    NORMALIZED_OVERHEAD_POLICY,
    PROPORTION_INTERVAL_METHOD,
    RELATIVE_GAP_ZERO_OPTIMUM_POLICY,
    OperationalEvent,
    summarize_gaps,
    summarize_numeric_distribution,
    summarize_operational_rates,
    summarize_proportion,
    summarize_runtime_comparison,
)


def test_wilson_interval_handles_all_success_all_failure_and_no_observations() -> None:
    all_success = summarize_proportion(10, 10, analysis_unit="case")
    all_failure = summarize_proportion(0, 10, analysis_unit="case")
    empty = summarize_proportion(0, 0, analysis_unit="case")

    assert all_success.rate == 1.0
    assert all_success.confidence_interval_lower == pytest.approx(0.7224672001)
    assert all_success.confidence_interval_upper == 1.0
    assert all_failure.rate == 0.0
    assert all_failure.confidence_interval_lower == 0.0
    assert all_failure.confidence_interval_upper == pytest.approx(0.2775327999)
    assert empty.rate is None
    assert empty.confidence_interval_lower is None
    assert empty.confidence_interval_upper is None
    assert all_success.to_dict()["confidence_interval_method"] == PROPORTION_INTERVAL_METHOD


@pytest.mark.parametrize(
    ("events", "observations", "match"),
    ((2, 1, "cannot exceed"), (-1, 1, "non-negative"), (0, -1, "non-negative")),
)
def test_proportion_rejects_invalid_counts(
    events: int,
    observations: int,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        summarize_proportion(events, observations, analysis_unit="case")


def test_numeric_distribution_uses_unrounded_type7_quartiles_and_mean() -> None:
    summary = summarize_numeric_distribution((100.0, 1.0, 3.0, 2.0))

    assert summary.to_dict() == {
        "count": 4,
        "minimum": 1.0,
        "q1": 1.75,
        "median": 2.5,
        "q3": 27.25,
        "maximum": 100.0,
        "iqr": 25.5,
        "mean": 26.5,
        "quartile_policy": "linear_interpolation_type7",
    }
    with pytest.raises(ValueError, match="at least one"):
        summarize_numeric_distribution(())
    for invalid in (nan, inf, -1.0):
        with pytest.raises(ValueError, match="finite and non-negative"):
            summarize_numeric_distribution((invalid,))


def test_gap_summary_excludes_zero_optimum_from_relative_distribution() -> None:
    summary = summarize_gaps((0.0, 4.0, 2.0), (0.0, 2.0, 2.0))
    payload = summary.to_dict()

    assert summary.comparison_count == 3
    assert summary.equality.event_count == 2
    assert summary.equality.rate == pytest.approx(2 / 3)
    assert summary.absolute_gap is not None
    assert summary.absolute_gap.mean == pytest.approx(2 / 3)
    assert summary.relative_gap is not None
    assert summary.relative_gap.count == 2
    assert summary.relative_gap.mean == 0.25
    assert summary.zero_optimum_count == 1
    assert summary.relative_gap_defined_count == 2
    assert summary.relative_gap_undefined_count == 1
    assert payload["relative_gap_zero_optimum_policy"] == (RELATIVE_GAP_ZERO_OPTIMUM_POLICY)


def test_gap_summary_handles_empty_input_and_rejects_impossible_comparator() -> None:
    empty = summarize_gaps((), ())
    assert empty.absolute_gap is None
    assert empty.relative_gap is None
    assert empty.equality.rate is None

    with pytest.raises(ValueError, match="equal lengths"):
        summarize_gaps((1.0,), ())
    with pytest.raises(ValueError, match="exceeds the exact optimum"):
        summarize_gaps((1.0,), (1.1,))


def test_runtime_summary_reports_median_ratio_and_normalized_overhead() -> None:
    summary = summarize_runtime_comparison((2.0, 4.0), (1.0, 2.0))

    assert summary.candidate is not None
    assert summary.baseline is not None
    assert summary.candidate.median == 3.0
    assert summary.baseline.median == 1.5
    assert summary.median_runtime_ratio == 2.0
    assert summary.normalized_median_overhead == 1.0
    assert summary.to_dict()["normalized_overhead_policy"] == NORMALIZED_OVERHEAD_POLICY


def test_runtime_summary_does_not_divide_by_zero_or_failed_empty_samples() -> None:
    zero_baseline = summarize_runtime_comparison((1.0, 2.0), (0.0, 0.0))
    missing_candidate = summarize_runtime_comparison((), (1.0,))

    assert zero_baseline.baseline_median_zero is True
    assert zero_baseline.median_runtime_ratio is None
    assert zero_baseline.normalized_median_overhead is None
    assert missing_candidate.candidate is None
    assert missing_candidate.median_runtime_ratio is None


def test_operational_rates_keep_step_and_generation_denominators_separate() -> None:
    per_step = summarize_operational_rates(
        (
            OperationalEvent(fallback_used=True, timed_out=False, support_expanded=False),
            OperationalEvent(fallback_used=False, timed_out=True, support_expanded=True),
            OperationalEvent(fallback_used=False, timed_out=False, support_expanded=False),
            OperationalEvent(fallback_used=False, timed_out=False, support_expanded=False),
        ),
        analysis_unit="optimizer_step",
    )
    per_generation = summarize_operational_rates(
        (
            OperationalEvent(fallback_used=True, timed_out=True, support_expanded=True),
            OperationalEvent(fallback_used=False, timed_out=False, support_expanded=False),
        ),
        analysis_unit="generation",
    )

    assert per_step.observation_count == 4
    assert per_step.fallback.rate == 0.25
    assert per_step.timeout.rate == 0.25
    assert per_step.support_expansion.rate == 0.25
    assert per_step.fallback.analysis_unit == "optimizer_step"
    assert per_generation.observation_count == 2
    assert per_generation.fallback.rate == 0.5
    assert per_generation.timeout.rate == 0.5
    assert per_generation.support_expansion.rate == 0.5
    assert per_generation.fallback.analysis_unit == "generation"


def test_operational_event_rejects_non_boolean_flags() -> None:
    with pytest.raises(TypeError, match="fallback_used"):
        OperationalEvent(  # type: ignore[arg-type]
            fallback_used=1,
            timed_out=False,
            support_expanded=False,
        )
