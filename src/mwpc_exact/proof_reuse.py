"""Two-sided certificate reuse under changing logits and finite support.

Infeasible conflicts transport under completion-set contraction. Feasible token
witnesses are tested against the new original input and may survive expansion.
When a retained witness attains the exact relaxed master bound, no CFG oracle
query or resource optimization is necessary. Independent checking stays required.
"""

from __future__ import annotations

from mwpc_exact.backend import ExactBackend
from mwpc_exact.budget_bounds import budget_input_fingerprint, validate_budget_batch
from mwpc_exact.conflict_certificate import (
    CertifiedConflict,
    ConflictCommitCertificate,
    ConflictCommitResult,
    check_conflict_commit,
    retained_support,
    rewarded_choices,
    token_path_ids,
)
from mwpc_exact.conflict_commit import ConflictCommitSolver, _master
from mwpc_exact.reference.budget_types import nonnegative_integer
from mwpc_exact.state import SelectionInput
from mwpc_exact.types import SolveStatus


class ProofReuseSolver:
    """Reusable exact solver; all caches belong to this explicitly created object."""

    def __init__(
        self, *, backend: ExactBackend = ExactBackend.RUST, use_conflicts: bool = True
    ) -> None:
        self._solver = ConflictCommitSolver(backend=backend)
        self._backend = backend
        self._use_conflicts = use_conflicts
        self._known_conflicts: list[CertifiedConflict] = []
        self._witnesses: list[tuple[int, ...]] = []

    def solve(self, state: SelectionInput, budget: int) -> ConflictCommitResult:
        nonnegative_integer(budget, "budget")
        # A witness is not keyed by scores or support size. The original-input
        # validator tests its bytes, grammar, fixed slots, EOS/PAD and every row.
        conflicts = (
            tuple(c for c in self._known_conflicts if retained_support(c.source, state))
            if self._use_conflicts
            else ()
        )
        candidate, nodes = _master(state, rewarded_choices(state), budget, conflicts, None)
        if candidate is not None:
            choices = rewarded_choices(state)
            selected = tuple(choices[j][0] for j in candidate)
            for witness in reversed(self._witnesses):
                if len(witness) != len(state.canvas) or any(
                    witness[p] != token for p, token in selected
                ):
                    continue
                try:
                    checked = validate_budget_batch(
                        state,
                        budget=budget,
                        witness_token_ids=witness,
                        committed_positions=tuple(p for p, _ in selected),
                    )
                except ValueError:
                    continue
                result = ConflictCommitResult(
                    SolveStatus.OPTIMAL,
                    budget,
                    checked.reward,
                    checked.committed_positions,
                    checked.committed_proposal_ids,
                    checked.matched_proposal_ids,
                    witness,
                    state.support.exactness_scope,
                    ConflictCommitCertificate(budget_input_fingerprint(state), conflicts, nodes, 0),
                    0,
                    0,
                    len(conflicts),
                    token_path_ids(state, witness),
                )
                check_conflict_commit(state, result)
                return result
        engine = (
            self._solver if self._use_conflicts else ConflictCommitSolver(backend=self._backend)
        )
        answer = engine.solve(state, budget)
        if answer.certificate is not None:
            for conflict in answer.certificate.conflicts:
                if conflict not in self._known_conflicts:
                    self._known_conflicts.append(conflict)
        if answer.witness_token_ids is not None and answer.witness_token_ids not in self._witnesses:
            self._witnesses.append(answer.witness_token_ids)
        return answer
