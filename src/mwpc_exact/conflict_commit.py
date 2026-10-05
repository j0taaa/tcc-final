"""Exact budgeted commitment by certified implicit conflict learning.

The established implicit hitting-set principle is specialized to finite-slot
CFG feasibility. The oracle carries no model scores; all optimization and
certificate bounds use exact rationals. Cached conflicts are used only after
checking completion-set containment.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from math import isfinite
from time import monotonic

from mwpc_exact.backend import ExactBackend
from mwpc_exact.budget_bounds import budget_input_fingerprint, validate_budget_batch
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.conflict_certificate import (
    CertifiedConflict,
    Choice,
    ConflictCommitCertificate,
    ConflictCommitResult,
    MasterNode,
    active_conflict,
    check_conflict_commit,
    relaxed_batch,
    restrict_choices,
    retained_support,
    rewarded_choices,
    token_path_ids,
)
from mwpc_exact.evaluation.selection import (
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    select_exact_mwpc,
)
from mwpc_exact.reference.budget_types import nonnegative_integer
from mwpc_exact.types import SolveStatus


class _Deadline(Exception):
    pass


def _master(
    state: SelectionInput,
    choices: tuple[tuple[Choice, Fraction], ...],
    budget: int,
    conflicts: tuple[CertifiedConflict, ...],
    deadline: float | None,
) -> tuple[tuple[int, ...] | None, tuple[MasterNode, ...]]:
    indices = {choice: j for j, (choice, _) in enumerate(choices)}
    cores = [active_conflict(state, conflict, indices) for conflict in conflicts]
    nodes: list[MasterNode] = []
    memo: dict[tuple[int, ...], tuple[tuple[int, ...] | None, int]] = {}

    def visit(excluded: tuple[int, ...]) -> tuple[tuple[int, ...] | None, int]:
        if deadline is not None and monotonic() >= deadline:
            raise _Deadline
        if excluded in memo:
            return memo[excluded]
        selected, upper = relaxed_batch(choices, budget, excluded)
        node_id = len(nodes)
        nodes.append(MasterNode(excluded, upper))
        violated = next(
            (j for j, core in enumerate(cores) if core is not None and set(core) <= set(selected)),
            None,
        )
        if violated is None:
            memo[excluded] = selected, node_id
            return selected, node_id
        core = cores[violated]
        assert core is not None
        children = []
        best: tuple[int, ...] | None = None
        best_score: Fraction | None = None
        for member in core:
            candidate, child = visit(tuple(sorted((*excluded, member))))
            children.append(child)
            value = nodes[child].upper_bound
            if value is not None and (best_score is None or value > best_score):
                best, best_score = candidate, value
        nodes[node_id] = MasterNode(excluded, best_score, violated, tuple(children))
        memo[excluded] = best, node_id
        return best, node_id

    best, root = visit(())
    assert root == 0
    return best, tuple(nodes)


class ConflictCommitSolver:
    """A private, input-scoped conflict cache; no global or model-specific state."""

    def __init__(self, *, backend: ExactBackend = ExactBackend.RUST) -> None:
        if not isinstance(backend, ExactBackend):
            raise TypeError("backend must be an ExactBackend")
        self.backend = backend
        self._conflicts: list[CertifiedConflict] = []

    def solve(
        self,
        state: SelectionInput,
        budget: int,
        *,
        timeout_seconds: float | None = None,
        max_oracle_calls: int | None = None,
    ) -> ConflictCommitResult:
        nonnegative_integer(budget, "budget")
        if timeout_seconds is not None and (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not isfinite(timeout_seconds)
            or timeout_seconds < 0
        ):
            raise ValueError("timeout_seconds must be finite and non-negative")
        if max_oracle_calls is not None:
            nonnegative_integer(max_oracle_calls, "max_oracle_calls")
        deadline = None if timeout_seconds is None else monotonic() + timeout_seconds
        conflicts = [c for c in self._conflicts if retained_support(c.source, state)]
        reused = len(conflicts)
        learned = 0
        calls = 0
        choices = rewarded_choices(state)

        def oracle(batch: tuple[Choice, ...]) -> SelectionResult:
            nonlocal calls
            if (max_oracle_calls is not None and calls >= max_oracle_calls) or (
                deadline is not None and monotonic() >= deadline
            ):
                raise _Deadline
            calls += 1
            restricted = restrict_choices(state, batch)
            timeout = (
                max(0.0, deadline - monotonic())
                if deadline is not None and self.backend is ExactBackend.RUST
                else None
            )
            answer = select_exact_mwpc(restricted, backend=self.backend, timeout_seconds=timeout)
            if answer.status is SelectionStatus.TIMEOUT:
                raise _Deadline
            if answer.status not in (
                SelectionStatus.OPTIMAL,
                SelectionStatus.INFEASIBLE_ON_SUPPORT,
            ):
                raise RuntimeError(f"finite CFG oracle failed: {answer.status}")
            return answer

        try:
            while True:
                candidate, nodes = _master(state, choices, budget, tuple(conflicts), deadline)
                certificate = ConflictCommitCertificate(
                    budget_input_fingerprint(state), tuple(conflicts), nodes, 0
                )
                if candidate is None:
                    result = ConflictCommitResult(
                        SolveStatus.INFEASIBLE_ON_SUPPORT,
                        budget,
                        None,
                        (),
                        (),
                        (),
                        None,
                        state.support.exactness_scope,
                        certificate,
                        calls,
                        learned,
                        reused,
                    )
                    check_conflict_commit(state, result)
                    return result
                batch = tuple(choices[j][0] for j in candidate)
                answer = oracle(batch)
                if answer.status is SelectionStatus.OPTIMAL:
                    assert answer.witness_token_ids is not None
                    checked = validate_budget_batch(
                        state,
                        budget=budget,
                        witness_token_ids=answer.witness_token_ids,
                        committed_positions=tuple(p for p, _ in batch),
                    )
                    result = ConflictCommitResult(
                        SolveStatus.OPTIMAL,
                        budget,
                        checked.reward,
                        checked.committed_positions,
                        checked.committed_proposal_ids,
                        checked.matched_proposal_ids,
                        checked.witness_token_ids,
                        state.support.exactness_scope,
                        certificate,
                        calls,
                        learned,
                        reused,
                        token_path_ids(state, checked.witness_token_ids),
                    )
                    check_conflict_commit(state, result)
                    return result
                # Deletion yields an inclusion-minimal conflict, never a guessed
                # conflict. Timeout in any deletion aborts unresolved, not UNSAT.
                core = list(batch)
                for choice in batch:
                    trial = tuple(c for c in core if c != choice)
                    if oracle(trial).status is SelectionStatus.INFEASIBLE_ON_SUPPORT:
                        core.remove(choice)
                basis = replace(state, proposals=())
                restricted = restrict_choices(basis, tuple(core))
                proof = budgeted_commit_frontier(restricted, 0)[0]
                if proof.status is not SolveStatus.INFEASIBLE_ON_SUPPORT:
                    raise RuntimeError("independent CFG proof disagrees with the oracle")
                conflict = CertifiedConflict(basis, tuple(core), proof)
                conflicts.append(conflict)
                self._conflicts.append(conflict)
                learned += 1
        except _Deadline:
            return ConflictCommitResult(
                SolveStatus.TIMEOUT,
                budget,
                None,
                (),
                (),
                (),
                None,
                state.support.exactness_scope,
                None,
                calls,
                learned,
                reused,
            )
