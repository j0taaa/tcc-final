"""Small rational fixed-reference utilities. Classical; no model/trainer."""

from fractions import Fraction as F
from itertools import combinations
from math import comb


def gamma(size):
    if type(size) is not int or not 1 <= size <= 64:
        raise ValueError("positive bounded reference count required")
    return min(F(1, 2), F(1, size - 1)) if size > 1 else F()


def validate(target, fixed):
    if not target or len(target) > 8 or any(type(v) is not int or v < 0 for v in target):
        raise ValueError("small original-ID target required; grammar validity is caller's duty")
    if any(
        type(i) is not int or not 0 <= i < len(target) or target[i] != v for i, v in fixed.items()
    ):
        raise ValueError("fixed original IDs must agree with the supervised target")


def reference_actions(target, fixed):
    validate(target, fixed)
    active = [i for i in range(len(target)) if i not in fixed]
    m = len(active)
    if not m:
        return {}
    if m == 1:
        i = active[0]
        return {((i, target[i]),): F(1)}
    g = gamma(m)
    return {
        tuple((i, target[i]) for i in subset): F(k, m) * g ** (k - 1) * (1 - g) ** (m - k)
        for k in range(1, m + 1)
        for subset in combinations(active, k)
    }


def reference_paths(target, fixed=None):
    """Enumerate reference paths only for the tiny independent oracle."""
    fixed = dict(fixed or {})
    validate(target, fixed)
    if len(target) > 4:
        raise ValueError("path enumeration is capped at four target IDs")
    if len(fixed) == len(target):
        return {(): F(1)}
    result = {}
    for action, probability in reference_actions(target, fixed).items():
        following = {**fixed, **dict(action)}
        for suffix, weight in reference_paths(target, following).items():
            result[(action, *suffix)] = probability * weight
    return result


def count_flow(length):
    """Visit probabilities including terminal0 and expected nonabsorbing steps."""
    gamma(length)
    visits = [F() for _ in range(length + 1)]
    visits[length] = F(1)
    for m in range(length, 0, -1):
        if m == 1:
            visits[0] += visits[m]
            continue
        g = gamma(m)
        for k in range(1, m + 1):
            probability = F(comb(m - 1, k - 1)) * g ** (k - 1) * (1 - g) ** (m - k)
            visits[m - k] += visits[m] * probability
    return tuple(visits), sum(visits[1:], F())


def reference_state_measure(target):
    """Direct nonabsorbing occupancy law, enumerated only for small targets."""
    validate(target, {})
    length = len(target)
    visits, expected = count_flow(length)
    result = {}
    for m in range(1, length + 1):
        probability = visits[m] / expected / comb(length, length - m)
        for subset in combinations(range(length), length - m):
            result[tuple((i, target[i]) for i in subset)] = probability
    return expected, result
