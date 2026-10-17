"""Optional exact symbolic identities for V4; no core-CI SymPy dependency."""

import json

import sympy as s


def main():
    x, lam, b1, b2 = s.symbols("x lam b1 b2")
    y, z = 1 - x, x * (1 - x)
    p, b = (x, y), (b1, b2)
    diagonal = [(6 + 2 * lam) * z**2 + 2 * (2 - lam) * z * a + 2 * (lam - 1) * z * a**2 for a in p]
    ell = [a * (1 - a - z) for a in p]
    q = (
        -sum(a * value**2 for a, value in zip(diagonal, b, strict=True))
        + 2 * lam * sum(a * value for a, value in zip(ell, b, strict=True)) ** 2
        + (2 * z + 6 * z**2) * sum(a * value for a, value in zip(p, b, strict=True)) ** 2
    )
    ss, dd, mm = b1 + b2, b1 - b2, x - y
    expected = z**2 * (
        (lam - 5) * ss**2 / 2 + (3 - lam) * mm * ss * dd + ((lam + 3) * mm**2 / 2 - 6) * dd**2
    )
    assert s.expand(q - expected) == 0
    aa, cc, off = (lam - 5) / 2, ((lam + 3) * mm**2 - 12) / 2, (3 - lam) * mm / 2
    assert s.expand(aa * cc - off**2 - ((lam - 6) * mm**2 + 15 - 3 * lam)) == 0
    print(
        json.dumps(
            {
                "status": "PASS_EXACT_SYMBOLIC_IDENTITIES",
                "identities": ["binary_unconstrained_form", "binary_determinant"],
                "sympy": s.__version__,
                "scope": "algebra only; not publication priority or useful application",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
