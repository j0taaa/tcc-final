"""Integer endpoint cores from classical planar convex approximation."""

from fractions import Fraction
from functools import cmp_to_key
from math import isqrt


def det(a, b):
    return a[0] * b[1] - a[1] * b[0]


def hull(points):
    """Exact monotone chain; CCW boundary without redundant collinear points."""
    points = sorted(set(points))
    if len(points) <= 1:
        return points
    chains = []
    for sequence in [points, reversed(points)]:
        chain = []
        for p in sequence:
            while len(chain) >= 2:
                a, b = chain[-2:]
                if det((b[0] - a[0], b[1] - a[1]), (p[0] - b[0], p[1] - b[1])) > 0:
                    break
                chain.pop()
            chain.append(p)
        chains.append(chain[:-1])
    return chains[0] + chains[1]


def segment_distance(point, a, b):
    """Squared distance as an unreduced integer numerator/denominator."""
    e = b[0] - a[0], b[1] - a[1]
    t = point[0] - a[0], point[1] - a[1]
    length = sum(x * x for x in e)
    dot = sum(x * y for x, y in zip(e, t, strict=True))
    if dot <= 0:
        return sum(x * x for x in t), 1
    if dot >= length:
        return sum((point[i] - b[i]) ** 2 for i in [0, 1]), 1
    return sum(x * x for x in t) * length - dot * dot, length


def compress(rows, grid):
    """Every real w: (1-1/(16*grid**2))*F_rows(w) <= F_core(w) <= F_rows(w).

    At most64*grid integer rows; no rational projection is output.
    """
    if not isinstance(grid, int) or grid < 1:
        raise ValueError("grid must be a positive integer")
    rows = [tuple(a) for a in rows]
    if any(len(a) != 2 or any(not isinstance(x, int) for x in a) for a in rows):
        raise ValueError("rows must contain pairs of integers")
    rows = [a for a in rows if a != (0, 0)]
    if not rows:
        return []
    positive = [a if a[0] > 0 or (a[0] == 0 and a[1] > 0) else (-a[0], -a[1]) for a in rows]
    if all(det(positive[0], a) == 0 for a in positive):
        return [tuple(sum(a[i] for a in positive) for i in [0, 1])]
    ordered = sorted(positive, key=cmp_to_key(lambda a, b: -((det(a, b) > 0) - (det(a, b) < 0))))
    point = tuple(-sum(a[i] for a in ordered) for i in [0, 1])
    points = [point]
    for a in ordered:
        point = point[0] + 2 * a[0], point[1] + 2 * a[1]
        points.extend([point, (-point[0], -point[1])])
    polygon = hull(points)
    u = max(polygon, key=lambda a: sum(x * x for x in a))
    v = max(polygon, key=lambda a: abs(det(u, a)))
    if det(u, v) < 0:
        v = -v[0], -v[1]
    volume = det(u, v)
    assert volume > 0
    mapped = [(v[1] * a[0] - v[0] * a[1], -u[1] * a[0] + u[0] * a[1]) for a in polygon]
    assert all(abs(x) <= 2 * volume and abs(y) <= volume for x, y in mapped)
    scaled = [(grid * x, grid * y) for x, y in mapped]
    selected = set()
    for side in range(4):
        for j in range(-4 * grid, 4 * grid):
            point = [
                (4 * grid * volume, j * volume),
                (j * volume, 4 * grid * volume),
                (-4 * grid * volume, j * volume),
                (j * volume, -4 * grid * volume),
            ][side]
            best_distance = None
            best_edge = 0
            for i, a in enumerate(scaled):
                distance = segment_distance(point, a, scaled[(i + 1) % len(scaled)])
                if (
                    best_distance is None
                    or distance[0] * best_distance[1] < best_distance[0] * distance[1]
                ):
                    best_distance, best_edge = distance, i
            for i in [best_edge, (best_edge + 1) % len(polygon)]:
                a = polygon[i]
                selected.update([a, (-a[0], -a[1])])
    reduced = hull(selected)
    half = len(reduced) // 2
    assert half > 1 and len(reduced) == 2 * half
    assert all(reduced[i + half] == (-reduced[i][0], -reduced[i][1]) for i in range(half))
    result = []
    for i in range(half):
        delta = tuple(reduced[i + 1][j] - reduced[i][j] for j in [0, 1])
        assert all(x % 2 == 0 for x in delta)
        result.append(tuple(x // 2 for x in delta))
    assert len(result) <= 64 * grid
    return result if len(result) < len(rows) else rows


def grid_for(epsilon, derivation_size):
    if (
        not isinstance(epsilon, (int, Fraction))
        or not isinstance(derivation_size, int)
        or not 0 < epsilon <= 1
        or derivation_size < 1
    ):
        raise ValueError("epsilon in (0,1] and positive expanded derivation size required")
    value = Fraction(derivation_size, 1) / epsilon
    bound = (value.numerator + value.denominator - 1) // value.denominator
    root = isqrt(bound)
    return root if root * root == bound else root + 1
