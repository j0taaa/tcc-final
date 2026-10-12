"""Classical linear-work integer angular aggregation; not a new TV principle."""

from fractions import Fraction

from .optimal_planar import det


def grid_for(epsilon, size):
    if not isinstance(epsilon, (int, Fraction)) or not 0 < epsilon <= 1:
        raise ValueError("epsilon must be exact and in (0,1]")
    if not isinstance(size, int) or size < 1:
        raise ValueError("positive integer derivation size required")
    value = 20 * size * (1 + Fraction(epsilon)) / Fraction(epsilon)
    return (value.numerator + value.denominator - 1) // value.denominator


def compress(rows, grid):
    """All real w: (1-20/grid)*F_rows(w)<=F_core(w)<=F_rows(w)."""
    if not isinstance(grid, int) or grid < 1:
        raise ValueError("grid must be a positive integer")
    rows = [tuple(a) for a in rows]
    if any(len(a) != 2 or any(not isinstance(x, int) for x in a) for a in rows):
        raise ValueError("rows must contain pairs of integers")
    rows = [a for a in rows if a != (0, 0)]
    if len(rows) <= grid:
        return rows
    if all(det(rows[0], a) == 0 for a in rows):
        positive = [a if a[0] > 0 or (a[0] == 0 and a[1] > 0) else (-a[0], -a[1]) for a in rows]
        return [tuple(sum(a[i] for a in positive) for i in [0, 1])]
    supports = [
        tuple(sum((1 if a[j] >= 0 else -1) * a[i] for a in rows) for i in [0, 1]) for j in [0, 1]
    ]
    u = max(supports, key=lambda a: sum(x * x for x in a))
    v = tuple(sum((1 if det(u, a) >= 0 else -1) * a[i] for a in rows) for i in [0, 1])
    assert det(u, v) > 0
    buckets = {}
    for a in rows:
        x, y = v[1] * a[0] - v[0] * a[1], -u[1] * a[0] + u[0] * a[1]
        if abs(x) >= abs(y):
            key = 0, (x > 0), (grid * y) // abs(x)
        else:
            key = 1, (y > 0), (grid * x) // abs(y)
        previous = buckets.get(key, (0, 0))
        buckets[key] = previous[0] + a[0], previous[1] + a[1]
    result = list(buckets.values())
    assert len(result) <= 8 * grid + 4
    return result
