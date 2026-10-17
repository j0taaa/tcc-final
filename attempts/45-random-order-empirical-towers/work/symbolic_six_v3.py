"""Exact symbolic checks of V3 identities; optional SymPy, outside core CI."""

import json
from itertools import combinations
from math import prod

import sympy as s


def main():
    z, w, v, x = s.symbols("z w v x")
    s2, s3, s4 = 1 - 2 * z, 1 - 3 * z + 3 * w, 1 - 4 * z + 2 * z * z + 4 * w - 4 * v
    aa = 1 - s2
    bb = aa * aa + s2 - 2 * s3 + s4
    ee, dd = s2 * s2 - s4, s2 - s3
    ff, kk = aa + 2 * s3 + ee, bb + aa
    di, ei = bb + aa * x * (2 - x), ee - 2 * dd * x + aa * x * x
    c0 = 10 * (z * z - w) + 4 * v
    rr = 2 * z + 6 * z * z + 2 * w + 4 * v
    ell = x * (1 - x - z)
    slack = di + 2 * ei - 4 * z * ell - rr * x
    identities = {
        "positive_diagonal": di + 2 * ei - (c0 + 12 * w * x + 2 * z * x * x),
        "completed_square_remainder": kk + 2 * ff - (1 + s2) ** 2 - rr,
        "direct_slack": slack - ((1 - x) * c0 - 6 * z * x * (1 - x) + 8 * z * z * x),
    }
    u, zi, wi, vi = s.symbols("u zi wi vi")
    positive = (
        2 * (1 + u) * x * x * u * u
        + 4 * x * u * u * zi
        + 2 * x * zi * zi
        + (6 + 4 * u) * (zi * zi - u * wi)
        + 4 * u * vi
    )
    replaced = slack.subs({z: x * u + zi, w: x * zi + wi, v: x * wi + vi})
    identities["positive_slack_expansion"] = (replaced - positive).subs(x, 1 - u)
    y = s.symbols("y:6")

    def elementary(k):
        return sum(prod(part) for part in combinations(y, k))

    expansion = sum(a * a * b * b for a, b in combinations(y, 2))
    expansion += sum(a * b * c * (a + b + c) for a, b, c in combinations(y, 3))
    expansion += 2 * sum(prod(part) for part in combinations(y, 4))
    identities["elementary_counting_expansion_six_variables"] = (
        elementary(2) ** 2 - sum(y) * elementary(3) - expansion
    )
    lam = s.symbols("lam")
    dgeneral = bb + lam * ee + (2 * aa - 2 * lam * dd) * x + aa * (lam - 1) * x * x
    rgeneral = kk + lam * (ff - (1 + s2) ** 2 / 2)
    cgeneral = (6 + 2 * lam) * z * z - (2 + 4 * lam) * w + 4 * (lam - 1) * v
    identities["family_diagonal"] = dgeneral - (
        cgeneral + (2 * (2 - lam) * z + 6 * lam * w) * x + 2 * (lam - 1) * z * x * x
    )
    identities["family_rank_remainder"] = rgeneral - (
        2 * z + 6 * z * z + 2 * (lam - 1) * w + 4 * (lam - 1) * v
    )
    minus_slack = (dgeneral - rgeneral * x).subs(lam, -3)
    identities["negative_endpoint_slack"] = minus_slack - (
        (1 - x) * (10 * w - 16 * v) + 2 * z * x * (4 * (1 - x) - 3 * z)
    )
    three_slack = (dgeneral - 6 * z * ell - rgeneral * x).subs(lam, 3)
    positive_three = (
        2 * x * x * u * u
        + (4 + s.Rational(16, 3) * u) * (zi * zi - s.Rational(3, 2) * u * wi)
        + (8 - s.Rational(16, 3) * u) * zi * zi
        + 8 * u * vi
    )
    identities["positive_endpoint_slack"] = (
        three_slack.subs({z: x * u + zi, w: x * zi + wi, v: x * wi + vi}) - positive_three
    ).subs(x, 1 - u)
    stronger = sum(a * a * b * b for a, b in combinations(y, 2))
    stronger += s.Rational(1, 2) * sum(a * b * c * (a + b + c) for a, b, c in combinations(y, 3))
    identities["stronger_elementary_counting_expansion"] = (
        elementary(2) ** 2 - s.Rational(3, 2) * sum(y) * elementary(3) - stronger
    )
    for name, expression in identities.items():
        assert s.expand(expression) == 0, (name, s.factor(expression))
    print(
        json.dumps(
            {
                "status": "PASS_EXACT_SYMBOLIC_IDENTITIES",
                "identities": list(identities),
                "sympy": s.__version__,
                "scope": "algebra, not general-budget safety or software proof",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
