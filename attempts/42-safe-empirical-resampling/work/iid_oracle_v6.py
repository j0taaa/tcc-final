"""Independent exact IID tape and symbolic proof checks, not model results."""

import argparse
import importlib
import itertools
import json
from collections import Counter
from fractions import Fraction as Q
from math import prod
from pathlib import Path

import sympy as sp

sampler = importlib.import_module("attempts.42-safe-empirical-resampling.work.iid_pair_v6")
algebra = importlib.import_module("attempts.42-safe-empirical-resampling.work.six_pool_algebra")


def symbolic():
    x, y, s2, s3, s4 = algebra.x, algebra.y, algebra.s2, algebra.s3, algebra.s4
    scale = sp.Symbol("scale")
    scaled = algebra.derive().subs(
        {
            algebra.m: scale,
            x: scale * x,
            y: scale * y,
            s2: scale**2 * s2,
            s3: scale**3 * s3,
            s4: scale**4 * s4,
        },
        simultaneous=True,
    )
    u = sp.Poly(scaled, scale).coeff_monomial(scale**4)
    a = 1 - s2
    b = a * a + s2 - 2 * s3 + s4
    g = 5 * x**4 - 6 * x**5 + 2 * x**6
    assert sp.expand(g - x * x * u.subs(y, x) + x * x * (b + a * x * (2 - x))) == 0
    assert sp.expand((b + a) - b * s2 - a * (2 * s3 - s4) - 2 * b * a - s2 * a * a) == 0
    deltas = []
    for classes in range(2, 33):
        p = Q(1, classes)
        g6 = 5 * p**4 - 6 * p**5 + 2 * p**6
        delta = (p * p - g6) / (p * (1 - p))
        assert delta == p + p * p - 4 * p**3 + 2 * p**4
        deltas.append(dict(classes=classes, delta6=str(delta)))
    return str(u), deltas


def exact_tapes(mass, labels, polynomial):
    # Unequal raw probabilities, aliases in one class, repeated raw states.
    states, classes = len(mass), len(set(labels))
    joint = Counter()
    for tape in itertools.product(range(states), repeat=6):
        weight = prod(mass[i] for i in tape)
        calls = []
        remaining = iter(tape[1:])
        first = object()
        objects = (first, *(object() for _ in range(5)))
        lookup = {obj: i for i, obj in enumerate(objects)}

        def draw(remaining=remaining, calls=calls, objects=objects):
            index = next(remaining)
            calls.append(index)
            return objects[len(calls)]

        def key(obj, tape=tape, lookup=lookup):
            return labels[tape[lookup[obj]]]

        def select(bound, calls=calls):
            calls.append(bound)
            return 0

        original, _ = sampler.pair(first, draw, key, select)
        assert original is first and calls[:5] == list(tape[1:])
        bound = calls[-1]
        for choice in range(bound):
            ids = iter(tape[1:])
            returned = sampler.pair(
                tape[0], lambda ids=ids: next(ids), lambda i: labels[i], lambda _, c=choice: c
            )
            joint[returned] += weight / bound
    assert sum(joint.values()) == 1
    assert all(sum(joint[i, j] for j in range(states)) == mass[i] for i in range(states))
    assert all(sum(joint[i, j] for i in range(states)) == mass[j] for j in range(states))
    p = [sum(mass[i] for i in range(states) if labels[i] == c) for c in range(classes)]
    class_joint = [
        [
            sum(
                joint[i, j]
                for i in range(states)
                for j in range(states)
                if labels[i] == a and labels[j] == b
            )
            for b in range(classes)
        ]
        for a in range(classes)
    ]
    for i in range(states):
        for j in range(states):
            assert joint[i, j] == class_joint[labels[i]][labels[j]] * (mass[i] / p[labels[i]]) * (
                mass[j] / p[labels[j]]
            )
    for i, probability in enumerate(p):
        assert class_joint[i][i] == 5 * probability**4 - 6 * probability**5 + 2 * probability**6
    u = sp.sympify(polynomial)
    for i in range(classes):
        for j in range(classes):
            if i == j:
                continue
            expected = (
                p[i]
                * p[j]
                * u.subs(
                    {
                        algebra.x: p[i],
                        algebra.y: p[j],
                        algebra.s2: sum(t * t for t in p),
                        algebra.s3: sum(t**3 for t in p),
                        algebra.s4: sum(t**4 for t in p),
                    },
                    simultaneous=True,
                )
            )
            numerator, denominator = expected.as_numer_denom()
            assert class_joint[i][j] == Q(int(numerator), int(denominator))
    return dict(
        raw_tapes=states**6,
        raw_marginals=list(map(str, mass)),
        class_joint=[[str(t) for t in row] for row in class_joint],
        repeated_originals_retained=any(joint[i, i] > 0 for i in range(states)),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    polynomial, deltas = symbolic()
    tapes = [
        exact_tapes((Q(1, 7), Q(2, 7), Q(1, 7), Q(3, 7)), (0, 0, 1, 2), polynomial),
        exact_tapes((Q(1, 10), Q(2, 10), Q(3, 10), Q(4, 10)), (0, 1, 2, 3), polynomial),
        exact_tapes((Q(1, 3), Q(2, 3)), (0, 0), polynomial),
    ]
    result = dict(
        scope="Exact rational/symbolic correctness only; no neural or priority claim",
        iid_polynomial=polynomial,
        balanced_deltas=deltas,
        cases=tapes,
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        dict(
            symbolic_identities=2,
            exact_raw_tapes=sum(t["raw_tapes"] for t in tapes),
            balanced_classes=len(deltas),
        )
    )
