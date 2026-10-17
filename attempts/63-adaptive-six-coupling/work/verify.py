"""Independent stdlib-only named-tape and dual verifier; never import the LP builder."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction as F
from itertools import product
from math import comb
from pathlib import Path


def pattern(t: tuple[int, ...]) -> tuple[str, dict[int, int]]:
    labels: dict[int, int] = {}
    for a in t:
        labels.setdefault(a, len(labels))
    return "".join(str(labels[a]) for a in t), labels


def verify(certificate: dict) -> dict:
    cap = certificate["cap"]
    assert cap in (4, 5, 6, 7), "unsupported cap"
    freq = {}
    states = set()
    for h in range(1, cap + 1):
        freq[h] = Counter(pattern(t)[0] for t in product(range(3), repeat=h))
        states.update(freq[h])
    expected = {s + ":" + a for s in states for a in set(s[1:])}
    assert set(certificate["primal"]) == expected, "wrong variable domain"
    x = {v: F(a) for v, a in certificate["primal"].items()}
    assert all(a >= 0 for a in x.values()), "negative primal flow"
    groups = defaultdict(list)
    uniform_cost = F(0)

    def variables(t: tuple[int, ...], j: int) -> list[str]:
        answer = []
        for h in range(1, cap + 1):
            s, labels = pattern(t[:h])
            if j in t[1:h]:
                answer.append(s + ":" + str(labels[j]))
        return answer

    for t in product(range(3), repeat=cap):
        out = [F(0)] * 3
        spent, stopped = F(0), F(0)
        for h in range(1, cap + 1):
            s, labels = pattern(t[:h])
            mass = F(0)
            for actual, anonymous in labels.items():
                name = s + ":" + str(anonymous)
                if name in x:
                    out[actual] += x[name]
                    mass += x[name]
            assert stopped + mass <= 1, "stopping mass exceeds reach"
            stopped += mass
            spent += h * mass
        assert stopped == 1, "not stopped by declared cap"
        groups[tuple(t.count(j) for j in range(3))].append((t, out))
        uniform_cost += spent / (3**cap)
    for n, tapes in groups.items():
        for j in range(3):
            marg = sum((out[j] for _, out in tapes), F(0))
            diag = sum((out[j] for t, out in tapes if t[0] == j), F(0))
            assert marg == len(tapes) * F(n[j], cap), "universal marginal coefficient"
            assert diag == len(tapes) * max(F(2 * n[j], cap) - 1, F(0)), "atom optimum coefficient"

    # Rebuild all dual rows independently, using actual named tapes rather than
    # the producer's restricted-growth recursion/permutation profile builder.
    ub_expected = {"flow:" + s for s in states if len(s) < cap}
    profiles = sorted(
        {tuple(c for c in n if c) for n in groups if tuple(sorted(n, reverse=True)) == n},
        reverse=True,
    )
    eq_expected = {"end:" + s for s in states if len(s) == cap}
    for n in profiles:
        for j in range(len(n)):
            eq_expected |= {
                tag + ":" + ",".join(map(str, n)) + ":" + str(j) for tag in ("marg", "diag")
            }
    assert set(certificate["dual_ub"]) == ub_expected, "wrong inequality dual domain"
    assert set(certificate["dual_eq"]) == eq_expected, "wrong equality dual domain"
    at = {v: F(0) for v in expected}
    dual_cost = F(cap)
    multipliers = certificate["dual_ub"] | certificate["dual_eq"]
    for name, value in multipliers.items():
        a = F(value)
        if name.startswith(("flow:", "end:")):
            if name.startswith("flow:"):
                assert a <= 0, "wrong inequality dual sign"
            s = name.split(":")[1]
            dual_cost += a
            for v in expected:
                pref = v.split(":")[0]
                if s.startswith(pref):
                    at[v] += a
        else:
            kind, profile, label = name.split(":")
            n = tuple(map(int, profile.split(",")))
            j = int(label)
            tapes = groups[n + (0,) * (3 - len(n))]
            rhs = len(tapes) * (F(n[j], cap) if kind == "marg" else max(F(2 * n[j], cap) - 1, F(0)))
            dual_cost += a * rhs
            for t, _ in tapes:
                if kind == "marg" or t[0] == j:
                    for v in variables(t, j):
                        at[v] += a
    for v in expected:
        s = v.split(":")[0]
        c = -(cap - len(s)) * F(freq[len(s)][s], 3 ** len(s))
        assert at[v] <= c, "dual reduced-cost inequality"
    assert dual_cost == uniform_cost, "nonzero exact primal/dual gap"

    # Independent weighted enumeration of the unconditioned key pair law.
    laws = [
        (F(1, 3),) * 3,
        (F(1, 2), F(1, 3), F(1, 6)),
        (F(1, 2), F(1, 2), F(0)),
        (F(9, 10), F(1, 20), F(1, 20)),
        (F(1), F(0), F(0)),
    ]
    for p in laws:
        joint = [[F(0)] * 3 for _ in range(3)]
        for tapes in groups.values():
            for t, out in tapes:
                w = F(1)
                for a in t:
                    w *= p[a]
                for j in range(3):
                    joint[t[0]][j] += w * out[j]
        for j in range(3):
            assert sum(joint[j]) == p[j]
            assert sum(row[j] for row in joint) == p[j]
            bound = sum(
                (
                    comb(cap, r)
                    * p[j] ** r
                    * (1 - p[j]) ** (cap - r)
                    * max(F(2 * r, cap) - 1, F(0))
                    for r in range(cap + 1)
                ),
                F(0),
            )
            assert joint[j][j] == bound
    regression = {4: F(31, 9), 6: F(386, 81)}.get(cap)
    if regression is not None:
        assert uniform_cost == regression, "known fair-point regression"
    return {
        "status": "VERIFIED",
        "cap": cap,
        "named_full_tapes": 3**cap,
        "named_multisets": len(groups),
        "variables": len(expected),
        "uniform_expected_calls": str(uniform_cost),
        "exact_dual_bound": str(dual_cost),
        "weighted_laws": len(laws),
        "neural_forwards": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cert = json.loads(args.certificate.read_text())
    result = verify(cert)
    corruptions = []
    for part in ("primal", "dual_eq"):
        bad = deepcopy(cert)
        name = next(iter(bad[part]))
        bad[part][name] = str(F(bad[part][name]) + 1)
        try:
            verify(bad)
        except AssertionError:
            corruptions.append(part)
        else:
            raise AssertionError("corrupt certificate was accepted")
    result["corruptions_rejected"] = corruptions
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
