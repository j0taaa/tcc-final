"""Counterexample search for the prospective blend; numerical results are not proof."""

import argparse
import json
from fractions import Fraction as Q
from pathlib import Path

import numpy as np


def joints(p):
    s2, s3, s4 = (sum(x**k for x in p) for k in (2, 3, 4))
    four, six = [], []
    for x in p:
        r4, r6 = [], []
        for y in p:
            u = (
                1
                + x
                + y
                - s2
                + 2 * (x * x + y * y)
                - s2 * (x + y)
                - 2 * s3
                - (x**3 + y**3)
                - 2 * x * y * (x + y)
                + s2 * s2
                + s2 * x * y
                + s4
                + x * y * (x * x + y * y)
            )
            r4.append(x * y * (1 + x + y - x * y - s2))
            r6.append(x * y * u)
        four.append(r4)
        six.append(r6)
    for i, x in enumerate(p):
        four[i][i] = 2 * x**3 - x**4
        six[i][i] = 5 * x**4 - 6 * x**5 + 2 * x**6
    return four, six


def candidate_gain(p):
    four, six = (np.asarray(j, dtype=float) for j in joints(p))
    edge = 2 * np.outer(p**3, p**3)
    safe = np.diag(edge.sum(axis=1)) - edge
    return ((len(p) - 1) * safe + four - six) / len(p)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    p = [Q(4, 5), Q(1, 10), Q(1, 10)]
    four, six = joints(p)
    f = (0, 1, -1)
    values = [sum(f[i] * j[i][k] * f[k] for i in range(3) for k in range(3)) for j in (four, six)]
    assert values == [-Q(17, 2500), -Q(111, 25000)]
    rng = np.random.default_rng(202610110427)
    cases, worst, obstruction = 0, (0, None), None
    for classes in range(2, 33):
        for concentration in (0.02, 0.1, 0.5, 1, 5, 50):
            for _ in range(100):
                p = rng.dirichlet(np.full(classes, concentration))
                p = p[p > 0]
                gain = candidate_gain(p)
                value = float(np.linalg.eigvalsh(gain)[0])
                cases += 1
                if value < worst[0]:
                    worst = value, p.tolist()
                if value < -1e-10:
                    obstruction = dict(probabilities=p.tolist(), minimum_gain_eigenvalue=value)
                    break
            if obstruction:
                break
        if obstruction:
            break
    result = dict(
        scope="Exploratory numerical obstruction search only; not proof, model or priority",
        seed=202610110427,
        cases=cases,
        worst_minimum_eigenvalue=worst[0],
        worst_probabilities=worst[1],
        obstruction=obstruction,
        exact_c6_c4_cross_covariances=list(map(str, values)),
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print({k: result[k] for k in ("cases", "worst_minimum_eigenvalue", "obstruction")})


if __name__ == "__main__":
    main()
