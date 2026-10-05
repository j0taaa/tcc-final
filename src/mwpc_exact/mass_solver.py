"""Anytime token-space WMC specialization using finite-slot CFG feasibility.

Search heuristics never enter certificate bounds. No polynomial worst-case
claim is made for arbitrary ambiguous grammars.
"""

from __future__ import annotations

import heapq
from dataclasses import replace
from fractions import Fraction
from math import isfinite, log
from time import monotonic

from mwpc_exact.backend import ExactBackend
from mwpc_exact.budget_proof import budget_proof_data, fraction_data
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.conflict_proof import state_data
from mwpc_exact.evaluation.selection import SelectionStatus, select_exact_mwpc
from mwpc_exact.language_coverage import check_language_coverage
from mwpc_exact.mass_certificate import (
    Box,
    MassStatus,
    PosteriorScope,
    ProbabilityInput,
    probability,
    restrict_box,
    verify_mass_proof,
)
from mwpc_exact.reference.budget_types import nonnegative_integer
from mwpc_exact.types import Proposal, SolveStatus


def probability_partition(
    inputs: ProbabilityInput,
    *,
    max_oracle_calls: int = 64,
    requested_tv: Fraction = Fraction(1, 20),
    scope: PosteriorScope = PosteriorScope.REPRESENTED,
    backend: ExactBackend = ExactBackend.RUST,
    timeout_seconds: float | None = None,
    language_coverage: object | None = None,
) -> dict[str, object]:
    nonnegative_integer(max_oracle_calls, "max_oracle_calls")
    epsilon = probability(requested_tv)
    if not isinstance(scope, PosteriorScope) or not isinstance(backend, ExactBackend):
        raise TypeError("scope/backend must be their explicit enums")
    if timeout_seconds is not None and (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not isfinite(timeout_seconds)
        or timeout_seconds < 0
    ):
        raise ValueError("timeout must be finite and nonnegative")
    deadline = None if timeout_seconds is None else monotonic() + timeout_seconds
    state = inputs.state
    if language_coverage is not None:
        check_language_coverage(state, language_coverage)
    outside = inputs.omitted_mass if language_coverage is None else Fraction()
    boxes: list[Box] = [state.support.rows]
    kinds = ["unresolved"]
    children: list[tuple[int, ...]] = [()]
    proofs: dict[int, dict[str, object]] = {}
    queue = [(-inputs.box_mass(boxes[0]), 0)]
    lower = Fraction()
    remaining = inputs.box_mass(boxes[0])
    calls = 0
    timed_out = False

    def append(box: Box) -> int:
        index = len(boxes)
        boxes.append(box)
        kinds.append("unresolved")
        children.append(())
        return index

    def extract(index: int, witness: tuple[int, ...]) -> None:
        # Subtract a witnessed singleton via disjoint first-difference boxes.
        box = boxes[index]
        for position, domain in enumerate(box):
            if len(domain) == 1:
                continue
            matching = tuple(
                (witness[position],) if i == position else row for i, row in enumerate(box)
            )
            other = tuple(
                tuple(t for t in domain if t != witness[position]) if i == position else row
                for i, row in enumerate(box)
            )
            left, right = append(matching), append(other)
            kinds[index] = "split"
            children[index] = (left, right)
            heapq.heappush(queue, (-inputs.box_mass(other), right))
            index, box = left, matching
        kinds[index] = "accepted"

    while queue:
        unknown = remaining + (outside if scope is PosteriorScope.FULL else Fraction())
        if lower and unknown / (lower + unknown) <= epsilon:
            break
        if deadline is not None and monotonic() >= deadline:
            timed_out = True
            break
        if calls >= max_oracle_calls:
            break
        negative_mass, index = heapq.heappop(queue)
        mass = -negative_mass
        if not mass:
            kinds[index] = "zero"
            continue
        restricted = restrict_box(state, boxes[index])
        # Approximate log-product priority only; any validated witness is sound.
        proposals: list[Proposal] = []
        for position, (tokens, weights) in enumerate(
            zip(state.support.rows, inputs.probabilities, strict=True)
        ):
            if state.canvas[position] is not None:
                continue
            scores = {
                t: log(p.numerator) - log(p.denominator)
                for t, p in zip(tokens, weights, strict=True)
                if p and t in boxes[index][position]
            }
            floor = min(scores.values())
            for token, score in scores.items():
                proposals.append(Proposal(len(proposals), position, token, score - floor))
        query = replace(restricted, proposals=tuple(proposals))
        calls += 1
        timeout = (
            max(0.0, deadline - monotonic())
            if deadline is not None and backend is ExactBackend.RUST
            else None
        )
        result = select_exact_mwpc(query, backend=backend, timeout_seconds=timeout)
        if result.status is SelectionStatus.TIMEOUT:
            heapq.heappush(queue, (negative_mass, index))
            timed_out = True
            break
        if result.status is SelectionStatus.OPTIMAL:
            witness = result.witness_token_ids
            extract(index, witness)
            accepted_mass = inputs.box_mass(tuple((t,) for t in witness))
            lower += accepted_mass
            remaining -= accepted_mass
        elif result.status is SelectionStatus.INFEASIBLE_ON_SUPPORT:
            proof_result = budgeted_commit_frontier(restricted, 0)
            if proof_result[0].status is not SolveStatus.INFEASIBLE_ON_SUPPORT:
                raise RuntimeError("independent infeasibility proof disagrees with CFG oracle")
            encoded = budget_proof_data(restricted, proof_result)
            proofs[index] = {
                k: v for k, v in encoded.items() if k not in ("input", "input_fingerprint")
            }
            kinds[index] = "infeasible"
            remaining -= mass
        else:
            raise RuntimeError(f"finite CFG oracle failed: {result.status}")
    unknown = remaining + (outside if scope is PosteriorScope.FULL else Fraction())
    bound = unknown / (lower + unknown) if lower else None
    status = (
        MassStatus.CERTIFIED
        if bound is not None and bound <= epsilon
        else MassStatus.ZERO_ON_SUPPORT
        if not lower and not remaining
        else MassStatus.TIMEOUT
        if timed_out
        else MassStatus.INCOMPLETE
    )
    data: dict[str, object] = {
        "schema_version": 1,
        "kind": "token_mass_partition",
        "input": state_data(state),
        "probabilities": [[fraction_data(p) for p in row] for row in inputs.probabilities],
        "input_fingerprint": inputs.fingerprint,
        "reference_scope": scope.value,
        "requested_tv": fraction_data(epsilon),
        "status": status.value,
        "oracle_calls": calls,
        **({"language_coverage": language_coverage} if language_coverage is not None else {}),
        "nodes": [
            {
                "box": box,
                "kind": kind,
                "children": branch,
                **({"proof": proofs[i]} if i in proofs else {}),
            }
            for i, (box, kind, branch) in enumerate(zip(boxes, kinds, children, strict=True))
        ],
        "envelope": {
            "lower": fraction_data(lower),
            "unresolved": fraction_data(remaining),
            "omitted": fraction_data(inputs.omitted_mass),
        },
    }
    verify_mass_proof(data, expected_input=inputs)
    return data
