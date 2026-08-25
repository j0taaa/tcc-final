"""Schedule-compatible construction of one primary proposal per position.

The model integration boundary is responsible for converting tensors to finite
CPU-side sequences and for supplying the same position mask used by the decoder
schedule.  This module then freezes the candidate collection independently of
grammar feasibility or finite-support construction.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from mwpc_exact.profiling import ComponentProfiler, ProfilingComponent
from mwpc_exact.types import Proposal, aggregate_proposals


class ProposalWeightMode(StrEnum):
    """Versioned conversions from model confidence to MWPC utility."""

    UNIT = "unit"
    CONFIDENCE = "confidence"


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _finite_confidence(value: object, position: int) -> float:
    field_name = f"confidence at position {position}"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    try:
        confidence = float(value)
    except OverflowError as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not isfinite(confidence):
        raise ValueError(f"{field_name} must be finite")
    return confidence


def _finite_sequence(value: object, field_name: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence")
    return value


def _position_tuple(value: object, field_name: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of positions")
    positions = tuple(
        _non_negative_integer(position, f"{field_name} item") for position in value
    )
    if len(set(positions)) != len(positions):
        raise ValueError(f"{field_name} must not contain duplicates")
    return positions


@dataclass(frozen=True, slots=True)
class ScheduleProposalBatch:
    """Immutable proposal collection selected by one schedule step.

    ``eligible_positions`` is canonical absolute-position order. ``proposals``
    is schedule rank: confidence descending, then absolute position ascending.
    """

    proposals: tuple[Proposal, ...]
    eligible_positions: tuple[int, ...]
    schedule_budget: int
    weight_mode: ProposalWeightMode
    first_proposal_id: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.weight_mode, ProposalWeightMode):
            raise TypeError("weight_mode must be a ProposalWeightMode")
        budget = _non_negative_integer(self.schedule_budget, "schedule_budget")
        first_id = _non_negative_integer(self.first_proposal_id, "first_proposal_id")
        eligible = _position_tuple(self.eligible_positions, "eligible_positions")
        if eligible != tuple(sorted(eligible)):
            raise ValueError("eligible_positions must be in ascending absolute-position order")

        proposals = tuple(self.proposals)
        aggregate_proposals(proposals)
        expected_count = min(budget, len(eligible))
        if len(proposals) != expected_count:
            raise ValueError(
                "proposal count must equal min(schedule_budget, eligible position count)"
            )
        if tuple(proposal.proposal_id for proposal in proposals) != tuple(
            range(first_id, first_id + expected_count)
        ):
            raise ValueError("proposal IDs must be contiguous in schedule-rank order")
        if len({proposal.position for proposal in proposals}) != len(proposals):
            raise ValueError("the schedule policy permits only one proposal per position")
        if not {proposal.position for proposal in proposals} <= set(eligible):
            raise ValueError("proposal positions must belong to eligible_positions")
        if any(proposal.model_confidence is None for proposal in proposals):
            raise ValueError("schedule proposals must retain model confidence")

        expected_order = tuple(
            sorted(
                proposals,
                key=lambda proposal: (
                    -_required_confidence(proposal),
                    proposal.position,
                ),
            )
        )
        if proposals != expected_order:
            raise ValueError(
                "proposals must use confidence-descending, position-ascending schedule order"
            )
        for proposal in proposals:
            confidence = _required_confidence(proposal)
            expected_weight = (
                1.0 if self.weight_mode is ProposalWeightMode.UNIT else confidence
            )
            if proposal.weight != expected_weight:
                raise ValueError(
                    f"proposal {proposal.proposal_id} weight does not match "
                    f"{self.weight_mode.value} mode"
                )

        object.__setattr__(self, "proposals", proposals)
        object.__setattr__(self, "eligible_positions", eligible)

    @property
    def candidate_positions(self) -> tuple[int, ...]:
        """Return selected absolute positions in canonical schedule rank."""

        return tuple(proposal.position for proposal in self.proposals)

    @property
    def diagnostics(self) -> dict[str, object]:
        """Return JSON-compatible replay metadata for proposal construction."""

        return {
            "policy": "baseline_schedule_primary_proposal_v1",
            "schedule_budget": self.schedule_budget,
            "eligible_position_count": len(self.eligible_positions),
            "eligible_positions": list(self.eligible_positions),
            "candidate_positions": list(self.candidate_positions),
            "proposal_count": len(self.proposals),
            "weight_mode": self.weight_mode.value,
            "confidence_to_weight": (
                "constant_one"
                if self.weight_mode is ProposalWeightMode.UNIT
                else "identity_non_negative"
            ),
            "schedule_tie_break": "confidence_descending_then_absolute_position_ascending",
            "first_proposal_id": self.first_proposal_id,
        }

    def to_dict(self) -> dict[str, object]:
        """Serialize the frozen candidate collection for offline replay."""

        return {
            "proposals": [
                {
                    "proposal_id": proposal.proposal_id,
                    "position": proposal.position,
                    "token_id": proposal.token_id,
                    "weight": proposal.weight,
                    "model_confidence": proposal.model_confidence,
                }
                for proposal in self.proposals
            ],
            "diagnostics": self.diagnostics,
        }


def _required_confidence(proposal: Proposal) -> float:
    confidence = proposal.model_confidence
    if confidence is None:
        raise ValueError("schedule proposals must retain model confidence")
    return confidence


def _build_schedule_proposals(
    *,
    predicted_token_ids: Sequence[int],
    confidence_values: Sequence[float],
    schedule_mask: Sequence[bool],
    k_s: int,
    weight_mode: ProposalWeightMode,
    first_proposal_id: int = 0,
) -> ScheduleProposalBatch:
    """Build the candidate collection used by one baseline schedule step.

    ``schedule_mask`` must be the decoder's final eligibility mask (currently
    masked positions inside any active block/window). Values at excluded
    positions are deliberately ignored, so tensor adapters may retain their
    ``-inf`` confidence sentinels there. Eligible confidences must be finite;
    confidence weights must additionally be non-negative.
    """

    if not isinstance(weight_mode, ProposalWeightMode):
        raise TypeError("weight_mode must be a ProposalWeightMode")
    budget = _non_negative_integer(k_s, "k_s")
    proposal_id_start = _non_negative_integer(first_proposal_id, "first_proposal_id")
    predictions = _finite_sequence(predicted_token_ids, "predicted_token_ids")
    confidences = _finite_sequence(confidence_values, "confidence_values")
    mask = _finite_sequence(schedule_mask, "schedule_mask")
    if not len(predictions) == len(confidences) == len(mask):
        raise ValueError(
            "predicted_token_ids, confidence_values, and schedule_mask must have equal length"
        )

    eligible: list[tuple[int, int, float]] = []
    for position, included in enumerate(mask):
        if not isinstance(included, bool):
            raise TypeError(f"schedule_mask item at position {position} must be a boolean")
        if not included:
            continue
        token_id = _non_negative_integer(
            predictions[position], f"predicted token ID at position {position}"
        )
        confidence = _finite_confidence(confidences[position], position)
        eligible.append((position, token_id, confidence))

    ranked = sorted(eligible, key=lambda item: (-item[2], item[0]))
    selected = ranked[:budget]
    if weight_mode is ProposalWeightMode.CONFIDENCE:
        negative_positions = [position for position, _, confidence in selected if confidence < 0.0]
        if negative_positions:
            raise ValueError(
                "selected confidence must be non-negative in confidence mode; "
                f"negative positions={negative_positions}"
            )
    proposals = tuple(
        Proposal(
            proposal_id=proposal_id_start + rank,
            position=position,
            token_id=token_id,
            weight=(1.0 if weight_mode is ProposalWeightMode.UNIT else confidence),
            model_confidence=confidence,
        )
        for rank, (position, token_id, confidence) in enumerate(selected)
    )
    return ScheduleProposalBatch(
        proposals=proposals,
        eligible_positions=tuple(position for position, _, _ in eligible),
        schedule_budget=budget,
        weight_mode=weight_mode,
        first_proposal_id=proposal_id_start,
    )


def build_schedule_proposals(
    *,
    predicted_token_ids: Sequence[int],
    confidence_values: Sequence[float],
    schedule_mask: Sequence[bool],
    k_s: int,
    weight_mode: ProposalWeightMode,
    first_proposal_id: int = 0,
    profiler: ComponentProfiler | None = None,
) -> ScheduleProposalBatch:
    """Build the candidate collection used by one baseline schedule step.

    ``schedule_mask`` must be the decoder's final eligibility mask. Values at
    excluded positions are ignored. Eligible confidences must be finite;
    confidence weights must additionally be non-negative. When supplied, the
    optional profiler records only proposal-policy construction.
    """

    if profiler is not None and not isinstance(profiler, ComponentProfiler):
        raise TypeError("profiler must be a ComponentProfiler or None")
    if profiler is None or not profiler.enabled:
        return _build_schedule_proposals(
            predicted_token_ids=predicted_token_ids,
            confidence_values=confidence_values,
            schedule_mask=schedule_mask,
            k_s=k_s,
            weight_mode=weight_mode,
            first_proposal_id=first_proposal_id,
        )
    with profiler.measure(ProfilingComponent.PROPOSAL_POLICY):
        batch = _build_schedule_proposals(
            predicted_token_ids=predicted_token_ids,
            confidence_values=confidence_values,
            schedule_mask=schedule_mask,
            k_s=k_s,
            weight_mode=weight_mode,
            first_proposal_id=first_proposal_id,
        )
    profiler.set_counter("proposal_count", len(batch.proposals))
    return batch
