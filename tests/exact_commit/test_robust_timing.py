from __future__ import annotations

import threading
from math import nan

import pytest

from mwpc_research.robust_timing import (
    QUARTILE_POLICY,
    cyclic_method_order,
    measure_call,
    summarize_distribution,
)


def test_type7_median_and_iqr_are_computed_from_unrounded_repetitions() -> None:
    summary = summarize_distribution((100.0, 1.0, 3.0, 2.0))

    assert summary.to_dict() == {
        "count": 4,
        "minimum": 1.0,
        "q1": 1.75,
        "median": 2.5,
        "q3": 27.25,
        "maximum": 100.0,
        "iqr": 25.5,
        "quartile_policy": QUARTILE_POLICY,
    }
    with pytest.raises(ValueError, match="at least one"):
        summarize_distribution(())
    with pytest.raises(ValueError, match="finite"):
        summarize_distribution((nan,))


def test_cyclic_order_balances_each_method_across_every_position() -> None:
    methods = ("unconstrained", "serial", "epic", "exact")
    orders = tuple(cyclic_method_order(methods, repetition) for repetition in range(8))

    assert orders[:4] == (
        ("unconstrained", "serial", "epic", "exact"),
        ("serial", "epic", "exact", "unconstrained"),
        ("epic", "exact", "unconstrained", "serial"),
        ("exact", "unconstrained", "serial", "epic"),
    )
    for method in methods:
        positions = [order.index(method) for order in orders]
        assert sorted(positions[:4]) == [0, 1, 2, 3]
        assert positions[4:] == positions[:4]


def test_measurement_excludes_setup_and_synchronizes_both_timing_boundaries() -> None:
    events: list[str] = []
    clock_values = iter((10.0, 12.0))

    events.append("method-specific setup")
    measured = measure_call(
        lambda: events.append("run") or "value",
        synchronize_accelerator=lambda: events.append("synchronize"),
        reset_accelerator_peak=lambda: events.append("reset peak"),
        read_accelerator_peak=lambda: (200, 250),
        read_process_rss=lambda: 100,
        maximum_elapsed_seconds=5.0,
        rss_sample_interval_seconds=1.0,
        clock=lambda: events.append("clock") or next(clock_values),
    )

    assert measured.value == "value"
    assert measured.error is None
    assert measured.elapsed_seconds == 2.0
    assert measured.process_sampled_peak_rss_bytes == 100
    assert measured.process_rss_sample_count >= 2
    assert events == [
        "method-specific setup",
        "synchronize",
        "reset peak",
        "clock",
        "run",
        "synchronize",
        "clock",
    ]


def test_failed_and_over_budget_calls_retain_distinct_errors() -> None:
    def raise_error() -> str:
        raise ValueError("boom")

    failed = measure_call(
        raise_error,
        synchronize_accelerator=lambda: None,
        reset_accelerator_peak=lambda: None,
        read_accelerator_peak=lambda: (0, 0),
        read_process_rss=lambda: 1,
        maximum_elapsed_seconds=2.0,
        rss_sample_interval_seconds=1.0,
        clock=iter((0.0, 1.0)).__next__,
    )
    timed_out = measure_call(
        lambda: "too late",
        synchronize_accelerator=lambda: None,
        reset_accelerator_peak=lambda: None,
        read_accelerator_peak=lambda: (0, 0),
        read_process_rss=lambda: 1,
        maximum_elapsed_seconds=1.0,
        rss_sample_interval_seconds=1.0,
        clock=iter((0.0, 2.0)).__next__,
    )

    assert isinstance(failed.error, ValueError)
    assert failed.value is None
    assert isinstance(timed_out.error, TimeoutError)
    assert timed_out.value is None


@pytest.mark.parametrize(
    "failure", ["synchronize", "reset", "rss", "start_clock", "end_clock", "peak"]
)
def test_sampler_is_always_joined_when_measurement_boundaries_raise(failure: str) -> None:
    before = set(threading.enumerate())
    ticks = 0

    def checked(name: str, value: object) -> object:
        if failure == name:
            raise RuntimeError(name)
        return value

    def clock() -> float:
        nonlocal ticks
        ticks += 1
        checked("start_clock" if ticks == 1 else "end_clock", None)
        return float(ticks)

    with pytest.raises(RuntimeError, match=failure):
        measure_call(
            lambda: None,
            synchronize_accelerator=lambda: checked("synchronize", None),
            reset_accelerator_peak=lambda: checked("reset", None),
            read_process_rss=lambda: checked("rss", 1),
            read_accelerator_peak=lambda: checked("peak", (0, 0)),
            maximum_elapsed_seconds=5.0,
            rss_sample_interval_seconds=1.0,
            clock=clock,
        )
    assert set(threading.enumerate()) == before


def test_background_rss_reader_failure_is_reported_and_joined() -> None:
    sampled = threading.Event()
    before = set(threading.enumerate())

    def read_rss() -> int:
        if threading.current_thread().name == "mwpc-rss-sampler":
            sampled.set()
            raise RuntimeError("background reader failed")
        return 1

    with pytest.raises(RuntimeError, match="background reader failed"):
        measure_call(
            lambda: sampled.wait(1.0),
            synchronize_accelerator=lambda: None,
            reset_accelerator_peak=lambda: None,
            read_process_rss=read_rss,
            read_accelerator_peak=lambda: (0, 0),
            maximum_elapsed_seconds=2.0,
            rss_sample_interval_seconds=0.001,
        )
    assert sampled.is_set()
    assert set(threading.enumerate()) == before
