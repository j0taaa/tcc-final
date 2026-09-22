"""Lossless ordering of sums of finite non-negative IEEE-754 input weights.

Public weights remain floats. Fractions are an internal comparison key, not a
new objective: they denote exactly the real value of each supplied binary float.
Keep original terms across token aggregation and epsilon normalization so that
rounding an intermediate public weight cannot change the winning path.
"""

from collections.abc import Iterable
from fractions import Fraction
from math import fsum, isfinite


def exact_sum(terms: Iterable[float]) -> Fraction:
    return sum((Fraction(term) for term in terms), Fraction())


def weight_terms(weight: float, terms: Iterable[float]) -> tuple[float, ...]:
    result = tuple(terms) or (weight,)
    if any(isinstance(term, bool) or not isinstance(term, (int, float)) for term in result):
        raise TypeError("weight_terms must contain real numbers")
    if any(not isfinite(term) or term < 0 for term in result):
        raise ValueError("weight_terms must be finite and non-negative")
    if fsum(result) != weight:
        raise ValueError("weight must equal the rounded sum of weight_terms")
    return tuple(float(term) for term in result)
