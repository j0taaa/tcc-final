"""Select a certified exact proposal; every tried depth is part of preparation."""

from fractions import Fraction
from itertools import pairwise
from time import monotonic, perf_counter, process_time

from mwpc_exact.cfg_posterior import CompilationLimit

from .envelope import prepare_envelope
from .posterior import class_weights


def prepare_certified(
    table,
    weights,
    tolerance="1/1000",
    *,
    method="handoff",
    depths=(1, 2, 3, 4, 6, 8, 12),
    timeout_seconds=120,
):
    tolerance = Fraction(tolerance)
    if not 0 < tolerance < 1 or method not in ("handoff", "closed", "grammar_hit"):
        raise ValueError("known envelope and tolerance strictly between0 and1 required")
    if not depths or any(type(d) is not int or d < 0 for d in depths):
        raise ValueError("nonnegative depth grid required")
    if any(a >= b for a, b in pairwise(depths)):
        raise ValueError("strictly increasing depth grid required")
    deadline = monotonic() + timeout_seconds
    sums, attempts = class_weights(table, weights), []
    for depth in (*depths, None):
        seconds = deadline - monotonic()
        if seconds <= 0:
            raise CompilationLimit("whole exact envelope preparation deadline")
        wall, cpu = perf_counter(), process_time()
        envelope = prepare_envelope(
            table,
            weights,
            depth,
            method=method,
            sums=sums,
            max_rejection=tolerance,
            timeout_seconds=seconds,
        )
        attempts.append(
            dict(
                depth=depth,
                lower=str(envelope.lower),
                tail=str(envelope.upper_tail),
                delta=None if envelope.delta is None else str(envelope.delta),
                bound="full" if depth is None else getattr(envelope, "bound", method),
                wall=perf_counter() - wall,
                cpu=process_time() - cpu,
            )
        )
        if monotonic() > deadline:
            raise CompilationLimit("whole exact envelope preparation deadline")
        if depth is None or (envelope.delta is not None and envelope.delta <= tolerance):
            return envelope, dict(
                depth=depth,
                delta=None if envelope.delta is None else str(envelope.delta),
                attempts=attempts,
                sample_scope="exact_on_full_original_product_conditioned_JSON",
            )
    raise RuntimeError("lost exact fallback")
