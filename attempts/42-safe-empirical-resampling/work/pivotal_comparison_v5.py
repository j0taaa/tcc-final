"""Complete rational pivotal laws; comparison is not a physical benchmark."""

import argparse
import importlib
import itertools
import json
from fractions import Fraction as Q
from functools import cache
from pathlib import Path

matching = importlib.import_module("attempts.42-safe-empirical-resampling.work.matching_probe")


@cache
def allocation_joint(state):
    active = [i for i, q in enumerate(state) if q.denominator != 1]
    k = len(state)
    if not active:
        assert sum(state) == 2
        return tuple(
            tuple(a * (b - (i == j)) / 2 for j, b in enumerate(state)) for i, a in enumerate(state)
        )
    assert len(active) >= 2
    result = [[Q(0) for _ in state] for _ in state]
    pair_count = len(active) * (len(active) - 1) // 2
    for i, j in itertools.combinations(active, 2):
        ni, nj = int(state[i]), int(state[j])
        a, b = state[i] - ni, state[j] - nj
        total = a + b
        choices = (
            ((0, total, b / total), (total, 0, a / total))
            if total < 1
            else ((1, total - 1, (1 - b) / (2 - total)), (total - 1, 1, (1 - a) / (2 - total)))
        )
        for first, second, probability in choices:
            child = list(state)
            child[i], child[j] = Q(ni) + first, Q(nj) + second
            joint = allocation_joint(tuple(child))
            for s, t in itertools.product(range(k), repeat=2):
                result[s][t] += probability * joint[s][t] / pair_count
    return tuple(map(tuple, result))


def run(path):
    cases = []
    for budget in (2, 4, 6, 8):
        for n in matching.partitions(budget, limit=budget):
            classic = allocation_joint(tuple(Q(2 * t, budget) for t in n))
            candidate = matching.joint(n)
            assert all(sum(row) == Q(t, budget) for t, row in zip(n, classic, strict=True))
            assert all(classic[i][i] == max(Q(0), Q(2 * t, budget) - 1) for i, t in enumerate(n))
            obstruction = matching.obstruction(n, budget, classic)
            cases.append(
                dict(
                    population=n,
                    budget=budget,
                    equal=classic == candidate,
                    classic=[[str(t) for t in row] for row in classic],
                    matching=[[str(t) for t in row] for row in candidate],
                    exact_obstruction=obstruction,
                )
            )
    path.write_text(
        json.dumps(
            dict(
                scope="Conditional rational law only; no priority, timing or neural claim",
                checked=len(cases),
                cases=cases,
            ),
            indent=2,
        )
        + "\n"
    )
    print(
        dict(
            checked=len(cases),
            differences=sum(not c["equal"] for c in cases),
            exact_obstructions=sum(c["exact_obstruction"] is not None for c in cases),
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
