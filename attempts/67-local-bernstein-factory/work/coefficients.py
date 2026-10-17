"""Small exact coefficient reference; not a complete sampler or fast bit engine."""

from dataclasses import dataclass
from fractions import Fraction as F
from functools import cached_property
from math import comb, isqrt


def degree_check(n, k):
    if not isinstance(n, int) or n < 16 or not isinstance(k, int) or not 0 <= k <= n:
        raise ValueError("Invalid degree/index")
    root = isqrt(n)
    if root * root != n or root & (root - 1):
        raise ValueError("Degree must be a power of four")


def stencil(n, k):
    degree_check(n, k)
    x, h = F(k, n), F(1, isqrt(n))
    step = h if x <= 1 - 2 * h else -h
    return x, x + step, x + 2 * step


@dataclass(frozen=True)
class Coefficients:
    function: object
    epsilon: F
    curvature: F
    lipschitz: F

    def __post_init__(self):
        if not 0 < self.epsilon <= F(1, 2) or min(self.curvature, self.lipschitz) < 0:
            raise ValueError("Invalid supplied bounds")

    @property
    def c(self):
        return self.curvature + self.lipschitz

    @property
    def initial_degree(self):
        n = 16
        while self.curvature / (8 * n) + 9 * self.c / (8 * n * isqrt(n)) > self.epsilon:
            n *= 4
        return n

    def coefficient(self, n, k):
        args = stencil(n, k)
        f0, f1, f2 = (F(self.function(x)) for x in args)
        dd = n * (f0 - 2 * f1 + f2)
        a = f0 - args[0] * (1 - args[0]) * dd / (2 * n)
        delta = self.c / (n * isqrt(n))
        return a - delta, a + delta, dd

    @cached_property
    def rows(self):
        return {}

    def row(self, n):
        if n not in self.rows:
            self.rows[n] = tuple(self.coefficient(n, k)[:2] for k in range(n + 1))
        return self.rows[n]

    def elevated_lower(self, old, k):
        n = 4 * old
        degree_check(n, k)
        row = self.row(old)
        total = sum(
            (
                comb(old, i) * comb(3 * old, k - i) * row[i][0]
                for i in range(max(0, k - 3 * old), min(old, k) + 1)
            ),
            F(),
        )
        return total / comb(n, k)

    def mixture_coefficient(self, n, k):
        degree_check(n, k)
        base = self.initial_degree
        if not self.c:
            raise ValueError("Affine input uses its direct classical factory")
        low = self.coefficient(n, k)[0]
        if n == base:
            weight = 1 - 2 * self.c / (n * isqrt(n))
            return low / weight, weight
        if n < 4 * base:
            raise ValueError("Degree precedes mixture levels")
        old = n // 4
        weight = 2 * self.c * (F(1, old * isqrt(old)) - F(1, n * isqrt(n)))
        return (low - self.elevated_lower(old, k)) / weight, weight
