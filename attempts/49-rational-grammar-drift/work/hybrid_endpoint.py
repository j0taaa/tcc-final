"""Routine angular shortcut, preserving endpoint size/error bounds."""

from . import angular_control, optimal_planar_fast
from .calibrated_endpoint import grid_for


def compress(rows, grid):
    if not isinstance(grid, int) or grid < 1:
        raise ValueError("grid must be a positive integer")
    candidate = angular_control.compress(rows, 320 * grid * grid)
    if len(candidate) <= 64 * grid:
        return candidate
    return optimal_planar_fast.compress(rows, grid)


__all__ = ["grid_for", "compress"]
