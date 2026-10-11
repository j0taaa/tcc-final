"""Exact collision repair; classical independent MH on the collision law.

Providers must describe unchanged P and Q on the same original event space.
This reference has no grammar compiler or claim of a new MH principle.
"""

from fractions import Fraction


def _weight(value):
    if type(value) not in (int, Fraction) or value < 0:
        raise ValueError("weight provider must return a nonnegative exact rational")
    return Fraction(value)


def repair_pair(first, second, draw_p, weight_q, rng):
    """Retain first literally; replace second only in an equality collision.

    draw_p is an independent original P draw. weight_q is proportional to Q
    by ONE unchanged constant, including zero outside Q's support. Equality
    must distinguish original events, not just their rendered bytes.
    """
    if first != second:
        return first, second
    old_weight = _weight(weight_q(first))
    if not old_weight:
        raise ValueError("collision has zero Q weight; providers are incompatible")
    proposed = draw_p()
    new_weight = _weight(weight_q(proposed))
    if new_weight >= old_weight:
        return first, proposed
    if not new_weight:
        return first, second
    ratio = new_weight / old_weight
    accept = rng.randrange(ratio.denominator) < ratio.numerator
    return first, proposed if accept else second


def coupled_pair(draw_p, draw_q, weight_q, rng):
    """Two original independent draws and at most one extra P proposal."""
    return repair_pair(draw_p(), draw_q(), draw_p, weight_q, rng)
