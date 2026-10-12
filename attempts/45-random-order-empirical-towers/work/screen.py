"""Independent adverse-only tower/population oracle; no neural experiments."""

import argparse
import json
import math
from functools import cache
from itertools import permutations
from pathlib import Path

import numpy as np


def compositions(total, length):
    if length == 1:
        yield (total,)
    else:
        for first in range(total + 1):
            for tail in compositions(total - first, length - 1):
                yield (first, *tail)


@cache
def profile_joint(profile):
    b = sum(profile)
    length = len(profile)
    result = np.zeros((length, length), dtype=np.int64)
    occupied = [i for i, r in enumerate(profile) if r]
    orders = 0
    for order in permutations(occupied):
        tickets = [i for i in order for _ in range(2 * profile[i])]
        for t, i in enumerate(tickets):
            result[i, tickets[(t + b) % (2 * b)]] += 1
        orders += 1
    assert orders == math.factorial(len(occupied))
    assert np.array_equal(result, result.T)
    assert np.array_equal(result.sum(axis=1), np.asarray(profile) * 2 * orders)
    assert np.array_equal(np.diag(result), np.maximum(2 * np.asarray(profile) - b, 0) * 2 * orders)
    return result / (2 * b * orders)


def prepare(length, b):
    counts = np.asarray(list(compositions(b, length)), dtype=np.int64)
    coefficients, joints = [], []
    for row in counts:
        order = sorted(range(length), key=lambda i: row[i])
        inverse = np.argsort(order)
        profile = tuple(int(row[i]) for i in order)
        joints.append(profile_joint(profile)[np.ix_(inverse, inverse)])
        coefficients.append(math.factorial(b) // math.prod(math.factorial(int(r)) for r in row))
    return counts, np.asarray(coefficients), np.asarray(joints)


def populations(length):
    denominator = {4: 8, 5: 9, 6: 10}[length]
    for counts in compositions(denominator, length):
        if min(counts) and tuple(sorted(counts)) == counts:
            yield (
                dict(kind="grid", counts=counts, denominator=denominator),
                np.asarray(counts) / denominator,
            )
    if length == 4:
        yield dict(kind="prior"), np.asarray([0.4, 0.3, 0.2, 0.1])
    rng = np.random.default_rng(20261012045 + length)
    for alpha in [0.1, 1.0, 10.0]:
        for index in range(128):
            p = rng.dirichlet(np.full(length, alpha))
            yield dict(kind="random", alpha=alpha, index=index), p


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    count = 0
    with (output / "rows.jsonl").open("w") as stream:
        for length in [4, 5, 6]:
            cases = list(populations(length))
            for b in [2, 4, 6, 8, 10, 12] if length < 6 else [2, 4, 6, 8]:
                counts, coeff, joints = prepare(length, b)
                print(json.dumps(dict(length=length, budget=b, profiles=len(counts))), flush=True)
                for case, p in cases:
                    weights = coeff * np.prod(p**counts, axis=1)
                    assert abs(weights.sum() - 1) < 1e-12
                    joint = np.einsum("r,rij->ij", weights, joints)
                    assert np.max(np.abs(joint.sum(axis=1) - p)) < 1e-12
                    covariance = joint - np.outer(p, p)
                    values, vectors = np.linalg.eigh(covariance)
                    row = dict(
                        length=length,
                        budget=b,
                        case=case,
                        p=p.tolist(),
                        eigenvalues=values.tolist(),
                    )
                    count += 1
                    stream.write(json.dumps(row) + "\n")
                    if values[-1] > 1e-9:
                        row.update(score=vectors[:, -1].tolist(), joint=joint.tolist(), cases=count)
                        (output / "obstruction.json").write_text(json.dumps(row, indent=2) + "\n")
                        print(json.dumps(dict(status="NUMERICAL_OBSTRUCTION", **row)), flush=True)
                        return
    result = dict(
        status="NO_FINITE_OBSTRUCTION_NOT_PROOF",
        cases=count,
        cached_profiles=profile_joint.cache_info().currsize,
    )
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
