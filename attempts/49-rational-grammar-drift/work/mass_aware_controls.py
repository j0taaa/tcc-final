"""Classical support coupling with certified scalar bounds; not a new method."""

from fractions import Fraction as F
from math import isqrt

from .public_audit import integers


def scalar(plan, values):
    inside = [0] * len(plan.terms)
    for node in plan.order:
        inside[node] = sum(plan.term_mass(term, values, inside) for term in plan.terms[node])
    return 0 if plan.root is None else inside[plan.root]


def sqrt_upper(value, precision=64):
    if value < 0:
        raise ValueError("nonnegative exact squared bound required")
    scaled = value * (1 << (2 * precision))
    rounded = isqrt(scaled.numerator // scaled.denominator)
    if F(rounded * rounded) < scaled:
        rounded += 1
    return F(rounded, 1 << precision)


def controls(plan, first, second, precision=64):
    if first.state != plan.state or second.state != plan.state:
        raise ValueError("same original canvas/support required")
    p, q = integers(first), integers(second)
    a, b = scalar(plan, p), scalar(plan, q)
    if not a or not b:
        return dict(status="ZERO_VALID_MASS_UNDEFINED_TV")
    rp = tuple(
        tuple(x if x and y else 0 for x, y in zip(l, r, strict=True))
        for l, r in zip(p, q, strict=True)
    )
    rq = tuple(
        tuple(y if x and y else 0 for x, y in zip(l, r, strict=True))
        for l, r in zip(p, q, strict=True)
    )
    r, t = scalar(plan, rp), scalar(plan, rq)
    assert bool(r) == bool(t)
    if not r:
        return dict(status="EXACT_DISJOINT_LAWS", lower=F(1), upper=F(1), bounds={})
    lost_p, lost_q = 1 - F(r, a), 1 - F(t, b)
    common = min(F(r, a), F(t, b))
    lower = max(lost_p, lost_q)
    roots = tuple(
        tuple(isqrt(x * y << (2 * precision)) for x, y in zip(l, r, strict=True))
        for l, r in zip(rp, rq, strict=True)
    )
    affinity_squared_lower = F(scalar(plan, roots) ** 2, r * t << (2 * precision * len(p)))
    assert 0 <= affinity_squared_lower <= 1
    conditional = dict(hellinger=sqrt_upper(1 - affinity_squared_lower, precision))
    for name, numerator, denominator, old_mass, new_mass in [
        ("chi_QP", rq, rp, r, t),
        ("chi_PQ", rp, rq, t, r),
    ]:
        uppers = tuple(
            tuple(
                ((x * x << precision) + y - 1) // y if y else 0 for x, y in zip(l, rr, strict=True)
            )
            for l, rr in zip(numerator, denominator, strict=True)
        )
        chi_upper = (
            F(old_mass * scalar(plan, uppers), new_mass * new_mass << (precision * len(p))) - 1
        )
        assert chi_upper >= 0
        conditional[name] = min(F(1), sqrt_upper(chi_upper, precision) / 2)
    ranges = [None] * len(plan.terms)
    for node in plan.order:
        terms = plan.terms[node]
        choices = []
        for term in terms:
            if term.choice is not None:
                position, index = term.choice
                x, y = rp[position][index], rq[position][index]
                if x and y:
                    ratio = F(y, x)
                    choices.append((ratio, ratio))
            elif term.children:
                x, y = (ranges[c] for c in term.children)
                if x is not None and y is not None:
                    choices.append((x[0] * y[0], x[1] * y[1]))
            else:
                choices.append((F(1), F(1)))
        ranges[node] = (
            None if not choices else (min(v[0] for v in choices), max(v[1] for v in choices))
        )
    lo, hi = (F(r, t) * v for v in ranges[plan.root])
    assert lo <= 1 <= hi
    conditional["range"] = F() if lo == hi else (1 - lo) * (hi - 1) / (hi - lo)
    bounds = {name: lower + common * value for name, value in conditional.items()}
    return dict(
        status="CERTIFIED_SCALAR_BOUNDS",
        lower=lower,
        upper=min(bounds.values()),
        bounds=bounds,
        conditional_bounds=conditional,
        lost_first=lost_p,
        lost_second=lost_q,
        sqrt_fraction_bits=precision,
    )
