"""Independent finite rational checks; no novelty or model-performance claim."""

import argparse
import importlib
import json
from fractions import Fraction as Q
from itertools import combinations, product
from math import comb, factorial
from pathlib import Path

reference = importlib.import_module(
    "attempts.42-safe-empirical-resampling.work.monotone_budget_v10"
)


def direct_c4(labels, classes):
    result = [[Q(0) for _ in range(classes)] for _ in range(classes)]
    b = len(labels)
    matchings = (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2)))
    for subset in combinations(range(b), 4):
        tape = [labels[i] for i in subset]
        scores = [sum(tape[i] == tape[j] for i, j in m) for m in matchings]
        good = [m for m, cost in zip(matchings, scores, strict=True) if cost == min(scores)]
        for matching in good:
            for i, j in matching:
                for x, y in ((i, j), (j, i)):
                    result[tape[x]][tape[y]] += Q(1, comb(b, 4) * 4 * len(good))
    return result


def joint(labels, classes):
    rows = []
    b = len(labels)
    for i in range(classes):
        if i not in labels:
            rows.append([Q(0) for _ in range(classes)])
            continue
        at = labels.index(i)
        tape = [labels[at], *labels[:at], *labels[at + 1 :]]
        row = reference.integer_row(tape, classes)
        rows.append([Q(labels.count(i) * value, b * sum(row)) for value in row])
    return rows


def count_vectors(total, classes):
    if classes == 1:
        yield (total,)
    else:
        for first in range(total + 1):
            for rest in count_vectors(total - first, classes - 1):
                yield (first, *rest)


def sampler_law(labels, classes):
    """Enumerate the sampler's actual bounded-coin decision tree."""
    result = [Q(0) for _ in labels]
    frontier = [((), Q(1))]
    while frontier:
        decisions, probability = frontier.pop()
        cursor = 0

        class NeedCoin(Exception):
            pass

        def coin(bound, tape=decisions):
            nonlocal cursor
            if cursor == len(tape):
                raise NeedCoin(bound)
            value = tape[cursor]
            cursor += 1
            return value

        try:
            selected = reference.partner(labels, classes, coin)
        except NeedCoin as pending:
            bound = pending.args[0]
            frontier.extend(((*decisions, value), probability / bound) for value in range(bound))
        else:
            assert selected != 0
            result[selected] += probability
    return result


def run(output):
    pool_checks, raw_checks, monotone_checks = 0, 0, 0
    for b in range(4, 9):
        for r in count_vectors(b, 3):
            labels = [i for i, count in enumerate(r) for _ in range(count)]
            base, actual = direct_c4(labels, 3), joint(labels, 3)
            for i in range(3):
                assert sum(actual[i]) == Q(r[i], b)
                for j in range(3):
                    if i != j:
                        assert actual[i][j] == base[i][j] + min(base[i][i], base[j][j]) / 2
            # Derive diagonals from row sums rather than shared formula.
            assert all(
                actual[i][i] == Q(r[i], b) - sum(actual[i][j] for j in range(3) if i != j)
                for i in range(3)
            )
            pool_checks += 1
    sampler_checks = 0
    for labels in (
        (0, 0, 0, 0),
        (0, 0, 1, 1),
        (0, 0, 0, 1, 1, 1),
        (0, 0, 0, 1, 1, 1, 2, 2),
        (0, 1, 2, 0, 2, 1),
    ):
        law = sampler_law(labels, 3)
        row = reference.integer_row(labels, 3)
        assert sum(law) == 1 and law[0] == 0
        for j in range(1, len(labels)):
            count = sum(value == labels[j] for value in labels[1:])
            assert law[j] == Q(row[labels[j]], sum(row) * count)
        sampler_checks += 1
    # Independent raw-state marginal and covariance lift, including aliases:
    # states0/1 share label0, state2 has label1. IID sampling WITH replacement.
    p, classes = (Q(1, 2), Q(1, 3), Q(1, 6)), 3
    label_of, score = (0, 0, 1), (Q(-3), Q(2), Q(5))
    for b in (4, 5, 6):
        second = [Q(0) for _ in p]
        cross, base_cross = Q(0), Q(0)
        for tape in product(range(len(p)), repeat=b):
            mass = Q(1)
            for state in tape:
                mass *= p[state]
            labels = [label_of[state] for state in tape]
            row = reference.integer_row(labels, classes)
            base = direct_c4(labels, classes)
            first_class = labels[0]
            for j in range(1, b):
                label = labels[j]
                members = sum(value == label for value in labels[1:])
                probability = Q(row[label], sum(row) * members)
                second[tape[j]] += mass * probability
                cross += mass * probability * score[tape[0]] * score[tape[j]]
                baseline_probability = (
                    base[first_class][label] / Q(labels.count(first_class), b) / members
                )
                base_cross += mass * baseline_probability * score[tape[0]] * score[tape[j]]
            raw_checks += 1
        assert second == list(p)
        assert cross <= base_cross
    # Exact balanced magnitudes, not a selected performance benchmark.
    balanced = []
    for classes in (2, 3, 4, 8):
        previous = Q(0)
        for b in (4, 5, 6, 8, 16, 32, 64):
            a = Q(0)
            denominator = b * (b - 1) * (b - 2) * (b - 3)
            for i in range(b + 1):
                di = Q(i * (i - 1) * (i - 2) * (2 * b - i - 3), denominator)
                for j in range(b - i + 1):
                    k = b - i - j
                    if classes == 2 and k:
                        continue
                    dj = Q(j * (j - 1) * (j - 2) * (2 * b - j - 3), denominator)
                    ways = factorial(b) // (factorial(i) * factorial(j) * factorial(k))
                    probability = Q(ways * (classes - 2) ** k, classes**b)
                    a += probability * min(di, dj)
            assert a >= previous
            previous = a
            delta = Q(classes - 1, classes**2) + Q(classes**2, classes - 1) * a
            assert delta <= Q(1, classes - 1)
            balanced.append(
                dict(classes=classes, budget=b, exact_delta=str(delta), delta=float(delta))
            )
            monotone_checks += 1
    data = dict(
        scope="Finite rational correctness checks, not model use or novelty",
        pool_checks=pool_checks,
        weighted_original_tapes=raw_checks,
        exact_sampler_laws=sampler_checks,
        monotone_balanced_checks=monotone_checks,
        balanced=balanced,
    )
    output.write_text(json.dumps(data, indent=2) + "\n")
    print({key: value for key, value in data.items() if key != "balanced"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
