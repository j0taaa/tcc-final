"""Exact star-query certificate audits; no neural evaluation or timing claims.

Vertices A are 0..n_a-1, B are n_a..len(caps)-1. Lower priority wins ties.
Run --audit only after freezing this source and its protocol in Git.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from math import lcm

import networkx as nx

Edge = tuple[int, int, F, F]


@dataclass(frozen=True)
class Instance:
    n_a: int
    caps: tuple[F, ...]
    edges: tuple[Edge, ...]
    costs: tuple[F, ...]
    interior: bool = True
    priority: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        n, k = len(self.caps), len(self.edges)
        if not 0 < self.n_a < n or not k or len(self.costs) != n:
            raise ValueError("nonempty bipartite instance required")
        if not all(isinstance(x, F) and x > 0 for x in (*self.caps, *self.costs)):
            raise ValueError("caps and costs must be positive Fractions")
        if not self.priority:
            object.__setattr__(self, "priority", tuple(range(k)))
        if sorted(self.priority) != list(range(k)):
            raise ValueError("priority must be a permutation of 0..K-1")
        seen, totals = set(), [F(0)] * n
        for a, b, u, v in self.edges:
            if not 0 <= a < self.n_a <= b < n or (a, b) in seen:
                raise ValueError("invalid or duplicate candidate edge")
            seen.add((a, b))
            for z, value in ((a, u), (b, v)):
                if not isinstance(value, F) or not 0 <= value <= self.caps[z]:
                    raise ValueError("component outside its cap")
                if self.interior and not 0 < value < self.caps[z]:
                    raise ValueError("interior components must be strictly inside caps")
                totals[z] += value
        if any(t > c or (self.interior and t >= c) for t, c in zip(totals, self.caps, strict=True)):
            raise ValueError("star masses require an outside symbol with remaining mass")

    def winner(self) -> int:
        return min(
            range(len(self.edges)), key=lambda i: (-sum(self.edges[i][2:]), self.priority[i])
        )


def query_set(inst: Instance, queried: frozenset[int]) -> frozenset[int]:
    queried = frozenset(queried)
    if not queried <= set(range(len(inst.caps))):
        raise ValueError("query vertex out of range")
    return queried


def query_cost(inst: Instance, queried: frozenset[int], prior: frozenset[int]) -> F:
    return sum((inst.costs[z] for z in queried - prior), F(0))


def bounds(inst: Instance, queried: frozenset[int]) -> tuple[list[F], list[F]]:
    low, high = [], []
    for a, b, u, v in inst.edges:
        low.append((u if a in queried else F(0)) + (v if b in queried else F(0)))
        high.append((u if a in queried else inst.caps[a]) + (v if b in queried else inst.caps[b]))
    return low, high


def pair_ok(inst: Instance, w: int, e: int, low: F, high: F, unknown: bool) -> bool:
    if high != low:
        return high < low
    return (inst.interior and unknown) or inst.priority[w] < inst.priority[e]


def certificate(inst: Instance, queried: frozenset[int], winner: int) -> bool:
    """Necessary and sufficient under the declared closed/interior star oracle."""
    queried = query_set(inst, queried)
    low, high = bounds(inst, queried)
    wa, wb = inst.edges[winner][:2]
    return all(
        e == winner or pair_ok(inst, winner, e, low[winner], high[e], not {wa, wb, a, b} <= queried)
        for e, (a, b, _, _) in enumerate(inst.edges)
    )


def optimal_certificate(
    inst: Instance, prior: frozenset[int] = frozenset(), winner: int | None = None
) -> frozenset[int] | None:
    """Offline optimum by four exact integer-capacity weighted minimum cuts."""
    prior = query_set(inst, prior)
    w = inst.winner() if winner is None else winner
    wa, wb, wu, wv = inst.edges[w]
    scale = lcm(*(c.denominator for c in inst.costs))
    weights = [int(c * scale) for c in inst.costs]
    infinite = 1 + sum(weights)
    best, best_cost = None, None
    for take_a, take_b in product((False, True), repeat=2):
        selected = {z for z, take in ((wa, take_a), (wb, take_b)) if take}
        banned = {wa, wb} - selected
        if prior & banned:
            continue
        forced, clauses = set(prior) | selected, []
        threshold = (wu if take_a else F(0)) + (wv if take_b else F(0))
        feasible = True
        for e, (a, b, u, v) in enumerate(inst.edges):
            if e == w:
                continue
            accepted = {}
            for x, y in product((False, True), repeat=2):
                upper = (u if x else inst.caps[a]) + (v if y else inst.caps[b])
                accepted[x, y] = pair_ok(
                    inst, w, e, threshold, upper, not (take_a and take_b and x and y)
                )
            if not accepted[True, True]:
                feasible = False
                break
            if accepted[False, False]:
                continue
            x_ok, y_ok = accepted[True, False], accepted[False, True]
            if x_ok and y_ok:
                clauses.append((a, b))
            else:
                if not y_ok:
                    forced.add(a)
                if not x_ok:
                    forced.add(b)
        for a, b in clauses:
            if a in banned:
                forced.add(b)
            if b in banned:
                forced.add(a)
        if not feasible or forced & banned:
            continue
        graph = nx.DiGraph()
        graph.add_nodes_from(("source", "sink"))
        for z in range(len(inst.caps)):
            if z not in forced | banned:
                ends = ("source", z) if z < inst.n_a else (z, "sink")
                graph.add_edge(*ends, capacity=weights[z])
        for a, b in clauses:
            if a not in forced and b not in forced:
                graph.add_edge(a, b, capacity=infinite)
        _, (source_side, sink_side) = nx.minimum_cut(
            graph, "source", "sink", flow_func=nx.algorithms.flow.edmonds_karp
        )
        chosen = forced | {z for z in sink_side if isinstance(z, int) and z < inst.n_a}
        chosen |= {z for z in source_side if isinstance(z, int) and z >= inst.n_a}
        result = frozenset(chosen)
        cost = query_cost(inst, result, prior)
        if best_cost is None or cost < best_cost:
            best, best_cost = result, cost
    return best


def independent_certificate(inst: Instance, queried: frozenset[int], winner: int) -> bool:
    """Compute pairwise adversarial delta responses, without bounds/pair_ok."""
    wa, wb, wu, wv = inst.edges[winner]
    for e, (a, b, u, v) in enumerate(inst.edges):
        if e == winner:
            continue
        gap, unattained = F(0), False
        for z, cap in enumerate(inst.caps):
            if z in queried:
                gap += u if z == a else v if z == b else F(0)
                gap -= wu if z == wa else wv if z == wb else F(0)
            elif z in (a, b):
                gap += cap  # Delta on the rival word also zeros a shared winner word.
                unattained = True
            elif z in (wa, wb):
                unattained = True  # Delta on another word zeros the winner.
        if gap > 0:
            return False
        if gap == 0 and not (inst.interior and unattained):
            if inst.priority[e] < inst.priority[winner]:
                return False
    return True


def brute_force(
    inst: Instance,
    prior: frozenset[int] = frozenset(),
    winner: int | None = None,
    counts: Counter[str] | None = None,
) -> frozenset[int] | None:
    """Independent full subset enumeration and adversarial-response certificate."""
    prior = query_set(inst, prior)
    w = inst.winner() if winner is None else winner
    remaining = sorted(set(range(len(inst.caps))) - prior)
    best, best_cost = None, None
    for mask in range(1 << len(remaining)):
        queried = prior | frozenset(z for i, z in enumerate(remaining) if mask >> i & 1)
        valid = independent_certificate(inst, queried, w)
        if counts is not None:
            counts["subset_checks"] += 1
            if certificate(inst, queried, w) != valid:
                raise AssertionError("certificate predicates disagree")
        cost = query_cost(inst, queried, prior)
        if valid and (best_cost is None or cost < best_cost):
            best, best_cost = queried, cost
    return best


def bestfirst_replay(
    inst: Instance,
    prior: frozenset[int] = frozenset(),
) -> tuple[int, tuple[frozenset[int], ...]]:
    """Replay known answers, acquiring only maximal-UB edge endpoints each round."""
    queried, rounds = query_set(inst, prior), []
    while True:
        low, high = bounds(inst, queried)
        candidates = sorted(range(len(low)), key=lambda i: (-low[i], inst.priority[i]))
        for candidate in candidates:
            if low[candidate] == max(low) and certificate(inst, queried, candidate):
                return candidate, tuple(rounds)
        edge = max(range(len(high)), key=lambda i: (high[i], -inst.priority[i]))
        new = frozenset(inst.edges[edge][:2]) - queried
        if not new:
            raise AssertionError("unsolved replay selected a fully known edge")
        rounds.append(new)
        queried |= new


def audit() -> dict[str, object]:
    counts: Counter[str] = Counter()

    def check(inst: Instance, prior: frozenset[int] = frozenset()) -> None:
        optimum, brute = optimal_certificate(inst, prior), brute_force(inst, prior, counts=counts)
        assert optimum is not None and brute is not None
        assert prior <= optimum and independent_certificate(inst, optimum, inst.winner())
        assert query_cost(inst, optimum, prior) == query_cost(inst, brute, prior)
        returned, rounds = bestfirst_replay(inst, prior)
        transcript = prior | frozenset().union(*rounds)
        assert returned == inst.winner() and independent_certificate(inst, transcript, returned)
        scores = [u + v for _, _, u, v in inst.edges]
        if inst.interior and len(set(inst.costs)) == 1 and scores.count(max(scores)) == 1:
            assert len(transcript - prior) <= 2 * len(optimum - prior) + 1

    def grid(mask: int, pattern: int, weighted: bool, interior: bool = True) -> Instance:
        edges = []
        for a, j in product(range(3), repeat=2):
            if mask >> (3 * a + j) & 1:
                if pattern == 0:
                    u, v = F(1, 8), F(1, 8)
                elif pattern == 1:
                    u, v = F(1 + (3 * a + 2 * j) % 7, 32), F(1 + (a + 5 * j) % 9, 40)
                else:
                    u = F(1 + (a + 2 * j) % 3, 8)
                    v = F(1, 2) - u
                edges.append((a, 3 + j, u, v))
        costs = tuple(F(1 + i % 3) if weighted else F(1) for i in range(6))
        priority = tuple(reversed(range(len(edges)))) if pattern == 2 else ()
        return Instance(3, (F(1),) * 6, tuple(edges), costs, interior, priority)

    for mask in range(1, 512):
        for pattern, weighted in product(range(3), (False, True)):
            check(grid(mask, pattern, weighted))
            counts["grid_cases"] += 1
    counts["nonempty_graphs"] = 511
    for interior, fractional in product((False, True), repeat=2):
        base = grid(511, 1, False, interior)
        costs = tuple(F(i + 1, i + 2) if fractional else F(1) for i in range(6))
        inst = Instance(3, base.caps, base.edges, costs, interior)
        for mask in range(64):
            check(inst, frozenset(i for i in range(6) if mask >> i & 1))
            counts["prior_cases"] += 1

    caps = (F(1), F(1, 4), F(1), F(1, 4))
    edges = ((0, 2, F(1, 2), F(1, 10)), (1, 3, F(1, 10), F(1, 10)))
    for interior in (False, True):
        inst = Instance(2, caps, edges, (F(1),) * 4, interior, (1, 0))
        assert certificate(inst, frozenset({0}), 0) == interior
        check(inst, frozenset({0}))
        counts["named_cases"] += 1
    boundary = Instance(
        2, (F(1),) * 4, ((0, 2, F(1), F(0)), (1, 3, F(0), F(1))), (F(1),) * 4, False, (1, 0)
    )
    check(boundary)
    counts["named_cases"] += 1
    non_vc = Instance(
        2,
        (F(25, 100), F(20, 100), F(42, 100), F(5, 100)),
        ((0, 2, F(22, 100), F(40, 100)), (1, 3, F(1, 100), F(1, 100))),
        (F(1),) * 4,
    )
    check(non_vc)
    for mask in range(16):
        queried = frozenset(i for i in range(4) if mask >> i & 1)
        formula = 2 in queried or (0 in queried and bool(queried & {1, 3}))
        assert certificate(non_vc, queried, 0) == formula
    counts["named_cases"] += 1

    for k in range(1, 5):
        scale, n_a = F(1, k + 2), k + 1
        caps = [F(3, 10)] + [F(1, 5)] * k + [F(1, 5), F(21, 100)] + [F(9, 100)] * k
        edges = [(0, n_a, F(23, 100), F(1, 100)), (0, n_a + 1, F(1, 100), F(1, 1000))]
        edges += [(i, n_a + 1 + i, F(1, 100), F(1, 1000)) for i in range(1, k + 1)]
        inst = Instance(
            n_a,
            tuple(c * scale for c in caps),
            tuple((a, b, u * scale, v * scale) for a, b, u, v in edges),
            (F(1),) * len(caps),
        )
        check(inst)
        optimum = optimal_certificate(inst)
        _, rounds = bestfirst_replay(inst)
        assert optimum is not None and len(optimum) == k + 1
        assert sum(map(len, rounds)) == 2 * k + 3
        counts["sharpness_cases"] += 1
    return {"status": "PASS", **dict(counts), "neural_evaluations": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if not args.audit:
        parser.error("pass --audit after freezing the protocol")
    print(json.dumps(audit(), sort_keys=True))
