"""Certify a feasible batch without running the budgeted optimizer.

The upper bound ignores grammar and includes ALL frozen proposals, even those
outside the current support. It applies to expansions with unchanged proposals.
It can be loose. These certificates are not semantic-accuracy guarantees and
do not change solver statuses or the represented exactness scope.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction

from mwpc_exact.eos_policy import EOSMode
from mwpc_exact.reference.budget_types import nonnegative_integer
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.types import ExactnessScope


def budget_input_fingerprint(state: SelectionInput) -> str:
    """Bind mathematical results to the original frozen finite input."""
    used = sorted({t for row in state.support.rows for t in row})
    data = {
        "grammar": state.grammar.to_dict(),
        "canvas": state.canvas,
        "rows": state.support.rows,
        "scope": state.support.exactness_scope.to_dict(),
        "proposals": [(p.proposal_id, p.position, p.token_id, p.weight) for p in state.proposals],
        "eos": state.eos_policy.to_dict(),
        "emissions": {
            t: None
            if state.tokenizer_adapter.emissions[t] is None
            else state.tokenizer_adapter.token_bytes(t).hex()
            for t in used
        },
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def proposal_rewards(state: SelectionInput) -> dict[tuple[int, int], Fraction]:
    """Aggregate duplicate matches exactly; floats denote their binary rationals."""
    rewards: dict[tuple[int, int], Fraction] = {}
    for proposal in state.proposals:
        key = (proposal.position, proposal.token_id)
        rewards[key] = rewards.get(key, Fraction()) + Fraction(proposal.weight)
    return rewards


def unconstrained_budget_bound(state: SelectionInput, budget: int) -> Fraction:
    """An upper bound over every support expansion with the same frozen proposals."""
    nonnegative_integer(budget, "budget")
    maxima = [Fraction() for _ in state.canvas]
    for (position, _), reward in proposal_rewards(state).items():
        if state.canvas[position] is None:
            maxima[position] = max(maxima[position], reward)
    return sum(sorted(maxima, reverse=True)[:budget], Fraction())


@dataclass(frozen=True)
class ValidatedBudgetBatch:
    witness_token_ids: tuple[int, ...]
    emitted_bytes: bytes
    committed_positions: tuple[int, ...]
    committed_proposal_ids: tuple[int, ...]
    matched_proposal_ids: tuple[int, ...]
    reward: Fraction


def validate_budget_batch(
    state: SelectionInput,
    *,
    budget: int,
    witness_token_ids: Iterable[int],
    committed_positions: Iterable[int],
) -> ValidatedBudgetBatch:
    """Check original tokens, fixed slots, EOS/PAD, grammar and exact reward.

    This does not construct a lattice or import any weighted optimizer. The
    Boolean recognizer is independently implemented from the resource parser.
    """
    nonnegative_integer(budget, "budget")
    if isinstance(witness_token_ids, (str, bytes)):
        raise ValueError("witness_token_ids must contain integer token IDs")
    if isinstance(committed_positions, (str, bytes)):
        raise ValueError("committed_positions must contain integer positions")
    tokens = tuple(witness_token_ids)
    positions = tuple(committed_positions)
    if len(tokens) != len(state.canvas):
        raise ValueError("witness must consume exactly the physical slots")
    for position, token in enumerate(tokens):
        nonnegative_integer(token, "witness token")
        if token not in state.support.rows[position]:
            raise ValueError("witness token is outside represented support")
        if state.canvas[position] is not None and token != state.canvas[position]:
            raise ValueError("witness changes a fixed position")
    for position in positions:
        nonnegative_integer(position, "committed position")
        if position >= len(tokens) or state.canvas[position] is not None:
            raise ValueError("commitments must target free physical positions")
    if len(set(positions)) != len(positions) or len(positions) > budget:
        raise ValueError("duplicate positions or exceeded physical budget")

    emitted = bytearray()
    after_eos = False
    policy = state.eos_policy
    for token in tokens:
        if policy.mode is not EOSMode.ABSENT:
            if after_eos:
                if token != policy.pad_token_id:
                    raise ValueError("only PAD is permitted after EOS")
                continue
            if token in policy.termination_token_ids:
                after_eos = True
                continue
            if token == policy.pad_token_id:
                raise ValueError("PAD before EOS is invalid")
        emission = state.tokenizer_adapter.emissions[token]
        if emission is None:
            raise ValueError("ordinary token has no byte emission")
        emitted.extend(emission)
    if policy.mode is EOSMode.REQUIRED and not after_eos:
        raise ValueError("required EOS is missing")
    if not recognizes_cnf(state.grammar, tuple(emitted)):
        raise ValueError("witness bytes are not accepted by the grammar")

    chosen = set(positions)
    matched = tuple(
        p.proposal_id for p in state.proposals if p.weight > 0 and tokens[p.position] == p.token_id
    )
    committed = tuple(
        p.proposal_id
        for p in state.proposals
        if p.weight > 0 and p.position in chosen and tokens[p.position] == p.token_id
    )
    reward = sum(
        (
            Fraction(p.weight)
            for p in state.proposals
            if p.weight > 0 and p.position in chosen and tokens[p.position] == p.token_id
        ),
        Fraction(),
    )
    return ValidatedBudgetBatch(
        tokens, bytes(emitted), tuple(sorted(positions)), committed, matched, reward
    )


@dataclass(frozen=True)
class BatchQualityCertificate:
    """A verified lower bound plus a support-independent relaxation upper bound."""

    budget: int
    batch: ValidatedBudgetBatch
    upper_bound: Fraction
    exactness_scope: ExactnessScope
    input_fingerprint: str

    @property
    def lower_bound(self) -> Fraction:
        return self.batch.reward

    @property
    def additive_gap_bound(self) -> Fraction:
        return self.upper_bound - self.lower_bound

    @property
    def approximation_ratio(self) -> Fraction:
        return self.lower_bound / self.upper_bound if self.upper_bound else Fraction(1)

    @property
    def optimal_under_support_expansion(self) -> bool:
        """True only for the SAME proposals/weights/fixed slots/grammar/EOS."""
        return self.lower_bound == self.upper_bound


def certify_budget_batch(
    state: SelectionInput,
    *,
    budget: int,
    witness_token_ids: Iterable[int],
    committed_positions: Iterable[int] | None = None,
) -> BatchQualityCertificate:
    """Certify an incumbent, optionally choosing its best B rewarded positions.

    A valid witness is required even for B=0. No optimizer runs and no timeout
    is converted into infeasibility. Callers can keep this certificate when a
    subsequent attempt to improve their incumbent exhausts its time budget.
    """
    nonnegative_integer(budget, "budget")
    if isinstance(witness_token_ids, (str, bytes)):
        raise ValueError("witness_token_ids must contain integer token IDs")
    tokens = tuple(witness_token_ids)
    if len(tokens) != len(state.canvas):
        raise ValueError("witness must consume exactly the physical slots")
    for token in tokens:
        nonnegative_integer(token, "witness token")
    if committed_positions is None:
        rewards = proposal_rewards(state)
        candidates = [
            (rewards.get((i, token), Fraction()), i)
            for i, token in enumerate(tokens)
            if state.canvas[i] is None and rewards.get((i, token), Fraction()) > 0
        ]
        committed_positions = tuple(
            i for _, i in sorted(candidates, key=lambda x: (-x[0], x[1]))[:budget]
        )
    batch = validate_budget_batch(
        state, budget=budget, witness_token_ids=tokens, committed_positions=committed_positions
    )
    upper = unconstrained_budget_bound(state, budget)
    if batch.reward > upper:
        raise RuntimeError("validated batch contradicts the relaxation upper bound")
    return BatchQualityCertificate(
        budget, batch, upper, state.support.exactness_scope, budget_input_fingerprint(state)
    )
