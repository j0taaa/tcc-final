"""Resource-augmented CFG-on-DAG reference, using exact rational arithmetic.

No subset enumeration or model dependence. Stable backpointers retain ORIGINAL
arcs, including epsilon arcs and their resource cost. All budgets share one chart.
The independent checker is in budget_certificate.py and never calls this solver.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from time import perf_counter
from typing import TypeAlias

from mwpc_exact.profiling import ComponentProfiler, ProfilingComponent
from mwpc_exact.reference.budget_types import (
    BudgetCertificate,
    BudgetPathResult,
    ChartKey,
    EpsilonKey,
    ResourceArc,
    ResourceDAG,
    nonnegative_integer,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.types import SolveStatus

Leaf: TypeAlias = tuple[EpsilonKey, int, EpsilonKey]
Binary: TypeAlias = tuple[ChartKey, ChartKey]


def budgeted_frontier(
    grammar: CnfGrammar,
    graph: ResourceDAG,
    max_budget: int,
    *,
    profiler: ComponentProfiler | None = None,
) -> tuple[BudgetPathResult, ...]:
    """Return a proved optimum or support infeasibility for every cap 0..max_budget."""
    monitor = profiler if profiler is not None else ComponentProfiler()
    with monitor.observe_wall_span():
        return _frontier(grammar, graph, max_budget, monitor)


def _frontier(
    grammar: CnfGrammar, graph: ResourceDAG, max_budget: int, monitor: ComponentProfiler
) -> tuple[BudgetPathResult, ...]:
    started = perf_counter() if monitor.enabled else 0.0
    nonnegative_integer(max_budget, "max_budget")
    outgoing: dict[int, list[ResourceArc]] = defaultdict(list)
    for arc in graph.arcs:
        if arc.label is None:
            outgoing[arc.source].append(arc)
    epsilon: dict[EpsilonKey, Fraction] = {}
    epsilon_back: dict[EpsilonKey, tuple[EpsilonKey, int] | None] = {}
    for source in graph.nodes:
        epsilon[source, source, 0] = Fraction()
        epsilon_back[source, source, 0] = None
        for node in graph.nodes:
            for cost in range(max_budget + 1):
                key = (source, node, cost)
                if key not in epsilon:
                    continue
                for arc in outgoing[node]:
                    next_cost = cost + arc.cost
                    if next_cost > max_budget:
                        continue
                    eps_target = (source, arc.target, next_cost)
                    value = epsilon[key] + arc.reward
                    if eps_target not in epsilon or value > epsilon[eps_target]:
                        epsilon[eps_target] = value
                        epsilon_back[eps_target] = (key, arc.arc_id)

    ends: dict[int, list[EpsilonKey]] = defaultdict(list)
    starts: dict[int, list[EpsilonKey]] = defaultdict(list)
    for key in epsilon:
        starts[key[0]].append(key)
        ends[key[1]].append(key)
    heads: dict[int | str, list[int]] = defaultdict(list)
    for production in grammar.terminal_productions:
        heads[grammar.terminal_labels[production.terminal_id]].append(production.head_id)
    chart: dict[ChartKey, Fraction] = {}
    back: dict[ChartKey, Leaf | Binary] = {}
    for arc in graph.arcs:
        if arc.label is None:
            continue
        for prefix in ends[arc.source]:
            for suffix in starts[arc.target]:
                cost = prefix[2] + arc.cost + suffix[2]
                if cost > max_budget:
                    continue
                value = epsilon[prefix] + arc.reward + epsilon[suffix]
                for head in heads[arc.label]:
                    chart_key = (head, prefix[0], suffix[1], cost)
                    if chart_key not in chart or value > chart[chart_key]:
                        chart[chart_key] = value
                        back[chart_key] = (prefix, arc.arc_id, suffix)
    for width in range(2, len(graph.nodes)):
        for start_index in range(len(graph.nodes) - width):
            source = graph.nodes[start_index]
            target = graph.nodes[start_index + width]
            for split in graph.nodes[start_index + 1 : start_index + width]:
                for binary_production in grammar.binary_productions:
                    for left_cost in range(max_budget + 1):
                        left = (binary_production.left_id, source, split, left_cost)
                        if left not in chart:
                            continue
                        for right_cost in range(max_budget - left_cost + 1):
                            right = (binary_production.right_id, split, target, right_cost)
                            if right not in chart:
                                continue
                            chart_key = (
                                binary_production.head_id,
                                source,
                                target,
                                left_cost + right_cost,
                            )
                            value = chart[left] + chart[right]
                            if chart_key not in chart or value > chart[chart_key]:
                                chart[chart_key] = value
                                back[chart_key] = (left, right)

    def epsilon_path(key: EpsilonKey) -> tuple[int, ...]:
        result: list[int] = []
        while epsilon_back[key] is not None:
            parent = epsilon_back[key]
            assert parent is not None
            key, arc_id = parent
            result.append(arc_id)
        return tuple(reversed(result))

    def grammar_path(key: ChartKey) -> tuple[int, ...]:
        pointer = back[key]
        if len(pointer) == 2:
            return grammar_path(pointer[0]) + grammar_path(pointer[1])
        prefix, arc_id, suffix = pointer
        return (*epsilon_path(prefix), arc_id, *epsilon_path(suffix))

    proof = BudgetCertificate(
        max_budget,
        tuple((*key, value) for key, value in sorted(epsilon.items())),
        tuple((*key, value) for key, value in sorted(chart.items())),
    )
    by_id = {arc.arc_id: arc for arc in graph.arcs}
    if monitor.enabled:
        monitor.add_duration(ProfilingComponent.PARSER, perf_counter() - started)
        monitor.set_counter("chart_entries", len(chart))
        started = perf_counter()
    results: list[BudgetPathResult] = []
    for cap in range(max_budget + 1):
        score: Fraction | None = None
        path: tuple[int, ...] | None = None
        for final in graph.finals:
            for cost in range(cap + 1):
                chart_key = (grammar.start_nonterminal_id, graph.start, final, cost)
                if chart_key in chart and (score is None or chart[chart_key] > score):
                    score, path = chart[chart_key], grammar_path(chart_key)
                eps_key = (graph.start, final, cost)
                if grammar.accepts_empty and eps_key in epsilon:
                    if score is None or epsilon[eps_key] > score:
                        score, path = epsilon[eps_key], epsilon_path(eps_key)
        labels = (
            tuple(by_id[i].label for i in path if by_id[i].label is not None)
            if path is not None
            else None
        )
        # Explicit construction avoids a type assertion about filtered Optional labels.
        visible = None if labels is None else tuple(x for x in labels if x is not None)
        results.append(
            BudgetPathResult(
                SolveStatus.OPTIMAL if path is not None else SolveStatus.INFEASIBLE_ON_SUPPORT,
                cap,
                score,
                path,
                visible,
                sum(by_id[i].cost for i in path) if path is not None else None,
                proof,
                graph.support_description,
            )
        )
    if monitor.enabled:
        monitor.add_duration(ProfilingComponent.BACKTRACKING, perf_counter() - started)
    return tuple(results)
