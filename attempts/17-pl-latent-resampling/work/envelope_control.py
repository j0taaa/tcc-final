"""Certified global scale for the untruncated exponential mixture."""

from fractions import Fraction as Q
from itertools import pairwise

from resampling import deadline, exp_bounds


def lower_scaled_exp(coefficient, exponent, error, end=None):
    if not exponent:
        return coefficient
    if exponent > 0:
        lower, _ = exp_bounds(exponent, error / coefficient, end)
        return coefficient * lower
    ratio = coefficient / error
    cutoff = max(0, (ratio.numerator // ratio.denominator).bit_length())
    if -exponent >= cutoff:
        return Q()  # coefficient * exp(exponent) <= error
    _, upper = exp_bounds(-exponent, error / coefficient, end)
    return coefficient / upper


def scale_certificate(problem, grid, end=None):
    p = problem
    tangents = [(s, sum((1 / (s + c) for c in p.c), Q())) for s in grid]
    endpoints = list(dict.fromkeys([*grid, p.H]))
    lower = []
    error = Q(1, 16 * len(grid))
    for x in endpoints:
        deadline(end)
        lower.append(
            [lower_scaled_exp(p.f(s) / p.f(x), t * (s - x), error, end) for s, t in tangents]
        )
    bound = min(
        sum((min(a, b) for a, b in zip(left, right, strict=True)), Q())
        for left, right in pairwise(lower)
    )
    ticks = max(512, bound.numerator * 1024 // bound.denominator)
    return Q(1024, ticks), len(endpoints) * len(tangents)
