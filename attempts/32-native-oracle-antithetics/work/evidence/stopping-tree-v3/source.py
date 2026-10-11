"""Opt-in adversarial tree optimization; numerical solver is NOT a proof."""

import argparse
import hashlib
import json
import math
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


def walk_expectation(n, p):
    r = (n - 2) // 2

    @lru_cache(None)
    def wait(w, same, opposite):
        if same >= r or opposite > same + 1:
            return F()
        return 1 + w * wait(w, same + 1, opposite) + (1 - w) * wait(w, same, opposite + 1)

    return 2 + p**2 * wait(p, 0, 0) + (1 - p) ** 2 * wait(1 - p, 0, 0)


def solve(n, p):
    words = [format(x, f"0{k}b") for k in range(1, n + 1) for x in range(2**k)]
    variables, costs = {}, []
    for word in words:
        mass = p ** word.count("1") * (1 - p) ** word.count("0")
        for out in ("0", "1", "continue") if len(word) < n else ("0", "1"):
            variables[word, out] = len(costs)
            costs.append(F() if out == "continue" else len(word) * mass)
    entries, rhs = [], []

    def row(items, target):
        entries.extend((len(rhs), j, value) for j, value in items)
        rhs.append(F(target))

    for word in words:
        terms = [(variables[word, out], 1) for out in ("0", "1")]
        if len(word) < n:
            terms.append((variables[word, "continue"], 1))
        if len(word) > 1:
            terms.append((variables[word[:-1], "continue"], -1))
        row(terms, 1 if len(word) == 1 else 0)
    # Padding a stopped prefix to n makes all class-law constraints independent
    # of p: full Bernstein coefficients, not just one numerical marginal.
    for first in ("0", "1"):
        for m in range(n + 1):
            terms = []
            for word in words:
                tail_ones = m - word.count("1")
                if word[0] == first and 0 <= tail_ones <= n - len(word):
                    terms.append((variables[word, "1"], math.comb(n - len(word), tail_ones)))
            target = F(math.comb(n, m) * (min(m, n - m) if first == "0" else max(0, 2 * m - n)), n)
            row(terms, target)
    rows, cols, vals = zip(*entries, strict=True)
    matrix = coo_matrix((vals, (rows, cols)), shape=(len(rhs), len(costs))).tocsr()
    result = linprog(
        np.array([float(x) for x in costs]),
        A_eq=matrix,
        b_eq=np.array([float(x) for x in rhs]),
        bounds=(0, None),
        method="highs",
    )
    expected = walk_expectation(n, p)
    record = dict(n=n, p=str(p), walk_cost=str(expected), solver_status=int(result.status))
    if not result.success:
        record["message"] = result.message
        return record
    record.update(
        lp_cost=float(result.fun),
        numerical_gap=float(expected) - float(result.fun),
        equality_residual=float(np.max(np.abs(matrix @ result.x - np.array(rhs, dtype=float)))),
        variables=len(costs),
        constraints=len(rhs),
    )
    # An exact rational dual certificate can certify only THIS finite tree/p.
    # Failure to reconstruct is kept explicitly; no floating tolerance credit.
    dual = [F(float(x)).limit_denominator(10**12) for x in result.eqlin.marginals]
    dual_cols = [F() for _ in costs]
    for i, j, value in entries:
        dual_cols[j] += value * dual[i]
    dual_value = sum(b * y for b, y in zip(rhs, dual, strict=True))
    feasible = all(y <= c for y, c in zip(dual_cols, costs, strict=True))
    record.update(
        exact_dual_feasible=feasible,
        exact_dual_value=str(dual_value),
        exact_dual_matches_walk=feasible and dual_value == expected,
    )
    if feasible and dual_value == expected:
        record["dual"] = [str(x) for x in dual]
    if record["numerical_gap"] > 1e-7:
        record["numerical_counterexample"] = True
        record["positive_primal"] = {
            f"{word}:{out}": float(result.x[j])
            for (word, out), j in variables.items()
            if result.x[j] > 1e-9
        }
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-budget", type=int, default=10)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refuse to overwrite evidence")
    rows = [
        solve(n, p)
        for n in range(2, args.max_budget + 1)
        for p in (F(0), F(1, 10), F(1, 3), F(1, 2), F(9, 10), F(1))
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            dict(
                scope="ALL finite stopping trees, finite tested n/p only; no neural benchmark",
                scipy=scipy.__version__,
                numpy=np.__version__,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                rows=rows,
            ),
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            dict(
                cases=len(rows),
                numerical_counterexamples=sum(
                    r.get("numerical_counterexample", False) for r in rows
                ),
                exact_dual_certificates=sum(r.get("exact_dual_matches_walk", False) for r in rows),
                errors=sum(r["solver_status"] != 0 for r in rows),
            )
        )
    )


if __name__ == "__main__":
    main()
