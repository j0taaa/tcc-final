"""Independent named-tape, original-identity, matching and cost-polynomial audit."""

from __future__ import annotations

import argparse
import json
import runpy
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def matchings(indices: tuple[int, ...]) -> list[tuple[tuple[int, int], ...]]:
    if not indices:
        return [()]
    first, tail = indices[0], indices[1:]
    return [
        ((first, partner), *rest)
        for partner in tail
        for rest in matchings(tuple(i for i in tail if i != partner))
    ]


def multiply(a: dict, b: dict) -> dict:
    out: Counter = Counter()
    for u, c in a.items():
        for v, d in b.items():
            out[tuple(x + y for x, y in zip(u, v, strict=True))] += c * d
    return {u: c for u, c in out.items() if c}


def power(a: dict, n: int) -> dict:
    out = {(0, 0, 0): 1}
    for _ in range(n):
        out = multiply(out, a)
    return out


def linear(*terms: tuple[int, dict]) -> dict:
    out: Counter = Counter()
    for c, p in terms:
        for n, d in p.items():
            out[n] += c * d
    return {n: c for n, c in out.items() if c}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("policy", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cert = json.loads(args.certificate.read_text())
    policy = json.loads(args.policy.read_text())
    module = runpy.run_path(str(Path(__file__).with_name("reference.py")))
    assert module["ACTIONS"] == policy["key_actions"]
    couple = module["couple"]
    primal = {v: F(a) for v, a in cert["primal"].items()}
    mats = matchings(tuple(range(6)))
    assert len(mats) == 15
    groups = defaultdict(
        lambda: {
            "actual": [[F(0)] * 3 for _ in range(3)],
            "matching": [[F(0)] * 3 for _ in range(3)],
            "count": 0,
        }
    )
    cost_coeff, stop_coeff = Counter(), {4: Counter(), 5: Counter(), 6: Counter()}
    transcripts, nodes = [], 0
    for t in product(range(3), repeat=6):
        payloads = [
            {"key": a, "original_index": i, "raw_alias": bytes((i, a))} for i, a in enumerate(t)
        ]
        calls = 0

        def draw(sequence: list[dict] = payloads) -> dict:
            nonlocal calls
            assert calls < 6, "requested a seventh payload"
            out = sequence[calls]
            calls += 1
            return out

        first, second, spent = couple(draw, lambda p: p["key"])
        assert first is payloads[0] and spent == calls
        assert any(second is payloads[i] for i in range(1, spent)), "not a nonfirst original"
        seen, prefix = {}, ""
        observed_flow = []
        for h, a in enumerate(t, start=1):
            prefix += seen.setdefault(a, str(len(seen)))
            for native, anonymous in seen.items():
                mass = primal.get(prefix + ":" + anonymous, F(0))
                if mass:
                    observed_flow.append((h, native, mass))
        assert observed_flow == [(spent, second["key"], F(1))], (
            "operational law differs from primal"
        )
        assert spent in (4, 5, 6)
        n = tuple(t.count(j) for j in range(3))
        group = groups[n]
        group["count"] += 1
        group["actual"][t[0]][second["key"]] += 1
        repeats = [sum(t[i] == t[j] for i, j in m) for m in mats]
        optimal = [m for m, r in zip(mats, repeats, strict=True) if r == min(repeats)]
        for m in optimal:
            partner = next(j if i == 0 else i for i, j in m if i == 0 or j == 0)
            group["matching"][t[0]][t[partner]] += F(1, len(optimal))
        cost_coeff[n] += spent
        stop_coeff[spent][n] += 1
        transcripts.append((t, spent, second["key"]))
        nodes += calls + len(mats)
        assert nodes <= 1_000_000, "declared transcript guard"
    ordered_mismatches = []
    for n, group in groups.items():
        a, b, count = group["actual"], group["matching"], group["count"]
        for i in range(3):
            assert sum(a[i]) == sum(b[i]) == F(count * n[i], 6)
            assert sum(row[i] for row in a) == sum(row[i] for row in b) == F(count * n[i], 6)
            assert a[i][i] == b[i][i] == count * max(F(n[i], 3) - 1, F(0))
            for j in range(3):
                assert a[i][j] + a[j][i] == b[i][j] + b[j][i], "symmetric law mismatch"
        if a != b:
            ordered_mismatches.append(n)

    # Polynomial identities after homogenization to total degree six. The
    # left side comes only from actual callback executions, not the LP builder.
    s = {(1, 0, 0): 1, (0, 1, 0): 1, (0, 0, 1): 1}
    e2 = {(1, 1, 0): 1, (1, 0, 1): 1, (0, 1, 1): 1}
    e3 = {(1, 1, 1): 1}
    u = multiply(e2, power(s, 4))
    v = multiply(power(e2, 2), power(s, 2))
    w = multiply(e3, power(s, 3))
    z = multiply(multiply(e2, e3), s)
    assert dict(cost_coeff) == linear((4, power(s, 6)), (2, u), (-2, v), (10, w), (-4, z))
    assert dict(stop_coeff[4]) == linear((1, power(s, 6)), (-2, u), (4, v), (-10, w))
    assert dict(stop_coeff[5]) == linear((2, u), (-6, v), (10, w), (4, z))
    laws = [
        (F(1, 3),) * 3,
        (F(1, 2), F(1, 3), F(1, 6)),
        (F(1, 2), F(1, 2), F(0)),
        (F(9, 10), F(1, 20), F(1, 20)),
        (F(1), F(0), F(0)),
    ]
    weighted = []
    for p in laws:
        joint = [[F(0)] * 3 for _ in range(3)]
        stop = Counter()
        for t, spent, j in transcripts:
            weight = F(1)
            for i in t:
                weight *= p[i]
            joint[t[0]][j] += weight
            stop[spent] += weight
        expected = sum((n * mass for n, mass in stop.items()), F(0))
        q = p[0] * p[1] + p[0] * p[2] + p[1] * p[2]
        r = p[0] * p[1] * p[2]
        assert expected == 4 + 2 * q - 2 * q * q + 10 * r - 4 * q * r <= F(386, 81)
        for i in range(3):
            assert sum(joint[i]) == sum(row[i] for row in joint) == p[i]
            assert joint[i][i] == 5 * p[i] ** 4 - 6 * p[i] ** 5 + 2 * p[i] ** 6
        weighted.append(
            {
                "p": list(map(str, p)),
                "stop_mass": {str(n): str(mass) for n, mass in sorted(stop.items())},
                "expected_calls": str(expected),
            }
        )
    result = {
        "status": "PASS",
        "named_full_tapes": len(transcripts),
        "named_multisets": len(groups),
        "perfect_matchings_per_tape": len(mats),
        "transcript_nodes": nodes,
        "policy_rows_by_depth": {
            str(h): sum(len(s) == h for s in module["ACTIONS"]) for h in (4, 5, 6)
        },
        "ordered_law_mismatch_multisets": [list(n) for n in ordered_mismatches],
        "symmetric_law_all_multisets": "exact equality",
        "homogeneous_cost_and_two_stop_identities": "all exact degree-six coefficients",
        "weighted_laws": weighted,
        "neural_forwards": 0,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
