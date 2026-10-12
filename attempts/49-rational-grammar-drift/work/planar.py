"""Exact-integer planar norm compression; an isolated research reference."""

from fractions import Fraction
from functools import cmp_to_key
from itertools import combinations
from math import ceil


def det(a, b):
    return a[0] * b[1] - a[1] * b[0]


def orient(a):
    sign = 1 if a[0] > 0 or (a[0] == 0 and a[1] > 0) else -1
    return sign, (sign * a[0], sign * a[1])


def compress(rows, grid):
    """All real queries: (1-8/grid) F_rows <= F_result <= F_rows.

    The output has at most 2*(grid+1) integer rows. No model or token sampler.
    """
    if not isinstance(grid, int) or grid < 8:
        raise ValueError("grid must be an integer >=8")
    rows = [tuple(a) for a in rows]
    if any(len(a) != 2 or any(not isinstance(x, int) for x in a) for a in rows):
        raise ValueError("rows must contain pairs of integers")
    rows = [a for a in rows if a != (0, 0)]
    if not rows:
        return []
    positive = [orient(a)[1] for a in rows]
    if all(det(positive[0], a) == 0 for a in positive):
        return [tuple(sum(a[k] for a in positive) for k in range(2))]
    ordered = sorted(positive, key=cmp_to_key(lambda a, b: -((det(a, b) > 0) - (det(a, b) < 0))))
    point = tuple(-sum(a[k] for a in ordered) for k in range(2))
    vertices = {point, (-point[0], -point[1])}
    for a in ordered:
        point = point[0] + 2 * a[0], point[1] + 2 * a[1]
        vertices.update([point, (-point[0], -point[1])])
    u, v = max(combinations(sorted(vertices), 2), key=lambda pair: abs(det(*pair)))
    volume = abs(det(u, v))

    def transform(a):
        return v[1] * a[0] - v[0] * a[1], -u[1] * a[0] + u[0] * a[1]

    assert volume > 0
    assert all(sum(abs(transform(a)[k]) for a in rows) == volume for k in range(2))
    buckets = {}
    for a in rows:
        sign, b = orient(transform(a))
        key = b[1] >= 0, grid * b[0] // (abs(b[0]) + abs(b[1]))
        old = buckets.get(key, (0, 0))
        buckets[key] = old[0] + sign * a[0], old[1] + sign * a[1]
    return [buckets[k] for k in sorted(buckets) if buckets[k] != (0, 0)]


def grid_for(epsilon, derivation_size):
    if (
        not isinstance(epsilon, (int, Fraction))
        or not isinstance(derivation_size, int)
        or not 0 < epsilon <= 1
        or derivation_size < 1
    ):
        raise ValueError("epsilon in (0,1] and positive expanded derivation size required")
    return max(8, ceil(Fraction(16 * derivation_size, 1) / epsilon))
