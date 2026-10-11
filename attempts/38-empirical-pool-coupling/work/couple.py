"""Cap-four, first-retained empirical coupling; no probabilities or model imports."""

from collections.abc import Callable, Hashable
from typing import TypeVar

T = TypeVar("T")


def pair(
    draw: Callable[[], T],
    key: Callable[[T], Hashable],
    randrange: Callable[[int], int],
) -> tuple[T, T, int]:
    """Use 3/4 complete iid draws; independent randrange must be uniform."""
    first, second, third = draw(), draw(), draw()
    a, b, c = key(first), key(second), key(third)
    if b == c:
        return first, second, 3
    if a == b or a == c:
        if randrange(2) == 0:
            return first, third if a == b else second, 3
        return first, draw(), 4
    fourth = draw()
    d = key(fourth)
    if d == a:
        return first, (second, third)[randrange(2)], 4
    if d == b or d == c:
        return first, fourth, 4
    return first, (second, third, fourth)[randrange(3)], 4
