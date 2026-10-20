"""Exact CPU prefix-replay planner; classical closure and fractional optimization.

``traces`` contains (positive integer weight, sequence of hashable query IDs).
Paths stop at the first query outside ``universe``. Progress is a weighted count,
not a normalized probability. See README.md for antecedents and the local scope.
"""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import pairwise

import networkx as nx

Trace = tuple[int, Sequence[Hashable]]


@dataclass(frozen=True, slots=True)
class Plan:
    selected: frozenset[Hashable]
    ratio: Fraction
    cut_count: int
    residual: Fraction
    progress: int


def _replay(traces: Sequence[Trace], selected: frozenset[Hashable]) -> int:
    """Direct first-missing replay, also used by the independent exhaustive oracle."""
    total = 0
    for weight, path in traces:
        for query in path:
            if query not in selected:
                break
            total += weight
    return total


def choose_plan(
    traces: Iterable[Trace],
    universe: Iterable[Hashable],
    affine_a: int,
    affine_b: int,
    *,
    mandatory: Iterable[Hashable],
) -> Plan:
    """Maximize exact weighted prefix progress / (a + b * number of queries).

    Every subset containing a nonempty mandatory set is admissible. No additional
    cardinality limit is imposed. The returned zero residual certifies optimality
    for these finite traces and this affine cost, not for a model trajectory.
    """
    if type(affine_a) is not int or type(affine_b) is not int:
        raise TypeError("affine costs must be integers")
    if affine_a < 0 or affine_b <= 0:
        raise ValueError("require a >= 0 and b > 0")
    queries = tuple(dict.fromkeys(universe))
    required = frozenset(mandatory)
    if not required or not required.issubset(queries):
        raise ValueError("mandatory must be a nonempty subset of universe")
    paths = tuple((weight, tuple(path)) for weight, path in traces)
    if any(type(weight) is not int or weight <= 0 for weight, _ in paths):
        raise ValueError("trace weights must be positive integers")

    # Integer IDs isolate graph vertices from arbitrary user query IDs.
    source, sink = 0, 1
    state = {query: i + 2 for i, query in enumerate(queries)}
    certificates: dict[tuple[int, Hashable], int] = {}
    prerequisites: dict[int, tuple[int, int]] = {}
    rewards: dict[int, int] = {}
    for weight, path in paths:
        previous = -1
        for query in path:
            if query not in state:
                break
            key = previous, query
            if key not in certificates:
                node = len(state) + 2 + len(certificates)
                certificates[key] = node
                prerequisites[node] = state[query], previous
                rewards[node] = 0
            node = certificates[key]
            rewards[node] += weight
            previous = node

    price = Fraction(0)
    previous_selected = frozenset(queries)
    for cut_count in range(1, len(queries) + 2):
        numerator, denominator = price.numerator, price.denominator
        state_cost = numerator * affine_b
        total_reward = denominator * sum(rewards.values())
        force = total_reward + state_cost * len(queries) + 1
        graph = nx.DiGraph()
        graph.add_nodes_from((source, sink))
        for query, node in state.items():
            graph.add_edge(node, sink, capacity=state_cost)
            if query in required:
                graph.add_edge(source, node, capacity=force)
        for node, (current, previous) in prerequisites.items():
            graph.add_edge(source, node, capacity=denominator * rewards[node])
            graph.add_edge(node, current, capacity=force)
            if previous != -1:
                graph.add_edge(node, previous, capacity=force)
        cut_value, (reachable, _) = nx.minimum_cut(
            graph, source, sink, flow_func=nx.algorithms.flow.preflow_push
        )
        selected = frozenset(query for query, node in state.items() if node in reachable)
        if not required.issubset(selected) or not selected.issubset(previous_selected):
            raise AssertionError("closure or nested-solution invariant failed")
        progress = _replay(paths, selected)
        cost = affine_a + affine_b * len(selected)
        residual = Fraction(progress) - price * cost
        expected_cut = total_reward - denominator * progress + state_cost * len(selected)
        if cut_value != expected_cut or residual < 0:
            raise AssertionError("integer cut/replay certificate mismatch")
        if residual == 0:
            return Plan(selected, Fraction(progress, cost), cut_count, residual, progress)
        price = Fraction(progress, cost)
        previous_selected = selected
    raise AssertionError("nonempty mandatory set requires at most N+1 cuts")


