"""Model-independent commit decisions and explicit decoder fallbacks.

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
from math import fsum, isclose, isfinite
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
        for position, (before, after) in enumerate(
            zip(input_canvas, updated_canvas, strict=True)
        ):
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
            if (
                self.commit_guarantee
                is not CommitGuarantee.BASELINE_FALLBACK_NO_EXACT_GUARANTEE
            ):
                raise ValueError("baseline fallback must remain explicitly non-exact")
            if self.fallback_reason is None:
                raise ValueError("baseline fallback requires a recorded reason")
        elif source is CommitSource.COMPLETE:
            if status is not SolveStatus.OPTIMAL or commits or any(
                token is None for token in input_canvas
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


def _prepare_proposals(
    proposals: Iterable[Proposal],
    *,
    slot_count: int,
    vocabulary_size: int,
) -> tuple[Proposal, ...]:
    items = tuple(proposals)
    aggregate_proposals(items)
    for proposal in items:
        if proposal.position >= slot_count:
            raise ValueError(
                f"proposal {proposal.proposal_id} position is outside the finite canvas"
            )
        if proposal.token_id >= vocabulary_size:
            raise ValueError(
                f"proposal {proposal.proposal_id} token is outside the exactness vocabulary"
            )
    return items


def _validate_optimal_result(
    result: ExactCommitResult,
    *,
    canvas: tuple[int | None, ...],
    proposals: tuple[Proposal, ...],
) -> None:
    validation = result.diagnostics.get("certificate_validation")
    if not isinstance(validation, Mapping) or validation.get("is_valid") is not True:
        raise ValueError(
            "OPTIMAL decoder input requires recorded independent certificate validation"
        )
    witness = result.witness_token_ids
    if len(witness) != len(canvas):
        raise ValueError("OPTIMAL witness must contain exactly one token per physical slot")
    vocabulary_size = result.exactness_scope.vocabulary_size
    if any(token_id >= vocabulary_size for token_id in witness):
        raise ValueError("OPTIMAL witness token is outside the exactness vocabulary")
    for position, fixed_token in enumerate(canvas):
        if fixed_token is not None and witness[position] != fixed_token:
            raise ValueError("OPTIMAL witness does not preserve the fixed input canvas")

    matched = tuple(
        proposal
        for proposal in proposals
        if proposal.weight > 0.0 and witness[proposal.position] == proposal.token_id
    )
    expected_ids = tuple(proposal.proposal_id for proposal in matched)
    if Counter(result.selected_proposal_ids) != Counter(expected_ids):
        raise ValueError("OPTIMAL selected proposal IDs disagree with the witness")
    expected_objective = fsum(proposal.weight for proposal in matched)
    if result.objective_value is None or not isclose(
        result.objective_value,
        expected_objective,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        raise ValueError("OPTIMAL objective disagrees with matched positive proposals")


def _proposal_accounting(
    *,
    position: int,
    token_id: int,
    proposals: tuple[Proposal, ...],
    selected_ids: frozenset[int],
) -> TokenCommit:
    matches = tuple(
        proposal
        for proposal in proposals
        if proposal.position == position and proposal.token_id == token_id
    )
    return TokenCommit(
        position=position,
        token_id=token_id,
        selected_proposal_ids=tuple(
            proposal.proposal_id
            for proposal in matches
            if proposal.proposal_id in selected_ids
        ),
        matching_proposal_ids=tuple(proposal.proposal_id for proposal in matches),
        matching_proposal_weight=fsum(proposal.weight for proposal in matches),
    )


def _exact_proposal_commits(
    result: ExactCommitResult,
    *,
    canvas: tuple[int | None, ...],
    proposals: tuple[Proposal, ...],
) -> tuple[TokenCommit, ...]:
    selected = frozenset(result.selected_proposal_ids)
    positions = sorted(
        {
            proposal.position
            for proposal in proposals
            if proposal.proposal_id in selected
        }
    )
    if any(canvas[position] is not None for position in positions):
        raise ValueError("selected decoder proposals must target currently masked positions")
    return tuple(
        _proposal_accounting(
            position=position,
            token_id=result.witness_token_ids[position],
            proposals=proposals,
            selected_ids=selected,
        )
        for position in positions
    )


def _witness_probabilities(
    value: object,
    *,
    slot_count: int,
) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("witness_token_probabilities must be a finite sequence")
    if len(value) != slot_count:
        raise ValueError("witness_token_probabilities and canvas must have equal length")
    probabilities: list[float] = []
    for position, raw_probability in enumerate(value):
        if isinstance(raw_probability, bool) or not isinstance(
            raw_probability,
            (int, float),
        ):
            raise TypeError(f"witness probability at position {position} must be real")
        probability = float(raw_probability)
        if not isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError(
                f"witness probability at position {position} must be finite and in [0, 1]"
            )
        probabilities.append(probability)
    return tuple(probabilities)


def _apply_commits(
    canvas: tuple[int | None, ...],
    commits: Sequence[TokenCommit],
) -> tuple[int | None, ...]:
    updated = list(canvas)
    seen: set[int] = set()
    for commit in commits:
        if commit.position >= len(updated):
            raise ValueError("commit position is outside the finite canvas")
        if commit.position in seen:
            raise ValueError("one decoder step cannot commit one position more than once")
        if updated[commit.position] is not None:
            raise ValueError("decoder commit cannot overwrite an already fixed position")
        updated[commit.position] = commit.token_id
        seen.add(commit.position)
    return tuple(updated)


def _assert_witness_compatible(
    updated_canvas: tuple[int | None, ...],
    witness_token_ids: tuple[int, ...],
) -> None:
    if len(updated_canvas) != len(witness_token_ids) or any(
        fixed_token is not None and fixed_token != witness_token_ids[position]
        for position, fixed_token in enumerate(updated_canvas)
    ):
        raise ValueError("committed canvas is not completable by the exact witness")


def _failure_reason(result: ExactCommitResult) -> str:
    parts = [f"solver_status={result.status.value}"]
    for key in ("error_stage", "error_type", "error_message"):
        value = result.diagnostics.get(key)
        if value is not None:
            parts.append(f"{key}={value}")
    adaptive = result.diagnostics.get("adaptive_support")
    if isinstance(adaptive, Mapping):
        stopped_reason = adaptive.get("stopped_reason")
        if stopped_reason is not None:
            parts.append(f"adaptive_stop={stopped_reason}")
    return "; ".join(parts)


def _attempted_k(result: ExactCommitResult) -> tuple[int, ...]:
    adaptive = result.diagnostics.get("adaptive_support")
    if not isinstance(adaptive, Mapping):
        return ()
    attempted = adaptive.get("attempted_k")
    if not isinstance(attempted, (list, tuple)):
        return ()
    if any(isinstance(item, bool) or not isinstance(item, int) for item in attempted):
        return ()
    return tuple(attempted)


def _step_diagnostics(
    *,
    result: ExactCommitResult,
    commits: tuple[TokenCommit, ...],
    source: CommitSource,
    guarantee: CommitGuarantee,
    fallback_strategy: FailureFallbackStrategy | None,
    fallback_reason: str | None,
    fallback_attempted: bool,
    fallback_succeeded: bool,
    witness_compatible: bool | None,
    fallback_handler_diagnostics: Mapping[str, object] | None = None,
    fallback_error: Exception | None = None,
) -> dict[str, object]:
    selected_ids = tuple(
        proposal_id for commit in commits for proposal_id in commit.selected_proposal_ids
    )
    matching_ids = tuple(
        proposal_id for commit in commits for proposal_id in commit.matching_proposal_ids
    )
    matching_weight = fsum(commit.matching_proposal_weight for commit in commits)
    fallback_class = (
        "witness_progress"
        if source is CommitSource.WITNESS_PROGRESS
        else "solver_failure"
        if fallback_attempted or source in {CommitSource.FALLBACK_FAILED, CommitSource.NO_COMMIT}
        else "none"
    )
    diagnostics: dict[str, object] = {
        "decoder": "exact_commit_decoder_v1",
        "original_solver_status": result.status.value,
        "original_exactness_scope": result.exactness_scope.to_dict(),
        "commit_source": source.value,
        "commit_guarantee": guarantee.value,
        "committed_position_count": len(commits),
        "committed_positions": [commit.position for commit in commits],
        "selected_proposal_ids": list(selected_ids),
        "matching_frozen_proposal_ids": list(matching_ids),
        "matching_frozen_proposal_weight": matching_weight,
        "proposal_backed_commit_count": sum(
            bool(commit.matching_proposal_ids) for commit in commits
        ),
        "fallback_class": fallback_class,
        "progress_fallback": source is CommitSource.WITNESS_PROGRESS,
        "progress_fallback_rule": (
            "witness_probability_descending_then_absolute_position_ascending"
            if source is CommitSource.WITNESS_PROGRESS
            else None
        ),
        "failure_fallback_attempted": fallback_attempted,
        "failure_fallback_succeeded": fallback_succeeded,
        "failure_fallback_strategy": (
            None if fallback_strategy is None else fallback_strategy.value
        ),
        "fallback_reason": fallback_reason,
        "support_expansion_attempted_k": list(_attempted_k(result)),
        "witness_compatible_after_commit": witness_compatible,
        "no_remasking_verified": True,
    }
    if fallback_handler_diagnostics is not None:
        diagnostics["fallback_handler_diagnostics"] = dict(fallback_handler_diagnostics)
    if fallback_error is not None:
        diagnostics["fallback_error_type"] = type(fallback_error).__name__
        diagnostics["fallback_error_message"] = str(fallback_error)
    return diagnostics


def _build_step_result(
    *,
    result: ExactCommitResult,
    canvas: tuple[int | None, ...],
    commits: tuple[TokenCommit, ...],
    source: CommitSource,
    guarantee: CommitGuarantee,
    fallback_strategy: FailureFallbackStrategy | None = None,
    fallback_reason: str | None = None,
    fallback_attempted: bool = False,
    fallback_succeeded: bool = False,
    witness_compatible: bool | None = None,
    fallback_handler_diagnostics: Mapping[str, object] | None = None,
    fallback_error: Exception | None = None,
) -> DecoderStepResult:
    updated = _apply_commits(canvas, commits)
    return DecoderStepResult(
        solver_result=result,
        input_canvas=canvas,
        updated_canvas=updated,
        commits=commits,
        commit_source=source,
        commit_guarantee=guarantee,
        fallback_strategy=fallback_strategy,
        fallback_reason=fallback_reason,
        diagnostics=_step_diagnostics(
            result=result,
            commits=commits,
            source=source,
            guarantee=guarantee,
            fallback_strategy=fallback_strategy,
            fallback_reason=fallback_reason,
            fallback_attempted=fallback_attempted,
            fallback_succeeded=fallback_succeeded,
            witness_compatible=witness_compatible,
            fallback_handler_diagnostics=fallback_handler_diagnostics,
            fallback_error=fallback_error,
        ),
    )


def apply_exact_commit_result(
    result: ExactCommitResult,
    *,
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    witness_token_probabilities: Sequence[float] | None = None,
    failure_fallback_strategy: FailureFallbackStrategy | None = None,
    failure_fallback: FailureFallbackHandler | None = None,
) -> DecoderStepResult:
    """Apply one exact result or an explicitly configured baseline fallback.

    For an empty optimal selected set, ``witness_token_probabilities`` must
    contain the model probability assigned to each witness token. The highest
    probability among still-masked positions is committed; equal values use
    the lowest absolute position. Failure callbacks return only raw token
    updates, and this layer independently recomputes any real proposal match.
    """

    if not isinstance(result, ExactCommitResult):
        raise TypeError("result must be an ExactCommitResult")
    if (failure_fallback_strategy is None) != (failure_fallback is None):
        raise ValueError("failure fallback strategy and callable must be supplied together")
    if failure_fallback_strategy is not None and not isinstance(
        failure_fallback_strategy,
        FailureFallbackStrategy,
    ):
        raise TypeError("failure_fallback_strategy must be a FailureFallbackStrategy")
    canvas_tokens = _normalize_canvas(canvas, "canvas")
    proposal_items = _prepare_proposals(
        proposals,
        slot_count=len(canvas_tokens),
        vocabulary_size=result.exactness_scope.vocabulary_size,
    )

    if result.status is SolveStatus.OPTIMAL:
        _validate_optimal_result(result, canvas=canvas_tokens, proposals=proposal_items)
        if result.selected_proposal_ids:
            commits = _exact_proposal_commits(
                result,
                canvas=canvas_tokens,
                proposals=proposal_items,
            )
            if not commits:
                raise ValueError("non-empty selected proposal set produced no physical commit")
            updated = _apply_commits(canvas_tokens, commits)
            _assert_witness_compatible(updated, result.witness_token_ids)
            return _build_step_result(
                result=result,
                canvas=canvas_tokens,
                commits=commits,
                source=CommitSource.EXACT_PROPOSALS,
                guarantee=CommitGuarantee.EXACT_MWPC_SELECTION,
                witness_compatible=True,
            )

        masked_positions = tuple(
            position for position, token_id in enumerate(canvas_tokens) if token_id is None
        )
        if not masked_positions:
            return _build_step_result(
                result=result,
                canvas=canvas_tokens,
                commits=(),
                source=CommitSource.COMPLETE,
                guarantee=CommitGuarantee.EXACT_WITNESS_PROGRESS,
                witness_compatible=True,
            )
        if witness_token_probabilities is None:
            raise ValueError(
                "witness_token_probabilities are required for deterministic witness progress"
            )
        probabilities = _witness_probabilities(
            witness_token_probabilities,
            slot_count=len(canvas_tokens),
        )
        position = min(masked_positions, key=lambda item: (-probabilities[item], item))
        commit = _proposal_accounting(
            position=position,
            token_id=result.witness_token_ids[position],
            proposals=proposal_items,
            selected_ids=frozenset(),
        )
        updated = _apply_commits(canvas_tokens, (commit,))
        _assert_witness_compatible(updated, result.witness_token_ids)
        return _build_step_result(
            result=result,
            canvas=canvas_tokens,
            commits=(commit,),
            source=CommitSource.WITNESS_PROGRESS,
            guarantee=CommitGuarantee.EXACT_WITNESS_PROGRESS,
            fallback_reason="optimal_zero_selected_proposals",
            witness_compatible=True,
        )

    reason = _failure_reason(result)
    if not any(token_id is None for token_id in canvas_tokens):
        return _build_step_result(
            result=result,
            canvas=canvas_tokens,
            commits=(),
            source=CommitSource.NO_COMMIT,
            guarantee=CommitGuarantee.NONE,
            fallback_reason=f"{reason}; canvas_already_complete",
        )
    if failure_fallback_strategy is None or failure_fallback is None:
        return _build_step_result(
            result=result,
            canvas=canvas_tokens,
            commits=(),
            source=CommitSource.NO_COMMIT,
            guarantee=CommitGuarantee.NONE,
            fallback_reason=f"{reason}; no_failure_fallback_configured",
        )

    request = FailureFallbackRequest(
        strategy=failure_fallback_strategy,
        solver_result=result,
        canvas=canvas_tokens,
        proposals=proposal_items,
        reason=reason,
    )
    try:
        selection = failure_fallback(request)
        if not isinstance(selection, FallbackSelection):
            raise TypeError("failure fallback must return a FallbackSelection")
        commits = tuple(
            _proposal_accounting(
                position=token.position,
                token_id=token.token_id,
                proposals=proposal_items,
                selected_ids=frozenset(),
            )
            for token in selection.tokens
        )
        if any(
            commit.token_id >= result.exactness_scope.vocabulary_size for commit in commits
        ):
            raise ValueError("fallback token is outside the exactness vocabulary")
        _apply_commits(canvas_tokens, commits)
    except Exception as error:
        return _build_step_result(
            result=result,
            canvas=canvas_tokens,
            commits=(),
            source=CommitSource.FALLBACK_FAILED,
            guarantee=CommitGuarantee.NONE,
            fallback_strategy=failure_fallback_strategy,
            fallback_reason=reason,
            fallback_attempted=True,
            fallback_succeeded=False,
            fallback_error=error,
        )

    source = (
        CommitSource.SERIAL_FALLBACK
        if failure_fallback_strategy is FailureFallbackStrategy.SERIAL
        else CommitSource.EPIC_FALLBACK
    )
    return _build_step_result(
        result=result,
        canvas=canvas_tokens,
        commits=commits,
        source=source,
        guarantee=CommitGuarantee.BASELINE_FALLBACK_NO_EXACT_GUARANTEE,
        fallback_strategy=failure_fallback_strategy,
        fallback_reason=reason,
        fallback_attempted=True,
        fallback_succeeded=True,
        fallback_handler_diagnostics=selection.diagnostics,
    )


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
    "apply_exact_commit_result",
]
