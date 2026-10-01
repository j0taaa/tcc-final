"""Joint selection under a physical-position budget, separate from ordinary MWPC.

This is an exact-rational research API, not a claim of fast production inference.
It accepts the same model-independent frozen state as the existing selectors.
Full witness matches and actual budgeted commitments are distinct fields.
"""

from __future__ import annotations

from mwpc_exact.budget_bounds import budget_input_fingerprint, validate_budget_batch
from mwpc_exact.budget_certificate import check_budget_commit_certificate
from mwpc_exact.budget_graph import (
    BudgetGraphLayout,
    compile_budget_graph,
    reconstruct_budget_tokens,
)
from mwpc_exact.budget_result import BudgetedCommitResult as BudgetedCommitResult
from mwpc_exact.evaluation.selection import SelectionInput
from mwpc_exact.reference.budgeted_parser import budgeted_frontier
from mwpc_exact.types import SolveStatus


def budgeted_commit_frontier(
    state: SelectionInput,
    max_budget: int,
    *,
    graph_layout: BudgetGraphLayout = BudgetGraphLayout.COMPACT,
) -> tuple[BudgetedCommitResult, ...]:
    """Maximize committed proposal reward jointly over all free slots and tokens."""
    fingerprint = budget_input_fingerprint(state)
    compiled = compile_budget_graph(state, layout=graph_layout)
    graph = compiled.graph
    results: list[BudgetedCommitResult] = []
    for path in budgeted_frontier(state.grammar, graph, max_budget):
        tokens = None
        commits: tuple[int, ...] = ()
        matched: tuple[int, ...] = ()
        committed_ids: tuple[int, ...] = ()
        if path.witness_arc_ids is not None:
            tokens, commits = reconstruct_budget_tokens(compiled, path.witness_arc_ids)
            if len(set(commits)) != len(commits) or len(commits) != path.consumed_budget:
                raise RuntimeError("Resource path double charges a physical slot")
            batch = validate_budget_batch(
                state, budget=path.budget, witness_token_ids=tokens, committed_positions=commits
            )
            matched, committed_ids = batch.matched_proposal_ids, batch.committed_proposal_ids
            if (
                batch.reward != path.objective_value
                or tuple(batch.emitted_bytes) != path.witness_terminal_labels
            ):
                raise RuntimeError("Budgeted objective does not equal original committed weights")
        result = BudgetedCommitResult(
            path.status,
            path.budget,
            path.objective_value,
            commits,
            committed_ids,
            matched,
            tokens,
            path.witness_terminal_labels,
            state.support.exactness_scope,
            path,
            graph,
            fingerprint,
            compiled,
        )
        full_report = check_budget_commit_certificate(state, result)
        if not full_report.accepted:
            raise RuntimeError(f"Original-input budget proof rejected: {full_report.errors}")
        results.append(result)
    return tuple(results)


def solve_budgeted_commit(
    state: SelectionInput,
    budget: int,
    *,
    graph_layout: BudgetGraphLayout = BudgetGraphLayout.COMPACT,
) -> BudgetedCommitResult:
    """One-cap convenience API; existing serial/EPIC/exact strategies are unchanged."""
    return budgeted_commit_frontier(state, budget, graph_layout=graph_layout)[budget]


def budgeted_progress_update(
    state: SelectionInput, result: BudgetedCommitResult
) -> tuple[tuple[int | None, ...], tuple[int, ...]]:
    """Fill up to B free slots from the certified witness; fallback has no reward."""
    if result.status is not SolveStatus.OPTIMAL or result.witness_token_ids is None:
        raise ValueError("progress requires an OPTIMAL witness")
    if result.budget == 0 and any(t is None for t in state.canvas):
        raise ValueError("a zero budget cannot guarantee progress")
    # Check state compatibility rather than silently accepting another state's witness.
    if result.input_fingerprint != budget_input_fingerprint(state):
        raise ValueError("result belongs to a different frozen input")
    report = check_budget_commit_certificate(state, result)
    if not report.accepted:
        raise ValueError(f"invalid original-input budget certificate: {report.errors}")
    chosen = list(result.committed_positions)
    fallback: list[int] = []
    for i, token in enumerate(state.canvas):
        if len(chosen) == result.budget:
            break
        if token is None and i not in chosen:
            chosen.append(i)
            fallback.append(i)
    updated = list(state.canvas)
    for i in chosen:
        updated[i] = result.witness_token_ids[i]
    if any(
        p.weight > 0
        and p.position in fallback
        and result.witness_token_ids[p.position] == p.token_id
        for p in state.proposals
    ):
        raise RuntimeError("unscored fallback contradicts budget optimality")
    return tuple(updated), tuple(fallback)
