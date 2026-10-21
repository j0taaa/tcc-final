"""Multiple-probe finite oracle; freeze this source/protocol before --audit.

Protocol: k=1..4 on the same 15 nonempty 2x2 graphs, three rational actual
tables and six forecasts as online_probe.py (including its equality table).
Enumerate every ordered iid-uniform head sequence WITH replacement exactly.
Check both expected bounds, perfect-arc per-run consistency, frozen k=1
equivalence, independent certificates, four-cut OPT and all 16 subsets.
Also high/low r=4,n=2 disjoint stars at k=2, enumerating all 8**2 sequences.
No PRNG, neural queries, timing, performance or priority claim.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import product

from online_probe import (
    Arcs,
    F,
    Fixture,
    Problem,
    Query,
    Result,
    bad_arcs,
    min_cover,
    probe_policy,
)


def multiple_probe_policy(
    p: Problem, predicted: Arcs, query: Query, k: int, selected: tuple[int, ...]
) -> Result:
    """Only the selected head's fixed witness may reject advice.

    All k choices are supplied before queries. Stop probing on the first failed
    selected witness; collateral errors in a returned vector are not inspected.
    The frozen one-probe completion receives a memoized callback, so its local
    cache need not know every earlier probe and no oracle query is repeated.
    """
    directed = {(a, b) for a, b in p.graph()} | {(b, a) for a, b in p.graph()}
    heads = {b for _, b in predicted}
    if type(k) is not int or k < 1 or not predicted <= directed:
        raise ValueError("positive k and public threatening-edge arcs required")
    if (heads and (len(selected) != k or not set(selected) <= heads)) or (not heads and selected):
        raise ValueError("supply k predicted heads, or an empty sequence for no arcs")
    cache: dict[int, dict[int, F]] = {}
    order: list[int] = []

    def acquire(z: int) -> dict[int, F]:
        if z not in cache:
            answer = dict(query(z))
            incident = {i for i, edge in enumerate(p.edges) if z in edge}
            if (
                set(answer) != incident
                or any(not isinstance(x, F) or not 0 < x < p.caps[z] for x in answer.values())
                or sum(answer.values(), F(0)) >= p.caps[z]
            ):
                raise ValueError("oracle violated positive normalized star contract")
            cache[z] = answer
            order.append(z)
        return cache[z]

    accepted = True if heads else None
    for target in selected:
        source = min(a for a, b in predicted if b == target)
        edge = next(i for i, ends in enumerate(p.edges) if set(ends) == {source, target})
        if acquire(source)[edge] + p.caps[target] <= p.tau:
            accepted = False
            break
    completion = probe_policy(
        p, predicted if accepted else frozenset(), acquire, selected[0] if accepted else None
    )
    assert not accepted or completion.accepted
    return Result(tuple(order), selected[0] if selected else None, accepted)


def robustness_constant(k: int) -> F:
    if k < 1:
        raise ValueError("positive k required")
    return F(1) if k == 1 else F(1, k) * F(k - 1, 2 * k) ** (k - 1)


def audit() -> dict[str, object]:
    counts: Counter[str] = Counter()

    def check(data: Fixture, forecasts: list[Arcs], ks: tuple[int, ...]) -> list[F]:
        data.validate()
        p = data.problem
        optimum = data.reference_optimum()
        if len(p.caps) == 4:
            assert optimum == data.brute_optimum(counts)
        actual = bad_arcs(p, data.values)
        mandatory = {b for _, b in actual}
        assert len(min_cover(p) | mandatory) <= 2 * optimum
        means = []
        for predicted in forecasts:
            heads = sorted({b for _, b in predicted})
            false, missed = len(set(heads) - mandatory), len(mandatory - set(heads))
            bad_witnesses = 0
            for target in heads:
                source = min(a for a, b in predicted if b == target)
                edge = next(i for i, ends in enumerate(p.edges) if set(ends) == {source, target})
                value = data.values[edge][int(source == p.edges[edge][1])]
                bad_witnesses += value + p.caps[target] <= p.tau
            for k in ks:
                total, runs, accepted_runs = 0, 0, 0
                sequences = product(heads, repeat=k) if heads else [()]
                for selected in sequences:
                    calls: list[int] = []

                    def query(z: int, seen: list[int] = calls) -> dict[int, F]:
                        assert z not in seen
                        seen.append(z)
                        return data.query(z)

                    result = multiple_probe_policy(p, predicted, query, k, selected)
                    assert result.queries == tuple(calls)
                    assert data.independent_certificate(frozenset(calls))
                    if predicted == actual:
                        assert len(calls) <= optimum + k
                    if k == 1:
                        direct = probe_policy(
                            p, predicted, data.query, selected[0] if heads else None
                        )
                        assert result == direct
                    total += len(calls)
                    accepted_runs += result.accepted is True
                    runs += 1
                assert runs == (len(heads) ** k if heads else 1)
                mean = F(total, runs)
                assert mean <= (2 + robustness_constant(k)) * optimum + k
                assert mean <= optimum + k + false + missed + k * bad_witnesses
                if heads:
                    assert F(accepted_runs, runs) == F(len(heads) - bad_witnesses, len(heads)) ** k
                means.append(mean)
                counts["policy_runs"] += runs
                counts["forecast_k_cases"] += 1
        counts["instances"] += 1
        return means

    cap = F(1, 32)
    all_pairs = tuple(product(range(2), range(2, 4)))
    for mask in range(1, 16):
        edges = tuple(edge for i, edge in enumerate(all_pairs) if mask >> i & 1)
        p = Problem(2, (cap,) * 4, edges, 9 * cap / 8)
        tables = [
            tuple(
                (
                    cap / 4
                    if pattern == 1 or (pattern == 2 and (a + b) % 2 == 0)
                    else cap / (8 if pattern == 0 else 16),
                    cap / 4
                    if pattern == 2 and (a + b) % 2 == 1
                    else cap / (8 if pattern == 0 else 16),
                )
                for a, b in edges
            )
            for pattern in range(3)
        ]
        all_arcs = frozenset((x, y) for a, b in edges for x, y in ((a, b), (b, a)))
        for values in tables:
            forecasts = [bad_arcs(p, table) for table in tables]
            forecasts += [all_arcs, frozenset(), all_arcs - bad_arcs(p, values)]
            check(Fixture(p, values), forecasts, (1, 2, 3, 4))
    r, n = 4, 2
    cap = F(1, 4 * (r * n + 1))
    edges = tuple((a, r + a * n + j) for a in range(r) for j in range(n))
    p = Problem(r, (cap,) * (r + r * n), edges, (1 + F(1, 4 * n)) * cap)
    high = Fixture(p, ((cap / (2 * n), cap / (8 * n)),) * len(edges))
    forecast = bad_arcs(p, high.values)
    (perfect,) = check(high, [forecast], (2,))
    low = Fixture(p, ((cap / (8 * n), cap / (8 * n)),) * len(edges))
    (wrong,) = check(low, [forecast], (2,))
    assert high.reference_optimum() == r * n and low.reference_optimum() == r
    assert perfect == r * n + 2 - F(1, r) and wrong == r
    return {
        "protocol": "A87-multiple-probe-CPU-v1",
        "counts": dict(counts),
        "stars_r4_n2_k2": {"perfect": str(perfect), "wrong": str(wrong)},
        "scope": "finite rational correctness only; no neural/performance/priority claim",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="only after source/protocol freeze")
    if parser.parse_args().audit:
        print(json.dumps(audit(), sort_keys=True))
