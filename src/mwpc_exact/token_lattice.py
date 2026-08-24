"""Finite layered token lattice with exact MWPC reward provenance.

This module deliberately stops before detokenization.  A :class:`TokenChoice`
identifies one represented token alternative across one physical canvas slot;
T603 expands those choices into byte-bearing ``TokenArc`` objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from itertools import product
from math import fsum, isfinite, prod

from mwpc_exact.support import PerPositionSupport
from mwpc_exact.types import Proposal, aggregate_proposals


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _id_tuple(value: object, field_name: str, *, unique: bool) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of integer IDs")
    result = tuple(_non_negative_integer(item, f"{field_name} item") for item in value)
    if unique and len(set(result)) != len(result):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


def _weight(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    try:
        normalized = float(value)
    except OverflowError as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not isfinite(normalized):
        raise ValueError(f"{field_name} must be finite")
    if normalized < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


@dataclass(frozen=True, slots=True)
class TokenChoice:
    """One token alternative crossing exactly one physical slot boundary."""

    token_edge_id: int
    position: int
    token_id: int
    source_boundary: int
    target_boundary: int
    weight: float = 0.0
    matched_proposal_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "token_edge_id",
            "position",
            "token_id",
            "source_boundary",
            "target_boundary",
        ):
            _non_negative_integer(getattr(self, field_name), field_name)
        if self.target_boundary <= self.source_boundary:
            raise ValueError("target_boundary must be greater than source_boundary")
        normalized_weight = _weight(self.weight, "weight")
        proposal_ids = _id_tuple(
            self.matched_proposal_ids,
            "matched_proposal_ids",
            unique=True,
        )
        if bool(proposal_ids) != (normalized_weight > 0.0):
            raise ValueError(
                "a token choice has positive weight exactly when it carries matching "
                "positive-weight proposal IDs"
            )
        object.__setattr__(self, "weight", normalized_weight)
        object.__setattr__(self, "matched_proposal_ids", proposal_ids)

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible token-choice metadata."""

        return {
            "token_edge_id": self.token_edge_id,
            "position": self.position,
            "token_id": self.token_id,
            "source_boundary": self.source_boundary,
            "target_boundary": self.target_boundary,
            "weight": self.weight,
            "matched_proposal_ids": list(self.matched_proposal_ids),
        }


