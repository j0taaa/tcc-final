"""Streaming native-law pair coupling; finite budget, no probability input."""

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def repair(
    first_class: bool,
    second: T,
    draw: Callable[[], T],
    project: Callable[[T], bool],
    *,
    budget: int,
) -> tuple[T, int]:
    if type(first_class) is not bool or type(budget) is not int or budget < 2:
        raise ValueError("binary class and integer total draw budget>=2 required")
    second_class = project(second)
    if type(second_class) is not bool:
        raise ValueError("projection must return bool")
    if second_class != first_class:
        return second, 0
    remaining, level, calls = budget - 2, 2, 0
    while remaining >= level:
        proposed = draw()
        projected = project(proposed)
        if type(projected) is not bool:
            raise ValueError("projection must return bool")
        calls += 1
        remaining -= 1
        level += 1 if projected == first_class else -1
        if level == 0:
            return proposed, calls
    return second, calls
