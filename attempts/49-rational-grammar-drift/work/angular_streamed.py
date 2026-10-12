"""Classical three-scan angular control with no Cartesian materialization."""

from .angular_control import grid_for


def _compress(factory, grid):
    if not isinstance(grid, int) or grid < 1:
        raise ValueError("grid must be a positive integer")
    xx = xy = yx = yy = 0
    for x, y in factory():
        sx, sy = 1 if x >= 0 else -1, 1 if y >= 0 else -1
        xx += sx * x
        xy += sx * y
        yx += sy * x
        yy += sy * y
    ux, uy = (xx, xy) if xx * xx + xy * xy >= yx * yx + yy * yy else (yx, yy)
    if ux == uy == 0:
        return []
    vx = vy = 0
    for x, y in factory():
        sign = 1 if ux * y - uy * x >= 0 else -1
        vx += sign * x
        vy += sign * y
    volume = ux * vy - uy * vx
    if volume == 0:
        return [(ux, uy)]
    assert volume > 0
    buckets = {}
    for a, b in factory():
        x, y = vy * a - vx * b, -uy * a + ux * b
        if x == y == 0:
            continue
        if abs(x) >= abs(y):
            key = 0, (x > 0), (grid * y) // abs(x)
        else:
            key = 1, (y > 0), (grid * x) // abs(y)
        previous = buckets.get(key, (0, 0))
        buckets[key] = previous[0] + a, previous[1] + b
    result = list(buckets.values())
    assert len(result) <= 8 * grid + 4
    return result


def _validate(rows):
    rows = [tuple(a) for a in rows]
    if any(len(a) != 2 or any(not isinstance(x, int) for x in a) for a in rows):
        raise ValueError("rows must contain pairs of integers")
    return rows


def compress(rows, grid):
    rows = _validate(rows)
    return _compress(lambda: iter(rows), grid)


def compress_product(left, right, grid):
    left, right = _validate(left), _validate(right)
    return _compress(lambda: ((a * x, b * y) for a, b in left for x, y in right), grid)


__all__ = ["compress", "compress_product", "grid_for"]
