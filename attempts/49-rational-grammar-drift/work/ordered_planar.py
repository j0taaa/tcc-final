"""Classical ordered zonotope geometry and monotone exact outside sweeps."""

import heapq
from functools import cmp_to_key

from .calibrated_endpoint import grid_for
from .optimal_planar import det, segment_distance
from .optimal_planar_fast import right_chain, rotate


def canonical(a):
    return a if a[0] > 0 or (a[0] == 0 and a[1] > 0) else (-a[0], -a[1])


def validate(rows):
    rows = [tuple(a) for a in rows]
    if any(len(a) != 2 or any(not isinstance(x, int) for x in a) for a in rows):
        raise ValueError("integer pairs required")
    return rows


def append(rows, a):
    if a == (0, 0):
        return
    if rows and det(rows[-1], a) == 0:
        rows[-1] = rows[-1][0] + a[0], rows[-1][1] + a[1]
    else:
        rows.append(a)


def ordered(rows):
    values = [canonical(a) for a in validate(rows) if a != (0, 0)]
    values.sort(key=cmp_to_key(lambda a, b: -((det(a, b) > 0) - (det(a, b) < 0))))
    result = []
    for a in values:
        append(result, a)
    return result


def geometry(rows):
    point = -sum(a[0] for a in rows), -sum(a[1] for a in rows)
    half = []
    for x, y in rows:
        half.append(point)
        point = point[0] + 2 * x, point[1] + 2 * y
    polygon = half + [(-x, -y) for x, y in half]
    u = max(polygon, key=lambda a: a[0] * a[0] + a[1] * a[1])
    v = max(polygon, key=lambda a: abs(det(u, a)))
    if det(u, v) < 0:
        v = -v[0], -v[1]
    volume = det(u, v)
    assert volume > 0
    mapped = [(v[1] * x - v[0] * y, -u[1] * x + u[0] * y) for x, y in polygon]
    assert all(abs(x) <= 2 * volume and abs(y) <= volume for x, y in mapped)
    return polygon, mapped, volume


def sweep(polygon, chain, grid, volume):
    pointer = 0
    for j in range(-4 * grid, 4 * grid):
        point = 4 * grid * volume, j * volume
        best = segment_distance(point, polygon[chain[pointer]], polygon[chain[pointer + 1]])
        while pointer + 2 < len(chain):
            candidate = segment_distance(
                point, polygon[chain[pointer + 1]], polygon[chain[pointer + 2]]
            )
            if candidate[0] * best[1] > best[0] * candidate[1]:
                break
            pointer += 1
            best = candidate
        yield point, (chain[pointer], chain[pointer + 1])


def compress_ordered(rows, grid):
    if not isinstance(grid, int) or grid < 1:
        raise ValueError("positive integer grid required")
    if len(rows) <= grid or len(rows) <= 1:
        return rows
    polygon, mapped, volume = geometry(rows)
    scaled = [(grid * x, grid * y) for x, y in mapped]
    chosen = [False] * len(polygon)
    half = len(polygon) // 2
    for side in range(4):
        turned = [rotate(a, side) for a in scaled]
        chain = right_chain(turned)
        for _, edge in sweep(turned, chain, grid, volume):
            for i in edge:
                chosen[i] = chosen[(i + half) % len(polygon)] = True
    reduced = [a for i, a in enumerate(polygon) if chosen[i]]
    size = len(reduced) // 2
    assert size >= 2 and len(reduced) == 2 * size
    assert all(reduced[i + size] == (-reduced[i][0], -reduced[i][1]) for i in range(size))
    result = []
    for i in range(size):
        delta = reduced[i + 1][0] - reduced[i][0], reduced[i + 1][1] - reduced[i][1]
        assert delta[0] % 2 == delta[1] % 2 == 0
        result.append(canonical((delta[0] // 2, delta[1] // 2)))
    pivot = 0
    for i in range(1, len(result)):
        if det(result[i], result[pivot]) < 0:
            pivot = i
    result = result[pivot:] + result[:pivot]
    assert all(det(a, b) > 0 for a, b in zip(result, result[1:]))
    assert len(result) <= 64 * grid
    return result if len(result) < len(rows) else rows


def compress(rows, grid):
    return compress_ordered(ordered(rows), grid)


def image(core, diagonal):
    a, b = diagonal
    for x, y in core:
        value = a * x, b * y
        if value != (0, 0):
            yield canonical(value)


class Item:
    __slots__ = ["row", "stream"]

    def __init__(self, row, stream):
        self.row, self.stream = row, stream

    def __lt__(self, other):
        value = det(self.row, other.row)
        return value > 0 or (value == 0 and self.stream < other.stream)


def compress_images(core, diagonals, grid):
    core, diagonals = validate(core), validate(diagonals)
    if any(a != canonical(a) for a in core) or any(det(a, b) < 0 for a, b in zip(core, core[1:])):
        raise ValueError("core must have canonical angular order")
    if any(a < 0 or b < 0 for a, b in diagonals):
        raise ValueError("original diagonal weights must be nonnegative")
    streams = [iter(image(core, row)) for row in diagonals]
    heap = []
    for i, stream in enumerate(streams):
        value = next(stream, None)
        if value is not None:
            heap.append(Item(value, i))
    heapq.heapify(heap)
    rows = []
    while heap:
        item = heapq.heappop(heap)
        append(rows, item.row)
        value = next(streams[item.stream], None)
        if value is not None:
            heapq.heappush(heap, Item(value, item.stream))
    return compress_ordered(rows, grid)


__all__ = ["compress", "compress_images", "grid_for"]
