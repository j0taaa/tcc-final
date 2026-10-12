"""Classical angular aggregation with exact a posteriori norm certification."""

from fractions import Fraction

from . import angular_streamed
from .angular_control import grid_for, lower_factor
from .norm_index import minimum_ratio


def compress(rows, grid):
    if not isinstance(grid, int) or grid < 1:
        raise ValueError("grid must be a positive integer")
    rows = angular_streamed._validate(rows)
    rows = [a for a in rows if a != (0, 0)]
    if len(rows) <= min(64, 8 * grid + 4):
        return rows
    trial = 1
    while True:
        candidate = angular_streamed.compress(rows, trial)
        if minimum_ratio(rows, candidate) >= 1 - Fraction(20, grid):
            return candidate
        if trial == grid:
            raise AssertionError("target-grid classical guarantee failed")
        trial = min(grid, 2 * trial)


def compress_product(left, right, grid):
    if len(left) * len(right) > 250_000:
        return angular_streamed.compress_product(left, right, grid)
    return compress([(a * x, b * y) for a, b in left for x, y in right], grid)


__all__ = ["compress", "compress_product", "grid_for", "lower_factor"]