def _enumerate(
    traces: Sequence[Trace], universe: Sequence[Hashable], required: frozenset[Hashable]
) -> list[tuple[frozenset[Hashable], int]]:
    rows = []
    for mask in range(1 << len(universe)):
        selected = frozenset(q for i, q in enumerate(universe) if mask & (1 << i))
        if required.issubset(selected):
            # Independent of certificates, cuts, and the sum of AND rewards.
            total = 0
            for weight, path in traces:
                accepted = 0
                for query in path:
                    if query not in selected:
                        break
                    accepted += 1
                total += weight * accepted
            rows.append((selected, total))
    return rows


def _audit_all_prices(rows: list[tuple[frozenset[Hashable], int]], b: int) -> int:
    """Check every linear-envelope cell and tie boundary, not only sampled prices."""
    best_by_size: dict[int, int] = {}
    for selected, progress in rows:
        size = len(selected)
        best_by_size[size] = max(best_by_size.get(size, -1), progress)
    boundaries = {Fraction(0)}
    for size, progress in best_by_size.items():
        for other_size, other_progress in best_by_size.items():
            if size != other_size:
                crossing = Fraction(progress - other_progress, b * (size - other_size))
                if crossing >= 0:
                    boundaries.add(crossing)
    ordered = sorted(boundaries)
    prices = sorted(
        boundaries | {(left + right) / 2 for left, right in pairwise(ordered)} | {ordered[-1] + 1}
    )
    previous_common: frozenset[Hashable] | None = None
    for price in prices:
        n, d = price.numerator, price.denominator
        scores = [d * progress - n * b * len(selected) for selected, progress in rows]
        optimum = max(scores)
        maxima = [
            selected for (selected, _), score in zip(rows, scores, strict=True) if score == optimum
        ]
        if previous_common is not None:
            assert all(selected.issubset(previous_common) for selected in maxima)
        previous_common = frozenset.intersection(*maxima)
    return len(prices)


def audit(seed: int = 86001, cases: int = 240) -> dict[str, int | str]:
    """Correctness only: no inference, GPU access, files, or performance claims."""
    rng = random.Random(seed)
    price_cells = 0
    for case in range(cases):
        size = 1 + case % 9
        universe = tuple(range(size))
        required = frozenset({0})
        paths: list[Trace] = [
            (rng.randint(1, 7), (0, *rng.sample(list(universe[1:]), rng.randrange(size))))
            for _ in range(rng.randint(1, 12))
        ]
        # Outsiders must truncate a trace, rather than allowing later recovery.
        paths.append((2, (0, "outside", *universe[1:])))
        a, b = rng.randrange(8), rng.randint(1, 6)
        plan = choose_plan(paths, universe, a, b, mandatory=required)
        rows = _enumerate(paths, universe, required)
        oracle = max(Fraction(progress, a + b * len(selected)) for selected, progress in rows)
        assert plan.ratio == oracle and plan.residual == 0
        assert plan.progress == dict(rows)[plan.selected] and plan.cut_count <= size + 1
        price_cells += _audit_all_prices(rows, b)
        actual = {m: (a + b * m) + rng.randrange(4 * (a + b * m) + 1) for m in range(1, size + 1)}
        kappa = max(Fraction(actual[m], a + b * m) for m in actual)
        best_real = max(Fraction(progress, actual[len(selected)]) for selected, progress in rows)
        assert Fraction(plan.progress, actual[len(plan.selected)]) >= best_real / kappa

    paths = [(1, ("s", "a", "c")), (1, ("s", "b", "c"))]
    assert _replay(paths, frozenset({"s", "a", "c"})) == 4  # Normalized yield is 2.
    plan = choose_plan([(3, ("s", "a"))], ("s", "a", "unused"), 0, 1, mandatory={"s"})
    assert "unused" not in plan.selected
    empty = choose_plan([], ("s", "unused"), 0, 1, mandatory={"s"})
    assert empty.ratio == 0 and empty.residual == 0
    for batch in range(1, 9):
        for size in range(1, 257):
            actual = 7 * ((size + batch - 1) // batch)
            lower = Fraction(7 * (batch + size), 2 * batch)
            assert lower <= actual <= 2 * lower
    return {"status": "PASS", "seed": seed, "families": cases, "price_cells": price_cells}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="run finite CPU correctness checks")
    parser.add_argument("--seed", type=int, default=86001)
    parser.add_argument("--cases", type=int, default=240)
    args = parser.parse_args()
    if not args.audit or args.cases <= 0:
        parser.error("require --audit and --cases > 0")
    print(json.dumps(audit(args.seed, args.cases), sort_keys=True))
