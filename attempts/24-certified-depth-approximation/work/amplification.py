"""Optional original-product change; certifies mass increase, not semantic gain."""

from copy import copy
from fractions import Fraction
from math import prod


def amplify(weights, numerators, lower, upper, *, factor=4):
    """Return (new weights, certificate), or None when no signal is certified."""
    if type(factor) is not int or factor <= 1:
        raise ValueError("integer factor strictly above1 required")
    if type(lower) is not int or type(upper) is not int or lower <= 0 or upper < 0:
        raise ValueError("positive lower and nonnegative upper in common integer units")
    mass = lower + upper
    if mass > prod(weights.denominators) or len(numerators) != len(weights.canvas):
        raise ValueError("certificate differs from original product dimensions/units")
    best = None
    for p, fixed in enumerate(weights.canvas):
        row = numerators[p]
        if fixed is not None:
            if not isinstance(row, dict) or row != {fixed: lower}:
                raise ValueError("fixed marginal lost original ID")
            continue
        if len(row) != weights.vocabulary_size or sum(row) != lower:
            raise ValueError("original marginal dimension/conservation differs")
        denominator = weights.denominators[p]
        for t, numerator in enumerate(row):
            if type(numerator) is not int or not 0 <= numerator <= lower:
                raise ValueError("invalid original marginal numerator")
            weight = weights.at(p, t)
            if not weight and numerator:
                raise ValueError("zero original support has positive marginal")
            if numerator * denominator <= weight * mass:
                continue
            top = denominator * (mass + (factor - 1) * numerator)
            bottom = mass * (denominator + (factor - 1) * weight)
            if best is None or top * best[3] > best[2] * bottom:
                best = p, t, top, bottom, numerator
    if best is None:
        return None
    p, t, top, bottom, numerator = best
    tilted = copy(weights)
    tilted.rows, tilted.denominators = list(weights.rows), list(weights.denominators)
    row = list(weights.rows[p])
    row[t] *= factor
    tilted.rows[p] = tuple(row)
    tilted.denominators[p] = sum(row)
    return tilted, dict(
        position=p,
        token=t,
        factor=factor,
        minimum_mass_ratio=str(Fraction(top, bottom)),
        prior_probability=str(Fraction(weights.at(p, t), weights.denominators[p])),
        full_conditional_lower=str(Fraction(numerator, mass)),
        scope="new_product; does_not_preserve_original_conditional_law_or_semantic_accuracy",
    )
