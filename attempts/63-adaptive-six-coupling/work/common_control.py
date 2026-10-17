"""Optimal classical completion-preserving control and exact operational audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from fractions import Fraction as F
from itertools import pairwise, permutations, product
from math import lcm
from pathlib import Path


def full_kernel(t: tuple[int, ...]) -> tuple[F, ...]:
    counts = [t.count(j) for j in range(3)]
    first = t[0]
    excess = [max(0, 2 * n - 6) for n in counts]
    result = []
    for j in range(3):
        if j == first:
            result.append(F(excess[j], counts[first]))
        else:
            k = 3 - first - j
            result.append(
                F(
                    counts[first] + counts[j] - counts[k] - excess[first] - excess[j] + excess[k],
                    2 * counts[first],
                )
            )
    assert sum(result) == 1 and min(result) >= 0
    return tuple(result)


def prepare() -> tuple[dict, dict, list[F], int]:
    full = {t: full_kernel(t) for t in product(range(3), repeat=6)}
    lower = {(): (F(0),) * 3}
    for h in range(1, 7):
        for s in product(range(3), repeat=h):
            choices = [full[s + suffix] for suffix in product(range(3), repeat=6 - h)]
            lower[s] = tuple(min(q[j] for q in choices) for j in range(3))
    endpoints = {F(0), F(1)}
    for s, a in lower.items():
        if not s:
            continue
        previous = lower[s[:-1]]
        cursor = sum(previous)
        for old, new in zip(previous, a, strict=True):
            assert new >= old
            cursor += new - old
            endpoints.add(cursor)
    grid = lcm(*(x.denominator for x in endpoints))
    return full, lower, sorted(endpoints), grid


def couple(draw, key, randbelow, lower: dict, grid: int) -> tuple:
    """One independent exact integer ticket; all interval endpoints lie on its grid."""
    ticket = randbelow(grid)
    if not 0 <= ticket < grid:
        raise ValueError("Invalid uniform integer ticket.")
    u = F(2 * ticket + 1, 2 * grid)
    payloads, labels = [], ()
    for _ in range(6):
        value = draw()
        actual = key(value)
        if actual not in (0, 1, 2):
            raise ValueError("Three fixed keys required.")
        payloads.append(value)
        previous = lower[labels]
        labels += (actual,)
        current = lower[labels]
        cursor = sum(previous)
        assert u >= cursor, "a previously stopped ticket reached a later node"
        for j in range(3):
            right = cursor + current[j] - previous[j]
            if cursor <= u < right:
                index = next(i for i in range(1, len(labels)) if labels[i] == j)
                return payloads[0], payloads[index], len(payloads)
            cursor = right
    raise AssertionError("Did not stop by six calls.")


def multiply(a: dict, b: dict) -> dict:
    out: Counter = Counter()
    for n, c in a.items():
        for m, d in b.items():
            out[tuple(x + y for x, y in zip(n, m, strict=True))] += c * d
    return {n: c for n, c in out.items() if c}


def power(a: dict, n: int) -> dict:
    out = {(0, 0, 0): F(1)}
    for _ in range(n):
        out = multiply(out, a)
    return out


def combine(*terms: tuple[F, dict]) -> dict:
    out: Counter = Counter()
    for c, p in terms:
        for n, v in p.items():
            out[n] += c * v
    return {n: c for n, c in out.items() if c}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    full, lower, endpoints, grid = prepare()
    cells = list(pairwise(endpoints))
    matchings = {
        tuple(sorted(tuple(sorted(p[i : i + 2])) for i in range(0, 6, 2)))
        for p in permutations(range(6))
    }
    assert len(matchings) == 15
    cost_coeff, a4_coeff, a5_coeff = Counter(), Counter(), Counter()
    results, nodes, replays = {}, 0, 0
    for t, q in full.items():
        losses = {m: sum(t[i] == t[j] for i, j in m) for m in matchings}
        best = [m for m, v in losses.items() if v == min(losses.values())]
        reference = [F(0)] * 3
        for m in best:
            partner = next(j if i == 0 else i for i, j in m if 0 in (i, j))
            reference[t[partner]] += F(1, len(best))
        assert tuple(reference) == q, "count formula differs from full matching"
        raw = [{"key": j, "index": i, "raw_alias": bytes((i, j))} for i, j in enumerate(t)]
        out, cost, stops = [F(0)] * 3, F(0), Counter()
        for lo, hi in cells:
            assert (lo * grid).denominator == (hi * grid).denominator == 1
            ticket = int(lo * grid)
            calls, coins = 0, 0

            def draw(sequence: list[dict] = raw) -> dict:
                nonlocal calls
                assert calls < 6
                value = sequence[calls]
                calls += 1
                return value

            def coin(n: int, value: int = ticket) -> int:
                nonlocal coins
                assert n == grid
                coins += 1
                return value

            first, second, spent = couple(draw, lambda a: a["key"], coin, lower, grid)
            assert coins == 1 and calls == spent and first is raw[0]
            assert any(second is raw[i] for i in range(1, spent))
            mass = hi - lo
            out[second["key"]] += mass
            cost += spent * mass
            stops[spent] += mass
            nodes += spent
            replays += 1
            assert nodes <= 1_000_000, "declared replay guard"
        assert tuple(out) == q
        for h in range(1, 7):
            actual = sum((mass for depth, mass in stops.items() if depth <= h), F(0))
            assert actual == sum(lower[t[:h]]), "prefix survival bound not attained"
        n = tuple(t.count(j) for j in range(3))
        cost_coeff[n] += cost
        a4_coeff[n] += sum((mass for h, mass in stops.items() if h <= 4), F(0))
        a5_coeff[n] += sum((mass for h, mass in stops.items() if h <= 5), F(0))
        results[t] = cost, stops
    s = {(1, 0, 0): F(1), (0, 1, 0): F(1), (0, 0, 1): F(1)}
    qpoly = {(1, 1, 0): F(1), (1, 0, 1): F(1), (0, 1, 1): F(1)}
    rpoly = {(1, 1, 1): F(1)}
    base = power(s, 6)
    u = multiply(qpoly, power(s, 4))
    v = multiply(power(qpoly, 2), power(s, 2))
    w = multiply(rpoly, power(s, 3))
    z = multiply(multiply(qpoly, rpoly), s)
    assert dict(cost_coeff) == combine(
        (F(47, 10), base), (F(3, 5), u), (F(-2, 5), v), (F(27, 5), w), (F(8), z)
    )
    assert {n: c for n, c in a4_coeff.items() if c} == combine(
        (F(1, 2), base), (F(-2, 5), u), (F(4, 5), v), (F(-28, 5), w)
    )
    assert {n: c for n, c in a5_coeff.items() if c} == combine(
        (F(4, 5), base), (F(-1, 5), u), (F(-2, 5), v), (F(1, 5), w), (F(-8), z)
    )
    laws = [
        (F(1, 3),) * 3,
        (F(1, 2), F(1, 3), F(1, 6)),
        (F(1, 2), F(1, 2), F(0)),
        (F(9, 10), F(1, 20), F(1, 20)),
        (F(1), F(0), F(0)),
    ]
    weighted = []
    for p in laws:
        expected, stop = F(0), Counter()
        for t, (cost, stops) in results.items():
            probability = F(1)
            for j in t:
                probability *= p[j]
            expected += probability * cost
            for h, mass in stops.items():
                stop[h] += probability * mass
        e2 = p[0] * p[1] + p[0] * p[2] + p[1] * p[2]
        e3 = p[0] * p[1] * p[2]
        candidate = 4 + 2 * e2 - 2 * e2**2 + 10 * e3 - 4 * e2 * e3
        formula = F(47, 10) + F(3, 5) * e2 - F(2, 5) * e2**2 + F(27, 5) * e3 + 8 * e2 * e3
        assert expected == formula
        assert expected - candidate >= F(7, 18)
        assert 1 - candidate / expected >= F(63, 835)
        weighted.append(
            {
                "p": list(map(str, p)),
                "control_expected_calls": str(expected),
                "candidate_expected_calls": str(candidate),
                "candidate_saving_fraction": str(1 - candidate / expected),
                "stop_mass": {str(h): str(mass) for h, mass in sorted(stop.items())},
            }
        )
    assert F(weighted[0]["control_expected_calls"]) == F(835, 162)
    result = {
        "status": "PASS",
        "named_tapes": len(full),
        "perfect_matchings_per_tape": len(matchings),
        "prepared_prefix_states": len(lower),
        "uniform_integer_grid": grid,
        "uniform_cells": len(cells),
        "operational_replays": replays,
        "transcript_read_nodes": nodes,
        "conditional_tape_law_and_prefix_optimal_survival": "all exact",
        "three_degree_six_polynomial_identities": "all coefficients exact",
        "weighted_laws": weighted,
        "neural_forwards": 0,
        "timing_measured": False,
        "published_package_executed": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
