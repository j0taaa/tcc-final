"""Exact classical sorted-prefix absolute-projection queries."""

from fractions import Fraction
from functools import cmp_to_key

from .optimal_planar import det


class NormIndex:
    def __init__(self, rows):
        rows = [
            a if a[0] > 0 or (a[0] == 0 and a[1] > 0) else (-a[0], -a[1])
            for a in rows
            if a != (0, 0)
        ]
        self.rows = sorted(rows, key=cmp_to_key(lambda a, b: -((det(a, b) > 0) - (det(a, b) < 0))))
        self.prefix = [(0, 0)]
        for x, y in self.rows:
            a, b = self.prefix[-1]
            self.prefix.append((a + x, b + y))

    def at(self, w):
        x, y = w
        if x < 0 or (x == 0 and y < 0):
            x, y = -x, -y
        lo, hi = 0, len(self.rows)
        while lo < hi:
            mid = (lo + hi) // 2
            a, b = self.rows[mid]
            dot = a * x + b * y
            if (dot < 0) if y >= 0 else (dot > 0):
                lo = mid + 1
            else:
                hi = mid
        a, b = self.prefix[lo]
        tx, ty = self.prefix[-1]
        value = (tx - 2 * a) * x + (ty - 2 * b) * y
        return value if y >= 0 else -value


def minimum_ratio(source, candidate):
    left, right = NormIndex(source), NormIndex(candidate)
    best = Fraction(1)
    for w in [(1, 0), (0, 1), *((-b, a) for a, b in [*source, *candidate] if a or b)]:
        before, after = left.at(w), right.at(w)
        if after > before or after < 0:
            raise ValueError("candidate is not a norm underapproximation")
        if before:
            best = min(best, Fraction(after, before))
    return best
