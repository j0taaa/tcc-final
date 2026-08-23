"""Scientific data contracts shared by reference and production solvers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import fsum, isfinite
from typing import Any, Self


class SolveStatus(StrEnum):
    """Mutually exclusive solver outcomes."""

    OPTIMAL = "optimal"
    INFEASIBLE_ON_SUPPORT = "infeasible_on_support"
    TIMEOUT = "timeout"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


class SupportKind(StrEnum):
    """How the finite support represented for one solve was constructed."""

    FULL = "full"
    TOP_K = "top_k"
    EXPLICIT = "explicit"


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    return value


def _int_tuple(value: object, field_name: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be a sequence of integers")
    items: tuple[object, ...] = tuple(value)
    return tuple(_require_int(item, f"{field_name} item") for item in items)


def _finite_float(value: object, field_name: str, *, non_negative: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    try:
        normalized = float(value)
    except OverflowError as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not isfinite(normalized):
        raise ValueError(f"{field_name} must be finite")
    if non_negative and normalized < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


@dataclass(frozen=True, slots=True)
class ExactnessScope:
    """Immutable support metadata bounding one solver claim.

    ``adaptive_expansions`` records successive top-K widths attempted after
    ``top_k``. It is metadata about represented support, never a claim of
    full-vocabulary optimality.
    """

    kind: SupportKind
    vocabulary_size: int
    included_special_tokens: tuple[int, ...] = ()
    top_k: int | None = None
    adaptive_expansions: tuple[int, ...] = ()
    pruning_description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, SupportKind):
            raise TypeError("kind must be a SupportKind")

        vocabulary_size = _require_int(self.vocabulary_size, "vocabulary_size")
        if vocabulary_size <= 0:
            raise ValueError("vocabulary_size must be positive")

        special_tokens = _int_tuple(self.included_special_tokens, "included_special_tokens")
        if len(set(special_tokens)) != len(special_tokens):
            raise ValueError("included_special_tokens must not contain duplicates")
        for token_id in special_tokens:
            if not 0 <= token_id < vocabulary_size:
                raise ValueError("included special token IDs must be within the vocabulary")
        object.__setattr__(self, "included_special_tokens", special_tokens)

        if self.top_k is not None:
            top_k = _require_int(self.top_k, "top_k")
            if not 0 < top_k <= vocabulary_size:
                raise ValueError("top_k must be positive and no larger than vocabulary_size")
        else:
            top_k = None

        expansions = _int_tuple(self.adaptive_expansions, "adaptive_expansions")
        object.__setattr__(self, "adaptive_expansions", expansions)

        if self.kind is SupportKind.TOP_K:
            if top_k is None:
                raise ValueError("TOP_K scope requires top_k")
            previous_width = top_k
            for width in expansions:
                if not previous_width < width <= vocabulary_size:
                    raise ValueError(
                        "adaptive_expansions must be strictly increasing after top_k "
                        "and no larger than vocabulary_size"
                    )
                previous_width = width
        else:
            if top_k is not None:
                raise ValueError(f"{self.kind.value} scope cannot define top_k")
            if expansions:
                raise ValueError(
                    f"{self.kind.value} scope cannot define adaptive_expansions"
                )

        if self.pruning_description is not None:
            if not isinstance(self.pruning_description, str):
                raise TypeError("pruning_description must be a string when provided")
            if not self.pruning_description.strip():
                raise ValueError("pruning_description must be non-empty when provided")

    def to_dict(self) -> dict[str, object]:
        """Return metadata made only of JSON-compatible values."""
        return {
            "kind": self.kind.value,
            "vocabulary_size": self.vocabulary_size,
            "included_special_tokens": list(self.included_special_tokens),
            "top_k": self.top_k,
            "adaptive_expansions": list(self.adaptive_expansions),
            "pruning_description": self.pruning_description,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        """Reconstruct and validate scope metadata parsed from JSON."""
        if not isinstance(data, Mapping):
            raise TypeError("exactness scope data must be a mapping")

        allowed = {
            "kind",
            "vocabulary_size",
            "included_special_tokens",
            "top_k",
            "adaptive_expansions",
            "pruning_description",
        }
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(repr(name) for name in unknown))
            raise ValueError(f"unknown exactness scope fields: {names}")
        missing = {"kind", "vocabulary_size"} - set(data)
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"missing exactness scope fields: {names}")

        kind_value = data["kind"]
        if not isinstance(kind_value, str):
            raise TypeError("kind must be a string")
        try:
            kind = SupportKind(kind_value)
        except ValueError as exc:
            raise ValueError(f"unknown support kind: {kind_value!r}") from exc

        top_k_value = data.get("top_k")
        top_k = None if top_k_value is None else _require_int(top_k_value, "top_k")
        pruning_description = data.get("pruning_description")
        if pruning_description is not None and not isinstance(pruning_description, str):
            raise TypeError("pruning_description must be a string when provided")

        return cls(
            kind=kind,
            vocabulary_size=_require_int(data["vocabulary_size"], "vocabulary_size"),
            included_special_tokens=_int_tuple(
                data.get("included_special_tokens", ()), "included_special_tokens"
            ),
            top_k=top_k,
            adaptive_expansions=_int_tuple(
                data.get("adaptive_expansions", ()), "adaptive_expansions"
            ),
            pruning_description=pruning_description,
        )


# Compatibility for the initial M0 scaffold. New APIs use ``SolveStatus``.
ExactCommitStatus = SolveStatus


@dataclass(frozen=True, slots=True)
class Proposal:
    """One weighted model proposal for one physical token slot."""

    proposal_id: int
    position: int
    token_id: int
    weight: float
    model_confidence: float | None = None

    def __post_init__(self) -> None:
        proposal_id = _require_int(self.proposal_id, "proposal_id")
        if proposal_id < 0:
            raise ValueError("proposal_id must be non-negative")
        position = _require_int(self.position, "position")
        if position < 0:
            raise ValueError("position must be non-negative")
        token_id = _require_int(self.token_id, "token_id")
        if token_id < 0:
            raise ValueError("token_id must be non-negative")
        object.__setattr__(
            self,
            "weight",
            _finite_float(self.weight, "weight", non_negative=True),
        )
        if self.model_confidence is not None:
            object.__setattr__(
                self,
                "model_confidence",
                _finite_float(
                    self.model_confidence,
                    "model_confidence",
                    non_negative=False,
                ),
            )


@dataclass(frozen=True, slots=True)
class AggregatedProposal:
    """Reward and provenance for one represented ``(position, token_id)``."""

    position: int
    token_id: int
    weight: float
    proposal_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        if _require_int(self.position, "position") < 0:
            raise ValueError("position must be non-negative")
        if _require_int(self.token_id, "token_id") < 0:
            raise ValueError("token_id must be non-negative")
        object.__setattr__(
            self,
            "weight",
            _finite_float(self.weight, "weight", non_negative=True),
        )
        proposal_ids = _int_tuple(self.proposal_ids, "proposal_ids")
        if not proposal_ids:
            raise ValueError("proposal_ids must be non-empty")
        if len(set(proposal_ids)) != len(proposal_ids):
            raise ValueError("proposal_ids must not contain duplicates")
        if any(proposal_id < 0 for proposal_id in proposal_ids):
            raise ValueError("proposal_ids must be non-negative")
        object.__setattr__(self, "proposal_ids", proposal_ids)


def aggregate_proposals(proposals: Iterable[Proposal]) -> tuple[AggregatedProposal, ...]:
    """Aggregate rewards by choice while preserving stable proposal provenance."""
    groups: dict[tuple[int, int], list[Proposal]] = {}
    seen_ids: set[int] = set()
    for proposal in proposals:
        if not isinstance(proposal, Proposal):
            raise TypeError("proposals must contain only Proposal instances")
        if proposal.proposal_id in seen_ids:
            raise ValueError(f"duplicate proposal_id: {proposal.proposal_id}")
        seen_ids.add(proposal.proposal_id)
        groups.setdefault((proposal.position, proposal.token_id), []).append(proposal)

    aggregated: list[AggregatedProposal] = []
    for (position, token_id), group in groups.items():
        try:
            total_weight = fsum(proposal.weight for proposal in group)
        except OverflowError as exc:
            raise ValueError(
                f"aggregated weight is not finite at position={position}, token_id={token_id}"
            ) from exc
        aggregated.append(
            AggregatedProposal(
                position=position,
                token_id=token_id,
                weight=total_weight,
                proposal_ids=tuple(proposal.proposal_id for proposal in group),
            )
        )
    return tuple(aggregated)


@dataclass(frozen=True, slots=True)
class ExactCommitResult:
    """Solver result plus the certificate needed for independent validation."""

    status: SolveStatus
    exactness_scope: ExactnessScope
    objective_value: float | None = None
    selected_proposal_ids: tuple[str, ...] = ()
    witness_token_ids: tuple[int, ...] = ()
    witness_terminal_labels: tuple[str, ...] = ()
    witness_graph_edge_ids: tuple[str, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.objective_value is not None:
            if not isfinite(self.objective_value) or self.objective_value < 0:
                raise ValueError("objective_value must be finite and non-negative")

        if self.status is SolveStatus.OPTIMAL:
            if self.objective_value is None:
                raise ValueError("OPTIMAL requires objective_value")
            if not self.witness_token_ids:
                raise ValueError("OPTIMAL requires a non-empty witness token sequence")
            if not self.witness_graph_edge_ids:
                raise ValueError("OPTIMAL requires a reconstructible witness path")
        elif self.selected_proposal_ids:
            raise ValueError("non-OPTIMAL results cannot claim selected proposals")
