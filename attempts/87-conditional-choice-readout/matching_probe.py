"""Matching-guided one-probe reference; freeze source/protocol before --audit.

Protocol: all 15 nonempty 2x2 graphs, every actual directed-arc subset and
every forecast subset; high=cap/4, low=cap/16, cap=1/32, tau=9cap/8.
Enumerate all uniform R choices exactly. Check expected cost <=2OPT, perfect
cost <=OPT+1, independent certificates and all 16 subsets versus four cuts.
Also the frozen r=1,2,4,8 stars with n=2,3 leaves, high/low actual tables and
high/actual/empty forecasts (coincident entries retained). Check an internal P edge
with R empty and an augmentation that replaces an initial matching edge.
Positive normalized stars and a true strict fixed threshold are required.
No neural queries, measurements, unknown-incumbent or priority claim.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from functools import cache
from itertools import product

from online_probe import Arcs, F, Fixture, Pair, Problem, Query, Result, bad_arcs, min_cover


def maximum_matching(edges: tuple[Pair, ...], n_a: int, initial: Arcs = frozenset()) -> Arcs:
    """Deterministic augmenting paths; retain every initially matched vertex."""
    left, right = dict(initial), {b: a for a, b in initial}
    if len(left) != len(initial) or len(right) != len(initial) or not initial <= set(edges):
        raise ValueError("initial edges must form a matching in the supplied graph")
    neighbors = {a: sorted(b for x, b in edges if x == a) for a in range(n_a)}

    def augment(a: int, seen: set[int]) -> bool:
        for b in neighbors[a]:
            if b in seen:
                continue
            seen.add(b)
            if b not in right or augment(right[b], seen):
                left[a], right[b] = b, a
                return True
        return False

    while True:
        if not any(a not in left and augment(a, set()) for a in range(n_a)):
            return frozenset(left.items())


@dataclass(frozen=True)
class Plan:
    heads: frozenset[int]
    pred_cover: frozenset[int]
    prediction: frozenset[int]
    base: frozenset[int]
    initial: Arcs
    matching: Arcs
    unmatched: frozenset[int]


@cache
def prepare(p: Problem, predicted: Arcs) -> Plan:
    """Cache only public topology/caps/threshold and fixed forecast arcs."""
    edges = p.graph()
    directed = {(x, y) for a, b in edges for x, y in ((a, b), (b, a))}
    if not predicted <= directed:
        raise ValueError("predicted witnesses must be adjacent threatening-edge endpoints")
    heads = frozenset(b for _, b in predicted)
    pred_cover = min_cover(p, heads)
    residual = tuple((a, b) for a, b in edges if a not in heads and b not in heads)
    initial = maximum_matching(residual, p.n_a)
    matching = maximum_matching(edges, p.n_a, initial)
    matched = frozenset(z for edge in matching for z in edge)
    prediction = heads | pred_cover
    return Plan(
        heads, pred_cover, prediction, min_cover(p), initial, matching, prediction - matched
    )


def matching_probe_policy(
    p: Problem, predicted: Arcs, query: Query, selected: int | None
) -> Result:
    """Supply selected uniformly from R externally, or None exactly when R is empty."""
    plan = prepare(p, predicted)
    if (plan.unmatched and selected not in plan.unmatched) or (
        not plan.unmatched and selected is not None
    ):
        raise ValueError("select one unmatched predicted head, or None when R is empty")
    answers: dict[int, dict[int, F]] = {}
    order: list[int] = []

    def acquire(z: int) -> None:
        if z in answers:
            return
        vector = dict(query(z))
        incident = {i for i, ends in enumerate(p.edges) if z in ends}
        if (
            set(vector) != incident
            or any(not isinstance(x, F) or not 0 < x < p.caps[z] for x in vector.values())
            or sum(vector.values(), F(0)) >= p.caps[z]
        ):
            raise ValueError("oracle violated positive normalized star contract")
        answers[z] = vector
        order.append(z)

    def active() -> list[int]:
        result = []
        for i, ends in enumerate(p.edges):
            upper = sum((answers[z][i] if z in answers else p.caps[z] for z in ends), F(0))
            if all(z in answers for z in ends) and upper >= p.tau:
                raise ValueError("false strict fixed-threshold promise")
            if upper > p.tau:
                result.append(i)
        return result

    def force() -> None:
        while True:
            pending = [set(p.edges[i]) - answers.keys() for i in active()]
            target = next((next(iter(unknown)) for unknown in pending if len(unknown) == 1), None)
            if target is None:
                return
            acquire(target)

    accepted = None
    if selected is not None:
        source = min(a for a, b in predicted if b == selected)
        assert source in plan.base
        acquire(source)
        edge = next(i for i, ends in enumerate(p.edges) if set(ends) == {source, selected})
        accepted = answers[source][edge] + p.caps[selected] > p.tau
    force()
    chosen = plan.prediction if accepted is not False else plan.base
    for z in sorted(chosen):
        if z not in answers and any(z in p.edges[i] for i in active()):
            acquire(z)
            force()
    if active():
        raise ValueError("chosen cover did not certify the threshold")
    return Result(tuple(order), selected, accepted)


def audit() -> dict[str, object]:
    counts: Counter[str] = Counter()

    def public(p: Problem, advice: Arcs) -> Plan:
        plan = prepare(p, advice)
        for matching in (plan.initial, plan.matching):
            assert matching <= set(p.graph())
            assert len({a for a, _ in matching}) == len(matching) == len({b for _, b in matching})
        matched0 = {z for edge in plan.initial for z in edge}
        matched = {z for edge in plan.matching for z in edge}
        assert len(plan.initial) == len(plan.pred_cover) and plan.pred_cover <= matched0 <= matched
        assert len(plan.matching) == len(plan.base)
        assert plan.unmatched <= plan.heads and not plan.unmatched & plan.base
        assert all(a in plan.base for a, b in advice if b in plan.unmatched)
        assert all(a in plan.prediction or b in plan.prediction for a, b in p.graph())
        counts["public_plans"] += 1
        return plan

    def check(data: Fixture, forecasts: tuple[Arcs, ...], plans: dict[Arcs, Plan]) -> list[F]:
        data.validate()
        p, optimum = data.problem, data.reference_optimum()
        if len(p.caps) == 4:
            assert optimum == data.brute_optimum(counts)
        actual, means = bad_arcs(p, data.values), []
        for advice in forecasts:
            plan, costs = plans[advice], []
            passed = 0
            for selected in sorted(plan.unmatched) or [None]:
                calls: list[int] = []

                def query(z: int, seen: list[int] = calls) -> dict[int, F]:
                    assert z not in seen
                    seen.append(z)
                    return data.query(z)

                result = matching_probe_policy(p, advice, query, selected)
                assert result.queries == tuple(calls)
                assert data.independent_certificate(frozenset(calls))
                if advice == actual:
                    assert len(calls) <= optimum + bool(plan.unmatched)
                passed += result.accepted is True
                assert plan.unmatched or result.accepted is None
                costs.append(len(calls))
                counts["policy_runs"] += 1
            expected = sum(
                (min(a for a, b in advice if b == target), target) in actual
                for target in plan.unmatched
            )
            assert F(passed, len(costs)) == (
                F(expected, len(plan.unmatched)) if plan.unmatched else 0
            )
            mean = F(sum(costs), len(costs))
            assert mean <= 2 * optimum
            means.append(mean)
            counts["forecast_cases"] += 1
        counts["instances"] += 1
        return means

    cap, all_pairs = F(1, 32), tuple(product(range(2), range(2, 4)))
    for mask in range(1, 16):
        edges = tuple(edge for i, edge in enumerate(all_pairs) if mask >> i & 1)
        p = Problem(2, (cap,) * 4, edges, 9 * cap / 8)
        directed = tuple(arc for a, b in edges for arc in ((a, b), (b, a)))
        forecasts = tuple(
            frozenset(arc for j, arc in enumerate(directed) if bits >> j & 1)
            for bits in range(1 << len(directed))
        )
        plans = {advice: public(p, advice) for advice in forecasts}
        for actual in forecasts:
            values = tuple(
                (cap / (4 if (a, b) in actual else 16), cap / (4 if (b, a) in actual else 16))
                for a, b in edges
            )
            assert bad_arcs(p, values) == actual
            check(Fixture(p, values), forecasts, plans)
    stars = []
    for r, n in product((1, 2, 4, 8), (2, 3)):
        cap = F(1, 4 * (r * n + 1))
        edges = tuple((a, r + a * n + j) for a in range(r) for j in range(n))
        p = Problem(r, (cap,) * (r + r * n), edges, (1 + F(1, 4 * n)) * cap)
        high = Fixture(p, ((cap / (2 * n), cap / (8 * n)),) * len(edges))
        low = Fixture(p, ((cap / (8 * n), cap / (8 * n)),) * len(edges))
        advice = bad_arcs(p, high.values)
        empty = frozenset()
        plans = {forecast: public(p, forecast) for forecast in (advice, empty)}
        high_means = check(high, (advice, advice, empty), plans)
        low_means = check(low, (advice, bad_arcs(p, low.values), empty), plans)
        assert high_means == [F(r * n + 1)] * 2 + [F(r * n + r)]
        assert low_means == [F(r)] * 3
        stars.append(
            {
                "r": r,
                "n": n,
                "high": [str(x) for x in high_means],
                "low": [str(x) for x in low_means],
            }
        )
    cap = F(1, 32)
    single = Problem(1, (cap,) * 2, ((0, 1),), 9 * cap / 8)
    internal = public(single, frozenset(((0, 1), (1, 0))))
    assert not internal.unmatched and internal.prediction == {0, 1}
    p = Problem(2, (cap,) * 4, ((0, 2), (1, 2), (1, 3)), 9 * cap / 8)
    changed = public(p, frozenset(((2, 0),)))
    assert changed.pred_cover == {1} and changed.initial == frozenset(((1, 2),))
    assert not changed.initial <= changed.matching
    counts["named_public_checks"] = 2
    return {
        "protocol": "A87-matching-probe-CPU-v1",
        "counts": dict(counts),
        "stars": stars,
        "scope": "finite rational correctness only; no neural/performance/priority claim",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="only after source/protocol freeze")
    if parser.parse_args().audit:
        print(json.dumps(audit(), sort_keys=True))
