"""Sparse classical count-flow LP for the fixed three-key ordered pair law."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from fractions import Fraction as F
from math import factorial
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.sparse import csr_matrix


def counts(cap: int) -> list[tuple[int, int, int]]:
    return [(a, b, h - a - b) for h in range(cap) for a in range(h + 1) for b in range(h - a + 1)]


def name(kind: str, k: tuple[int, ...], j: int | None = None) -> str:
    base = kind + ":" + ",".join(map(str, k))
    return base if j is None else base + ":" + str(j)


def target(k: tuple[int, ...], cap: int) -> list[F]:
    n = (k[0] + 1, k[1], k[2])
    d = [max(0, 2 * v - cap) for v in n]
    return [
        F(d[0], n[0]),
        F(n[0] + n[1] - n[2] - d[0] - d[1] + d[2], 2 * n[0]),
        F(n[0] + n[2] - n[1] - d[0] - d[2] + d[1], 2 * n[0]),
    ]


def build(cap: int) -> dict:
    states = counts(cap)
    names = [name("c", k) for k in states if sum(k) < cap - 1]
    names += [name(kind, k, j) for kind in ("s", "a") for k in states for j in range(3) if k[j]]
    index = {v: i for i, v in enumerate(names)}
    rows = [("root", {index[name("c", (0, 0, 0))]: F(1)}, F(1))]

    def add(row: Counter, variable: str, value: F) -> None:
        if variable in index:
            row[index[variable]] += value

    for k in states[1:]:
        h = sum(k)
        parents = []
        for ell in range(3):
            if k[ell]:
                parent = tuple(v - (i == ell) for i, v in enumerate(k))
                parents.append((parent, F(k[ell], h)))
        flow: Counter = Counter()
        add(flow, name("c", k), F(1))
        for j in range(3):
            add(flow, name("s", k, j), F(1))
        for parent, weight in parents:
            add(flow, name("c", parent), -weight)
        rows.append((name("flow", k), dict(flow), F(0)))
        for j in range(3):
            if not k[j]:
                continue
            row: Counter = Counter()
            add(row, name("a", k, j), F(1))
            add(row, name("s", k, j), F(-1))
            for parent, weight in parents:
                add(row, name("a", parent, j), -weight)
            rows.append((name("acc", k, j), dict(row), F(0)))
        if h == cap - 1:
            q = target(k, cap)
            assert sum(q) == 1 and min(q) >= 0
            for j in range(3):
                if k[j]:
                    rows.append((name("end", k, j), {index[name("a", k, j)]: F(1)}, q[j]))
                else:
                    assert q[j] == 0
    cost = [F(0)] * len(names)
    for k in states:
        h = sum(k)
        if h < cap - 1:
            m = factorial(h)
            for v in k:
                m //= factorial(v)
            cost[index[name("c", k)]] = F(m, 3**h)
    return {"states": states, "names": names, "rows": rows, "cost": cost}


def exact(problem: dict, x: list[F], dual: list[F]) -> dict:
    primal = all(v >= 0 for v in x) and all(
        sum((v * x[i] for i, v in row.items()), F(0)) == rhs for _, row, rhs in problem["rows"]
    )
    reduced = [F(0)] * len(x)
    for (_, row, _), v in zip(problem["rows"], dual, strict=True):
        for i, a in row.items():
            reduced[i] += v * a
    feasible_dual = all(v <= c for v, c in zip(reduced, problem["cost"], strict=True))
    primal_cost = 1 + sum((v * c for v, c in zip(x, problem["cost"], strict=True)), F(0))
    dual_cost = 1 + sum(
        (rhs * v for (_, _, rhs), v in zip(problem["rows"], dual, strict=True)), F(0)
    )
    return {
        "primal_feasible": primal,
        "dual_feasible": feasible_dual,
        "primal_cost": str(primal_cost),
        "dual_cost": str(dual_cost),
        "duality_gap": str(primal_cost - dual_cost),
        "certified": primal and feasible_dual and primal_cost == dual_cost,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cap", type=int, choices=range(4, 12), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    problem = build(args.cap)
    row_indices, col_indices, data = [], [], []
    for i, (_, row, _) in enumerate(problem["rows"]):
        for j, v in row.items():
            row_indices.append(i)
            col_indices.append(j)
            data.append(float(v))
    matrix = csr_matrix(
        (data, (row_indices, col_indices)), shape=(len(problem["rows"]), len(problem["names"]))
    )
    result = linprog(
        np.array([float(c) for c in problem["cost"]]),
        A_eq=matrix,
        b_eq=np.array([float(b) for _, _, b in problem["rows"]]),
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
        "target": "fixed full ordered pair law, conditional first0",
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "states": len(problem["states"]),
        "variables": len(problem["names"]),
        "equalities": len(problem["rows"]),
        "matrix_nonzeros": matrix.nnz,
        "solver_status": int(result.status),
        "solver_message": result.message,
        "round_to_zero_threshold": 1e-10,
        "reconstruction_max_denominator": 100_000_000,
        "status": "INCONCLUSIVE",
    }
    if result.success:
        raw_x, raw_dual = result.x, result.eqlin.marginals

        def rational(v: float) -> F:
            return F(0) if abs(v) < 1e-10 else F(float(v)).limit_denominator(100_000_000)

        x = [rational(v) for v in raw_x]
        dual = [rational(v) for v in raw_dual]
        checked = exact(problem, x, dual)
        record.update(checked)
        record["status"] = "CERTIFIED" if checked["certified"] else "INCONCLUSIVE"
        record["primal"] = dict(zip(problem["names"], map(str, x), strict=True))
        record["dual"] = {
            label: str(v) for (label, _, _), v in zip(problem["rows"], dual, strict=True)
        }
        record["raw_float_solution"] = {"primal": raw_x.tolist(), "dual": raw_dual.tolist()}
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in record.items() if k not in ("primal", "dual", "raw_float_solution")}
        )
    )
    if record["status"] != "CERTIFIED":
        sys.exit(2)


if __name__ == "__main__":
    main()
