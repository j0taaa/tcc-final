"""Independent original-input checker for conflict-guided commitment.

No search optimizer is imported. Certified CFG-infeasible choice sets plus a
cover of the master search space prove an upper bound; a token witness proves
the matching lower bound. Established resource proofs certify each conflict.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from typing import cast

from mwpc_exact.budget_bounds import (
    budget_input_fingerprint,
    proposal_rewards,
    validate_budget_batch,
)
from mwpc_exact.budget_certificate import check_budget_commit_certificate
from mwpc_exact.budget_result import BudgetedCommitResult
from mwpc_exact.reference.budget_types import nonnegative_integer
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.types import ExactnessScope, SolveStatus, SupportKind

Choice = tuple[int, int]


def restrict_choices(state: SelectionInput, choices: tuple[Choice, ...]) -> SelectionInput:
    """Fix represented choices, retain every other row, and remove all rewards."""
    assignments: dict[int, int] = {}
    for position, token in choices:
        nonnegative_integer(position, "position")
        nonnegative_integer(token, "token")
        if position >= len(state.canvas) or token not in state.support.rows[position]:
            raise ValueError("conflict choice is outside the original support")
        if position in assignments or state.canvas[position] not in (None, token):
            raise ValueError("duplicate or contradictory conflict position")
        assignments[position] = token
    canvas = tuple(assignments.get(i, t) for i, t in enumerate(state.canvas))
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=state.tokenizer_adapter.vocabulary_size,
            required_special_token_ids=state.support.exactness_scope.included_special_tokens,
        ),
        explicit_support={
            i: row if canvas[i] is None else (cast(int, canvas[i]),)
            for i, row in enumerate(state.support.rows)
        },
    )
    return replace(state, canvas=canvas, support=support, proposals=())


def retained_support(source: SelectionInput, target: SelectionInput) -> bool:
    """Sufficient, deliberately conservative proof of completion-set containment."""
    return (
        source.grammar == target.grammar
        and source.eos_policy == target.eos_policy
        and source.tokenizer_adapter == target.tokenizer_adapter
        and len(source.canvas) == len(target.canvas)
        and all(a is None or a == b for a, b in zip(source.canvas, target.canvas, strict=True))
        and all(
            set(b) <= set(a) for a, b in zip(source.support.rows, target.support.rows, strict=True)
        )
    )


def rewarded_choices(state: SelectionInput) -> tuple[tuple[Choice, Fraction], ...]:
    return tuple(
        sorted(
            (choice, reward)
            for choice, reward in proposal_rewards(state).items()
            if reward > 0
            and state.canvas[choice[0]] is None
            and choice[1] in state.support.rows[choice[0]]
        )
    )


def relaxed_batch(
    choices: tuple[tuple[Choice, Fraction], ...], budget: int, excluded: tuple[int, ...]
) -> tuple[tuple[int, ...], Fraction]:
    """Exact uniform-budget relaxation: one highest allowed token per position."""
    removed = set(excluded)
    best: dict[int, int] = {}
    for j, ((position, _), reward) in enumerate(choices):
        if j not in removed and (position not in best or reward > choices[best[position]][1]):
            best[position] = j
    selected = tuple(sorted(sorted(best.values(), key=lambda j: (-choices[j][1], j))[:budget]))
    return selected, sum((choices[j][1] for j in selected), Fraction())


def active_conflict(
    state: SelectionInput, conflict: CertifiedConflict, indices: dict[Choice, int]
) -> tuple[int, ...] | None:
    """Discharge already fixed matches; contradictory/absent members cannot occur."""
    core = []
    for position, token in conflict.choices:
        fixed = state.canvas[position]
        if fixed is not None:
            if fixed != token:
                return None
        elif (position, token) in indices:
            core.append(indices[position, token])
        else:
            return None
    return tuple(core)


@dataclass(frozen=True)
class CertifiedConflict:
    source: SelectionInput
    choices: tuple[Choice, ...]
    infeasibility: BudgetedCommitResult


@dataclass(frozen=True)
class MasterNode:
    excluded: tuple[int, ...]
    upper_bound: Fraction | None
    conflict_index: int | None = None
    children: tuple[int, ...] = ()


@dataclass(frozen=True)
class ConflictCommitCertificate:
    input_fingerprint: str
    conflicts: tuple[CertifiedConflict, ...]
    master_nodes: tuple[MasterNode, ...]
    root: int


@dataclass(frozen=True)
class ConflictCommitResult:
    status: SolveStatus
    budget: int
    objective_value: Fraction | None
    committed_positions: tuple[int, ...]
    committed_proposal_ids: tuple[int, ...]
    matched_proposal_ids: tuple[int, ...]
    witness_token_ids: tuple[int, ...] | None
    exactness_scope: ExactnessScope
    certificate: ConflictCommitCertificate | None
    oracle_calls: int
    learned_conflicts: int
    reused_conflicts: int
    witness_graph_edge_ids: tuple[int, ...] | None = None


def token_path_ids(state: SelectionInput, tokens: tuple[int, ...]) -> tuple[int, ...]:
    """Canonical original token-lattice edges, retaining all physical slots."""
    offset = 0
    path = []
    for row, token in zip(state.support.rows, tokens, strict=True):
        path.append(offset + row.index(token))
        offset += len(row)
    return tuple(path)


def check_conflict_commit(state: SelectionInput, result: ConflictCommitResult) -> None:
    """Raise on forged/foreign certificates; never execute a weighted optimizer."""
    nonnegative_integer(result.budget, "budget")
    if not isinstance(result.status, SolveStatus):
        raise ValueError("status must be an explicit SolveStatus")
    for values in (
        result.committed_positions,
        result.committed_proposal_ids,
        result.matched_proposal_ids,
    ):
        for value in values:
            nonnegative_integer(value, "selected identifier")
    if result.status not in (SolveStatus.OPTIMAL, SolveStatus.INFEASIBLE_ON_SUPPORT):
        raise ValueError("unresolved status has no exact conflict certificate")
    certificate = result.certificate
    if certificate is None or certificate.input_fingerprint != budget_input_fingerprint(state):
        raise ValueError("missing or foreign original-input certificate")
    if result.exactness_scope != state.support.exactness_scope:
        raise ValueError("certificate support scope differs from the input")
    choices = rewarded_choices(state)
    indices = {choice: j for j, (choice, _) in enumerate(choices)}
    cores: list[tuple[int, ...] | None] = []
    for conflict in certificate.conflicts:
        if not retained_support(conflict.source, state):
            raise ValueError("conflict reuse lacks retained-support containment")
        restricted = restrict_choices(conflict.source, conflict.choices)
        proof = conflict.infeasibility
        if proof.status is not SolveStatus.INFEASIBLE_ON_SUPPORT or proof.budget != 0:
            raise ValueError("conflict does not carry a zero-resource infeasibility proof")
        report = check_budget_commit_certificate(restricted, proof)
        if not report.accepted:
            raise ValueError(f"invalid CFG conflict proof: {report.errors}")
        cores.append(active_conflict(state, conflict, indices))
    nodes = certificate.master_nodes
    nonnegative_integer(certificate.root, "root")
    if certificate.root >= len(nodes) or nodes[certificate.root].excluded:
        raise ValueError("master root must cover every represented batch")
    visited: set[int] = set()
    pending = [certificate.root]
    while pending:
        node_id = pending.pop()
        if node_id in visited:
            continue
        visited.add(node_id)
        node = nodes[node_id]
        if node.upper_bound is not None and (
            not isinstance(node.upper_bound, Fraction) or node.upper_bound < 0
        ):
            raise ValueError("master bounds must be non-negative exact rationals")
        for j in node.excluded:
            nonnegative_integer(j, "excluded choice")
            if j >= len(choices):
                raise ValueError("excluded choice is outside the reward universe")
        if node.excluded != tuple(sorted(set(node.excluded))):
            raise ValueError("master exclusion set is not canonical")
        if node.conflict_index is None:
            _, expected = relaxed_batch(choices, result.budget, node.excluded)
            if node.children or node.upper_bound != expected:
                raise ValueError("master leaf has an incorrect relaxation bound")
            continue
        nonnegative_integer(node.conflict_index, "conflict index")
        if node.conflict_index >= len(cores):
            raise ValueError("master uses an unknown conflict")
        core = cores[node.conflict_index]
        if core is None or set(core) & set(node.excluded):
            raise ValueError("master conflict is absent or already excluded")
        if len(node.children) != len(core):
            raise ValueError("master branches do not cover every conflict member")
        bounds: list[Fraction] = []
        for member, child_id in zip(core, node.children, strict=True):
            nonnegative_integer(child_id, "child index")
            if child_id >= len(nodes):
                raise ValueError("master child is missing")
            child = nodes[child_id]
            if child.excluded != tuple(sorted((*node.excluded, member))):
                raise ValueError("master branch removed an uncertified alternative")
            if child.upper_bound is not None:
                bounds.append(child.upper_bound)
            pending.append(child_id)
        expected_bound = max(bounds) if bounds else None
        if node.upper_bound != expected_bound:
            raise ValueError("master composition bound is incorrect")
    bound = nodes[certificate.root].upper_bound
    if result.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
        if bound is not None or result.objective_value is not None or result.witness_token_ids:
            raise ValueError("infeasibility was conflated with zero reward")
        if (
            result.committed_positions
            or result.committed_proposal_ids
            or result.matched_proposal_ids
        ):
            raise ValueError("infeasibility has spurious selected proposals")
        return
    if result.witness_token_ids is None or bound is None:
        raise ValueError("optimal result lacks an original token witness")
    if result.witness_graph_edge_ids is not None:
        for edge_id in result.witness_graph_edge_ids:
            nonnegative_integer(edge_id, "witness graph edge")
    checked = validate_budget_batch(
        state,
        budget=result.budget,
        witness_token_ids=result.witness_token_ids,
        committed_positions=result.committed_positions,
    )
    if result.witness_graph_edge_ids != token_path_ids(state, checked.witness_token_ids):
        raise ValueError("witness path does not traverse the original token lattice")
    if (
        not isinstance(result.objective_value, Fraction)
        or result.objective_value != bound
        or checked.reward != bound
        or checked.committed_proposal_ids != result.committed_proposal_ids
        or checked.matched_proposal_ids != result.matched_proposal_ids
    ):
        raise ValueError("original witness does not attain the certified upper bound")
