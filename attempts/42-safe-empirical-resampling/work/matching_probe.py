"""Exact small matching oracle; no practical compiler or model benchmark."""

import argparse
import json
from collections import Counter
from fractions import Fraction as Q
from functools import cache
from math import comb, prod
from pathlib import Path

import numpy as np


@cache
def completions(r):
    if not any(r):
        return 0, 1
    i = next(i for i, n in enumerate(r) if n)
    best, count = sum(r), 0
    for j, n in enumerate(r):
        choices = n - (i == j)
        if choices <= 0:
            continue
        left = list(r)
        left[i] -= 1
        left[j] -= 1
        bad, ways = completions(tuple(left))
        bad += i == j
        if bad < best:
            best, count = bad, 0
        if bad == best:
            count += choices * ways
    return best, count


@cache
def joint(r):
    b = sum(r)
    bad, count = completions(r)
    result = []
    assert bad == max(0, max(r) - b // 2)
    for i, ni in enumerate(r):
        row = []
        for j, nj in enumerate(r):
            choices = ni * (nj - (i == j))
            if choices <= 0:
                row.append(Q(0))
                continue
            left = list(r)
            left[i] -= 1
            left[j] -= 1
            child_bad, child_count = completions(tuple(left))
            row.append(Q(choices * child_count, b * count) if child_bad + (i == j) == bad else Q(0))
        assert sum(row) == Q(ni, b)
        assert row[i] == max(Q(0), Q(2 * ni, b) - 1)
        result.append(tuple(row))
    return tuple(result)


def partitions(n, minimum=1, limit=6):
    if n == 0:
        yield ()
    elif limit:
        for first in range(minimum, n + 1):
            for tail in partitions(n - first, first, limit - 1):
                yield (first, *tail)


def pools(n, b):
    if len(n) == 1:
        if b <= n[0]:
            yield (b,)
    else:
        for first in range(max(0, b - sum(n[1:])), min(n[0], b) + 1):
            for rest in pools(n[1:], b - first):
                yield (first, *rest)


def source_joint(n, b):
    output = [[Q(0) for _ in n] for _ in n]
    for r in pools(n, b):
        weight = Q(prod(comb(ni, ri) for ni, ri in zip(n, r, strict=True)), comb(sum(n), b))
        matrix = joint(r)
        for i in range(len(n)):
            for j in range(len(n)):
                output[i][j] += weight * matrix[i][j]
    return output


def obstruction(n, b, matrix):
    p = [Q(ni, sum(n)) for ni in n]
    covariance = [[matrix[i][j] - p[i] * p[j] for j in range(len(n))] for i in range(len(n))]
    values, vectors = np.linalg.eigh(np.array(covariance, dtype=float))
    if values[-1] <= 1e-10:
        return None
    f = [Q(float(x)).limit_denominator(100_000) for x in vectors[:, -1]]
    value = sum(f[i] * covariance[i][j] * f[j] for i in range(len(n)) for j in range(len(n)))
    assert value > 0
    return dict(
        population=n,
        budget=b,
        score=list(map(str, f)),
        exact_covariance=str(value),
        joint=[[str(x) for x in row] for row in matrix],
    )


def independent_check(n):
    labels = tuple(i for i, count in enumerate(n) for _ in range(count))

    def matching(nodes):
        if not nodes:
            yield ()
        else:
            for k in range(1, len(nodes)):
                for tail in matching(nodes[1:k] + nodes[k + 1 :]):
                    yield ((nodes[0], nodes[k]), *tail)

    choices = list(matching(tuple(range(len(labels)))))
    bad = [sum(labels[i] == labels[j] for i, j in m) for m in choices]
    good = [m for m, score in zip(choices, bad, strict=True) if score == min(bad)]
    assert completions(n) == (min(bad), len(good))
    counts = Counter(
        (labels[x], labels[y]) for m in good for i, j in m for x, y in ((i, j), (j, i))
    )
    actual = joint(n)
    assert all(
        actual[i][j] == Q(counts[i, j], len(good) * len(labels))
        for i in range(len(n))
        for j in range(len(n))
    )


def run(output):
    checked = 0
    failure = None
    oracle_count = 0
    for b in range(2, 13, 2):
        for n in partitions(b):
            if b <= 8:
                independent_check(n)
                oracle_count += 1
            failure = obstruction(n, b, joint(n))
            checked += 1
            if failure:
                break
        print("conditional", b, checked, bool(failure), flush=True)
        if failure:
            break
    if not failure:
        for m in range(4, 15):
            for n in partitions(m):
                for b in range(2, m + 1, 2):
                    failure = obstruction(n, b, source_joint(n, b))
                    checked += 1
                    if failure:
                        break
                if failure:
                    break
            print("population", m, checked, bool(failure), flush=True)
            if failure:
                break
    output.write_text(
        json.dumps(
            dict(
                scope="Rational joint oracle; numerical spectral check only; no model run.",
                checked=checked,
                independent_matching_oracles=oracle_count,
                class_limit=6,
                obstruction=failure,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
