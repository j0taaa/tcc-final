"""Classical two-sided controls, with original-token marginals and explicit costs."""

from fractions import Fraction as F
from math import isqrt, prod

from .ideal_controls import chi_lower
from .mass_aware_controls import controls as mass_controls
from .mass_aware_controls import scalar, sqrt_upper
from .public_audit import integers
from .sampler_overlap import controls as overlap_controls


def controls(plan, first, second, posteriors=None, baseline=None, precision=64):
    if first.state != plan.state or second.state != plan.state:
        raise ValueError("same original support/canvas is required")
    left, right = (plan.evaluate(x) for x in [first, second]) if posteriors is None else posteriors
    if left.inputs != first or right.inputs != second:
        raise ValueError("supplied marginals do not belong to these probability tables")
    if not left.valid_mass or not right.valid_mass:
        return dict(status="ZERO_VALID_MASS_UNDEFINED_TV")
    p, q = integers(first), integers(second)
    a, b = scalar(plan, p), scalar(plan, q)
    mass = (
        mass_controls(plan, first, second, precision)
        if baseline is None
        else baseline["mass_aware"]
    )
    overlap = (
        overlap_controls(plan, first, second, precision)
        if baseline is None
        else baseline["sampler_overlap"]
    )
    upper_bounds = dict(mass=mass["upper"], overlap=overlap["upper"])
    lower_bounds = dict(
        marginal=max(
            (
                sum((abs(x - y) for x, y in zip(row_p, row_q, strict=True)), F()) / 2
                for row_p, row_q in zip(left.marginals, right.marginals, strict=True)
            ),
            default=F(),
        )
    )
    delta = F(1, 1 << precision)
    roots = tuple(
        tuple(isqrt(x * y << (2 * precision)) for x, y in zip(row_p, row_q, strict=True))
        for row_p, row_q in zip(p, q, strict=True)
    )
    squared_lower = F(scalar(plan, roots) ** 2, a * b << (2 * precision * len(p)))
    upper_bounds["hellinger"] = sqrt_upper(1 - squared_lower, precision)
    affinity_upper = sqrt_upper(min(F(1), squared_lower / (1 - delta) ** (2 * len(p))), precision)
    lower_bounds["hellinger"] = max(F(), 1 - affinity_upper)
    if mass["status"] == "EXACT_DISJOINT_LAWS":
        lower_bounds["support"] = F(1)
    else:
        lost_p, lost_q = F(mass["lost_first"]), F(mass["lost_second"])
        lower_bounds["support"] = max(lost_p, lost_q)
        r, t = a * (1 - lost_p), b * (1 - lost_q)
        choices = [
            [F(y, x) for x, y in zip(row_p, row_q, strict=True) if x and y]
            for row_p, row_q in zip(p, q, strict=True)
        ]
        lo = F(r, t) * prod(min(row) for row in choices)
        hi = F(r, t) * prod(max(row) for row in choices)
        assert 0 < lo <= 1 <= hi
        for name, distance in [
            ("chi_QP", max(1 - lo, hi - 1)),
            ("chi_PQ", max(1 - 1 / hi, 1 / lo - 1)),
        ]:
            value = chi_lower(
                F(mass["conditional_bounds"][name]), len(p), mass["sqrt_fraction_bits"]
            )
            conditional = 2 * value * value / distance if distance else F()
            lower_bounds[name] = min(lost_p, lost_q) + min(1 - lost_p, 1 - lost_q) * conditional
    if baseline is not None:
        upper_bounds.update(
            original_hellinger=F(baseline["hellinger_upper"]),
            original_range=F(baseline["range_upper"]),
        )
    assert 0 <= max(lower_bounds.values()) <= min(upper_bounds.values()) <= 1
    return dict(
        status="CERTIFIED_CLASSICAL_INTERVAL",
        lower=max(lower_bounds.values()),
        upper=min(upper_bounds.values()),
        lower_bounds=lower_bounds,
        bounds=upper_bounds,
        interpretation="Classical controls; not a near-relative guarantee or novelty claim",
    )
