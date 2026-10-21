"""Fixed-threshold one-random-probe oracle; freeze before running --audit.

Protocol: all 15 nonempty 2x2 graphs, three positive rational response tables,
three table-based forecasts plus all/no/inverted actual arcs. Enumerate every
uniform audit choice exactly, compare all 16 query subsets and the frozen
four-cut reference. Also r=1,2,4,8 disjoint stars with n=2,3 leaves: perfect,
no-arc and wrong-center forecasts. No neural, timing or priority claim.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from itertools import product

import networkx as nx
from star_certificates import F, Instance, optimal_certificate

Pair = tuple[int, int]
Arcs = frozenset[Pair]
Query = Callable[[int], dict[int, F]]


@dataclass(frozen=True)
class Problem:
    """Public data only; the policy never receives unknown response values."""

    n_a: int
    caps: tuple[F, ...]
    edges: tuple[Pair, ...]
    tau: F

    def __post_init__(self) -> None:
        if not 0 < self.n_a < len(self.caps) or not self.edges or self.tau <= 0:
            raise ValueError("nonempty positive bipartite problem required")
        if any(not isinstance(c, F) or c <= 0 for c in self.caps):
            raise ValueError("positive rational caps required")
        if any(
            sum(part, F(0)) >= F(1, 2) for part in (self.caps[: self.n_a], self.caps[self.n_a :])
        ):
            raise ValueError("reserve positive root probability outside the candidates")
        if len(set(self.edges)) != len(self.edges) or any(
            not 0 <= a < self.n_a <= b < len(self.caps) for a, b in self.edges
        ):
            raise ValueError("invalid candidate edges")

    def graph(self) -> tuple[Pair, ...]:
        return tuple((a, b) for a, b in self.edges if self.caps[a] + self.caps[b] > self.tau)


def min_cover(p: Problem, removed: frozenset[int] = frozenset()) -> frozenset[int]:
    """Unit-cost bipartite cover, using only caps/topology/the known threshold."""
    graph = nx.DiGraph()
    graph.add_nodes_from(("s", "t"))
    for z in range(len(p.caps)):
        if z not in removed:
            graph.add_edge(*(("s", z) if z < p.n_a else (z, "t")), capacity=1)
    for a, b in p.graph():
        if a not in removed and b not in removed:
            graph.add_edge(a, b, capacity=len(p.caps) + 1)
    _, (left, right) = nx.minimum_cut(graph, "s", "t", flow_func=nx.algorithms.flow.edmonds_karp)
    return frozenset(
        z
        for z in range(len(p.caps))
        if z not in removed and ((z < p.n_a and z in right) or (z >= p.n_a and z in left))
    )


@dataclass(frozen=True)
class Result:
    queries: tuple[int, ...]
    selected: int | None
    accepted: bool | None


def probe_policy(p: Problem, predicted: Arcs, query: Query, selected: int | None) -> Result:
    """Enumerate randomness externally: selected is uniform on predicted arc heads.

    A query reveals a whole incident vector. Only returned vectors enter stopping
    decisions; forecasts select acquisitions and never replace actual responses.
    """
    directed = {(a, b) for a, b in p.graph()} | {(b, a) for a, b in p.graph()}
    if not predicted <= directed:
        raise ValueError("predicted arcs must lie on initially threatening edges")
    mandatory = frozenset(b for _, b in predicted)
    if (mandatory and selected not in mandatory) or (not mandatory and selected is not None):
        raise ValueError("select exactly one predicted head, or None for no arcs")
    cache: dict[int, dict[int, F]] = {}
    order: list[int] = []

    def acquire(z: int) -> None:
        if z in cache:
            return
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

    accepted = None
    if mandatory:
        source = min(a for a, b in predicted if b == selected)
        acquire(source)
        edge = next(i for i, ends in enumerate(p.edges) if set(ends) == {source, selected})
        assert selected is not None
        accepted = cache[source][edge] + p.caps[selected] > p.tau
    chosen = mandatory | min_cover(p, mandatory) if accepted else min_cover(p)
    for z in sorted(chosen):
        acquire(z)
    forced = set()
    for i, (a, b) in enumerate(p.edges):
        unknown = {a, b} - cache.keys()
        upper = sum((cache[z][i] if z in cache else p.caps[z] for z in (a, b)), F(0))
        if upper > p.tau:
            if len(unknown) != 1:
                raise ValueError("false incumbent promise or incomplete cover")
            forced |= unknown
    for z in sorted(forced):
        acquire(z)
    for i, (a, b) in enumerate(p.edges):
        upper = sum((cache[z][i] if z in cache else p.caps[z] for z in (a, b)), F(0))
        if upper > p.tau or (a in cache and b in cache and upper >= p.tau):
            raise ValueError("transcript does not certify the strict fixed threshold")
    return Result(tuple(order), selected, accepted)


def bad_arcs(p: Problem, values: tuple[tuple[F, F], ...]) -> Arcs:
    return frozenset(
        (source, target)
        for (a, b), (u, v) in zip(p.edges, values, strict=True)
        for source, target, x in ((a, b, u), (b, a, v))
        if x + p.caps[target] > p.tau
    )


@dataclass(frozen=True)
class Fixture:
    problem: Problem
    values: tuple[tuple[F, F], ...]

    def validate(self) -> None:
        p = self.problem
        totals = [F(0)] * len(p.caps)
        for (a, b), (u, v) in zip(p.edges, self.values, strict=True):
            assert 0 < u < p.caps[a] and 0 < v < p.caps[b] and u + v < p.tau
            totals[a] += u
            totals[b] += v
        assert all(t < c for t, c in zip(totals, p.caps, strict=True))

    def query(self, z: int) -> dict[int, F]:
        return {
            i: self.values[i][int(z == b)]
            for i, (a, b) in enumerate(self.problem.edges)
            if z in (a, b)
        }

    def independent_certificate(self, queried: frozenset[int]) -> bool:
        """Independent adversarial delta on each unobserved incident word."""
        for i, ends in enumerate(self.problem.edges):
            gap = -self.problem.tau
            for side, z in enumerate(ends):
                gap += self.values[i][side] if z in queried else self.problem.caps[z]
            if gap > 0:  # Equality with an unknown positive head is unattained.
                return False
        return True

    def brute_optimum(self, counts: Counter[str]) -> int:
        n = len(self.problem.caps)
        best = n
        for mask in range(1 << n):
            queried = frozenset(z for z in range(n) if mask >> z & 1)
            counts["subset_checks"] += 1
            if self.independent_certificate(queried):
                best = min(best, len(queried))
        return best

    def reference_optimum(self) -> int:
        """Known exclusive winner turns the frozen reference into fixed tau."""
        p = self.problem
        aw, bw = p.n_a, len(p.caps) + 1
        caps = (*p.caps[: p.n_a], p.tau, *p.caps[p.n_a :], p.tau)
        edges = tuple((a, b + 1, u, v) for (a, b), (u, v) in zip(p.edges, self.values, strict=True))
        edges += ((aw, bw, p.tau / 2, p.tau / 2),)
        inst = Instance(p.n_a + 1, caps, edges, (F(1),) * len(caps))
        answer = optimal_certificate(inst, frozenset((aw, bw)), len(edges) - 1)
        assert answer is not None
        return len(answer) - 2


def audit() -> dict[str, object]:
    counts: Counter[str] = Counter()

    def check(data: Fixture, forecasts: list[Arcs], expected_opt: int | None = None) -> list[F]:
        data.validate()
        p = data.problem
        opt = data.reference_optimum()
        if len(p.caps) == 4:
            assert opt == data.brute_optimum(counts)
        if expected_opt is not None:
            assert opt == expected_opt
        actual = bad_arcs(p, data.values)
        averages = []
        for forecast in forecasts:
            heads = sorted({b for _, b in forecast})
            costs = []
            for selected in heads or [None]:
                calls: list[int] = []

                def query(z: int, seen: list[int] = calls) -> dict[int, F]:
                    assert z not in seen
                    seen.append(z)
                    return data.query(z)

                result = probe_policy(p, forecast, query, selected)
                assert result.queries == tuple(calls)
                assert data.independent_certificate(frozenset(calls))
                if forecast == actual:
                    assert len(calls) <= opt + 1
                costs.append(len(calls))
                counts["policy_runs"] += 1
            mean = F(sum(costs), len(costs))
            assert mean <= 3 * opt + 1
            averages.append(mean)
            counts["forecast_cases"] += 1
        counts["instances"] += 1
        return averages

    cap = F(1, 32)
    all_pairs = tuple(product(range(2), range(2, 4)))
    for mask in range(1, 16):
        edges = tuple(e for i, e in enumerate(all_pairs) if mask >> i & 1)
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
            forecasts = [bad_arcs(p, t) for t in tables]
            forecasts += [all_arcs, frozenset(), all_arcs - bad_arcs(p, values)]
            check(Fixture(p, values), forecasts)
    stars = []
    for r, n in product((1, 2, 4, 8), (2, 3)):
        cap = F(1, 4 * (r * n + 1))
        edges = tuple((a, r + a * n + j) for a in range(r) for j in range(n))
        p = Problem(r, (cap,) * (r + r * n), edges, (1 + F(1, 4 * n)) * cap)
        high = Fixture(p, ((cap / (2 * n), cap / (8 * n)),) * len(edges))
        forecast = bad_arcs(p, high.values)
        perfect, zero = check(high, [forecast, frozenset()], r * n)
        assert perfect == r * n + 1 and zero == r * n + r
        low = Fixture(p, ((cap / (8 * n), cap / (8 * n)),) * len(edges))
        (wrong,) = check(low, [forecast], r)
        assert wrong == r
        stars.append(
            {
                "r": r,
                "n": n,
                "perfect": str(perfect),
                "no_arcs": str(zero),
                "wrong_centers": str(wrong),
            }
        )
    return {
        "protocol": "A87-fixed-threshold-online-probe-CPU-v1",
        "counts": dict(counts),
        "stars": stars,
        "scope": "finite rational correctness only; no neural/performance/priority claim",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="only after source/protocol freeze")
    if parser.parse_args().audit:
        print(json.dumps(audit(), sort_keys=True))
