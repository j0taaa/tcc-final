"""Classical exact sign/range-sum query; no Cartesian product is built."""

from functools import cmp_to_key


def product_norm(first, second, query, counters=None):
    if len(first) < len(second):
        first, second = second, first
    u, v = query
    axis = 0
    rows = []
    for c, d in second:
        if d < 0:
            c, d = -c, -d
        if d:
            rows.append((c, d))
        else:
            axis += abs(c)
    comparisons = 0

    def compare(left, right):
        nonlocal comparisons
        comparisons += 1
        value = left[0] * right[1] - right[0] * left[1]
        return (value > 0) - (value < 0)

    rows.sort(key=cmp_to_key(compare))
    prefix = [(0, 0)]
    for c, d in rows:
        x, y = prefix[-1]
        prefix.append((x + c, y + d))
    cx, dy = prefix[-1]
    result = 0
    searches = 0
    for a, b in first:
        s, t = u * a, v * b
        result += abs(s) * axis
        if not s:
            result += abs(t) * dy
            continue
        lo, hi = 0, len(rows)
        while lo < hi:
            mid = (lo + hi) // 2
            c, d = rows[mid]
            searches += 1
            if (s * c + t * d <= 0) == (s > 0):
                lo = mid + 1
            else:
                hi = mid
        x, y = prefix[lo]
        if s < 0:
            x, y = cx - x, dy - y
        result += s * cx + t * dy - 2 * (s * x + t * y)
    if counters is not None:
        counters.update(
            logical_pairs=len(first) * len(second),
            sorted_rows=len(rows),
            input_rows=len(first) + len(second),
            sort_comparisons=comparisons,
            sign_comparisons=searches,
        )
    return result
