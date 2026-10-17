"""Numerical proposal plus exact rational primal/dual reconstruction, cap6/K3."""

from __future__ import annotations

import argparse
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

PROFILES = ((6,), (5, 1), (4, 2), (4, 1, 1), (3, 3), (3, 2, 1), (2, 2, 2))


def canonical(tape: tuple[int, ...]) -> tuple[int, ...]:
    seen: list[int] = []
    result = []
    for a in tape:
        if a not in seen:
            seen.append(a)
        result.append(seen.index(a))
    return tuple(result)


def actions(s: tuple[int, ...]) -> list[int]:
    return sorted(set(s[1:]))


def build() -> dict:
    states = [(0,)]
    for h in range(1, 6):
        states += [
            (*s, a) for s in states.copy() if len(s) == h for a in range(min(max(s) + 1, 2) + 1)
        ]
    variables = [(s, a) for s in states for a in actions(s)]
    index = {v: i for i, v in enumerate(variables)}
    names = ["".join(map(str, s)) + ":" + str(a) for s, a in variables]
    ub, eq = [], []
    for s in states:
        coeff = Counter(index[(s[:h], a)] for h in range(1, len(s) + 1) for a in actions(s[:h]))
        tag = ("end:" if len(s) == 6 else "flow:") + "".join(map(str, s))
        (eq if len(s) == 6 else ub).append((tag, dict(coeff), F(1)))

    def output(t: tuple[int, ...], j: int) -> Counter:
        row: Counter = Counter()
        for h in range(1, 7):
            pref = t[:h]
            if j not in pref[1:]:
                continue
            seen = list(dict.fromkeys(pref))
            row[index[(canonical(pref), seen.index(j))]] += 1
        return row

    for n in PROFILES:
        words = tuple(i for i, count in enumerate(n) for _ in range(count))
        tapes = sorted(set(permutations(words)))
        for j, count in enumerate(n):
            marg: Counter = Counter()
            diag: Counter = Counter()
            for t in tapes:
                row = output(t, j)
                marg.update(row)
                if t[0] == j:
                    diag.update(row)
            suffix = ",".join(map(str, n)) + ":" + str(j)
            eq.append(("marg:" + suffix, dict(marg), F(len(tapes) * count, 6)))
            eq.append(("diag:" + suffix, dict(diag), len(tapes) * max(F(count, 3) - 1, F(0))))
    cost = [
        -(6 - len(s)) * F(factorial(3) // factorial(3 - len(set(s))), 3 ** len(s))
        for s, _ in variables
    ]
    return {"states": len(states), "names": names, "ub": ub, "eq": eq, "cost": cost}


def exact_check(problem: dict, x: list[F], y: list[F], z: list[F]) -> dict:
    def dot(row: dict, vector: list[F]) -> F:
        return sum((a * vector[i] for i, a in row.items()), F(0))

    primal = all(a >= 0 for a in x)
    primal &= all(dot(row, x) <= b for _, row, b in problem["ub"])
    primal &= all(dot(row, x) == b for _, row, b in problem["eq"])
    at = [F(0)] * len(x)
    for (_, row, _), multiplier in zip(problem["ub"] + problem["eq"], y + z, strict=True):
        for i, a in row.items():
            at[i] += a * multiplier
    dual = all(a <= 0 for a in y) and all(a <= c for a, c in zip(at, problem["cost"], strict=True))
    pcost = 6 + sum((c * a for c, a in zip(problem["cost"], x, strict=True)), F(0))
    dcost = 6 + sum(
        (b * a for (_, _, b), a in zip(problem["ub"] + problem["eq"], y + z, strict=True)), F(0)
    )
    return {
        "primal_feasible": bool(primal),
        "dual_feasible": dual,
        "primal_cost": str(pcost),
        "dual_cost": str(dcost),
        "duality_gap": str(pcost - dcost),
        "certified": bool(primal and dual and pcost == dcost),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    p = build()

    def dense(rows: list) -> np.ndarray:
        return np.array(
            [[coeff.get(i, 0) for i in range(len(p["names"]))] for _, coeff, _ in rows],
            dtype=np.float64,
        )

    result = linprog(
        np.array([float(c) for c in p["cost"]]),
        A_ub=dense(p["ub"]),
        b_ub=[float(r[2]) for r in p["ub"]],
        A_eq=dense(p["eq"]),
        b_eq=[float(r[2]) for r in p["eq"]],
        bounds=(0, None),
        method="highs-ds",
        options={
            "time_limit": 60,
            "dual_feasibility_tolerance": 1e-9,
            "primal_feasibility_tolerance": 1e-9,
        },
    )
    record = {
        "schema": 1,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "solver_status": int(result.status),
        "solver_message": result.message,
        "states": p["states"],
        "variables": len(p["names"]),
        "inequalities": len(p["ub"]),
        "equalities": len(p["eq"]),
        "reconstruction_max_denominator": 100_000_000,
        "status": "INCONCLUSIVE",
    }
    if result.success:
        raw = [result.x, result.ineqlin.marginals, result.eqlin.marginals]
        x, y, z = [[F(float(a)).limit_denominator(100_000_000) for a in vec] for vec in raw]
        checked = exact_check(p, x, y, z)
        record.update(checked)
        record["status"] = "CERTIFIED" if checked["certified"] else "INCONCLUSIVE"
        record["primal"] = dict(zip(p["names"], map(str, x), strict=True))
        record["dual_ub"] = {r[0]: str(a) for r, a in zip(p["ub"], y, strict=True)}
        record["dual_eq"] = {r[0]: str(a) for r, a in zip(p["eq"], z, strict=True)}
        record["raw_float_solution"] = {
            "primal": raw[0].tolist(),
            "dual_ub": raw[1].tolist(),
            "dual_eq": raw[2].tolist(),
        }
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in record.items()
                if k not in ("primal", "dual_ub", "dual_eq", "raw_float_solution")
            }
        )
    )
    if record["status"] != "CERTIFIED":
        sys.exit(2)


if __name__ == "__main__":
    main()
