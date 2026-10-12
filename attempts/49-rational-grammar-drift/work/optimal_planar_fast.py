"""Exact logarithmic outside-polygon queries; classical convex geometry."""

from functools import cmp_to_key
from itertools import pairwise

from .optimal_planar import det, grid_for, hull, segment_distance


def rotate(a, side):
    return [(a[0], a[1]), (a[1], -a[0]), (-a[0], -a[1]), (-a[1], a[0])][side]


def right_chain(polygon):
    start = min(range(len(polygon)), key=lambda i: (polygon[i][1], -polygon[i][0]))
    end = max(range(len(polygon)), key=lambda i: (polygon[i][1], polygon[i][0]))
    indices = [start]
    while indices[-1] != end:
        indices.append((indices[-1] + 1) % len(polygon))
        assert len(indices) <= len(polygon)
    assert len(indices) >= 2
    assert all(polygon[a][1] < polygon[b][1] for a, b in pairwise(indices))
    return indices


def nearest_edge(polygon, chain, point):
    """point.x exceeds every polygon.x; return original indices of a nearest edge."""

    def distance(index):
        a = polygon[chain[index]]
        return (point[0] - a[0]) ** 2 + (point[1] - a[1]) ** 2

    lo, hi = 0, len(chain) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if distance(mid) <= distance(mid + 1):
            hi = mid
        else:
            lo = mid + 1
    best, edge = None, None
    for i in [lo - 1, lo]:
        if 0 <= i < len(chain) - 1:
            a, b = chain[i : i + 2]
            value = segment_distance(point, polygon[a], polygon[b])
            if best is None or value[0] * best[1] < best[0] * value[1]:
                best, edge = value, (a, b)
    assert edge is not None
    return edge


def geometry(rows):
    """Integer polygon/constant-factor normalized coordinates, rank2 inputs only."""
    positive = [a if a[0] > 0 or (a[0] == 0 and a[1] > 0) else (-a[0], -a[1]) for a in rows]
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
    return polygon, mapped, volume


def compress(rows, grid):
    """SAME64k-row/1-1/(16k²) guarantee; O(m*log(m+2)) exact operations."""
    if not isinstance(grid, int) or grid < 1:
        raise ValueError("grid must be a positive integer")
    rows = [tuple(a) for a in rows]
    if any(len(a) != 2 or any(not isinstance(x, int) for x in a) for a in rows):
        raise ValueError("rows must contain pairs of integers")
    rows = [a for a in rows if a != (0, 0)]
    if not rows:
        return []
    if len(rows) <= grid:
        return rows
    if all(det(rows[0], a) == 0 for a in rows):
        positive = [a if a[0] > 0 or (a[0] == 0 and a[1] > 0) else (-a[0], -a[1]) for a in rows]
        return [tuple(sum(a[i] for a in positive) for i in [0, 1])]
    polygon, mapped, volume = geometry(rows)
    scaled = [(grid * x, grid * y) for x, y in mapped]
    selected = set()
    for side in range(4):
        turned = [rotate(a, side) for a in scaled]
        chain = right_chain(turned)
        for j in range(-4 * grid, 4 * grid):
            point = [
                (4 * grid * volume, j * volume),
                (j * volume, 4 * grid * volume),
                (-4 * grid * volume, j * volume),
                (j * volume, -4 * grid * volume),
            ][side]
            for index in nearest_edge(turned, chain, rotate(point, side)):
                a = polygon[index]
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


__all__ = ["compress", "grid_for"]
