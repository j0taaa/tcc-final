"""Adaptive reference posterior with a caller-selected, deterministic TV budget.

Returns the exact posterior on J_d; its error versus J is explicit. Failed
certification increases depth or falls back to full inference, never to an
uncertified sample. Controls share preparation and original vocabulary weights.
"""

from fractions import Fraction
from itertools import pairwise
from time import monotonic, perf_counter, process_time

from mwpc_exact.cfg_posterior import CompilationLimit

from .certificate import CounterTable, conditional_error
from .handoff import OverflowFrontier
from .posterior import class_weights
from .stack_control import StackPosterior, StackPrepared


def evaluate_certified(
    table,
    weights,
    tolerance,
    *,
    method="handoff",
    depths=(1, 2, 3, 4, 6, 8),
    timeout_seconds=120,
    max_edges=10_000_000,
    max_cells=10_000_000,
    max_terms=50_000_000,
):
    tolerance = Fraction(tolerance)
    if not 0 < tolerance < 1:
        raise ValueError("tolerance must be strictly between zero and one")
    if method not in ("closed", "handoff", "grammar_hit", "suffix_hit", "hit"):
        raise ValueError("unknown certificate method")
    if not depths or any(type(d) is not int or d < 0 for d in depths):
        raise ValueError("depths must be nonnegative integers")
    if any(a >= b for a, b in pairwise(depths)):
        raise ValueError("depths must be strictly increasing")
    deadline = monotonic() + timeout_seconds
    attempts = []
    sums = class_weights(table, weights)
    counter = CounterTable(table) if method != "grammar_hit" else None

    def remaining():
        seconds = deadline - monotonic()
        if seconds <= 0:
            raise CompilationLimit("whole adaptive query deadline; no sample certified")
        return seconds

    for depth in (*depths, None):
        wall, cpu = perf_counter(), process_time()
        tracked = depth is not None and method in ("grammar_hit", "handoff")
        prepared = StackPrepared(
            table,
            weights.canvas,
            max_depth=depth,
            track_overflow=tracked,
            max_edges=max_edges,
            max_cells=max_cells,
            max_terms=max_terms,
            timeout_seconds=remaining(),
        )
        posterior = StackPosterior(prepared, weights, sums=sums)
        upper, used = Fraction(), "full" if depth is None else "zero_lower_mass"
        if posterior.total and depth is not None:
            if tracked:
                frontier = OverflowFrontier(
                    prepared, weights, sums=sums, timeout_seconds=remaining()
                )
                upper, used = frontier.mass, "grammar_hit"
                if method == "handoff" and conditional_error(posterior.mass, upper) > tolerance:
                    upper, _ = frontier.handoff(counter, timeout_seconds=remaining())
                    used = "handoff"
            else:
                upper, _ = counter.tail(
                    weights,
                    depth,
                    mode="closed" if method == "closed" else method,
                    sums=sums,
                    timeout_seconds=remaining(),
                )
                used = method
        delta = conditional_error(posterior.mass, upper) if posterior.total else None
        attempts.append(
            dict(
                depth=depth,
                lower_mass=str(posterior.mass),
                upper_tail=str(upper),
                delta=None if delta is None else str(delta),
                bound=used,
                nodes=prepared.graph_nodes,
                edges=prepared.graph_edges,
                wall=perf_counter() - wall,
                cpu=process_time() - cpu,
            )
        )
        remaining()
        if depth is None or (delta is not None and delta <= tolerance):
            return posterior, dict(
                scope="exact_on_full_language"
                if depth is None
                else "certified_depth_approximation",
                depth=depth,
                delta="0" if depth is None else str(delta),
                upper_tail=str(upper),
                attempts=attempts,
            )
        del posterior, prepared
    raise RuntimeError("adaptive decoder lost full fallback")
