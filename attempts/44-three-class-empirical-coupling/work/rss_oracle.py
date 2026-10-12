"""Independent four-draw RSS law and exact conditional comparison, not data."""

import argparse
import json
from fractions import Fraction as Q
from itertools import permutations, product
from math import prod
from pathlib import Path

from .oracle import diagonal, joint


def rss_law(p, order):
    rank = {c: i for i, c in enumerate(order)}
    result = [[Q(0) for _ in p] for _ in p]
    for a, b, c, d in product(range(3), repeat=4):
        mass = prod(p[i] for i in (a, b, c, d)) / 2
        low = min((a, b), key=rank.__getitem__)
        high = max((c, d), key=rank.__getitem__)
        result[low][high] += mass
        result[high][low] += mass
    return result


def quadratic(j, f):
    return sum(j[i][k] * f[i] * f[k] for i in range(3) for k in range(3))


def run(output):
    p = (Q(1, 3),) * 3
    between = [[int(i == j) * p[i] - p[i] * p[j] for j in range(3)] for i in range(3)]
    checks = 0
    for order in permutations(range(3)):
        rss = rss_law(p, order)
        assert all(sum(row) == Q(1, 3) for row in rss)
        for budget in range(6, 65):
            candidate = joint(p, budget)
            excess = [
                [rss[i][j] - candidate[i][j] - Q(2, 81) * between[i][j] for j in range(3)]
                for i in range(3)
            ]
            assert all(sum(row) == 0 for row in excess)
            for i in range(3):
                assert excess[i][i] >= 0
                for j in range(i):
                    assert excess[i][i] * excess[j][j] - excess[i][j] ** 2 >= 0
            checks += 1
    thresholds = []
    bound = Q(8, 27)
    for budget in (6, 8, 16, 32, 64):
        delta = (1 - 9 * diagonal(Q(1, 3), budget)) / 2
        for cost in (Q(1), Q(21, 20), Q(11, 10)):
            thresholds.append(
                dict(
                    budget=budget,
                    full_cost_ratio=str(cost),
                    strict_advantage_beta=str((cost - 1) / (cost * delta - bound)),
                    twenty_percent_beta=str((cost - Q(4, 5)) / (cost * delta - Q(4, 5) * bound)),
                )
            )
    p, f = (Q(4, 5), Q(1, 10), Q(1, 10)), (0, 1, -1)
    adverse = {b: quadratic(joint(p, b), f) for b in (4, 6)}
    best_rss = min(quadratic(rss_law(p, order), f) for order in permutations(range(3)))
    assert best_rss == Q(-83, 7500) < adverse[4] < adverse[6]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            dict(
                scope="Exact theoretical comparison at true balance; not model observations.",
                balanced_budget_order_checks=checks,
                best_nonuniform_rss_cross_covariance=str(best_rss),
                nonuniform_C4_C6={str(k): str(v) for k, v in adverse.items()},
                cost_conditions=thresholds,
                limitations="Continuous RSS, CV and mass-aware inverses are not bounded here.",
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
