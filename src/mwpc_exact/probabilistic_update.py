"""Proof-checked sampling and finite-canvas parallel commitment.

This API is separate from MWPC reward optimization. Distribution guarantees
refer to the declared frozen grammar-conditioned mean-field predictive.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from random import Random

from mwpc_exact.mass_certificate import (
    PosteriorScope,
    ProbabilityInput,
    probability,
    verify_mass_proof,
)
from mwpc_exact.reference.budget_types import nonnegative_integer


@dataclass(frozen=True)
class ProbabilisticUpdate:
    canvas: tuple[int | None, ...]
    witness_token_ids: tuple[int, ...]
    committed_positions: tuple[int, ...]
    reference_scope: PosteriorScope
    certified_tv_bound: Fraction


def certified_parallel_update(
    inputs: ProbabilityInput,
    proof: object,
    *,
    committed_positions: Iterable[int],
    rng: Random,
    scope: PosteriorScope,
    max_tv: Fraction,
) -> ProbabilisticUpdate:
    checked = verify_mass_proof(proof, expected_input=inputs)
    positions = tuple(committed_positions)
    if len(positions) != len(set(positions)):
        raise ValueError("commitment positions must be unique")
    for position in positions:
        nonnegative_integer(position, "position")
        if position >= len(inputs.state.canvas) or inputs.state.canvas[position] is not None:
            raise ValueError("commitment requires a currently masked physical slot")
    witness = checked.sample(rng, scope=scope, max_tv=max_tv)
    selected = set(positions)
    canvas = tuple(witness[i] if i in selected else t for i, t in enumerate(inputs.state.canvas))
    bound = checked.tv_bound(scope)
    assert bound is not None
    return ProbabilisticUpdate(canvas, witness, tuple(sorted(positions)), scope, bound)


def trajectory_tv_bound(per_step_tolerances: Iterable[Fraction]) -> Fraction:
    """Union/coupling bound, requiring a certified transition at every step/state.

    This arithmetic alone does not verify those premises or cover a fallback.
    """
    return min(Fraction(1), sum((probability(v) for v in per_step_tolerances), Fraction()))
