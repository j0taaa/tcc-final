from __future__ import annotations

from dataclasses import FrozenInstanceError
from math import inf, nan

import pytest

from mwpc_exact import (
    Proposal,
    ProposalWeightMode,
    ScheduleProposalBatch,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    build_schedule_proposals,
    build_token_lattice,
)


def test_saved_predictions_are_deterministic_with_position_tie_break() -> None:
    inputs = {
        "predicted_token_ids": (90, 11, 22, 33, 44, 55),
        "confidence_values": (-inf, 0.7, 0.9, 0.9, 0.7, nan),
        "schedule_mask": (False, True, True, True, True, False),
        "k_s": 3,
        "weight_mode": ProposalWeightMode.UNIT,
        "first_proposal_id": 40,
    }

    first = build_schedule_proposals(**inputs)  # type: ignore[arg-type]
    second = build_schedule_proposals(**inputs)  # type: ignore[arg-type]

    assert first == second
    assert first.candidate_positions == (2, 3, 1)
    assert first.eligible_positions == (1, 2, 3, 4)
    assert first.proposals == (
        Proposal(40, position=2, token_id=22, weight=1.0, model_confidence=0.9),
        Proposal(41, position=3, token_id=33, weight=1.0, model_confidence=0.9),
        Proposal(42, position=1, token_id=11, weight=1.0, model_confidence=0.7),
    )
    assert first.diagnostics["schedule_tie_break"] == (
        "confidence_descending_then_absolute_position_ascending"
    )
    assert first.to_dict()["proposals"] == [
        {
            "proposal_id": 40,
            "position": 2,
            "token_id": 22,
            "weight": 1.0,
            "model_confidence": 0.9,
        },
        {
            "proposal_id": 41,
            "position": 3,
            "token_id": 33,
            "weight": 1.0,
            "model_confidence": 0.9,
        },
        {
            "proposal_id": 42,
            "position": 1,
            "token_id": 11,
            "weight": 1.0,
            "model_confidence": 0.7,
        },
    ]


def test_confidence_mode_uses_non_negative_confidence_as_utility() -> None:
    batch = build_schedule_proposals(
        predicted_token_ids=(1, 2, 3),
        confidence_values=(0.0, 0.25, 2.0),
        schedule_mask=(True, True, True),
        k_s=5,
        weight_mode=ProposalWeightMode.CONFIDENCE,
    )

    assert len(batch.proposals) == 3
    assert len(batch.proposals) <= batch.schedule_budget
    assert batch.candidate_positions == (2, 1, 0)
    assert tuple(proposal.weight for proposal in batch.proposals) == (2.0, 0.25, 0.0)
    assert tuple(proposal.model_confidence for proposal in batch.proposals) == (
        2.0,
        0.25,
        0.0,
    )
    assert batch.diagnostics["confidence_to_weight"] == "identity_non_negative"


def test_zero_budget_and_empty_eligibility_return_no_proposals() -> None:
    zero_budget = build_schedule_proposals(
        predicted_token_ids=(4, 5),
        confidence_values=(0.9, 0.8),
        schedule_mask=(True, True),
        k_s=0,
        weight_mode=ProposalWeightMode.UNIT,
    )
    empty_mask = build_schedule_proposals(
        predicted_token_ids=(4, 5),
        confidence_values=(-inf, nan),
        schedule_mask=(False, False),
        k_s=2,
        weight_mode=ProposalWeightMode.UNIT,
    )

    assert zero_budget.proposals == ()
    assert zero_budget.eligible_positions == (0, 1)
    assert empty_mask.proposals == ()
    assert empty_mask.eligible_positions == ()


def test_unit_mode_retains_signed_schedule_confidence_as_metadata() -> None:
    batch = build_schedule_proposals(
        predicted_token_ids=(8, 9),
        confidence_values=(-2.0, -1.0),
        schedule_mask=(True, True),
        k_s=1,
        weight_mode=ProposalWeightMode.UNIT,
    )

    assert batch.proposals == (
        Proposal(0, position=1, token_id=9, weight=1.0, model_confidence=-1.0),
    )


@pytest.mark.parametrize("confidence", [-0.1, -inf, inf, nan])
def test_confidence_mode_rejects_invalid_candidate_utilities(confidence: float) -> None:
    message = (
        "selected confidence must be non-negative"
        if confidence == -0.1
        else "confidence at position 0"
    )
    with pytest.raises(ValueError, match=message):
        build_schedule_proposals(
            predicted_token_ids=(1,),
            confidence_values=(confidence,),
            schedule_mask=(True,),
            k_s=1,
            weight_mode=ProposalWeightMode.CONFIDENCE,
        )


