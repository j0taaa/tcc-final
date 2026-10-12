"""Independent ticket transport, finite source products and exact RNG trees."""

import argparse
import json
from collections import defaultdict
from fractions import Fraction as Q
from itertools import product
from math import comb, prod
from pathlib import Path

from .coupling import pair


def transport(counts):
    tickets = [i for i, n in enumerate(counts) for _ in range(2 * n)]
    b = sum(counts)
    j = [[Q(0) for _ in range(3)] for _ in range(3)]
    for t, i in enumerate(tickets):
        j[i][tickets[(t + b) % (2 * b)]] += Q(1, 2 * b)
    return j


def diagonal(p, b):
    return sum(
        Q(2 * r - b, b) * comb(b, r) * p**r * (1 - p) ** (b - r) for r in range(b // 2 + 1, b + 1)
    )


def joint(p, b):
    d = [diagonal(v, b) for v in p]
    return [
        [
            d[i] if i == j else (p[i] + p[j] - p[3 - i - j] - d[i] - d[j] + d[3 - i - j]) / 2
            for j in range(3)
        ]
        for i in range(3)
    ]


def psd(p, b):
    j = joint(p, b)
    w = [p[i] ** 2 - j[i][i] for i in range(3)]
    for i in range(3):
        assert all(v >= 0 for v in j[i]) and sum(j[i]) == p[i] and w[i] >= 0
        for k in range(i):
            cross = p[i] * p[k] - j[i][k]
            assert w[i] * w[k] - cross**2 >= 0
    return j


def original_law(p, labels, b):
    result = [[Q(0) for _ in p] for _ in p]
    for tape in product(range(len(p)), repeat=b):
        mass = prod(p[v] for v in tape)
        counts = [sum(labels[v] == i for v in tape) for i in range(3)]
        anchor = labels[tape[0]]
        row = transport(counts)[anchor]
        for c in range(3):
            eligible = [v for v in tape[1:] if labels[v] == c]
            if row[c]:
                assert eligible
                weight = mass * row[c] / Q(counts[anchor], b) / len(eligible)
                for v in eligible:
                    result[tape[0]][v] += weight
    return result


class Choice(Exception):
    def __init__(self, size):
        self.size = size


def sampler_law(labels):
    states = [dict(position=i, label=c, bytes=b"alias") for i, c in enumerate(labels)]
    result = defaultdict(Q)

    def visit(digits, weight):
        cursor = 0

        class RNG:
            def randrange(self, n):
                nonlocal cursor
                if cursor == len(digits):
                    raise Choice(n)
                digit = digits[cursor]
                cursor += 1
                assert 0 <= digit < n
                return digit

        iterator = iter(states)
        try:
            a, b = pair(iterator.__next__, lambda z: z["label"], len(labels), RNG())
        except Choice as choice:
            for digit in range(choice.size):
                visit([*digits, digit], weight / choice.size)
            return
        assert a is states[0] and b is states[b["position"]] and b["position"] > 0
        assert next(iterator, None) is None
        result[b["position"]] += weight

    visit([], Q(1))
    counts = [labels.count(i) for i in range(3)]
    row = transport(counts)[labels[0]]
    for v in range(1, len(labels)):
        c = labels[v]
        multiplicity = counts[c] - int(c == labels[0])
        expected = row[c] / Q(counts[labels[0]], len(labels)) / multiplicity
        assert result[v] == expected
    assert sum(result.values()) == 1


def polynomial(b):
    coefficients = [Q(0)] * (b + 1)
    for r in range(b // 2 + 1, b + 1):
        for k in range(b - r + 1):
            coefficients[r + k] += Q(2 * r - b, b) * comb(b, r) * comb(b - r, k) * (-1) ** k
    return coefficients


def run(output):
    minors, payloads, tapes, polynomials = 0, 0, 0, 0
    for denominator in range(2, 15):
        for a in range(denominator + 1):
            for b in range(denominator - a + 1):
                p = tuple(Q(v, denominator) for v in (a, b, denominator - a - b))
                for budget in range(2, 21):
                    psd(p, budget)
                    minors += 1
    for probabilities, labels, budgets in (
        ((Q(1, 6), Q(1, 3), Q(1, 2)), (0, 1, 2), (2, 3, 4, 5, 6)),
        (tuple(Q(i, 15) for i in range(1, 6)), (0, 0, 1, 2, 2), (2, 3, 4)),
    ):
        class_p = [sum(probabilities[i] for i, c in enumerate(labels) if c == j) for j in range(3)]
        for budget in budgets:
            observed = original_law(probabilities, labels, budget)
            class_j = psd(class_p, budget)
            for i, pi in enumerate(probabilities):
                assert sum(observed[i]) == pi
                assert sum(row[i] for row in observed) == pi
                for k, pk in enumerate(probabilities):
                    expected = (
                        class_j[labels[i]][labels[k]]
                        * pi
                        * pk
                        / class_p[labels[i]]
                        / class_p[labels[k]]
                    )
                    assert observed[i][k] == expected
            payloads += 1
    for budget in range(2, 6):
        for labels in product(range(3), repeat=budget):
            sampler_law(labels)
            tapes += 1
    for b in range(4, 31, 2):
        d = polynomial(b)
        second = [d[k + 2] * (k + 2) * (k + 1) for k in range(b - 1)]
        expected = [Q(0)] * (b - 1)
        m = b // 2
        factor = 2 * (b - 1) * comb(b - 2, m - 1)
        for k in range(m):
            expected[m - 1 + k] = factor * comb(m - 1, k) * (-1) ** k
        assert second == expected and polynomial(b + 1)[:-1] == d and polynomial(b + 1)[-1] == 0
        polynomials += 1
    p, f = (Q(4, 5), Q(1, 10), Q(1, 10)), (0, 1, -1)
    cov = {
        b: sum(joint(p, b)[i][k] * f[i] * f[k] for i in range(3) for k in range(3)) for b in (4, 6)
    }
    assert cov[4] == Q(-17, 2500) and cov[6] == Q(-111, 25000) and cov[6] > cov[4]
    balanced = [
        dict(
            budget=b,
            diagonal=str(diagonal(Q(1, 3), b)),
            between_factor=str((1 + 9 * diagonal(Q(1, 3), b)) / 2),
        )
        for b in (2, 4, 6, 8, 16, 32, 64)
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            dict(
                scope="Exact correction/proof aids; no neural utility or publication priority.",
                rational_matrix_laws=minors,
                original_source_products=payloads,
                exhaustive_sampler_tapes=tapes,
                polynomial_identities=polynomials,
                adverse_C4={str(b): str(v) for b, v in cov.items()},
                balanced=balanced,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
