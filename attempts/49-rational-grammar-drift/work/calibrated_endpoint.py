"""V8 endpoint compressor with the full permitted per-gate error budget."""

from fractions import Fraction
from math import isqrt

from .angular_control import grid_for as validate
from .optimal_planar_fast import compress


def grid_for(epsilon, size):
    validate(epsilon, size)
    value = size * (1 + Fraction(epsilon)) / (16 * Fraction(epsilon))
    grid = max(1, isqrt(value.numerator // value.denominator))
    return grid + (grid * grid * value.denominator < value.numerator)


def lower_factor(grid):
    return 1 - Fraction(1, 16 * grid * grid)


__all__ = ["compress", "grid_for", "lower_factor"]
