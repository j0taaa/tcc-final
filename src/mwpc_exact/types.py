"""Scientific data contracts shared by reference and production solvers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import fsum, isfinite
from types import MappingProxyType
from typing import Self, TypeAlias


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


def _stable_ids(value: object, field_name: str, *, allow_empty: bool) -> tuple[int, ...]:
    ids = _int_tuple(value, field_name)
    if not allow_empty and not ids:
        raise ValueError(f"{field_name} must be non-empty")
    if len(set(ids)) != len(ids):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(stable_id < 0 for stable_id in ids):
        raise ValueError(f"{field_name} must be non-negative")
    return ids


TerminalLabel: TypeAlias = int | str


def _terminal_label(value: object) -> TerminalLabel:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise TypeError("terminal labels must be byte integers or strings")
    if isinstance(value, int):
        if not 0 <= value <= 255:
            raise ValueError("integer terminal labels must be bytes in [0, 255]")
    elif not value:
        raise ValueError("string terminal labels must be non-empty")
    return value


def _terminal_tuple(value: object) -> tuple[TerminalLabel, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError("witness_terminal_labels must be a sequence")
    return tuple(_terminal_label(label) for label in value)


def _freeze_json(value: object, field_name: str) -> object:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{field_name} must not contain NaN or infinity")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{field_name} keys must be strings")
            frozen[key] = _freeze_json(item, f"{field_name}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, field_name) for item in value)
    raise TypeError(f"{field_name} must contain only JSON-compatible values")


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


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


@dataclass(frozen=True, slots=True)
class Proposal:
    """One weighted model proposal for one physical token slot.

    ``weight`` is the MWPC utility. ``model_confidence`` is separate analysis
    metadata and is never implicitly added to that utility.
    """

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
    """Sum MWPC utility by choice while preserving stable proposal provenance.

    First-seen choice order and input proposal-ID order are retained for
    deterministic traversal; model confidence is deliberately not aggregated.
    """
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
class TokenArc:
    """One token choice crossing a physical slot boundary."""

    token_edge_id: int
    slot: int
    token_id: int
    source_boundary: int
    target_boundary: int
    emitted_bytes: bytes
    weight: float = 0.0
    matched_proposal_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("token_edge_id", "slot", "token_id", "source_boundary"):
            value = _require_int(getattr(self, field_name), field_name)
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        target_boundary = _require_int(self.target_boundary, "target_boundary")
        if target_boundary <= self.source_boundary:
            raise ValueError("target_boundary must be greater than source_boundary")
        if not isinstance(self.emitted_bytes, (bytes, bytearray)):
            raise TypeError("emitted_bytes must be bytes")
        object.__setattr__(self, "emitted_bytes", bytes(self.emitted_bytes))
        object.__setattr__(
            self,
            "weight",
            _finite_float(self.weight, "weight", non_negative=True),
        )
        object.__setattr__(
            self,
            "matched_proposal_ids",
            _stable_ids(
                self.matched_proposal_ids,
                "matched_proposal_ids",
                allow_empty=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class TerminalEdge:
    """One weighted terminal edge with stable token provenance."""

    edge_id: int
    source_state: int
    target_state: int
    terminal_label: TerminalLabel
    weight: float = 0.0
    provenance_token_edge_id: int | None = None
    matched_proposal_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("edge_id", "source_state", "target_state"):
            value = _require_int(getattr(self, field_name), field_name)
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")
        if self.source_state == self.target_state:
            raise ValueError("terminal edges cannot be self-loops")
        object.__setattr__(self, "terminal_label", _terminal_label(self.terminal_label))
        object.__setattr__(
            self,
            "weight",
            _finite_float(self.weight, "weight", non_negative=True),
        )
        if self.provenance_token_edge_id is not None:
            provenance_id = _require_int(
                self.provenance_token_edge_id, "provenance_token_edge_id"
            )
            if provenance_id < 0:
                raise ValueError("provenance_token_edge_id must be non-negative")
        object.__setattr__(
            self,
            "matched_proposal_ids",
            _stable_ids(
                self.matched_proposal_ids,
                "matched_proposal_ids",
                allow_empty=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class WeightedTerminalDAG:
    """Finite terminal graph with stable node and edge IDs.

    Full topological validation and indexing belong to T400. This boundary
    already rejects missing endpoints and ambiguous IDs.
    """

    node_ids: tuple[int, ...]
    start_node_id: int
    final_node_ids: tuple[int, ...]
    edges: tuple[TerminalEdge, ...] = ()

    def __post_init__(self) -> None:
        node_ids = _stable_ids(self.node_ids, "node_ids", allow_empty=False)
        start_node_id = _require_int(self.start_node_id, "start_node_id")
        if start_node_id not in node_ids:
            raise ValueError("start_node_id must reference an existing node")
        final_node_ids = _stable_ids(
            self.final_node_ids, "final_node_ids", allow_empty=False
        )
        missing_finals = set(final_node_ids) - set(node_ids)
        if missing_finals:
            raise ValueError("final_node_ids must reference existing nodes")

        if isinstance(self.edges, (str, bytes)) or not isinstance(self.edges, Iterable):
            raise TypeError("edges must be a sequence of TerminalEdge instances")
        edges = tuple(self.edges)
        if not all(isinstance(edge, TerminalEdge) for edge in edges):
            raise TypeError("edges must contain only TerminalEdge instances")
        edge_ids = tuple(edge.edge_id for edge in edges)
        if len(set(edge_ids)) != len(edge_ids):
            raise ValueError("edge IDs must be unique")
        node_set = set(node_ids)
        if any(
            edge.source_state not in node_set or edge.target_state not in node_set
            for edge in edges
        ):
            raise ValueError("every edge endpoint must reference an existing node")

        object.__setattr__(self, "node_ids", node_ids)
        object.__setattr__(self, "final_node_ids", final_node_ids)
        object.__setattr__(self, "edges", edges)


@dataclass(frozen=True, slots=True)
class ExactCommitResult:
    """Solver result plus the certificate needed for independent validation."""

    status: SolveStatus
    exactness_scope: ExactnessScope
    objective_value: float | None = None
    selected_proposal_ids: tuple[int, ...] = ()
    witness_token_ids: tuple[int, ...] = ()
    witness_terminal_labels: tuple[TerminalLabel, ...] = ()
    witness_graph_edge_ids: tuple[int, ...] = ()
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, SolveStatus):
            raise TypeError("status must be a SolveStatus")
        if not isinstance(self.exactness_scope, ExactnessScope):
            raise TypeError("exactness_scope must be an ExactnessScope")

        if self.objective_value is not None:
            object.__setattr__(
                self,
                "objective_value",
                _finite_float(
                    self.objective_value,
                    "objective_value",
                    non_negative=True,
                ),
            )

        selected_ids = _stable_ids(
            self.selected_proposal_ids,
            "selected_proposal_ids",
            allow_empty=True,
        )
        witness_token_ids = _int_tuple(self.witness_token_ids, "witness_token_ids")
        if any(token_id < 0 for token_id in witness_token_ids):
            raise ValueError("witness_token_ids must be non-negative")
        terminal_labels = _terminal_tuple(self.witness_terminal_labels)
        witness_edge_ids = _stable_ids(
            self.witness_graph_edge_ids,
            "witness_graph_edge_ids",
            allow_empty=True,
        )
        object.__setattr__(self, "selected_proposal_ids", selected_ids)
        object.__setattr__(self, "witness_token_ids", witness_token_ids)
        object.__setattr__(self, "witness_terminal_labels", terminal_labels)
        object.__setattr__(self, "witness_graph_edge_ids", witness_edge_ids)

        frozen_diagnostics = _freeze_json(self.diagnostics, "diagnostics")
        if not isinstance(frozen_diagnostics, Mapping):
            raise TypeError("diagnostics must be a mapping")
        object.__setattr__(self, "diagnostics", frozen_diagnostics)

        if self.status is SolveStatus.OPTIMAL:
            if self.objective_value is None:
                raise ValueError("OPTIMAL requires objective_value")
            if not witness_token_ids:
                raise ValueError("OPTIMAL requires a non-empty witness token sequence")
            if not terminal_labels:
                raise ValueError("OPTIMAL requires witness terminal labels")
            if not witness_edge_ids:
                raise ValueError("OPTIMAL requires a reconstructible witness path")
            if len(terminal_labels) != len(witness_edge_ids):
                raise ValueError(
                    "witness terminal labels and graph edge IDs must have equal length"
                )
        elif any(
            (
                self.objective_value is not None,
                bool(selected_ids),
                bool(witness_token_ids),
                bool(terminal_labels),
                bool(witness_edge_ids),
            )
        ):
            raise ValueError("non-OPTIMAL results cannot expose an objective or certificate")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible result without dropping stable IDs."""
        return {
            "status": self.status.value,
            "objective_value": self.objective_value,
            "selected_proposal_ids": list(self.selected_proposal_ids),
            "witness_token_ids": list(self.witness_token_ids),
            "witness_terminal_labels": list(self.witness_terminal_labels),
            "witness_graph_edge_ids": list(self.witness_graph_edge_ids),
            "exactness_scope": self.exactness_scope.to_dict(),
            "diagnostics": _thaw_json(self.diagnostics),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        """Reconstruct and validate a result parsed from JSON."""
        if not isinstance(data, Mapping):
            raise TypeError("exact commit result data must be a mapping")
        allowed = {
            "status",
            "objective_value",
            "selected_proposal_ids",
            "witness_token_ids",
            "witness_terminal_labels",
            "witness_graph_edge_ids",
            "exactness_scope",
            "diagnostics",
        }
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(repr(name) for name in unknown))
            raise ValueError(f"unknown exact commit result fields: {names}")
        missing = {"status", "exactness_scope"} - set(data)
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"missing exact commit result fields: {names}")

        status_value = data["status"]
        if not isinstance(status_value, str):
            raise TypeError("status must be a string")
        try:
            status = SolveStatus(status_value)
        except ValueError as exc:
            raise ValueError(f"unknown solve status: {status_value!r}") from exc

        scope_data = data["exactness_scope"]
        if not isinstance(scope_data, Mapping):
            raise TypeError("exactness_scope must be a mapping")
        objective_data = data.get("objective_value")
        objective = (
            None
            if objective_data is None
            else _finite_float(objective_data, "objective_value", non_negative=True)
        )
        diagnostics = data.get("diagnostics", {})
        if not isinstance(diagnostics, Mapping):
            raise TypeError("diagnostics must be a mapping")

        return cls(
            status=status,
            exactness_scope=ExactnessScope.from_dict(scope_data),
            objective_value=objective,
            selected_proposal_ids=_int_tuple(
                data.get("selected_proposal_ids", ()), "selected_proposal_ids"
            ),
            witness_token_ids=_int_tuple(
                data.get("witness_token_ids", ()), "witness_token_ids"
            ),
            witness_terminal_labels=_terminal_tuple(
                data.get("witness_terminal_labels", ())
            ),
            witness_graph_edge_ids=_int_tuple(
                data.get("witness_graph_edge_ids", ()), "witness_graph_edge_ids"
            ),
            diagnostics=diagnostics,
        )
