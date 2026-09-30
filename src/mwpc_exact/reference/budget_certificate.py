"""Independent upper-potential optimality checker; does not import the optimizer.

It checks inequalities, not Bellman equalities or solver backpointers. A feasible
path attains the checked upper bound, giving a mathematical optimality proof.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction

from mwpc_exact.reference.budget_types import (
    BudgetCertificateReport,
    BudgetPathResult,
    ResourceDAG,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.types import SolveStatus


def check_budget_certificate(
    grammar: CnfGrammar, graph: ResourceDAG, result: BudgetPathResult
) -> BudgetCertificateReport:
    """Accept only a mathematically certified optimum/support-infeasibility claim."""
    errors: list[str] = []
    proof = result.certificate
    if (
        isinstance(proof.max_budget, bool)
        or not isinstance(proof.max_budget, int)
        or isinstance(result.budget, bool)
        or not isinstance(result.budget, int)
        or not 0 <= result.budget <= proof.max_budget
    ):
        return BudgetCertificateReport(False, ("invalid budget",))
    rank = {node: i for i, node in enumerate(graph.nodes)}
    nonterminals = {node.symbol_id for node in grammar.nonterminals}
    eps = {row[:3]: row[3] for row in proof.epsilon_bounds}
    cfg = {row[:4]: row[4] for row in proof.grammar_bounds}
    if len(eps) != len(proof.epsilon_bounds) or len(cfg) != len(proof.grammar_bounds):
        errors.append("duplicate potential key")
    for (u, v, k), value in eps.items():
        if (
            u not in rank
            or v not in rank
            or rank[u] > rank[v]
            or not isinstance(k, int)
            or isinstance(k, bool)
            or not 0 <= k <= proof.max_budget
            or not isinstance(value, Fraction)
            or value < 0
        ):
            errors.append("invalid epsilon potential")
    for (a, u, v, k), value in cfg.items():
        if (
            a not in nonterminals
            or u not in rank
            or v not in rank
            or rank[u] >= rank[v]
            or not isinstance(k, int)
            or isinstance(k, bool)
            or not 0 <= k <= proof.max_budget
            or not isinstance(value, Fraction)
            or value < 0
        ):
            errors.append("invalid grammar potential")
    if errors:
        return BudgetCertificateReport(False, tuple(errors))

    for node in graph.nodes:
        if (node, node, 0) not in eps or eps[node, node, 0] < 0:
            errors.append("missing epsilon identity")
    ending: dict[int, list[tuple[int, int, Fraction]]] = defaultdict(list)
    starting: dict[int, list[tuple[int, int, Fraction]]] = defaultdict(list)
    for (u, v, k), val in eps.items():
        ending[v].append((u, k, val))
        starting[u].append((v, k, val))
    for arc in graph.arcs:
        if arc.label is None:
            for source, cost, bound in ending[arc.source]:
                next_cost = cost + arc.cost
                if next_cost <= proof.max_budget:
                    key = (source, arc.target, next_cost)
                    if key not in eps or eps[key] < bound + arc.reward:
                        errors.append("epsilon transition inequality violated")
        else:
            for production in grammar.terminal_productions:
                if grammar.terminal_labels[production.terminal_id] != arc.label:
                    continue
                for u, k1, left in ending[arc.source]:
                    for v, k2, right in starting[arc.target]:
                        if k1 + arc.cost + k2 > proof.max_budget:
                            continue
                        chart_key = (production.head_id, u, v, k1 + arc.cost + k2)
                        if chart_key not in cfg or cfg[chart_key] < left + arc.reward + right:
                            errors.append("terminal inequality violated")
    # Deliberately independent traversal from the optimizer's span/budget loops.
    left_ends: dict[tuple[int, int], list[tuple[int, int, Fraction]]] = defaultdict(list)
    right_starts: dict[tuple[int, int], list[tuple[int, int, Fraction]]] = defaultdict(list)
    for (a, u, v, k), val in cfg.items():
        left_ends[a, v].append((u, k, val))
        right_starts[a, u].append((v, k, val))
    for binary_production in grammar.binary_productions:
        for split_node in graph.nodes:
            entries = left_ends[binary_production.left_id, split_node]
            for u, k1, left in entries:
                for v, k2, right in right_starts[binary_production.right_id, split_node]:
                    if k1 + k2 > proof.max_budget:
                        continue
                    chart_key = (binary_production.head_id, u, v, k1 + k2)
                    if chart_key not in cfg or cfg[chart_key] < left + right:
                        errors.append("binary inequality violated")

    roots = [
        val
        for (a, u, v, k), val in cfg.items()
        if a == grammar.start_nonterminal_id
        and u == graph.start
        and v in graph.finals
        and k <= result.budget
    ]
    if grammar.accepts_empty:
        roots.extend(
            val
            for (u, v, k), val in eps.items()
            if u == graph.start and v in graph.finals and k <= result.budget
        )
    upper = max(roots) if roots else None
    if result.exactness_scope != graph.support_description:
        errors.append("support specification mismatch")
    if result.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
        if upper is not None or any(
            x is not None
            for x in (
                result.objective_value,
                result.witness_arc_ids,
                result.witness_terminal_labels,
                result.consumed_budget,
            )
        ):
            errors.append("unsupported infeasibility claim")
    elif result.status is SolveStatus.OPTIMAL and result.witness_arc_ids is not None:
        by_id = {arc.arc_id: arc for arc in graph.arcs}
        current, cost, score = graph.start, 0, Fraction()
        labels: list[int | str] = []
        for arc_id in result.witness_arc_ids:
            witness_arc = by_id.get(arc_id)
            if witness_arc is None or witness_arc.source != current:
                errors.append("invalid original witness path")
                break
            current = witness_arc.target
            cost += witness_arc.cost
            score += witness_arc.reward
            if witness_arc.label is not None:
                labels.append(witness_arc.label)
        if (
            current not in graph.finals
            or cost > result.budget
            or cost != result.consumed_budget
            or tuple(labels) != result.witness_terminal_labels
            or not recognizes_cnf(grammar, tuple(labels))
        ):
            errors.append("witness not feasible")
        if score != result.objective_value or upper != score:
            errors.append("witness does not attain independently checked upper bound")
    else:
        errors.append("status has no optimality/infeasibility proof")
    return BudgetCertificateReport(not errors, tuple(sorted(set(errors))))
