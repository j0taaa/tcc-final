"""Moment normalizer and rational rejection plan; no outer or RNG sampler."""

from fractions import Fraction as F
from math import comb, isqrt

from residual import check, jets


def falling(n, j):
    value = 1
    for i in range(j):
        value *= n - i
    return value


def polynomial(t):
    return F(9, 20) + F(21, 20) * t * t + t**4 / 12


class Proposal:
    def __init__(self, m, k, h):
        check(m, k, h)
        self.m, self.k, self.h = m, k, F(h)
        self.left, self.right = max(0, k - 3 * m), min(m, k)
        self.root, self.x = isqrt(m), F(k, 4 * m)
        factorial = [F(falling(m, j) * falling(k, j), falling(4 * m, j)) for j in range(5)]
        self.raw_moments = (
            F(1),
            factorial[1],
            factorial[1] + factorial[2],
            factorial[1] + 3 * factorial[2] + factorial[3],
            factorial[1] + 7 * factorial[2] + 6 * factorial[3] + factorial[4],
        )
        mean = F(k, 4)
        second = self.raw_moments[2] - mean**2
        fourth = sum((comb(4, j) * (-mean) ** (4 - j) * self.raw_moments[j] for j in range(5)), F())
        self.total = F(9, 20) + F(21, 20) * second / m + fourth / (12 * m * m)
        self.mass = self.h * self.total / (m * self.root)
        self.term_bound = self.h / (21 * m * self.root)
        self.increment_weight = 7 * self.h / (4 * m * self.root)
        self.term_probability = 2 * self.term_bound / self.increment_weight
        self.residual_probability = 2 * self.mass / self.increment_weight
        self.fair_probability = 1 - self.term_probability - self.residual_probability

    def point_polynomial(self, i):
        return polynomial((F(i) - F(self.k, 4)) / self.root)

    def point_weight(self, i):
        if not self.left <= i <= self.right:
            return F()
        return F(comb(self.m, i) * comb(3 * self.m, self.k - i), comb(4 * self.m, self.k)) * (
            self.point_polynomial(i)
        )

    def ratio(self, i):
        return F(
            (self.m - i) * (self.k - i),
            (i + 1) * (3 * self.m - self.k + i + 1),
        ) * (self.point_polynomial(i + 1) / self.point_polynomial(i))

    def envelope(self, i):
        return self.h * self.point_polynomial(i) / (self.m * self.root)

    def term_coin(self, function):
        _, _, old_second = jets(function, self.m, self.x)
        _, _, new_second = jets(function, 4 * self.m, self.x)
        term = self.x * (1 - self.x) * (old_second - new_second) / (2 * (4 * self.m - 1))
        return F(1, 2) + term / (2 * self.term_bound)

    def residual_coin(self, function, i):
        if not self.left <= i <= self.right:
            raise ValueError("Point outside hypergeometric support")
        f0, slope, second = jets(function, self.m, self.x)
        y, z = F(i, self.m), F(i, self.m) - self.x
        fy, _, second_y = jets(function, self.m, y)
        remainder = fy - f0 - slope * z - second * z * z / 2
        residual = -remainder + y * (1 - y) * (second_y - second) / (2 * (self.m - 1))
        return F(1, 2) + residual / (2 * self.envelope(i)), residual


class RejectionPlan:
    """Classical mode/level-set geometric envelope, without sampling RNG."""

    def __init__(self, proposal):
        self.proposal = proposal
        self.mode_ratio_queries = self.cutoff_weight_queries = 0
        lo, hi = proposal.left, proposal.right
        while lo < hi:
            mid = (lo + hi) // 2
            self.mode_ratio_queries += 1
            if proposal.ratio(mid) >= 1:
                lo = mid + 1
            else:
                hi = mid
        self.mode = lo
        self.mode_weight = proposal.point_weight(lo)
        self.cutoff_weight_queries += 1
        self.cutoffs = []
        for sign in (-1, 1):
            distance = 1
            while True:
                self.cutoff_weight_queries += 1
                if proposal.point_weight(lo + sign * distance) <= self.mode_weight / 2:
                    break
                distance *= 2
            self.cutoffs.append(distance)
        self.left, self.right = self.cutoffs
        self.relative_mass = 2 * self.left + 2 * self.right - 1
        self.expected_attempts = self.mode_weight * self.relative_mass / proposal.total

    def relative_height(self, i):
        offset = i - self.mode
        if -self.left < offset < self.right:
            return F(1)
        distance, cutoff = (-offset, self.left) if offset < 0 else (offset, self.right)
        return F(1, 2) * (1 - F(1, 2 * cutoff)) ** (distance - cutoff)
