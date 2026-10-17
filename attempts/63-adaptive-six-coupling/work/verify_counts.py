"""Independent count-flow dual and ALL named-tail Markov realization audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction as F
from itertools import product
from math import comb
from pathlib import Path


def ways(k: tuple[int, ...]) -> int:
    return comb(sum(k), k[0]) * comb(k[1] + k[2], k[1])


def coefficient(k: tuple[int, ...], cap: int) -> tuple[F, ...]:
    n0, n1, n2 = k[0] + 1, k[1], k[2]
    if 2 * n0 >= cap:
        return F(2 * n0 - cap, n0), F(n1, n0), F(n2, n0)
    if 2 * n1 >= cap:
        return F(0), F(1), F(0)
    if 2 * n2 >= cap:
        return F(0), F(0), F(1)
    return F(0), F(cap - 2 * n2, 2 * n0), F(cap - 2 * n1, 2 * n0)


def verify(cert: dict) -> dict:
    cap = cert["cap"]
    assert 4 <= cap <= 11
    domain = sorted(
        (k for k in product(range(cap), repeat=3) if sum(k) < cap), key=lambda k: (sum(k), k)
    )

    def label(kind: str, k: tuple[int, ...], j: int | None = None) -> str:
        suffix = ":" + str(j) if j is not None else ""
        return kind + ":" + ",".join(str(v) for v in k) + suffix

    variables = {label("c", k) for k in domain if sum(k) < cap - 1}
    variables |= {
        label(kind, k, j) for kind in ("a", "s") for k in domain for j in range(3) if k[j]
    }
    assert set(cert["primal"]) == variables
    x = {v: F(a) for v, a in cert["primal"].items()}
    assert all(a >= 0 for a in x.values())
    rows = [("root", {label("c", (0, 0, 0)): F(1)}, F(1))]
    parents = {}
    for k in domain[1:]:
        ps = []
        for ell in range(3):
            if k[ell]:
                parent = tuple(k[i] - int(i == ell) for i in range(3))
                ps.append((parent, F(ways(parent), ways(k))))
        parents[k] = ps
        flow = Counter({label("s", k, j): F(1) for j in range(3) if k[j]})
        if sum(k) < cap - 1:
            flow[label("c", k)] = F(1)
        for p, weight in ps:
            flow[label("c", p)] -= weight
        rows.append((label("flow", k), dict(flow), F(0)))
        for j in range(3):
            if not k[j]:
                continue
            row = {label("a", k, j): F(1), label("s", k, j): F(-1)}
            for p, weight in ps:
                if p[j]:
                    row[label("a", p, j)] = -weight
            rows.append((label("acc", k, j), row, F(0)))
        if sum(k) == cap - 1:
            q = coefficient(k, cap)
            for j in range(3):
                if k[j]:
                    rows.append((label("end", k, j), {label("a", k, j): F(1)}, q[j]))
                else:
                    assert q[j] == 0
    assert set(cert["dual"]) == {tag for tag, _, _ in rows}
    dual = {tag: F(v) for tag, v in cert["dual"].items()}
    objective = {v: F(0) for v in variables}
    for k in domain:
        if sum(k) < cap - 1:
            objective[label("c", k)] = F(ways(k), 3 ** sum(k))
    reduced = {v: F(0) for v in variables}
    lower_bound = F(1)
    for tag, row, rhs in rows:
        assert sum((x[v] * a for v, a in row.items()), F(0)) == rhs, "primal row"
        lower_bound += dual[tag] * rhs
        for v, a in row.items():
            reduced[v] += dual[tag] * a
    assert all(reduced[v] <= objective[v] for v in variables), "dual reduced cost"
    expected = 1 + sum((x[v] * c for v, c in objective.items()), F(0))
    assert expected == lower_bound, "nonzero exact gap"

    # Realize stop/continue probabilities along every NAMED tail order. Count
    # constraints alone cannot catch confusing normalized flow with reach.
    actions = {}
    for k, ps in parents.items():
        reach = sum((w * x[label("c", p)] for p, w in ps), F(0))
        stops = tuple(x.get(label("s", k, j), F(0)) for j in range(3))
        continued = x.get(label("c", k), F(0))
        assert sum(stops) + continued == reach
        actions[k] = (reach, stops, continued)
    groups = defaultdict(lambda: [F(0)] * 3)
    costs, operational_cost, steps = defaultdict(F), F(0), 0
    for t in product(range(3), repeat=cap - 1):
        k, alive, spent, out = [0, 0, 0], F(1), F(1), [F(0)] * 3
        for a in t:
            if not alive:
                break
            spent += alive
            k[a] += 1
            reach, stopped, continued = actions[tuple(k)]
            assert reach > 0, "an impossible state was reached"
            for j in range(3):
                out[j] += alive * stopped[j] / reach
            alive *= continued / reach
            steps += 1
            assert steps <= 1_000_000, "declared prefix guard"
        assert alive == 0 and sum(out) == 1
        final = tuple(t.count(j) for j in range(3))
        for j in range(3):
            groups[final][j] += out[j]
        costs[final] += spent
        operational_cost += spent / (3 ** (cap - 1))
    for k, out in groups.items():
        q = coefficient(k, cap)
        assert all(out[j] == ways(k) * q[j] for j in range(3)), "terminal ordered-law coefficient"
    assert operational_cost == expected
    known = {4: F(31, 9), 5: F(31, 9), 6: F(386, 81), 7: F(386, 81)}
    if cap in known:
        assert expected == known[cap], "known full-history optimum regression"

    laws = [
        (F(1, 3),) * 3,
        (F(1, 2), F(1, 3), F(1, 6)),
        (F(1, 2), F(1, 2), F(0)),
        (F(9, 10), F(1, 20), F(1, 20)),
        (F(1), F(0), F(0)),
    ]
    weighted = []
    for p in laws:
        work = F(0)
        for first in range(3):
            remaining = [j for j in range(3) if j != first]
            for mapping in ((first, *remaining), (first, *remaining[::-1])):
                for k, total_cost in costs.items():
                    w = p[first] / 2
                    for j in range(3):
                        w *= p[mapping[j]] ** k[j]
                    work += w * total_cost
        weighted.append({"p": list(map(str, p)), "symmetric_policy_expected_calls": str(work)})
    return {
        "status": "VERIFIED",
        "cap": cap,
        "scope": "exact full ordered target law at U3, not unproved all-P minimax",
        "count_states": len(domain),
        "variables": len(variables),
        "rows": len(rows),
        "named_tail_words_first0": 3 ** (cap - 1),
        "terminal_count_groups": len(groups),
        "operational_prefix_steps": steps,
        "exact_primal_cost": str(expected),
        "exact_dual_bound": str(lower_bound),
        "weighted_laws": weighted,
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
    for part in ("primal", "dual"):
        bad = deepcopy(cert)
        v = next(iter(bad[part]))
        bad[part][v] = str(F(bad[part][v]) + 1)
        try:
            verify(bad)
        except AssertionError:
            corruptions.append(part)
        else:
            raise AssertionError("corrupt certificate accepted")
    result["corruptions_rejected"] = corruptions
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
