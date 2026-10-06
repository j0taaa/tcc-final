"""Independent correspondence checks from original inputs to budget proofs.

No optimizer or graph-building function is imported. Completeness is checked
using node meanings and a multiset of all required prefix/closing transitions.
The independent resource-potential checker then proves optimality on this graph.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from typing import TYPE_CHECKING

from mwpc_exact.budget_bounds import budget_input_fingerprint, validate_budget_batch
from mwpc_exact.eos_policy import EOSMode, TokenRole
from mwpc_exact.reference.budget_certificate import check_budget_certificate
from mwpc_exact.reference.budget_types import BudgetCertificateReport
from mwpc_exact.state import SelectionInput
from mwpc_exact.types import SolveStatus, TerminalLabel

if TYPE_CHECKING:
    from mwpc_exact.budget_graph import CompiledBudgetGraph
    from mwpc_exact.budget_result import BudgetedCommitResult

ArcKey = tuple[int, int, TerminalLabel | None, Fraction, int]
ClosingKey = tuple[int, int, TerminalLabel | None, Fraction, int, int, int, TokenRole]


def check_budget_graph(
    state: SelectionInput, compiled: CompiledBudgetGraph
) -> BudgetCertificateReport:
    """Check every legal original choice, with no reliance on compiler output."""
    errors: list[str] = []
    layout = compiled.layout
    if layout not in ("private", "compact"):
        return BudgetCertificateReport(False, ("unknown graph layout",))
    count = len(state.canvas)
    node_by_id = {node.node_id: node for node in compiled.nodes}
    if len(node_by_id) != len(compiled.nodes) or set(node_by_id) != set(compiled.graph.nodes):
        return BudgetCertificateReport(False, ("node meanings do not cover the original graph",))
    prefix_ids: dict[tuple[int, int | None, bytes], int] = {}
    for node in compiled.nodes:
        if not isinstance(node.after_eos, bool) or isinstance(node.position, bool):
            errors.append("invalid physical node meaning")
            continue
        if not node.prefix:
            if (
                not 0 <= node.position <= count
                or node.node_id != 2 * node.position + int(node.after_eos)
                or node.private_token_id is not None
            ):
                errors.append("invalid boundary node meaning")
        else:
            key = (node.position, node.private_token_id, node.prefix)
            if node.after_eos or key in prefix_ids:
                errors.append("invalid or duplicate prefix node meaning")
            prefix_ids[key] = node.node_id
    for position in range(count + 1):
        for after in (False, True):
            boundary = node_by_id.get(2 * position + int(after))
            if boundary is None or (boundary.position, boundary.after_eos, boundary.prefix) != (
                position,
                after,
                b"",
            ):
                errors.append("missing physical boundary")
    if errors:
        return BudgetCertificateReport(False, tuple(sorted(set(errors))))

    legal: list[tuple[int, int, TokenRole, bytes]] = []
    expected_prefixes: set[tuple[int, int | None, bytes]] = set()
    private_count = 2 * (count + 1)
    for position, tokens in enumerate(state.support.rows):
        for token in tokens:
            raw = state.tokenizer_adapter.emissions[token]
            is_special = state.eos_policy.mode is not EOSMode.ABSENT and (
                token in state.eos_policy.termination_token_ids
                or token == state.eos_policy.pad_token_id
            )
            if raw is not None and not is_special:
                legal.append((position, token, TokenRole.ORDINARY, raw))
                private_count += len(raw) - 1
                owner = token if layout == "private" else None
                expected_prefixes.update((position, owner, raw[:end]) for end in range(1, len(raw)))
            if state.eos_policy.mode is not EOSMode.ABSENT:
                if token in state.eos_policy.termination_token_ids:
                    legal.append((position, token, TokenRole.EOS, b""))
                if token == state.eos_policy.pad_token_id:
                    legal.append((position, token, TokenRole.PAD, b""))
    if set(prefix_ids) != expected_prefixes:
        return BudgetCertificateReport(
            False, ("prefix nodes do not equal original token prefixes",)
        )
    if compiled.private_node_count != private_count or len(compiled.graph.nodes) > private_count:
        errors.append("incorrect node-count certificate")

    expected_prefix_arcs: Counter[ArcKey] = Counter()
    for (position, owner, prefix), node_id in prefix_ids.items():
        parent = 2 * position if len(prefix) == 1 else prefix_ids[position, owner, prefix[:-1]]
        expected_prefix_arcs[parent, node_id, prefix[-1], Fraction(), 0] += 1
    expected_closings: Counter[ClosingKey] = Counter()
    for position, token, role, word in legal:
        target = 2 * (position + 1) + int(role is not TokenRole.ORDINARY)
        if role is TokenRole.ORDINARY:
            owner = token if layout == "private" else None
            if (position, owner, word) in prefix_ids:
                source, label = prefix_ids[position, owner, word], None
            else:
                source = 2 * position if len(word) == 1 else prefix_ids[position, owner, word[:-1]]
                label = word[-1]
        else:
            source, label = 2 * position + int(role is TokenRole.PAD), None
        closing_key = (source, target, label, Fraction(), 0, position, token, role)
        expected_closings[closing_key] += 1
        # Independently aggregate original proposal rows, without sharing the
        # compiler's aggregation function or trusting a precomputed reward.
        reward = sum(
            (
                Fraction(p.weight)
                for p in state.proposals
                if p.position == position and p.token_id == token
            ),
            Fraction(),
        )
        if state.canvas[position] is None and reward > 0:
            expected_closings[source, target, label, reward, 1, position, token, role] += 1

    closing_by_id = {end.arc_id: end for end in compiled.closings}
    if len(closing_by_id) != len(compiled.closings):
        errors.append("duplicate closing identity")
    if not set(closing_by_id) <= {a.arc_id for a in compiled.graph.arcs}:
        errors.append("closing identity is not an original arc")
    actual_prefix_arcs: Counter[ArcKey] = Counter()
    actual_closings: Counter[ClosingKey] = Counter()
    for arc in compiled.graph.arcs:
        base = (arc.source, arc.target, arc.label, arc.reward, arc.cost)
        closing = closing_by_id.get(arc.arc_id)
        if closing is None:
            actual_prefix_arcs[base] += 1
        else:
            actual_closings[(*base, closing.position, closing.token_id, closing.role)] += 1
    if actual_prefix_arcs != expected_prefix_arcs:
        errors.append("prefix arcs do not exactly represent original emissions")
    if actual_closings != expected_closings:
        errors.append("token closures do not exactly represent original choices and rewards")
    expected_finals = (
        (2 * count + 1,)
        if state.eos_policy.mode is EOSMode.REQUIRED
        else (2 * count, 2 * count + 1)
        if state.eos_policy.mode is EOSMode.OPTIONAL
        else (2 * count,)
    )
    if compiled.graph.start != 0 or compiled.graph.finals != expected_finals:
        errors.append("graph endpoints do not match original EOS policy")
    scope = f"exact_on_support: {state.support.fingerprint}; EOS={state.eos_policy.to_dict()}"
    if compiled.graph.support_description != scope:
        errors.append("graph support specification differs from original input")
    return BudgetCertificateReport(not errors, tuple(sorted(set(errors))))


def check_budget_commit_certificate(
    state: SelectionInput, result: BudgetedCommitResult
) -> BudgetCertificateReport:
    """Verify both original-input correspondence and resource-graph optimality."""
    graph_report = check_budget_graph(state, result.compiled_graph)
    if not graph_report.accepted:
        return graph_report
    errors: list[str] = []
    path = result.path_result
    if result.proof_graph != result.compiled_graph.graph:
        errors.append("result graph differs from checked compiled graph")
    if (result.budget, result.status, result.objective_value) != (
        path.budget,
        path.status,
        path.objective_value,
    ):
        errors.append("result metadata differs from the resource proof")
    if result.exactness_scope != state.support.exactness_scope:
        errors.append("result exactness scope differs from original input")
    if result.input_fingerprint != budget_input_fingerprint(state):
        errors.append("result belongs to a different original input")
    if errors:
        return BudgetCertificateReport(False, tuple(errors))
    report = check_budget_certificate(state.grammar, result.proof_graph, path)
    if not report.accepted:
        return report
    if result.status is SolveStatus.OPTIMAL:
        if result.witness_token_ids is None or path.witness_arc_ids is None:
            return BudgetCertificateReport(False, ("missing original token witness",))
        try:
            batch = validate_budget_batch(
                state,
                budget=result.budget,
                witness_token_ids=result.witness_token_ids,
                committed_positions=result.committed_positions,
            )
            closing = {end.arc_id: end for end in result.compiled_graph.closings}
            arcs = {a.arc_id: a for a in result.proof_graph.arcs}
            ends = [closing[a] for a in path.witness_arc_ids if a in closing]
            tokens = tuple(end.token_id for end in ends)
            positions = tuple(end.position for end in ends)
            commits = tuple(closing[a].position for a in path.witness_arc_ids if arcs[a].cost)
            if tokens != batch.witness_token_ids or positions != tuple(range(len(state.canvas))):
                errors.append("resource path does not encode the claimed original tokens")
            if commits != batch.committed_positions:
                errors.append("resource path does not encode the claimed physical commitments")
            if (
                batch.reward != result.objective_value
                or batch.committed_proposal_ids != result.committed_proposal_ids
                or batch.matched_proposal_ids != result.matched_proposal_ids
                or tuple(batch.emitted_bytes) != result.witness_terminal_labels
                or result.witness_terminal_labels != path.witness_terminal_labels
            ):
                errors.append("original batch metadata differs from independent recomputation")
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"invalid original batch: {exc}")
    elif (
        result.witness_token_ids is not None
        or result.witness_terminal_labels is not None
        or result.committed_positions
        or result.committed_proposal_ids
        or result.matched_proposal_ids
    ):
        errors.append("infeasible result carries original witness metadata")
    return BudgetCertificateReport(not errors, tuple(sorted(set(errors))))
