"""Tiny oracle reference, not a production decoder or novelty claim."""

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def pair(
    draw: Callable[[], T],
    classify: Callable[[T], bool],
    *,
    barrier: int,
    max_draws: int | None = None,
) -> tuple[T, T, int]:
    """Retain the first draw; deterministic cap returns the original second.

    Classify must be fixed independently of the draws and return a binary
    class. An arbitrary external timeout has no marginal-preserving fallback
    guarantee. This function never consults class probabilities or scores.
    """
    if isinstance(barrier, bool) or not isinstance(barrier, int) or barrier < 2:
        raise ValueError("barrier must be an integer >=2")
    if max_draws is not None and (
        isinstance(max_draws, bool) or not isinstance(max_draws, int) or max_draws < 2
    ):
        raise ValueError("max_draws must be None or an integer >=2")
    first, original_second = draw(), draw()
    level = 1 if classify(first) else barrier - 1
    level += 1 if classify(original_second) else -1
    last, used = original_second, 2
    while 0 < level < barrier:
        if max_draws is not None and used >= max_draws:
            return first, original_second, used
        last = draw()
        used += 1
        level += 1 if classify(last) else -1
    return first, last, used
