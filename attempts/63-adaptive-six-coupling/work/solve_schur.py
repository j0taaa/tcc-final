"""Search original optimal faces for classical nonnegative Schur certificates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from fractions import Fraction as F
from itertools import permutations
from math import factorial
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from solve_counts import build, exact, name


def s_power(n: int) -> dict:
    return {
        (a, b, n - a - b): F(factorial(n), factorial(a) * factorial(b) * factorial(n - a - b))
        for a in range(n + 1)
        for b in range(n - a + 1)
    }


def state_polynomial(k: tuple[int, ...], cap: int) -> dict:
    out: Counter = Counter()
    h, degree = sum(k), cap - 1
    weight = F(factorial(h), 2 * factorial(k[0]) * factorial(k[1]) * factorial(k[2]))
    for order in permutations(range(3)):
        powers = [0, 0, 0]
        powers[order[0]], powers[order[1]], powers[order[2]] = k[0] + 1, k[1], k[2]
        for extra, c in s_power(degree - h - 1).items():
            n = tuple(a + b for a, b in zip(powers, extra, strict=True))
            out[n] += weight * c
    return dict(out)


def quotient(poly: dict) -> dict:
    derivative: Counter = Counter()
    for n, c in poly.items():
        for j, sign in ((1, 1), (0, -1)):
            if n[j]:
                exponent = tuple(v - int(i == j) for i, v in enumerate(n))
                derivative[exponent] += sign * n[j] * c
    out: Counter = Counter()
    for (a, b, c), value in derivative.items():
        assert value == -derivative[b, a, c]
        if a > b:
            for r in range(a - b):
                out[a - 1 - r, b + r, c] += value
    return {n: c for n, c in out.items() if c}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cap", type=int, choices=range(4, 12), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base_path = Path(__file__).parent / f"evidence/v10/cap{args.cap}/certificate.json"
    base_raw = base_path.read_bytes()
    base = json.loads(base_raw)
    assert base["certified"]
    problem = build(args.cap)
    indices = {v: i for i, v in enumerate(problem["names"])}
    qrows: dict = {}
    for k in problem["states"]:
        if sum(k) < args.cap - 1:
            for monomial, c in quotient(state_polynomial(k, args.cap)).items():
                qrows.setdefault(monomial, {})[indices[name("c", k)]] = c
    equalities = problem["rows"] + [
        (
            "optimal_face",
            {i: c for i, c in enumerate(problem["cost"]) if c},
            F(base["primal_cost"]) - 1,
        )
    ]

    def sparse(rows: list[dict]) -> csr_matrix:
        ii, jj, vv = [], [], []
        for i, row in enumerate(rows):
            for j, v in row.items():
                if v:
                    ii.append(i)
                    jj.append(j)
                    vv.append(float(v))
        return csr_matrix((vv, (ii, jj)), shape=(len(rows), len(problem["names"])))

    result = linprog(
        np.zeros(len(problem["names"])),
        A_eq=sparse([r for _, r, _ in equalities]),
        b_eq=[float(b) for _, _, b in equalities],
        A_ub=sparse([{i: -c for i, c in row.items()} for row in qrows.values()]),
        b_ub=np.zeros(len(qrows)),
        bounds=(0, None),
        method="highs-ds",
        options={
            "time_limit": 60,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
        },
    )
    record = {
        "schema": 1,
        "cap": args.cap,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "reference_certificate_sha256": hashlib.sha256(base_raw).hexdigest(),
        "reference_optimum": base["primal_cost"],
        "reference_lower_bound_reused": True,
        "states": len(problem["states"]),
        "variables": len(problem["names"]),
        "schur_inequalities": len(qrows),
        "solver_status": int(result.status),
        "solver_message": result.message,
        "status": "INCONCLUSIVE",
        "round_to_zero_threshold": 1e-10,
        "reconstruction_max_denominator": 100_000_000,
    }
    if result.success:
        x = [
            F(0) if abs(v) < 1e-10 else F(float(v)).limit_denominator(100_000_000) for v in result.x
        ]
        old_dual = [F(base["dual"][tag]) for tag, _, _ in problem["rows"]]
        checked = exact(problem, x, old_dual)
        coefficients = {
            n: sum((c * x[i] for i, c in row.items()), F(0)) for n, row in qrows.items()
        }
        nonnegative = all(c >= 0 for c in coefficients.values())
        certified = checked["certified"] and nonnegative
        record.update(checked)
        record["nonnegative_schur_coefficients"] = nonnegative
        record["status"] = "MINIMAX_CERTIFIED" if certified else "INCONCLUSIVE"
        record["primal"] = dict(zip(problem["names"], map(str, x), strict=True))
        record["proposed_schur_coefficients"] = {
            ",".join(map(str, n)): str(c) for n, c in coefficients.items()
        }
        record["raw_float_solution"] = {
            "primal": result.x.tolist(),
            "equality_dual": result.eqlin.marginals.tolist(),
            "inequality_dual": result.ineqlin.marginals.tolist(),
        }
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in record.items()
                if k not in ("primal", "proposed_schur_coefficients", "raw_float_solution")
            }
        )
    )
    if record["status"] != "MINIMAX_CERTIFIED":
        sys.exit(2)


if __name__ == "__main__":
    main()
