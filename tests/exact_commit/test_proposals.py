from __future__ import annotations

from dataclasses import FrozenInstanceError
from math import fsum, inf, nan

import pytest

from mwpc_exact import Proposal, aggregate_proposals


@pytest.mark.parametrize("weight", [-1.0, inf, -inf, nan, True])
def test_proposal_rejects_invalid_weight(weight: object) -> None:
    error = TypeError if weight is True else ValueError
    with pytest.raises(error):
        Proposal(0, position=0, token_id=1, weight=weight)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["proposal_id", "position", "token_id"])
def test_proposal_rejects_invalid_integer_ids(field: str) -> None:
    values = {"proposal_id": 0, "position": 0, "token_id": 1, "weight": 1.0}
    values[field] = -1
    with pytest.raises(ValueError, match="non-negative"):
        Proposal(**values)  # type: ignore[arg-type]


def test_proposal_is_immutable_and_normalizes_numeric_metadata() -> None:
    proposal = Proposal(7, position=2, token_id=11, weight=3, model_confidence=1)

    assert proposal.weight == 3.0
    assert isinstance(proposal.weight, float)
    assert proposal.model_confidence == 1.0
    with pytest.raises(FrozenInstanceError):
        proposal.weight = 4.0  # type: ignore[misc]


def test_aggregation_rejects_duplicate_proposal_ids_across_choices() -> None:
    proposals = (
        Proposal(7, position=0, token_id=10, weight=1.0),
        Proposal(7, position=1, token_id=11, weight=2.0),
    )

    with pytest.raises(ValueError, match="duplicate proposal_id: 7"):
        aggregate_proposals(proposals)


def test_aggregation_preserves_all_ids_and_uses_stable_accurate_sum() -> None:
    weights = (1e16, 1.0, 1.0)
    proposals = tuple(
        Proposal(
            proposal_id,
            position=3,
            token_id=42,
            weight=weight,
            model_confidence=confidence,
        )
        for proposal_id, weight, confidence in zip(
            (9, 4, 12), weights, (0.9, 0.2, 0.7), strict=True
        )
    )

    (aggregated,) = aggregate_proposals(proposals)

    assert aggregated.position == 3
    assert aggregated.token_id == 42
    assert aggregated.weight == fsum(weights)
    assert aggregated.proposal_ids == (9, 4, 12)
    assert not hasattr(aggregated, "model_confidence")


def test_multiple_tokens_at_one_position_remain_separate_and_stable() -> None:
    proposals = (
        Proposal(5, position=2, token_id=20, weight=1.0),
        Proposal(6, position=2, token_id=21, weight=2.0),
        Proposal(7, position=2, token_id=20, weight=3.0),
    )

    aggregated = aggregate_proposals(proposals)

    assert tuple((choice.position, choice.token_id) for choice in aggregated) == (
        (2, 20),
        (2, 21),
    )
    assert aggregated[0].proposal_ids == (5, 7)
    assert aggregated[0].weight == 4.0
    assert aggregated[1].proposal_ids == (6,)


def test_empty_proposal_collection_has_empty_aggregation() -> None:
    assert aggregate_proposals(()) == ()
