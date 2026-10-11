"""Numerical counterexample search only; NOT exact sampling or a benchmark."""

import argparse
import json
from functools import cache
from math import comb, prod
from pathlib import Path

import numpy as np


@cache
def pool_joint(counts):
    counts = np.array(counts)
    active = np.flatnonzero(counts)
    p = counts[active] / counts.sum()
    h = int(np.argmax(p))
    joint = np.zeros((len(p), len(p)))
    if p[h] >= 0.5:
        joint[h] = p
        joint[:, h] = p
        joint[h, h] = 2 * p[h] - 1
    else:
        lo, hi = 0.0, 1 / (4 * p[h])

        def roots(x):
            return 2 * p * x / (1 + np.sqrt(np.maximum(0, 1 - 4 * p * x)))

        major = roots(hi).sum() < 1
        for _ in range(90):
            middle = (lo + hi) / 2
            b = roots(middle)
            difference = b.sum() - 1 if not major else b.sum() - 2 * b[h]
            if (difference < 0) != major:
                lo = middle
            else:
                hi = middle
        x = (lo + hi) / 2
        b = roots(x)
        if major:
            b[h] = 1 - b[h]
        a = b / np.sqrt(x)
        joint = np.outer(a, a)
        np.fill_diagonal(joint, 0)
    assert np.allclose(joint.sum(axis=0), p, atol=3e-13, rtol=3e-13), counts
    assert joint.min() >= 0
    assert np.allclose(np.diag(joint), np.maximum(0, 2 * p - 1), atol=3e-13)
    full = np.zeros((len(counts), len(counts)))
    full[np.ix_(active, active)] = joint
    return full


def partitions(n, minimum=1, limit=5):
    if n == 0:
        yield ()
    elif limit:
        for first in range(minimum, n + 1):
            for tail in partitions(n - first, first, limit - 1):
                yield (first, *tail)


def counts_in_pool(population, budget):
    if len(population) == 1:
        if budget <= population[0]:
            yield (budget,)
        return
    for first in range(max(0, budget - sum(population[1:])), min(population[0], budget) + 1):
        for tail in counts_in_pool(population[1:], budget - first):
            yield (first, *tail)


def source_joint(population, budget):
    m = sum(population)
    joint = np.zeros((len(population), len(population)))
    for r in counts_in_pool(population, budget):
        weight = prod(comb(n, k) for n, k in zip(population, r, strict=True)) / comb(m, budget)
        joint += weight * pool_joint(r)
    p = np.array(population) / m
    assert np.allclose(joint.sum(axis=0), p, atol=1e-12, rtol=1e-12)
    return joint, joint - np.outer(p, p)


def run(maximum, output):
    checked, worst = 0, dict(eigenvalue=-1.0)
    obstruction = None
    for m in range(4, maximum + 1):
        for population in partitions(m):
            for budget in range(2, m + 1):
                joint, covariance = source_joint(population, budget)
                eigenvalues, vectors = np.linalg.eigh(covariance)
                value = float(eigenvalues[-1])
                checked += 1
                if value > worst["eigenvalue"]:
                    worst = dict(
                        population=population,
                        budget=budget,
                        eigenvalue=value,
                        vector=vectors[:, -1].tolist(),
                        joint=joint.tolist(),
                    )
                if value > 1e-9:
                    obstruction = worst
                    break
            if obstruction:
                break
        print(m, checked, worst["eigenvalue"], flush=True)
        if obstruction:
            break
    output.write_text(
        json.dumps(
            dict(
                scope="Numerical obstruction search, not a proof or external model measurement",
                checked=checked,
                maximum=maximum,
                class_limit=5,
                worst=worst,
                obstruction=obstruction,
                cached_pool_states=pool_joint.cache_info().currsize,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--maximum", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.maximum, args.output)
