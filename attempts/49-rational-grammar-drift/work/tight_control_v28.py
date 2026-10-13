"""Classical moment lower controls using charged grammar-restricted ranges."""

from fractions import Fraction as F

from .ideal_controls import chi_lower
from .mass_aware_controls import controls as mass_controls
from .mass_aware_controls import scalar
from .public_audit import integers
from .two_sided_controls import controls as previous


def controls(plan, first, second, posteriors=None, baseline=None, precision=64):
    result = previous(plan, first, second, posteriors, baseline, precision)
    if result["status"] != "CERTIFIED_CLASSICAL_INTERVAL":
        return result
    mass = (
        mass_controls(plan, first, second, precision)
        if baseline is None
        else baseline["mass_aware"]
    )
    if mass["status"] == "EXACT_DISJOINT_LAWS":
        return result
    p, q = integers(first), integers(second)
    ranges = [None] * len(plan.terms)
    for node in plan.order:
        choices = []
        for term in plan.terms[node]:
            if term.choice is not None:
                position, index = term.choice
                x, y = p[position][index], q[position][index]
                if x and y:
                    ratio = F(y, x)
                    choices.append((ratio, ratio))
            elif term.children:
                left, right = (ranges[c] for c in term.children)
                if left is not None and right is not None:
                    choices.append((left[0] * right[0], left[1] * right[1]))
            else:
                choices.append((F(1), F(1)))
        if choices:
            ranges[node] = min(x for x, _ in choices), max(y for _, y in choices)
    a, b = 1 - F(mass["lost_first"]), 1 - F(mass["lost_second"])
    # Integer per-position multipliers differ between heads; use integer masses.
    scale = F(scalar(plan, p), scalar(plan, q)) * a / b
    lo, hi = (scale * x for x in ranges[plan.root])
    assert 0 < lo <= 1 <= hi
    for name, distance in [
        ("chi_QP", max(1 - lo, hi - 1)),
        ("chi_PQ", max(1 - 1 / hi, 1 / lo - 1)),
    ]:
        v = chi_lower(F(mass["conditional_bounds"][name]), len(p), precision)
        lower = min(1 - a, 1 - b) + min(a, b) * (2 * v * v / distance if distance else F())
        assert lower >= result["lower_bounds"][name]
        result["lower_bounds"]["grammar_" + name] = lower
    result["lower"] = max(result["lower_bounds"].values())
    assert result["lower"] <= result["upper"]
    result["common_likelihood_range"] = [lo, hi]
    return result
