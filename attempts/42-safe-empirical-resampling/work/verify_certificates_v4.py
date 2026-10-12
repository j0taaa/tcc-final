"""Verify B=6 proof certificates without using either certificate producer."""

import argparse
import importlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from math import prod
from pathlib import Path

import sympy as sp

algebra = importlib.import_module("attempts.42-safe-empirical-resampling.work.six_pool_algebra")
M, x, y = algebra.m, algebra.x, algebra.y
W = algebra.derive()
D = prod(M - j for j in range(6))


def partitions(total, minimum=1):
    if not total:
        yield ()
    for first in range(minimum, total + 1):
        for rest in partitions(total - first, first):
            yield (first, *rest)


def diagonal(t):
    return (
        t * (t - 1) * prod(M - j for j in range(2, 6))
        - t * (t - 1) * (M - t) * (M - t - 1) * (M - 4) * (M - 5)
        - 2 * t * (t - 1) * (t - 2) * prod(M - t - j for j in range(3))
    )


def specified_matrix(population, groups):
    fixed = W.subs({s: sum(t**k for t in population) for k, s in enumerate(algebra.sums[2:], 2)})
    joint = [
        [
            diagonal(ni) if i == j else ni * nj * fixed.subs({x: ni, y: nj})
            for j, nj in enumerate(population)
        ]
        for i, ni in enumerate(population)
    ]
    return sp.Matrix(
        [
            [
                sp.expand(
                    D * sum(population[i] for i in a) * sum(population[j] for j in b)
                    - M**2 * sum(joint[i][j] for i in a for j in b)
                )
                for b in groups
            ]
            for a in groups
        ]
    ), joint


def identities():
    s2, s3, s4 = algebra.s2, algebra.s3, algebra.s4
    a, d = M**2 - s2, 15 * M - 30
    b0 = a**2 + M**2 * s2 - 2 * M * s3 + s4 - d * a
    assert (
        sp.expand(
            diagonal(x)
            - x**2 * W.subs(y, x)
            + x**2 * (b0 + a * x * (2 * M - x))
            + x * (30 * M**2 - 126 * M + 120)
        )
        == 0
    )
    assert (
        sp.expand(
            (b0 + a * M**2) * M**2 - b0 * s2 - a * (2 * M * s3 - s4) - 2 * b0 * a - (s2 + d) * a**2
        )
        == 0
    )


def verify_majority(path):
    data = json.loads(path.read_text())
    expected = {p for r in range(4, 8) for p in partitions(r)}
    assert {tuple(c["minority"]) for c in data["cases"]} == expected
    assert len(data["cases"]) == len(expected) and not data["failures"]
    checked = 0
    u = sp.Symbol("u")
    for case in data["cases"]:
        minority = case["minority"]
        r = sum(minority)
        types = sorted(set(minority))
        groups = [tuple(i for i, t in enumerate(minority) if t == size) for size in types]
        matrix, _ = specified_matrix([*minority, M - r], groups)
        expected_minors = {
            indices
            for k in range(1, len(groups) + 1)
            for indices in itertools.combinations(range(len(groups)), k)
        }
        assert {tuple(c["indices"]) for c in case["minors"]} == expected_minors
        assert len(case["minors"]) == len(expected_minors)
        assert case["threshold"] == 2 * r + 1
        for certificate in case["minors"]:
            indices = certificate["indices"]
            stated = sp.sympify(certificate["factor"], locals={"M": M})
            assert sp.expand(matrix.extract(indices, indices).det() - stated) == 0
            actual = sp.Poly(stated.subs(M, u + 2 * r + 1), u).all_coeffs()
            assert actual == list(map(sp.Integer, certificate["shifted_coefficients"]))
            assert all(c >= 0 for c in actual)
            checked += 1
    return checked


def verify_finite(path):
    data = json.loads(path.read_text())
    expected = set()
    considered = 0
    for m in range(6, 28):
        for n in partitions(m):
            considered += 1
            a = m * m - sum(t * t for t in n)
            b0 = a * a + sum(t * t * (m - t) ** 2 for t in n) - (15 * m - 30) * a
            if b0 < 0 and len(n) > 2 and m != 6 and not (2 * max(n) > m and m - max(n) <= 7):
                expected.add(n)
    assert data["populations_considered"] == considered
    assert {tuple(c["population"]) for c in data["cases"]} == expected
    assert len(data["cases"]) == len(expected)
    for case in data["cases"]:
        n = case["population"]
        types = sorted(Counter(n))
        groups = [tuple(i for i, t in enumerate(n) if t == size) for size in types]
        symbolic, joint = specified_matrix(n, groups)
        matrix = symbolic.subs(M, sum(n))
        assert all(sum(matrix.row(i)) == 0 for i in range(matrix.rows))
        contrasts = [joint[g[0]][g[1]] - joint[g[0]][g[0]] for g in groups if len(g) > 1]
        assert [int(t.subs(M, sum(n))) for t in contrasts] == case["contrasts"]
        assert all(t >= 0 for t in case["contrasts"])
        matrix = matrix[:-1, :-1]
        assert matrix.tolist() == case["scaled_gram"]
        lower = sp.Matrix([[Fraction(t) for t in row] for row in case["lower"]])
        pivots = list(map(Fraction, case["pivots"]))
        assert all(t >= 0 for t in pivots)
        assert lower * sp.diag(*pivots) * lower.T == matrix
    return len(expected), considered


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--majority", type=Path, required=True)
    parser.add_argument("--finite", type=Path, required=True)
    args = parser.parse_args()
    identities()
    minors = verify_majority(args.majority)
    finite, populations = verify_finite(args.finite)
    print(
        dict(
            symbolic_identities=2,
            principal_minors=minors,
            finite_cases=finite,
            finite_population_coverage=populations,
        )
    )