@dataclass(frozen=True, slots=True)
class TokenLatticePath:
    """One complete, independently checkable path through a token lattice."""

    token_edge_ids: tuple[int, ...]
    token_ids: tuple[int, ...]
    objective_value: float
    matched_proposal_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        edge_ids = _id_tuple(self.token_edge_ids, "token_edge_ids", unique=True)
        token_ids = _id_tuple(self.token_ids, "token_ids", unique=False)
        proposal_ids = _id_tuple(
            self.matched_proposal_ids,
            "matched_proposal_ids",
            unique=True,
        )
        if len(edge_ids) != len(token_ids):
            raise ValueError("token_edge_ids and token_ids must have equal length")
        objective = _weight(self.objective_value, "objective_value")
        if bool(proposal_ids) != (objective > 0.0):
            raise ValueError(
                "a token path has positive objective exactly when it matches positive-weight "
                "proposal IDs"
            )
        object.__setattr__(self, "token_edge_ids", edge_ids)
        object.__setattr__(self, "token_ids", token_ids)
        object.__setattr__(self, "objective_value", objective)
        object.__setattr__(self, "matched_proposal_ids", proposal_ids)

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible path metadata."""

        return {
            "token_edge_ids": list(self.token_edge_ids),
            "token_ids": list(self.token_ids),
            "objective_value": self.objective_value,
            "matched_proposal_ids": list(self.matched_proposal_ids),
        }


@dataclass(frozen=True, slots=True)
class TokenLattice:
    """Immutable finite lattice whose complete paths consume every canvas slot."""

    support: PerPositionSupport
    boundary_ids: tuple[int, ...]
    choices: tuple[TokenChoice, ...]
    proposal_ids: tuple[int, ...] = ()
    unrepresented_proposal_ids: tuple[int, ...] = ()
    zero_weight_proposal_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.support, PerPositionSupport):
            raise TypeError("support must be a PerPositionSupport")
        boundary_ids = _id_tuple(self.boundary_ids, "boundary_ids", unique=True)
        expected_boundaries = tuple(range(len(self.support.rows) + 1))
        if boundary_ids != expected_boundaries:
            raise ValueError(
                "boundary_ids must contain exactly one boundary per slot plus the terminal "
                f"boundary: expected {expected_boundaries}"
            )

        choices = tuple(self.choices)
        if not all(isinstance(choice, TokenChoice) for choice in choices):
            raise TypeError("choices must contain only TokenChoice instances")
        expected_tokens = tuple(
            (position, token_id)
            for position, row in enumerate(self.support.rows)
            for token_id in row
        )
        actual_tokens = tuple((choice.position, choice.token_id) for choice in choices)
        if actual_tokens != expected_tokens:
            raise ValueError(
                "token choices must match every support row exactly in canonical position/token "
                "order"
            )
        if tuple(choice.token_edge_id for choice in choices) != tuple(range(len(choices))):
            raise ValueError("token choice IDs must be contiguous in canonical choice order")
        for choice in choices:
            if choice.source_boundary != choice.position:
                raise ValueError("each token choice must start at its physical slot boundary")
            if choice.target_boundary != choice.position + 1:
                raise ValueError("each token choice must consume exactly one physical slot")

        proposal_ids = _id_tuple(self.proposal_ids, "proposal_ids", unique=True)
        unrepresented_ids = _id_tuple(
            self.unrepresented_proposal_ids,
            "unrepresented_proposal_ids",
            unique=True,
        )
        zero_weight_ids = _id_tuple(
            self.zero_weight_proposal_ids,
            "zero_weight_proposal_ids",
            unique=True,
        )
        proposal_id_set = set(proposal_ids)
        if not set(unrepresented_ids) <= proposal_id_set:
            raise ValueError("unrepresented proposal IDs must belong to proposal_ids")
        if not set(zero_weight_ids) <= proposal_id_set:
            raise ValueError("zero-weight proposal IDs must belong to proposal_ids")
        matched_ids = tuple(
            proposal_id for choice in choices for proposal_id in choice.matched_proposal_ids
        )
        if len(set(matched_ids)) != len(matched_ids):
            raise ValueError("a positive proposal ID may be attached to only one token choice")
        if not set(matched_ids) <= proposal_id_set:
            raise ValueError("matched proposal IDs must belong to proposal_ids")
        if set(matched_ids) & set(unrepresented_ids):
            raise ValueError("matched proposal IDs cannot also be unrepresented")
        if set(matched_ids) & set(zero_weight_ids):
            raise ValueError("zero-weight proposal IDs cannot be attached as matches")
        expected_positive_ids = proposal_id_set - set(zero_weight_ids)
        accounted_positive_ids = set(matched_ids) | (set(unrepresented_ids) - set(zero_weight_ids))
        if accounted_positive_ids != expected_positive_ids:
            raise ValueError(
                "every positive proposal must be attached once or recorded as unrepresented"
            )

        try:
            maximum_objective = fsum(
                max(choice.weight for choice in choices if choice.position == position)
                for position in range(self.slot_count)
            )
        except OverflowError as exc:
            raise ValueError("the maximum complete token-path objective must be finite") from exc
        if not isfinite(maximum_objective):
            raise ValueError("the maximum complete token-path objective must be finite")

        object.__setattr__(self, "boundary_ids", boundary_ids)
        object.__setattr__(self, "choices", choices)
        object.__setattr__(self, "proposal_ids", proposal_ids)
        object.__setattr__(self, "unrepresented_proposal_ids", unrepresented_ids)
        object.__setattr__(self, "zero_weight_proposal_ids", zero_weight_ids)

    @property
    def slot_count(self) -> int:
        """Return the exact number of physical canvas slots consumed by every path."""

        return len(self.support.rows)

    @property
    def start_boundary(self) -> int:
        return self.boundary_ids[0]

    @property
    def final_boundary(self) -> int:
        return self.boundary_ids[-1]

    @property
    def choices_by_position(self) -> tuple[tuple[TokenChoice, ...], ...]:
        """Return token choices grouped by their absolute canvas position."""

        return tuple(
            tuple(choice for choice in self.choices if choice.position == position)
            for position in range(self.slot_count)
        )

    @property
    def path_count(self) -> int:
        """Return the exact Cartesian-product path count without enumerating paths."""

        return prod(len(row) for row in self.support.rows)

    @property
    def matched_positive_proposal_ids(self) -> tuple[int, ...]:
        """Return every represented positive proposal ID in stable choice order."""

        return tuple(
            proposal_id for choice in self.choices for proposal_id in choice.matched_proposal_ids
        )

    @property
    def unrepresented_positive_proposal_ids(self) -> tuple[int, ...]:
        """Return positive proposals whose choices are absent from this support."""

        zero_ids = set(self.zero_weight_proposal_ids)
        return tuple(
            proposal_id
            for proposal_id in self.unrepresented_proposal_ids
            if proposal_id not in zero_ids
        )

    def iter_paths(self) -> Iterator[TokenLatticePath]:
        """Enumerate complete paths in deterministic Cartesian-product order.

        This is intended for tiny correctness fixtures and exhaustive oracles;
        production code should consume the lattice graph directly.
        """

        for choices in product(*self.choices_by_position):
            yield self._path_from_choices(choices)

    def validate_path(self, path: TokenLatticePath) -> None:
        """Independently verify that ``path`` consumes each slot exactly once."""

        if not isinstance(path, TokenLatticePath):
            raise TypeError("path must be a TokenLatticePath")
        if len(path.token_edge_ids) != self.slot_count:
            raise ValueError(f"a complete token path must consume exactly {self.slot_count} slots")
        selected: list[TokenChoice] = []
        for position, token_edge_id in enumerate(path.token_edge_ids):
            if token_edge_id >= len(self.choices):
                raise ValueError(f"unknown token edge ID: {token_edge_id}")
            choice = self.choices[token_edge_id]
            if choice.position != position:
                raise ValueError("a complete token path must choose exactly one edge per slot")
            selected.append(choice)
        expected = self._path_from_choices(tuple(selected))
        if path != expected:
            raise ValueError("token path metadata does not match its selected token edges")

    def _path_from_choices(self, choices: Sequence[TokenChoice]) -> TokenLatticePath:
        try:
            objective = fsum(choice.weight for choice in choices)
        except OverflowError as exc:
            raise ValueError("token path objective must be finite") from exc
        return TokenLatticePath(
            token_edge_ids=tuple(choice.token_edge_id for choice in choices),
            token_ids=tuple(choice.token_id for choice in choices),
            objective_value=objective,
            matched_proposal_ids=tuple(
                proposal_id for choice in choices for proposal_id in choice.matched_proposal_ids
            ),
        )

    @property
    def diagnostics(self) -> dict[str, object]:
        """Return machine-readable lattice construction diagnostics."""

        return {
            "slot_count": self.slot_count,
            "boundary_count": len(self.boundary_ids),
            "token_choice_count": len(self.choices),
            "token_path_count": self.path_count,
            "support_kind": self.support.exactness_scope.kind.value,
            "represented_support_row_sizes": [len(row) for row in self.support.rows],
            "represented_support_sha256": self.support.fingerprint,
            "proposal_ids": list(self.proposal_ids),
            "matched_positive_proposal_ids": list(self.matched_positive_proposal_ids),
            "unrepresented_proposal_ids": list(self.unrepresented_proposal_ids),
            "unrepresented_positive_proposal_ids": list(self.unrepresented_positive_proposal_ids),
            "zero_weight_proposal_ids": list(self.zero_weight_proposal_ids),
        }

    def to_dict(self) -> dict[str, object]:
        """Serialize the finite support, choices, and construction diagnostics."""

        return {
            "boundary_ids": list(self.boundary_ids),
            "start_boundary": self.start_boundary,
            "final_boundary": self.final_boundary,
            "token_choices": [choice.to_dict() for choice in self.choices],
            "support": self.support.to_dict(),
            "diagnostics": self.diagnostics,
        }


def build_token_lattice(
    *,
    support: PerPositionSupport,
    proposals: Iterable[Proposal] = (),
) -> TokenLattice:
    """Build one deterministic layered token lattice over validated support.

    Proposals whose token alternative is absent from a pruned support cannot be
    matched and are recorded explicitly in diagnostics.  Positive proposal IDs
    are attached only to their exact represented ``(position, token_id)``
    choice.  Zero-weight proposal IDs are retained in diagnostics but are not
    selected-set provenance under the MWPC contract.
    """

    if not isinstance(support, PerPositionSupport):
        raise TypeError("support must be a PerPositionSupport")
    proposal_items = tuple(proposals)
    aggregated = aggregate_proposals(proposal_items)
    permitted = set(support.permitted_token_ids)
    for proposal in proposal_items:
        if proposal.position >= len(support.canvas):
            raise ValueError(
                f"proposal {proposal.proposal_id} position is outside the finite canvas"
            )
        if proposal.token_id >= support.exactness_scope.vocabulary_size:
            raise ValueError(
                f"proposal {proposal.proposal_id} token ID is outside the exactness-scope "
                "vocabulary"
            )
        if proposal.token_id not in permitted:
            raise ValueError(
                f"proposal {proposal.proposal_id} uses a non-permitted token ID: "
                f"{proposal.token_id}"
            )
        fixed_token = support.canvas[proposal.position]
        if fixed_token is not None and proposal.token_id != fixed_token:
            raise ValueError(
                f"proposal {proposal.proposal_id} conflicts with fixed canvas token at "
                f"position {proposal.position}"
            )
        if (
            support.proposal_token_inclusion_enabled
            and proposal.token_id not in support.rows[proposal.position]
        ):
            raise ValueError(
                "support claims proposal-token inclusion but omits proposal "
                f"{proposal.proposal_id} at position {proposal.position}"
            )

    reward_by_choice = {
        (proposal.position, proposal.token_id): proposal.weight for proposal in aggregated
    }
    positive_ids_by_choice: dict[tuple[int, int], list[int]] = {}
    for proposal in proposal_items:
        if proposal.weight > 0.0:
            positive_ids_by_choice.setdefault((proposal.position, proposal.token_id), []).append(
                proposal.proposal_id
            )

    choices: list[TokenChoice] = []
    for position, row in enumerate(support.rows):
        for token_id in row:
            key = (position, token_id)
            choices.append(
                TokenChoice(
                    token_edge_id=len(choices),
                    position=position,
                    token_id=token_id,
                    source_boundary=position,
                    target_boundary=position + 1,
                    weight=reward_by_choice.get(key, 0.0),
                    matched_proposal_ids=tuple(positive_ids_by_choice.get(key, ())),
                )
            )

    represented_choices = {
        (position, token_id) for position, row in enumerate(support.rows) for token_id in row
    }
    return TokenLattice(
        support=support,
        boundary_ids=tuple(range(len(support.rows) + 1)),
        choices=tuple(choices),
        proposal_ids=tuple(proposal.proposal_id for proposal in proposal_items),
        unrepresented_proposal_ids=tuple(
            proposal.proposal_id
            for proposal in proposal_items
            if (proposal.position, proposal.token_id) not in represented_choices
        ),
        zero_weight_proposal_ids=tuple(
            proposal.proposal_id for proposal in proposal_items if proposal.weight == 0.0
        ),
    )
