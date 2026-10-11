"""Competent compact empirical-Fréchet control: same optimal class law."""

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def repair(
    first_class: bool,
    second: T,
    draw: Callable[[], T],
    project: Callable[[T], bool],
    randbelow: Callable[[int], int],
    *,
    budget: int,
) -> tuple[T, int]:
    if type(first_class) is not bool or type(budget) is not int or budget < 2:
        raise ValueError("binary class and integer total draw budget>=2 required")
    counts, others, representatives = [0, 0], [0, 0], {}
    counts[first_class] = 1
    for i in range(budget - 1):
        value = second if i == 0 else draw()
        cls = project(value)
        if type(cls) is not bool:
            raise ValueError("projection must return bool")
        counts[cls] += 1
        others[cls] += 1
        if others[cls] == 1 or randbelow(others[cls]) == 0:
            representatives[cls] = value
    flip = randbelow(counts[first_class]) < min(counts)
    return representatives[not first_class if flip else first_class], budget - 2
