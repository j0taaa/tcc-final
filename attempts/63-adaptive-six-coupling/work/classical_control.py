"""Complete lazy count-polynomial/CDF control; exact audit, not package/timing data."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import pairwise, product
from pathlib import Path


def all_pairings(vertices: tuple[int, ...]) -> list[dict[int, int]]:
    if not vertices:
        return [{}]
    root, tail = vertices[0], vertices[1:]
    out = []
    for mate in tail:
        for rest in all_pairings(tuple(i for i in tail if i != mate)):
            out.append(rest | {root: mate, mate: root})
    return out


def prepare() -> tuple[dict, dict, list[F]]:
    pairs = all_pairings(tuple(range(6)))
    assert len(pairs) == 15
    full, endpoints = {}, {F(0), F(1)}
    for t in product(range(3), repeat=6):
        loss = [sum(t[i] == t[m[i]] for i in range(6)) for m in pairs]
        best = [m for m, v in zip(pairs, loss, strict=True) if v == min(loss)]
        probabilities = tuple(F(sum(t[m[0]] == j for m in best), len(best)) for j in range(3))
        assert sum(probabilities) == 1
        full[t] = probabilities
        endpoints.update((probabilities[0], probabilities[0] + probabilities[1]))
    intervals = {}
    for h in range(1, 7):
        for prefix in product(range(3), repeat=h):
            completions = [full[prefix + suffix] for suffix in product(range(3), repeat=6 - h)]
            intervals[prefix] = tuple(
                (
                    max(sum(q[:j], F(0)) for q in completions),
                    min(sum(q[: j + 1], F(0)) for q in completions),
                )
                for j in range(3)
            )
    return full, intervals, sorted(endpoints)


def couple(draw, key, u: F, intervals: dict) -> tuple:
    """Use one independent U and intersect all future-completion CDF intervals."""
    payloads, keys = [], ()
    for _ in range(6):
        original = draw()
        label = key(original)
        if label not in (0, 1, 2):
            raise ValueError("Three fixed labels required.")
        payloads.append(original)
        keys += (label,)
        for j, (lo, hi) in enumerate(intervals[keys]):
            if lo <= u < hi:
                index = next(i for i in range(1, len(keys)) if keys[i] == j)
                return payloads[0], payloads[index], len(payloads)
    raise AssertionError("did not stop")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    full, intervals, endpoints = prepare()
    cells = [(lo, hi, (lo + hi) / 2) for lo, hi in pairwise(endpoints)]
    tape_results, nodes = {}, 0
    groups = defaultdict(lambda: {"count": 0, "joint": [[F(0)] * 3 for _ in range(3)]})
    for t, q in full.items():
        out = [F(0)] * 3
        cost = F(0)
        stops = Counter()
        raw = [{"key": j, "index": i, "raw_alias": bytes((i, j))} for i, j in enumerate(t)]
        for lo, hi, u in cells:
            calls = 0

            def draw(sequence: list[dict] = raw) -> dict:
                nonlocal calls
                assert calls < 6
                item = sequence[calls]
                calls += 1
                return item

            first, second, spent = couple(draw, lambda payload: payload["key"], u, intervals)
            assert first is raw[0] and calls == spent
            assert any(second is raw[i] for i in range(1, spent))
            mass = hi - lo
            out[second["key"]] += mass
            cost += mass * spent
            stops[spent] += mass
            nodes += spent
            assert nodes <= 1_000_000, "declared transcript guard"
        assert tuple(out) == q, "lazy law differs from full matching on a tape"
        n = tuple(t.count(j) for j in range(3))
        group = groups[n]
        group["count"] += 1
        for j in range(3):
            group["joint"][t[0]][j] += out[j]
        tape_results[t] = cost, stops
    for n, group in groups.items():
        joint, count = group["joint"], group["count"]
        for j in range(3):
            assert sum(joint[j]) == sum(row[j] for row in joint) == F(count * n[j], 6)
            assert joint[j][j] == count * max(F(n[j], 3) - 1, F(0))
    laws = [
        (F(1, 3),) * 3,
        (F(1, 2), F(1, 3), F(1, 6)),
        (F(1, 2), F(1, 2), F(0)),
        (F(9, 10), F(1, 20), F(1, 20)),
        (F(1), F(0), F(0)),
    ]
    weighted = []
    for p in laws:
        expected, stop_mass = F(0), Counter()
        for t, (cost, stops) in tape_results.items():
            probability = F(1)
            for j in t:
                probability *= p[j]
            expected += probability * cost
            for h, mass in stops.items():
                stop_mass[h] += probability * mass
        e2 = p[0] * p[1] + p[0] * p[2] + p[1] * p[2]
        e3 = p[0] * p[1] * p[2]
        candidate = 4 + 2 * e2 - 2 * e2**2 + 10 * e3 - 4 * e2 * e3
        weighted.append(
            {
                "p": list(map(str, p)),
                "control_expected_calls": str(expected),
                "candidate_expected_calls": str(candidate),
                "candidate_saving_fraction": str(1 - candidate / expected),
                "stop_mass": {str(h): str(mass) for h, mass in sorted(stop_mass.items())},
            }
        )
    assert F(weighted[0]["control_expected_calls"]) >= F(386, 81), (
        "contradicts verified lower bound"
    )
    result = {
        "status": "PASS",
        "scope": "complete own adaptation of classical count-polynomial exact short circuiting",
        "published_package_executed": False,
        "named_tapes": len(tape_results),
        "named_multisets": len(groups),
        "cdf_endpoints": list(map(str, endpoints)),
        "uniform_cells": len(cells),
        "operational_replays": len(cells) * len(tape_results),
        "transcript_nodes": nodes,
        "prepared_prefix_states": len(intervals),
        "weighted_laws": weighted,
        "neural_forwards": 0,
        "timing_measured": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
