"""Certified lower bounds on ideal scalar UPPER bounds, never lower bounds on TV."""

from fractions import Fraction as F
from math import isqrt


def sqrt_lower(value, precision=64):
    if value <= 0:
        return F()
    scaled = value * (1 << (2 * precision))
    return F(isqrt(scaled.numerator // scaled.denominator), 1 << precision)


def hellinger_lower(observed, slots, precision=64):
    delta = F(1, 1 << precision)
    affinity_squared_upper = (1 - max(F(), observed - delta) ** 2) / (1 - delta) ** (2 * slots)
    return sqrt_lower(1 - affinity_squared_upper, precision)


def chi_lower(observed, slots, precision=64):
    delta = F(1, 1 << precision)
    squared_lower = (1 + max(F(), 2 * observed - delta) ** 2) / (1 + delta) ** slots - 1
    return min(F(1), sqrt_lower(squared_lower, precision) / 2)


def controls(baseline, slots, nodes):
    result = dict(
        original_hellinger=hellinger_lower(
            F(baseline["hellinger_upper"]), slots, baseline["sqrt_fraction_bits"]
        ),
        original_range=F(baseline["range_upper"]),
    )
    mass = baseline["mass_aware"]
    if mass["status"] == "EXACT_DISJOINT_LAWS":
        result["common_disjoint"] = F(1)
    else:
        loss = max(F(mass["lost_first"]), F(mass["lost_second"]))
        common = 1 - loss
        precision = mass["sqrt_fraction_bits"]
        for name, observed in mass["conditional_bounds"].items():
            observed = F(observed)
            lower = (
                hellinger_lower(observed, slots, precision)
                if name == "hellinger"
                else chi_lower(observed, slots, precision)
                if name.startswith("chi_")
                else observed
            )
            result["common_" + name] = loss + common * lower
    overlap = baseline["sampler_overlap"]
    result["sampler_overlap"] = (
        F(1)
        if overlap["status"] == "EXACT_DISJOINT_LAWS"
        else max(F(), F(overlap["upper"]) - F(2 * nodes, 1 << overlap["dyadic_fraction_bits"]))
    )
    assert all(0 <= value <= 1 for value in result.values())
    return dict(
        ideal_upper_lower_bound=min(result.values()),
        individual_lower_bounds=result,
        interpretation="Lower bounds on ideal control uppers; NOT lower bounds on TV",
    )
