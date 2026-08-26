"""Immutable decoder commit and fallback contracts.

The exact solver result and the action taken by the decoder remain separate.
An optimal selected batch is committed exactly, an empty optimal batch may
commit one token from its certified witness, and a serial/EPIC callback may
make progress after a non-optimal solver status without acquiring an exactness
claim.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from types import MappingProxyType
from typing import Protocol

from mwpc_exact.types import ExactCommitResult, Proposal, SolveStatus, aggregate_proposals


class FailureFallbackStrategy(StrEnum):
    """Baseline strategy invoked after an inconclusive/non-optimal exact solve."""

    SERIAL = "serial"
    EPIC = "epic"


class CommitSource(StrEnum):
    """Mutually exclusive source of the physical token update."""

    EXACT_PROPOSALS = "exact_proposals"
    WITNESS_PROGRESS = "witness_progress"
    SERIAL_FALLBACK = "serial_fallback"
    EPIC_FALLBACK = "epic_fallback"
    FALLBACK_FAILED = "fallback_failed"
    NO_COMMIT = "no_commit"
    COMPLETE = "complete"


class CommitGuarantee(StrEnum):
    """Guarantee attached to the update, never inferred from fallback success."""

    EXACT_MWPC_SELECTION = "exact_mwpc_selection"
    EXACT_WITNESS_PROGRESS = "exact_witness_progress"
    BASELINE_FALLBACK_NO_EXACT_GUARANTEE = "baseline_fallback_no_exact_guarantee"
    NONE = "none"


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _id_tuple(value: object, field_name: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of IDs")
    ids = tuple(_non_negative_integer(item, f"{field_name} item") for item in value)
    if len(set(ids)) != len(ids):
        raise ValueError(f"{field_name} must not contain duplicates")
    return ids


def _finite_non_negative(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    normalized = float(value)
    if not isfinite(normalized) or normalized < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return normalized


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


def _normalize_canvas(value: object, field_name: str) -> tuple[int | None, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence of token IDs or None")
    canvas: list[int | None] = []
    for position, token_id in enumerate(value):
        if token_id is None:
            canvas.append(None)
        else:
            canvas.append(
                _non_negative_integer(token_id, f"{field_name} token at position {position}")
            )
    if not canvas:
        raise ValueError(f"{field_name} must contain at least one physical slot")
    return tuple(canvas)


@dataclass(frozen=True, slots=True)
class TokenCommit:
    """One physical update with independently recomputed proposal accounting."""

    position: int
    token_id: int
    selected_proposal_ids: tuple[int, ...] = ()
    matching_proposal_ids: tuple[int, ...] = ()
    matching_proposal_weight: float = 0.0

    def __post_init__(self) -> None:
        _non_negative_integer(self.position, "position")
        _non_negative_integer(self.token_id, "token_id")
        selected = _id_tuple(self.selected_proposal_ids, "selected_proposal_ids")
        matching = _id_tuple(self.matching_proposal_ids, "matching_proposal_ids")
        if not set(selected) <= set(matching):
            raise ValueError("selected proposal IDs must be real matches for this token commit")
        object.__setattr__(self, "selected_proposal_ids", selected)
        object.__setattr__(self, "matching_proposal_ids", matching)
        object.__setattr__(
            self,
            "matching_proposal_weight",
            _finite_non_negative(
                self.matching_proposal_weight,
                "matching_proposal_weight",
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "position": self.position,
            "token_id": self.token_id,
            "selected_proposal_ids": list(self.selected_proposal_ids),
            "matching_proposal_ids": list(self.matching_proposal_ids),
            "matching_proposal_weight": self.matching_proposal_weight,
        }


@dataclass(frozen=True, slots=True)
class FallbackToken:
    """One raw position/token update proposed by a serial or EPIC callback."""

    position: int
    token_id: int

    def __post_init__(self) -> None:
        _non_negative_integer(self.position, "position")
        _non_negative_integer(self.token_id, "token_id")

    def to_dict(self) -> dict[str, int]:
        return {"position": self.position, "token_id": self.token_id}


@dataclass(frozen=True, slots=True)
class FallbackSelection:
    """Structured baseline callback output with no solver-status field."""

    tokens: tuple[FallbackToken, ...]
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        tokens = tuple(self.tokens)
        if not tokens or not all(isinstance(token, FallbackToken) for token in tokens):
            raise ValueError("fallback selection must contain at least one FallbackToken")
        positions = tuple(token.position for token in tokens)
        if len(set(positions)) != len(positions):
            raise ValueError("fallback selection must not update one position more than once")
        frozen = _freeze_json(self.diagnostics, "diagnostics")
        if not isinstance(frozen, Mapping):
            raise TypeError("diagnostics must be a mapping")
        object.__setattr__(self, "tokens", tokens)
        object.__setattr__(self, "diagnostics", frozen)

    def to_dict(self) -> dict[str, object]:
        return {
            "tokens": [token.to_dict() for token in self.tokens],
            "diagnostics": _thaw_json(self.diagnostics),
        }


@dataclass(frozen=True, slots=True)
class FailureFallbackRequest:
    """Frozen information supplied to a configured baseline callback."""

    strategy: FailureFallbackStrategy
    solver_result: ExactCommitResult
    canvas: tuple[int | None, ...]
    proposals: tuple[Proposal, ...]
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.strategy, FailureFallbackStrategy):
            raise TypeError("strategy must be a FailureFallbackStrategy")
        if not isinstance(self.solver_result, ExactCommitResult):
            raise TypeError("solver_result must be an ExactCommitResult")
        if self.solver_result.status is SolveStatus.OPTIMAL:
            raise ValueError("failure fallback requests require a non-optimal solver result")
        object.__setattr__(self, "canvas", _normalize_canvas(self.canvas, "canvas"))
        proposals = tuple(self.proposals)
        aggregate_proposals(proposals)
        object.__setattr__(self, "proposals", proposals)
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("reason must be a non-empty string")


class FailureFallbackHandler(Protocol):
    """Callable adapter implemented by the serial or EPIC integration layer."""

    def __call__(self, request: FailureFallbackRequest, /) -> FallbackSelection: ...


@dataclass(frozen=True, slots=True)
class DecoderStepResult:
    """Physical canvas update while retaining the original exact-solver status."""

    solver_result: ExactCommitResult
    input_canvas: tuple[int | None, ...]
    updated_canvas: tuple[int | None, ...]
    commits: tuple[TokenCommit, ...]
    commit_source: CommitSource
    commit_guarantee: CommitGuarantee
    fallback_strategy: FailureFallbackStrategy | None = None
    fallback_reason: str | None = None
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.solver_result, ExactCommitResult):
            raise TypeError("solver_result must be an ExactCommitResult")
        if not isinstance(self.commit_source, CommitSource):
            raise TypeError("commit_source must be a CommitSource")
        if not isinstance(self.commit_guarantee, CommitGuarantee):
            raise TypeError("commit_guarantee must be a CommitGuarantee")
        if self.fallback_strategy is not None and not isinstance(
            self.fallback_strategy,
            FailureFallbackStrategy,
        ):
            raise TypeError("fallback_strategy must be a FailureFallbackStrategy or None")

        input_canvas = _normalize_canvas(self.input_canvas, "input_canvas")
        updated_canvas = _normalize_canvas(self.updated_canvas, "updated_canvas")
        if len(input_canvas) != len(updated_canvas):
            raise ValueError("input_canvas and updated_canvas must have equal length")
        commits = tuple(self.commits)
        if not all(isinstance(commit, TokenCommit) for commit in commits):
            raise TypeError("commits must contain only TokenCommit instances")
        commit_by_position = {commit.position: commit for commit in commits}
        if len(commit_by_position) != len(commits):
            raise ValueError("commits must not update one position more than once")
        for position, (before, after) in enumerate(zip(input_canvas, updated_canvas, strict=True)):
            commit = commit_by_position.get(position)
            if commit is None:
                if before != after:
                    raise ValueError("updated_canvas changed a position absent from commits")
                continue
            if before is not None:
                raise ValueError("decoder commits cannot overwrite an already fixed position")
            if after != commit.token_id:
                raise ValueError("updated_canvas does not contain the recorded committed token")

        self._validate_source_contract(input_canvas, commits)
        if self.fallback_reason is not None and (
            not isinstance(self.fallback_reason, str) or not self.fallback_reason
        ):
            raise ValueError("fallback_reason must be a non-empty string when provided")
        frozen = _freeze_json(self.diagnostics, "diagnostics")
        if not isinstance(frozen, Mapping):
            raise TypeError("diagnostics must be a mapping")
        object.__setattr__(self, "input_canvas", input_canvas)
        object.__setattr__(self, "updated_canvas", updated_canvas)
        object.__setattr__(self, "commits", commits)
        object.__setattr__(self, "diagnostics", frozen)

    def _validate_source_contract(
        self,
        input_canvas: tuple[int | None, ...],
        commits: tuple[TokenCommit, ...],
    ) -> None:
        status = self.solver_result.status
        source = self.commit_source
        selected_ids = tuple(
            proposal_id for commit in commits for proposal_id in commit.selected_proposal_ids
        )
        if source is CommitSource.EXACT_PROPOSALS:
            if status is not SolveStatus.OPTIMAL or not commits:
                raise ValueError("exact proposal commits require a non-empty OPTIMAL batch")
            if self.commit_guarantee is not CommitGuarantee.EXACT_MWPC_SELECTION:
                raise ValueError("exact proposal commits require the MWPC selection guarantee")
            if Counter(selected_ids) != Counter(self.solver_result.selected_proposal_ids):
                raise ValueError("committed proposal IDs differ from the exact selected set")
            if self.fallback_strategy is not None or self.fallback_reason is not None:
                raise ValueError("exact proposal commits cannot carry fallback metadata")
        elif source is CommitSource.WITNESS_PROGRESS:
            if status is not SolveStatus.OPTIMAL or len(commits) != 1:
                raise ValueError("witness progress requires one commit from an OPTIMAL result")
            if self.solver_result.selected_proposal_ids or selected_ids:
                raise ValueError("witness progress cannot invent selected proposal IDs")
            if self.commit_guarantee is not CommitGuarantee.EXACT_WITNESS_PROGRESS:
                raise ValueError("witness progress requires its distinct witness guarantee")
            if self.fallback_strategy is not None or self.fallback_reason is None:
                raise ValueError("witness progress needs a reason and no failure strategy")
        elif source in {CommitSource.SERIAL_FALLBACK, CommitSource.EPIC_FALLBACK}:
            expected_strategy = (
                FailureFallbackStrategy.SERIAL
                if source is CommitSource.SERIAL_FALLBACK
                else FailureFallbackStrategy.EPIC
            )
            if status is SolveStatus.OPTIMAL or not commits:
                raise ValueError("baseline fallback commits require a non-optimal solver result")
            if self.fallback_strategy is not expected_strategy:
                raise ValueError("fallback source and configured strategy disagree")
            if selected_ids:
                raise ValueError("baseline fallback cannot create exact selected proposal IDs")
            if self.commit_guarantee is not CommitGuarantee.BASELINE_FALLBACK_NO_EXACT_GUARANTEE:
                raise ValueError("baseline fallback must remain explicitly non-exact")
            if self.fallback_reason is None:
                raise ValueError("baseline fallback requires a recorded reason")
        elif source is CommitSource.COMPLETE:
            if (
                status is not SolveStatus.OPTIMAL
                or commits
                or any(token is None for token in input_canvas)
            ):
                raise ValueError("complete requires an OPTIMAL result and a fully fixed canvas")
            if self.commit_guarantee is not CommitGuarantee.EXACT_WITNESS_PROGRESS:
                raise ValueError("complete retains the exact witness guarantee")
        else:
            if commits or selected_ids:
                raise ValueError("failed/unhandled fallback outcomes cannot expose commits")
            if self.commit_guarantee is not CommitGuarantee.NONE:
                raise ValueError("failed/unhandled fallback outcomes have no commit guarantee")
            if status is SolveStatus.OPTIMAL:
                raise ValueError("an OPTIMAL result cannot be labeled as an unhandled failure")
            if self.fallback_reason is None:
                raise ValueError("failed/unhandled fallback outcomes require a reason")

    @property
    def selected_proposal_ids(self) -> tuple[int, ...]:
        return tuple(
            proposal_id for commit in self.commits for proposal_id in commit.selected_proposal_ids
        )

    @property
    def matching_proposal_ids(self) -> tuple[int, ...]:
        return tuple(
            proposal_id for commit in self.commits for proposal_id in commit.matching_proposal_ids
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "solver_result": self.solver_result.to_dict(),
            "input_canvas": list(self.input_canvas),
            "updated_canvas": list(self.updated_canvas),
            "commits": [commit.to_dict() for commit in self.commits],
            "commit_source": self.commit_source.value,
            "commit_guarantee": self.commit_guarantee.value,
            "fallback_strategy": (
                None if self.fallback_strategy is None else self.fallback_strategy.value
            ),
            "fallback_reason": self.fallback_reason,
            "diagnostics": _thaw_json(self.diagnostics),
        }


FailureFallbackCallable = Callable[[FailureFallbackRequest], FallbackSelection]


__all__ = [
    "CommitGuarantee",
    "CommitSource",
    "DecoderStepResult",
    "FailureFallbackCallable",
    "FailureFallbackHandler",
    "FailureFallbackRequest",
    "FailureFallbackStrategy",
    "FallbackSelection",
    "FallbackToken",
    "TokenCommit",
]
