"""Minimal anonymous six-pool population-law feasibility/secondary U3 LP."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from fractions import Fraction as F
from itertools import permutations
from math import prod
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.sparse import csr_matrix


def patterns(length: int) -> list[str]:
    if length == 1:
        return ["0"]
    return [p + str(j) for p in patterns(length - 1) for j in range(max(map(int, p)) + 2)]


def partitions(n: int, maximum: int = 6) -> list[tuple[int, ...]]:
    if not n:
        return [()]
    return [(a, *p) for a in range(min(n, maximum), 0, -1) for p in partitions(n - a, a)]


def canonical(word: tuple[int, ...]) -> tuple[str, dict[int, int]]:
    mapping: dict[int, int] = {}
    result = "".join(str(mapping.setdefault(j, len(mapping))) for j in word)
    return result, mapping


def target(n: tuple[int, ...]) -> list[F]:
    q = [F(0)] * len(n)
    if max(n) >= 3:
        heavy = n.index(max(n))
        if heavy:
            q[heavy] = F(1)
        else:
            q[0] = F(2 * n[0] - 6, n[0])
            for j in range(1, len(n)):
                q[j] = F(n[j], n[0])
    else:
        profile = tuple(sorted(n, reverse=True))
        for j in range(1, len(n)):
            if profile == (2, 2, 2):
                joint = F(1, 6)
            elif profile == (2, 2, 1, 1):
                joint = {(2, 2): F(1, 5), (1, 1): F(1, 30)}.get((n[0], n[j]), F(1, 15))
            elif profile == (2, 1, 1, 1, 1):
                joint = F(1, 12) if 2 in (n[0], n[j]) else F(1, 36)
            else:
                assert profile == (1, 1, 1, 1, 1, 1)
                joint = F(1, 30)
            q[j] = joint * F(6, n[0])
    assert min(q) >= 0 and sum(q) == 1
    return q


def build() -> dict:
    words = [p for n in range(1, 7) for p in patterns(n)]
    names = ["c:" + p for p in words if len(p) < 6]
    names += [
        f"s:{p}:{j}" for p in words for j in range(max(map(int, p)) + 1) if j or p.count("0") > 1
    ]
    index = {tag: i for i, tag in enumerate(names)}
    rows = [("root", {index["c:0"]: F(1)}, F(1))]
    for p in words[1:]:
        row = {index["c:" + p[:-1]]: F(-1)}
        for tag in ["c:" + p] + [f"s:{p}:{j}" for j in range(6)]:
            if tag in index:
                row[index[tag]] = F(1)
        rows.append(("flow:" + p, row, F(0)))
    for first in range(1, 7):
        for rest in partitions(6 - first):
            n = (first, *rest)
            tail = (0,) * (first - 1) + tuple(j for j, v in enumerate(rest, 1) for _ in range(v))
            tapes = sorted(set(permutations(tail)))
            q = target(n)
            for j in range(len(n)):
                row: Counter = Counter()
                for t in tapes:
                    p, mapping = canonical((0, *t))
                    for h in range(2, 7):
                        tag = f"s:{p[:h]}:{mapping[j]}"
                        if tag in index:
                            row[index[tag]] += F(1, len(tapes))
                rows.append(("end:" + ",".join(map(str, n)) + f":{j}", dict(row), q[j]))
    rows.append(("distinct4", {index["c:0123"]: F(1)}, F(0)))
    objective = [F(0)] * len(names)
    for p in words:
        if len(p) < 6:
            k = len(set(p))
            objective[index["c:" + p]] = (
                F(prod(2 - j for j in range(k - 1)), 3 ** (len(p) - 1)) if k <= 3 else F(0)
            )
    return {"words": words, "names": names, "rows": rows, "objective": objective}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    problem = build()
    ii, jj, vv = [], [], []
    for i, (_, row, _) in enumerate(problem["rows"]):
        for j, v in row.items():
            if v:
                ii.append(i)
                jj.append(j)
                vv.append(float(v))
    result = linprog(
        [float(v) for v in problem["objective"]],
        A_eq=csr_matrix((vv, (ii, jj)), shape=(len(problem["rows"]), len(problem["names"]))),
        b_eq=[float(v) for _, _, v in problem["rows"]],
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
        "status": "INCONCLUSIVE",
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "anonymous_prefixes": len(problem["words"]),
        "variables": len(problem["names"]),
        "rows": len(problem["rows"]),
        "solver_status": int(result.status),
        "solver_message": result.message,
        "reconstruction_zero_threshold": 1e-10,
        "reconstruction_max_denominator": 100_000_000,
        "primary_constraint": "Stop on first four distinct keys; hard cap6, fixed matching law",
        "secondary_objective": "U3 expected source calls, not all-P minimax",
    }
    if result.success:

        def rational(v: float) -> F:
            return F(0) if abs(v) < 1e-10 else F(float(v)).limit_denominator(100_000_000)

        x = list(map(rational, result.x))
        dual = list(map(rational, result.eqlin.marginals))
        primal_ok = min(x) >= 0 and all(
            sum((v * x[j] for j, v in row.items()), F(0)) == b for _, row, b in problem["rows"]
        )
        reduced = [F(0)] * len(x)
        for (_, row, _), y in zip(problem["rows"], dual, strict=True):
            for j, v in row.items():
                reduced[j] += y * v
        dual_ok = all(v <= c for v, c in zip(reduced, problem["objective"], strict=True))
        value = 1 + sum((v * c for v, c in zip(x, problem["objective"], strict=True)), F(0))
        bound = 1 + sum((b * y for (_, _, b), y in zip(problem["rows"], dual, strict=True)), F(0))
        record.update(
            status="CERTIFIED" if primal_ok and dual_ok and value == bound else "INCONCLUSIVE",
            primal_feasible=primal_ok,
            dual_feasible=dual_ok,
            secondary_U3_cost=str(value),
            secondary_U3_dual_bound=str(bound),
            secondary_gap=str(value - bound),
            primal=dict(zip(problem["names"], map(str, x), strict=True)),
            dual=dict(zip((tag for tag, _, _ in problem["rows"]), map(str, dual), strict=True)),
            raw_float_solution={
                "primal": result.x.tolist(),
                "dual": result.eqlin.marginals.tolist(),
            },
        )
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
