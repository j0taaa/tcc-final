"""Rational proof reference only; caller must supply the same terminal kernel."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from fractions import Fraction as F


def normalized(raw: Sequence) -> tuple[F, ...]:
    values = tuple(map(F, raw))
    if not values or min(values) < 0:
        raise ValueError("A nonempty finite nonnegative vector is required")
    total = sum(values)
    return tuple(v / total for v in values) if total else (F(1, len(values)),) * len(values)


def terminal_mean(
    first: Sequence, draw: Callable[[], Sequence | None], budget: int
) -> tuple[tuple[F, ...], int]:
    """Retain normalized first; None helpers are charged noncompleting draws."""
    if not isinstance(budget, int) or budget < 0:
        raise ValueError("The finite helper budget must be a nonnegative integer")
    original = normalized(first)
    total, retained = list(original), 1
    for _ in range(budget):
        raw = draw()
        if raw is not None:
            point = normalized(raw)
            if len(point) != len(total):
                raise ValueError("Every terminal vector must have the same labels")
            total = [a + b for a, b in zip(total, point, strict=True)]
            retained += 1
    return tuple(v / retained for v in total), retained - 1


def rounded_simplex(point: Sequence, digits: int) -> tuple[F, ...]:
    """Largest remainders; returns exact decimal-grid values, not original IDs."""
    point = tuple(map(F, point))
    if not point or min(point) < 0 or sum(point) != 1:
        raise ValueError("A simplex point is required")
    if not isinstance(digits, int) or not 0 <= digits <= 18:
        raise ValueError("Choose a finite decimal precision in [0,18]")
    scale = 10**digits
    integers = [int(v * scale) for v in point]
    remainders = [v * scale - a for v, a in zip(point, integers, strict=True)]
    order = sorted(range(len(point)), key=lambda j: (-remainders[j], j))
    for j in order[: scale - sum(integers)]:
        integers[j] += 1
    return tuple(F(a, scale) for a in integers)
