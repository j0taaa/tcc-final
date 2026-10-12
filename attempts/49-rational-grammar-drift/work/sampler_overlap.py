"""Classical sampler coupling; downward dyadic evaluation gives a TV upper."""

from fractions import Fraction as F

from .public_audit import integers


def overlap_upper(plan, first, second, precision=64):
    if precision < 1:
        raise ValueError("positive dyadic precision required")
    scale = 1 << precision
    left, right, common = ([0] * len(plan.terms) for _ in range(3))
    for node in plan.order:
        pairs = [
            (plan.term_mass(term, first, left), plan.term_mass(term, second, right))
            for term in plan.terms[node]
        ]
        a, b = sum(x for x, _ in pairs), sum(y for _, y in pairs)
        left[node], right[node] = a, b
        if not a or not b:
            continue
        weighted = 0
        for term, (x, y) in zip(plan.terms[node], pairs, strict=True):
            product = scale
            for child in term.children:
                product = product * common[child] // scale
            weighted += min(x * b, y * a) * product
        common[node] = weighted // (a * b)
        assert 0 <= common[node] <= scale
    if plan.root is None or not left[plan.root] or not right[plan.root]:
        return None, 0, 0
    return F(scale - common[plan.root], scale), left[plan.root], right[plan.root]


def controls(plan, first, second, precision=64):
    if first.state != plan.state or second.state != plan.state:
        raise ValueError("same original canvas/support required")
    p, q = integers(first), integers(second)
    full, a, b = overlap_upper(plan, p, q, precision)
    if full is None:
        return dict(status="ZERO_VALID_MASS_UNDEFINED_TV")
    rp = tuple(
        tuple(x if x and y else 0 for x, y in zip(left, right, strict=True))
        for left, right in zip(p, q, strict=True)
    )
    rq = tuple(
        tuple(y if x and y else 0 for x, y in zip(left, right, strict=True))
        for left, right in zip(p, q, strict=True)
    )
    conditional, r, t = overlap_upper(plan, rp, rq, precision)
    if conditional is None:
        assert full == 1
        return dict(status="EXACT_DISJOINT_LAWS", upper=F(1), bounds=dict(full=full))
    upper = max(1 - F(r, a), 1 - F(t, b)) + min(F(r, a), F(t, b)) * conditional
    assert 0 <= upper <= 1
    return dict(
        status="CERTIFIED_SAMPLER_COUPLING",
        upper=min(full, upper),
        bounds=dict(full=full, common_support=upper),
        conditional_upper=conditional,
        dyadic_fraction_bits=precision,
    )
