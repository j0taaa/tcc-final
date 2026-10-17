"""Exact classical moment-law/checkerboard reference, NOT a neural decoder."""

from fractions import Fraction
from itertools import combinations
from math import comb


def count_law(k, q):
    q = Fraction(q)
    if k < 3 or not 0 < q < 1:
        raise ValueError("Require K>=3 and a nondegenerate rational cut")
    mu = k * q
    mean = 1 + (k - 1) * q
    lower = mean.numerator // mean.denominator
    theta = mean - lower
    low_mass = mu * (1 - theta) / lower
    high_mass = mu * theta / (lower + 1)
    return {
        n: mass
        for n, mass in ((0, 1 - low_mass - high_mass), (lower, low_mass), (lower + 1, high_mass))
        if mass
    }


def coarse_law(k, q):
    for n, mass in count_law(k, q).items():
        for subset in combinations(range(k), n):
            yield frozenset(subset), mass / comb(k, n)


def clock_cdf(k, q, thresholds):
    """Polynomial coefficients; conditional independent interval uniforms."""
    q = Fraction(q)
    if len(thresholds) != k or any(not 0 <= u <= 1 for u in thresholds):
        raise ValueError("Require K unit-interval thresholds")
    law = count_law(k, q)
    degree = max(law)
    coefficients = [Fraction(1)] + [Fraction(0)] * degree
    for threshold in thresholds:
        low = min(threshold / (1 - q), 1)
        high = max((threshold - (1 - q)) / q, 0)
        coefficients = [
            coefficients[n] * low + (coefficients[n - 1] * high if n else 0)
            for n in range(degree + 1)
        ]
    return sum(mass * coefficients[n] / comb(k, n) for n, mass in law.items())


def avoidance(k, q, subset_size):
    return sum(
        mass * Fraction(comb(k - subset_size, n), comb(k, n))
        for n, mass in count_law(k, q).items()
        if n <= k - subset_size
    )
