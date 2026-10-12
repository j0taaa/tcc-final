"""Independent exact absorbing-chain law; no simulation or neural benchmark."""

import argparse
import json
from fractions import Fraction as Q
from itertools import product
from pathlib import Path

from .excursion import pair


def solve(a, b):
    """Rational elimination, with multiple right-hand columns."""
    n = len(a)
    rows = [list(x) + list(y) for x, y in zip(a, b, strict=True)]
    for i in range(n):
        k = next(k for k in range(i, n) if rows[k][i])
        rows[i], rows[k] = rows[k], rows[i]
        pivot = rows[i][i]
        rows[i] = [value / pivot for value in rows[i]]
        for k in range(n):
            if k != i:
                factor = rows[k][i]
                rows[k] = [x - factor * y for x, y in zip(rows[k], rows[i], strict=True)]
    return [row[n:] for row in rows]


def chain(probabilities, labels, m):
    """Actual transition rewards of first/last original states and N moments."""
    joint = [[Q(0) for _ in labels] for _ in labels]
    moments = []
    for first, label in enumerate(labels):
        transient = [[Q(0) for _ in range(m - 1)] for _ in range(m - 1)]
        absorb = [[Q(0) for _ in labels] for _ in range(m - 1)]
        for i in range(m - 1):
            for last, p in enumerate(probabilities):
                height = i + 1 + (1 if labels[last] == label else -1)
                if height in (0, m):
                    absorb[i][last] += p
                else:
                    transient[i][height - 1] += p
        matrix = [[Q(i == j) - transient[i][j] for j in range(m - 1)] for i in range(m - 1)]
        law = solve(matrix, [[*row, Q(1)] for row in absorb])
        second_rhs = [
            [1 + 2 * sum(transient[i][j] * law[j][-1] for j in range(m - 1))] for i in range(m - 1)
        ]
        second = solve(matrix, second_rhs)[0][0]
        moments.append((1 + law[0][-1], 1 + 2 * law[0][-1] + second))
        for last in range(len(labels)):
            joint[first][last] = probabilities[first] * law[0][last]
    expected = sum(p * row[0] for p, row in zip(probabilities, moments, strict=True))
    squared = sum(p * row[1] for p, row in zip(probabilities, moments, strict=True))
    return joint, expected, squared


def formula(p, m):
    q = 1 - p
    if p == q:
        return Q(1, 2 * m)
    return (p - q) * p**m / (p**m - q**m)


def check(probabilities, labels, m):
    j, expected, _ = chain(probabilities, labels, m)
    for i, p in enumerate(probabilities):
        assert sum(j[i]) == p
        assert sum(row[i] for row in j) == p
        assert all(j[i][k] == j[k][i] for k in range(len(labels)))
    assert expected == m
    p = sum(prob for prob, label in zip(probabilities, labels, strict=True) if label)
    diagonal = sum(
        j[i][k] for i in range(len(labels)) for k in range(len(labels)) if labels[i] and labels[k]
    )
    assert diagonal == formula(p, m)
    kappa = p * p - diagonal
    assert kappa >= 0
    if 0 < p < 1:
        values = [(Q(i), Q((-1) ** i), Q(i * i)) for i in range(len(labels))]
        mu = [sum(probabilities[i] * values[i][d] for i in range(len(labels))) for d in range(3)]
        means = [
            [
                sum(probabilities[i] * values[i][d] for i in range(len(labels)) if labels[i] == c)
                / (p if c else 1 - p)
                for d in range(3)
            ]
            for c in (0, 1)
        ]
        for d in range(3):
            for e in range(3):
                actual = (
                    sum(
                        j[i][k] * values[i][d] * values[k][e]
                        for i in range(len(labels))
                        for k in range(len(labels))
                    )
                    - mu[d] * mu[e]
                )
                assert actual == -kappa * (means[1][d] - means[0][d]) * (means[1][e] - means[0][e])


def kernel_checks():
    checked = 0
    for m in range(2, 6):
        for tape in product((0, 1), repeat=10):
            height, end = 2 * tape[0] - 1, None
            for index in range(1, len(tape)):
                height += 2 * tape[index] - 1
                if height == 0 or abs(height) == m:
                    end = index
                    break
            if end is None:
                continue
            sources = tuple((i, label) for i, label in enumerate(tape))
            iterator = iter(sources)
            first, last, count = pair(iterator.__next__, lambda z: z[1], m)
            assert first is sources[0] and last is sources[end] and count == end + 1
            reversed_word = tuple(reversed(tape[:count]))
            reverse_height = 2 * reversed_word[0] - 1
            for index in range(1, len(reversed_word)):
                reverse_height += 2 * reversed_word[index] - 1
                assert (reverse_height == 0 or abs(reverse_height) == m) == (index == count - 1)
            checked += 1
    return checked


def run(output):
    checked = 0
    for m in range(2, 11):
        for n in range(2, 5):
            weights = tuple(range(1, n + 1))
            probabilities = tuple(Q(w, sum(weights)) for w in weights)
            for labels in product((0, 1), repeat=n):
                check(probabilities, labels, m)
                checked += 1
        for numerator in range(1, 20):
            p = Q(numerator, 20)
            check((1 - p, p), (0, 1), m)
            checked += 1
    balanced = []
    for m in range(2, 17):
        _, expected, second = chain((Q(1, 2), Q(1, 2)), (0, 1), m)
        repeat = 2 * formula(Q(1, 2), m)
        assert expected * repeat == 1
        assert second - expected**2 == Q(m * (m - 1) * (m - 2), 3)
        balanced.append(
            dict(
                barrier=m,
                queries=str(expected),
                repeat=str(repeat),
                variance_of_queries=str(second - expected**2),
            )
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            dict(
                scope=(
                    "Independent exact chain law and finite implementation checks; "
                    "no neural measurements or priority certificate."
                ),
                rational_chain_laws=checked,
                finite_terminating_tapes=kernel_checks(),
                balanced_frontiers=balanced,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
