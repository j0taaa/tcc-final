"""Finite raw-payload Markov oracle independent of the capped sampler."""

import argparse
import json
from collections import defaultdict
from fractions import Fraction as Q
from itertools import product
from pathlib import Path

from .bounded import pair


def law(probabilities, labels, m, cap):
    joint = [[Q(0) for _ in labels] for _ in labels]
    expected = Q(0)
    for first, first_label in enumerate(labels):
        states = {(1, None): probabilities[first]}
        for t in range(2, cap + 1):
            next_states = defaultdict(Q)
            for (old_height, old_same), mass in states.items():
                for index, p in enumerate(probabilities):
                    height = old_height + (1 if labels[index] == first_label else -1)
                    same = index if labels[index] == first_label else old_same
                    weight = mass * p
                    if height == 0:
                        selected = index
                    elif height == m or t == cap:
                        assert same is not None
                        selected = same
                    else:
                        next_states[height, same] += weight
                        continue
                    joint[first][selected] += weight
                    expected += t * weight
            states = next_states
        assert not states
    return joint, expected


def covariance_check(p, labels, j):
    n = len(p)
    for i in range(n):
        assert sum(j[i]) == p[i]
        assert sum(row[i] for row in j) == p[i]
        assert all(j[i][k] == j[k][i] for k in range(n))
    mass = sum(p[i] for i in range(n) if labels[i])
    off = sum(j[i][k] for i in range(n) for k in range(n) if labels[i] and not labels[k])
    kappa = off - mass * (1 - mass)
    assert kappa >= 0
    if 0 < mass < 1:
        g = [(Q(i), Q((-1) ** i), Q(i * i)) for i in range(n)]
        for d in range(3):
            for e in range(3):
                mean_d = sum(p[i] * g[i][d] for i in range(n))
                mean_e = sum(p[i] * g[i][e] for i in range(n))
                differences = [
                    sum(p[i] * g[i][k] for i in range(n) if labels[i]) / mass
                    - sum(p[i] * g[i][k] for i in range(n) if not labels[i]) / (1 - mass)
                    for k in (d, e)
                ]
                cov = sum(j[i][k] * g[i][d] * g[k][e] for i in range(n) for k in range(n))
                assert cov - mean_d * mean_e == -kappa * differences[0] * differences[1]
    return kappa


def run(output):
    rational, tapes = 0, 0
    for n in range(2, 5):
        p = tuple(Q(i + 1, n * (n + 1) // 2) for i in range(n))
        for labels in product((0, 1), repeat=n):
            for m in range(2, 7):
                old_kappa = Q(0)
                for cap in range(2, 13):
                    j, expected = law(p, labels, m, cap)
                    assert 2 <= expected <= min(m, cap)
                    kappa = covariance_check(p, labels, j)
                    assert kappa >= old_kappa
                    old_kappa = kappa
                    rational += 1
    for m in range(2, 7):
        for cap in range(2, 11):
            for labels in product((0, 1), repeat=cap):
                height, same, selected, end = 2 * labels[0] - 1, None, None, None
                for t in range(1, cap):
                    height += 2 * labels[t] - 1
                    if labels[t] == labels[0]:
                        same = t
                    if height == 0 or abs(height) == m or t == cap - 1:
                        selected = t if height == 0 else same
                        end = t
                        break
                assert selected is not None and selected > 0 and end is not None
                sources = tuple((i, label) for i, label in enumerate(labels))
                iterator = iter(sources)
                a, b, count = pair(iterator.__next__, lambda z: z[1], m, cap)
                assert a is sources[0] and b is sources[selected] and count == end + 1
                tapes += 1
    tail_checks = []
    for m in (3, 4, 6, 8):
        for cap in (16, 32, 64):
            j, expected = law((Q(1, 2), Q(1, 2)), (0, 1), m, cap)
            repeat = j[0][0] + j[1][1]
            assert expected * repeat >= 1
            tail_checks.append(dict(barrier=m, cap=cap, queries=str(expected), repeat=str(repeat)))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            dict(
                scope="Exact capped payload law; no neural run, timing or priority certificate.",
                rational_laws=rational,
                original_payload_tapes=tapes,
                balanced_examples=tail_checks,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    run(parser.parse_args().output)
