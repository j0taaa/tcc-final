"""Exact complete random-anchor empirical-rank controls; no model or timing."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import permutations, product
from pathlib import Path


def position_order(anchor: int, mode: str) -> tuple[int, ...]:
    if mode == "ascending":
        return (anchor, *(i for i in range(6) if i != anchor))
    assert mode == "cyclic"
    return tuple((anchor + i) % 6 for i in range(6))


def full_partner(t: tuple[int, ...], anchor: int, mode: str) -> int:
    order = position_order(anchor, mode)
    position_key = dict(zip(order, t, strict=True))
    ranked = sorted(range(6), key=lambda i: (position_key[i], i))
    mate = ranked[(ranked.index(anchor) + 3) % 6]
    assert mate != anchor
    return position_key[mate]


def prepare() -> dict:
    possible = defaultdict(set)
    for mode in ("ascending", "cyclic"):
        for anchor in range(6):
            for t in product(range(3), repeat=6):
                j = full_partner(t, anchor, mode)
                for h in range(1, 7):
                    possible[mode, anchor, t[:h]].add(j)
    return dict(possible)


def couple(draw, key, anchor: int, mode: str, possible: dict) -> tuple:
    payloads, keys = [], ()
    for _ in range(6):
        value = draw()
        actual = key(value)
        if actual not in (0, 1, 2):
            raise ValueError("Three fixed labels required.")
        payloads.append(value)
        keys += (actual,)
        allowed = possible[mode, anchor, keys]
        if len(allowed) == 1:
            chosen = next(iter(allowed))
            indices = [i for i in range(1, len(keys)) if keys[i] == chosen]
            if indices:
                return payloads[0], payloads[indices[0]], len(payloads)
    raise AssertionError("No partner by six queries.")


def primal_output(t: tuple[int, ...], x: dict) -> tuple[F, ...]:
    seen, s, out = {}, "", [F(0)] * 3
    for actual in t:
        s += seen.setdefault(actual, str(len(seen)))
        for label, anonymous in seen.items():
            out[label] += x.get(s + ":" + anonymous, F(0))
    assert sum(out) == 1
    return tuple(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cert_path = Path(__file__).parent / "evidence/v3/cap6/certificate.json"
    x = {name: F(v) for name, v in json.loads(cert_path.read_text())["primal"].items()}
    possible = prepare()
    # Independent perfect-matching enumeration by all position permutations,
    # rather than either earlier recursive matching builder.
    matchings = {
        tuple(sorted(tuple(sorted(p[h : h + 2])) for h in range(0, 6, 2)))
        for p in permutations(range(6))
    }
    assert len(matchings) == 15

    def matrix() -> list:
        return [[F(0)] * 3 for _ in range(3)]

    groups = defaultdict(
        lambda: {name: matrix() for name in ("matching", "candidate", "ascending", "cyclic")}
    )
    costs = {name: {} for name in ("ascending", "cyclic")}
    stops = {name: {} for name in costs}
    replay_count, nodes = 0, 0
    for t in product(range(3), repeat=6):
        n = tuple(t.count(j) for j in range(3))
        group = groups[n]
        raw = [{"key": j, "index": i, "raw_alias": bytes((i, j))} for i, j in enumerate(t)]
        q = primal_output(t, x)
        for j in range(3):
            group["candidate"][t[0]][j] += q[j]
        best_loss = min(sum(t[i] == t[j] for i, j in m) for m in matchings)
        best = [m for m in matchings if sum(t[i] == t[j] for i, j in m) == best_loss]
        for m in best:
            mate = next(j if i == 0 else i for i, j in m if 0 in (i, j))
            group["matching"][t[0]][t[mate]] += F(1, len(best))
        for mode in costs:
            spent_mean, stop_mass = F(0), Counter()
            for anchor in range(6):
                calls = 0

                def draw(sequence: list[dict] = raw) -> dict:
                    nonlocal calls
                    assert calls < 6
                    item = sequence[calls]
                    calls += 1
                    return item

                first, second, spent = couple(draw, lambda a: a["key"], anchor, mode, possible)
                assert first is raw[0] and calls == spent
                assert any(second is raw[i] for i in range(1, spent))
                assert second["key"] == full_partner(t, anchor, mode)
                group[mode][t[0]][second["key"]] += F(1, 6)
                spent_mean += F(spent, 6)
                stop_mass[spent] += F(1, 6)
                replay_count += 1
                nodes += spent
                assert nodes <= 1_000_000, "declared replay guard"
            costs[mode][t] = spent_mean
            stops[mode][t] = stop_mass
    for group in groups.values():
        assert group["candidate"] == group["matching"]
        for mode in costs:
            assert group[mode] == group["matching"], "full ordered multiset law mismatch"
    laws = [
        (F(1, 3),) * 3,
        (F(1, 2), F(1, 3), F(1, 6)),
        (F(1, 2), F(1, 2), F(0)),
        (F(9, 10), F(1, 20), F(1, 20)),
        (F(1), F(0), F(0)),
    ]
    reports = []
    for mode in costs:
        weighted = []
        for p in laws:
            mean, stop = F(0), Counter()
            for t, spent in costs[mode].items():
                weight = F(1)
                for j in t:
                    weight *= p[j]
                mean += weight * spent
                for h, mass in stops[mode][t].items():
                    stop[h] += weight * mass
            e2 = p[0] * p[1] + p[0] * p[2] + p[1] * p[2]
            e3 = p[0] * p[1] * p[2]
            candidate = 4 + 2 * e2 - 2 * e2**2 + 10 * e3 - 4 * e2 * e3
            weighted.append(
                {
                    "p": list(map(str, p)),
                    "control_expected_calls": str(mean),
                    "candidate_expected_calls": str(candidate),
                    "candidate_saving_fraction": str(1 - candidate / mean),
                    "stop_mass": {str(h): str(mass) for h, mass in sorted(stop.items())},
                }
            )
        assert F(weighted[0]["control_expected_calls"]) >= F(386, 81)
        reports.append({"query_order": mode, "weighted_laws": weighted})
    result = {
        "status": "PASS",
        "operational_replays": replay_count,
        "transcript_read_nodes": nodes,
        "prepared_prefix_states": len(possible),
        "named_multisets": len(groups),
        "full_ordered_multiset_laws": "exact equality for both controls, candidate, matching",
        "methods": reports,
        "neural_forwards": 0,
        "timing_measured": False,
        "published_package_executed": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
