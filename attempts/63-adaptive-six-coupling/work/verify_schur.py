"""Independent global cost polynomial/long-division Schur audit plus old dual."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from fractions import Fraction as F
from itertools import permutations
from math import comb
from pathlib import Path

from verify_counts import verify


def multiply(left: dict, right: dict) -> dict:
    out: Counter = Counter()
    for a, v in left.items():
        for b, w in right.items():
            out[tuple(a[j] + b[j] for j in range(3))] += v * w
    return {a: v for a, v in out.items() if v}


def sum_power(n: int) -> dict:
    out = {(0, 0, 0): F(1)}
    for _ in range(n):
        out = multiply(out, {(1, 0, 0): F(1), (0, 1, 0): F(1), (0, 0, 1): F(1)})
    return out


def cost_polynomial(cert: dict) -> dict:
    degree = cert["cap"] - 1
    result = Counter(sum_power(degree))
    for variable, raw in cert["primal"].items():
        if not variable.startswith("c:"):
            continue
        k = tuple(map(int, variable.split(":")[1].split(",")))
        h = sum(k)
        ways = comb(h, k[0]) * comb(k[1] + k[2], k[1])
        mass = F(raw) * ways / 2
        if not mass:
            continue
        for order in permutations(range(3)):
            exponent = [0, 0, 0]
            for j, v in enumerate((k[0] + 1, k[1], k[2])):
                exponent[order[j]] = v
            term = multiply({tuple(exponent): mass}, sum_power(degree - h - 1))
            for n, v in term.items():
                result[n] += v
    return dict(result)


def schur_long_division(poly: dict) -> dict:
    residual: Counter = Counter()
    for n, v in poly.items():
        for j in (0, 1):
            if n[j]:
                exponent = tuple(n[i] - int(i == j) for i in range(3))
                residual[exponent] += (-1 if j == 0 else 1) * n[j] * v
    remaining = {n: v for n, v in residual.items() if v}
    quotient: Counter = Counter()
    while remaining:
        n = max(remaining)
        a, b, c = n
        assert a > 0, "derivative difference is not divisible by p0-p1"
        v = remaining.pop(n)
        quotient[a - 1, b, c] += v
        extra = (a - 1, b + 1, c)
        remaining[extra] = remaining.get(extra, F(0)) + v
        if not remaining[extra]:
            remaining.pop(extra)
    return {n: v for n, v in quotient.items() if v}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cert = json.loads(args.certificate.read_text())
    cap = cert["cap"]
    base_raw = (Path(__file__).parent / f"evidence/v10/cap{cap}/certificate.json").read_bytes()
    assert hashlib.sha256(base_raw).hexdigest() == cert["reference_certificate_sha256"]
    base = json.loads(base_raw)
    # Reuse is explicit: recheck the OLD unrestricted exact dual against the
    # NEW primal and re-realize every named tail, never use the numerical dual.
    old = verify({"cap": cap, "primal": cert["primal"], "dual": base["dual"]})
    poly = cost_polynomial(cert)
    for permutation in permutations(range(3)):
        transformed = {tuple(n[j] for j in permutation): v for n, v in poly.items()}
        assert transformed == poly, "cost polynomial is not symmetric"
    q = schur_long_division(poly)
    assert min(q.values(), default=F(0)) >= 0, "negative Schur coefficient"
    uniform = sum(poly.values()) / (3 ** (cap - 1))
    assert uniform == F(base["primal_cost"]) == F(old["exact_dual_bound"])
    result = old | {
        "status": "MINIMAX_VERIFIED",
        "scope": "all-P minimax source work for fixed full ordered target law, three allowed keys",
        "reference_lower_bound_reused": True,
        "global_expected_work_upper": str(uniform),
        "homogeneous_cost_degree": cap - 1,
        "cost_coefficients": {",".join(map(str, n)): str(v) for n, v in poly.items()},
        "schur_coefficients": {",".join(map(str, n)): str(v) for n, v in q.items()},
        "negative_schur_coefficients": 0,
        "new_neural_forwards": 0,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("cost_coefficients", "schur_coefficients")
            }
        )
    )


if __name__ == "__main__":
    main()