def test_confidence_mode_does_not_reject_unselected_signed_confidence() -> None:
    batch = build_schedule_proposals(
        predicted_token_ids=(1, 2),
        confidence_values=(0.9, -0.1),
        schedule_mask=(True, True),
        k_s=1,
        weight_mode=ProposalWeightMode.CONFIDENCE,
    )

    assert batch.proposals == (
        Proposal(0, position=0, token_id=1, weight=0.9, model_confidence=0.9),
    )


@pytest.mark.parametrize(
    ("overrides", "error", "message"),
    [
        ({"k_s": -1}, ValueError, "k_s must be non-negative"),
        ({"k_s": True}, TypeError, "k_s must be an integer"),
        ({"first_proposal_id": -1}, ValueError, "first_proposal_id must be non-negative"),
        ({"predicted_token_ids": (1, -2)}, ValueError, "predicted token ID"),
        ({"predicted_token_ids": (1, True)}, TypeError, "predicted token ID"),
        ({"confidence_values": (0.5, True)}, TypeError, "confidence at position 1"),
        ({"schedule_mask": (True, 1)}, TypeError, "schedule_mask item"),
        ({"schedule_mask": (True,)}, ValueError, "must have equal length"),
    ],
)
def test_policy_rejects_malformed_inputs(
    overrides: dict[str, object], error: type[Exception], message: str
) -> None:
    inputs: dict[str, object] = {
        "predicted_token_ids": (1, 2),
        "confidence_values": (0.5, 0.4),
        "schedule_mask": (True, True),
        "k_s": 2,
        "weight_mode": ProposalWeightMode.UNIT,
    }
    inputs.update(overrides)

    with pytest.raises(error, match=message):
        build_schedule_proposals(**inputs)  # type: ignore[arg-type]


def test_weight_mode_requires_explicit_enum() -> None:
    with pytest.raises(TypeError, match="ProposalWeightMode"):
        build_schedule_proposals(
            predicted_token_ids=(1,),
            confidence_values=(0.5,),
            schedule_mask=(True,),
            k_s=1,
            weight_mode="unit",  # type: ignore[arg-type]
        )


def test_batch_is_immutable_and_rejects_noncanonical_manual_state() -> None:
    batch = build_schedule_proposals(
        predicted_token_ids=(5, 6),
        confidence_values=(0.2, 0.8),
        schedule_mask=(True, True),
        k_s=2,
        weight_mode=ProposalWeightMode.UNIT,
    )
    with pytest.raises(FrozenInstanceError):
        batch.schedule_budget = 1  # type: ignore[misc]

    with pytest.raises(ValueError, match="schedule order"):
        ScheduleProposalBatch(
            proposals=(
                Proposal(0, position=0, token_id=5, weight=1.0, model_confidence=0.2),
                Proposal(1, position=1, token_id=6, weight=1.0, model_confidence=0.8),
            ),
            eligible_positions=batch.eligible_positions,
            schedule_budget=2,
            weight_mode=ProposalWeightMode.UNIT,
        )


def test_nonproposal_support_alternatives_keep_zero_reward() -> None:
    batch = build_schedule_proposals(
        predicted_token_ids=(2, 1),
        confidence_values=(0.8, 0.7),
        schedule_mask=(True, True),
        k_s=1,
        weight_mode=ProposalWeightMode.CONFIDENCE,
    )
    support = build_per_position_support(
        canvas=(None, None),
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=3),
        explicit_support={0: (0, 2), 1: (0, 1)},
        proposals=batch.proposals,
    )
    lattice = build_token_lattice(support=support, proposals=batch.proposals)

    choices = {(choice.position, choice.token_id): choice for choice in lattice.choices}
    assert choices[(0, 2)].weight == 0.8
    assert choices[(0, 2)].matched_proposal_ids == (0,)
    assert choices[(0, 0)].weight == 0.0
    assert choices[(0, 0)].matched_proposal_ids == ()
    assert choices[(1, 1)].weight == 0.0


def test_generic_solver_boundary_still_allows_duplicate_choice_provenance() -> None:
    batch = build_schedule_proposals(
        predicted_token_ids=(2,),
        confidence_values=(0.8,),
        schedule_mask=(True,),
        k_s=1,
        weight_mode=ProposalWeightMode.UNIT,
    )
    duplicate_choice = Proposal(
        9,
        position=0,
        token_id=2,
        weight=3.0,
        model_confidence=0.5,
    )
    proposals = (*batch.proposals, duplicate_choice)
    support = build_per_position_support(
        canvas=(None,),
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=3),
        explicit_support={0: (1, 2)},
        proposals=proposals,
    )
    lattice = build_token_lattice(support=support, proposals=proposals)

    matching_choice = next(choice for choice in lattice.choices if choice.token_id == 2)
    assert matching_choice.weight == 4.0
    assert matching_choice.matched_proposal_ids == (0, 9)
