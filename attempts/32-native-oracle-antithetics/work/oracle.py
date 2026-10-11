"""Bounded native-law coupling; no probabilities, normalizer or ranking edits."""

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def repair(first_class: bool, second: T, draw: Callable[[], T], project: Callable[[T], bool]):
    """Retain second unless a stationary two-draw class transition succeeds.

    first_class is observed on the unchanged first native draw. draw MUST be
    a fresh independent sample from exactly the same frozen law as second.
    project is deterministic and fixed before any draws. Returns payload,
    auxiliary draw count. A whole ranking payload, not just its winner.
    """
    if type(first_class) is not bool:
        raise ValueError("binary class required")
    second_class = project(second)
    if type(second_class) is not bool:
        raise ValueError("projection must return bool")
    if second_class != first_class:
        return second, 0
    proposed = draw()
    proposed_class = project(proposed)
    if type(proposed_class) is not bool:
        raise ValueError("projection must return bool")
    if proposed_class == first_class:
        return second, 1
    test_class = project(draw())
    if type(test_class) is not bool:
        raise ValueError("projection must return bool")
    return (proposed if test_class == proposed_class else second), 2
