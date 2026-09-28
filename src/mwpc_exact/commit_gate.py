"""Counterfactual commitment gate around the unchanged exact optimizer.

Alternative-token bonus B > sum(original weights) reduces each counterfactual
query to ordinary non-negative MWPC on exactly the original support. If an
alternative exists, every optimum receives B. Rescoring uses original proposals.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from math import fsum, isfinite
from time import perf_counter

from mwpc_exact.backend import ExactBackend
from mwpc_exact.evaluation.selection import (
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    recompute_witness_selection,
    select_exact_mwpc,
)
from mwpc_exact.profiling import ComponentProfiler
from mwpc_exact.types import Proposal


@dataclass(frozen=True)
class CounterfactualMargin:
    position: int
    forced_on_support: bool
    alternative_score: float | None
    margin: float | None
    result: SelectionResult


@dataclass(frozen=True)
class CommitGateResult:
    status: SelectionStatus
    optimizer: SelectionResult | None
    queries: tuple[CounterfactualMargin, ...]
    certified_positions: tuple[int, ...]
    committed_positions: tuple[int, ...]
    progress_fallback: bool
    runtime_seconds: float


def select_stable_commit(
    state: SelectionInput,
    *,
    tolerance: float,
    total_timeout_seconds: float = 10.0,
    numerical_guard: float = 1e-10,
    backend: ExactBackend = ExactBackend.RUST,
    profiler: ComponentProfiler | None = None,
    clock: Callable[[], float] = perf_counter,
) -> CommitGateResult:
    """Return a conservative stable subset, or a separately labelled progress token.

    Failure/late queries produce no commits. ``OPTIMAL`` describes completed
    counterfactual optimization on this support, not semantic or trajectory quality.
    The numerical guard deliberately defers near-boundary floating-point cases.
    """
    for name, value in (
        ("tolerance", tolerance),
        ("total_timeout_seconds", total_timeout_seconds),
        ("numerical_guard", numerical_guard),
    ):
        if isinstance(value, bool) or not isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and non-negative")
    started = clock()
    total_weight = fsum(p.weight for p in state.proposals)
    bonus = total_weight + max(1.0, total_weight)
    if not isfinite(bonus) or not bonus > total_weight:
        raise ValueError("counterfactual bonus overflow")
    guard = numerical_guard * max(1.0, total_weight)
    queries: list[CounterfactualMargin] = []
    optimum: SelectionResult | None = None

    def finish(
        status: SelectionStatus,
        certified: tuple[int, ...] = (),
        commits: tuple[int, ...] = (),
        fallback: bool = False,
    ) -> CommitGateResult:
        elapsed = clock() - started
        if elapsed >= total_timeout_seconds:
            status, certified, commits, fallback = SelectionStatus.TIMEOUT, (), (), False
        return CommitGateResult(
            status, optimum, tuple(queries), certified, commits, fallback, elapsed
        )

    def solve(query: SelectionInput) -> SelectionResult | None:
        remaining = total_timeout_seconds - (clock() - started)
        if remaining <= 0:
            return None
        return select_exact_mwpc(
            query,
            backend=backend,
            timeout_seconds=remaining if backend is ExactBackend.RUST else None,
            profiler=profiler,
        )

    optimum = solve(state)
    if optimum is None:
        return finish(SelectionStatus.TIMEOUT)
    if optimum.status is not SelectionStatus.OPTIMAL:
        return finish(optimum.status)
    assert optimum.score is not None
    selected = set(optimum.selected_proposal_ids)
    positions = sorted(
        {
            p.position
            for p in state.proposals
            if p.proposal_id in selected and state.canvas[p.position] is None
        }
    )
    next_id = max((p.proposal_id for p in state.proposals), default=-1) + 1
    certified = []
    for position in positions:
        chosen = optimum.witness_token_ids[position]
        alternatives = [t for t in state.support.rows[position] if t != chosen]
        added = tuple(Proposal(next_id + i, position, t, bonus) for i, t in enumerate(alternatives))
        query = replace(state, proposals=state.proposals + added)
        result = solve(query)
        if result is None:
            return finish(SelectionStatus.TIMEOUT)
        if result.status is not SelectionStatus.OPTIMAL:
            # Original witness still exists. Infeasibility here is inconsistent.
            status = (
                SelectionStatus.ERROR
                if result.status is SelectionStatus.INFEASIBLE_ON_SUPPORT
                else result.status
            )
            queries.append(CounterfactualMargin(position, False, None, None, result))
            return finish(status)
        forced = result.witness_token_ids[position] == chosen
        alternative_score = None
        margin = None
        if not forced:
            _, alternative_score = recompute_witness_selection(state, result.witness_token_ids)
            margin = optimum.score - alternative_score
            if margin < -guard:
                queries.append(
                    CounterfactualMargin(position, False, alternative_score, margin, result)
                )
                return finish(SelectionStatus.ERROR)
        queries.append(CounterfactualMargin(position, forced, alternative_score, margin, result))
        if forced or (margin is not None and margin > tolerance + guard):
            certified.append(position)
    commits = tuple(certified)
    fallback = False
    if not commits and any(token is None for token in state.canvas):
        fallback = True
        candidates = [
            p for p in state.proposals if p.proposal_id in selected and p.position in positions
        ]
        position = (
            max(candidates, key=lambda p: (p.weight, -p.position)).position
            if candidates
            else state.canvas.index(None)
        )
        commits = (position,)
    return finish(SelectionStatus.OPTIMAL, tuple(certified), commits, fallback)
