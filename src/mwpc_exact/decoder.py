"""Apply certified exact results or explicit non-exact decoder fallbacks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from math import fsum, isclose, isfinite

from mwpc_exact.decoder_types import (
    CommitGuarantee,
    CommitSource,
    DecoderStepResult,
    FailureFallbackCallable,
    FailureFallbackHandler,
    FailureFallbackRequest,
    FailureFallbackStrategy,
    FallbackSelection,
    FallbackToken,
    TokenCommit,
    _normalize_canvas,
)
from mwpc_exact.profiling import ComponentProfiler, ProfilingComponent
from mwpc_exact.types import ExactCommitResult, Proposal, SolveStatus, aggregate_proposals
from mwpc_exact.validated import ValidatedExactCommit


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
            proposal.proposal_id for proposal in matches if proposal.proposal_id in selected_ids
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
        {proposal.position for proposal in proposals if proposal.proposal_id in selected}
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


def _witness_progress_positions(
    value: Sequence[int] | None,
    *,
    canvas: tuple[int | None, ...],
) -> tuple[int, ...]:
    masked_positions = tuple(
        position for position, token_id in enumerate(canvas) if token_id is None
    )
    if value is None:
        return masked_positions
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("witness_progress_positions must be a finite sequence")
    positions: list[int] = []
    for raw_position in value:
        if isinstance(raw_position, bool) or not isinstance(raw_position, int):
            raise TypeError("witness progress positions must be integers")
        if raw_position < 0 or raw_position >= len(canvas):
            raise ValueError("witness progress position is outside the finite canvas")
        if canvas[raw_position] is not None:
            raise ValueError("witness progress positions must be currently masked")
        positions.append(raw_position)
    if len(set(positions)) != len(positions):
        raise ValueError("witness_progress_positions must not contain duplicates")
    if not positions and masked_positions:
        raise ValueError("witness_progress_positions must permit progress on a masked slot")
    return tuple(positions)


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
    profiler: ComponentProfiler | None,
    fallback_strategy: FailureFallbackStrategy | None = None,
    fallback_reason: str | None = None,
    fallback_attempted: bool = False,
    fallback_succeeded: bool = False,
    witness_compatible: bool | None = None,
    fallback_handler_diagnostics: Mapping[str, object] | None = None,
    fallback_error: Exception | None = None,
) -> DecoderStepResult:
    if profiler is None or not profiler.enabled:
        updated = _apply_commits(canvas, commits)
    else:
        with profiler.measure(ProfilingComponent.COMMIT_UPDATE):
            updated = _apply_commits(canvas, commits)
        profiler.set_counter("commit_count", len(commits))
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
    result: ValidatedExactCommit | ExactCommitResult,
    *,
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    witness_token_probabilities: Sequence[float] | None = None,
    witness_progress_positions: Sequence[int] | None = None,
    failure_fallback_strategy: FailureFallbackStrategy | None = None,
    failure_fallback: FailureFallbackHandler | None = None,
    profiler: ComponentProfiler | None = None,
) -> DecoderStepResult:
    """Apply one exact result or an explicitly configured baseline fallback.

    For an empty optimal selected set, ``witness_token_probabilities`` must
    contain the model probability assigned to each witness token. The highest
    probability among the optional ``witness_progress_positions`` boundary is
    committed; omitted positions permit every still-masked slot and equal
    values use the lowest absolute position. Failure callbacks return only raw
    token updates, and this layer independently recomputes any real proposal
    match.
    """

    if isinstance(result, ValidatedExactCommit):
        result = result.result
    elif not isinstance(result, ExactCommitResult):
        raise TypeError("result must be a ValidatedExactCommit or ExactCommitResult")
    elif result.status is SolveStatus.OPTIMAL:
        raise ValueError("OPTIMAL decoder input requires a ValidatedExactCommit")
    if profiler is not None and not isinstance(profiler, ComponentProfiler):
        raise TypeError("profiler must be a ComponentProfiler or None")
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
                profiler=profiler,
                witness_compatible=True,
            )

        masked_positions = _witness_progress_positions(
            witness_progress_positions,
            canvas=canvas_tokens,
        )
        if not masked_positions:
            return _build_step_result(
                result=result,
                canvas=canvas_tokens,
                commits=(),
                source=CommitSource.COMPLETE,
                guarantee=CommitGuarantee.EXACT_WITNESS_PROGRESS,
                profiler=profiler,
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
            profiler=profiler,
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
            profiler=profiler,
            fallback_reason=f"{reason}; canvas_already_complete",
        )
    if failure_fallback_strategy is None or failure_fallback is None:
        return _build_step_result(
            result=result,
            canvas=canvas_tokens,
            commits=(),
            source=CommitSource.NO_COMMIT,
            guarantee=CommitGuarantee.NONE,
            profiler=profiler,
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
        if any(commit.token_id >= result.exactness_scope.vocabulary_size for commit in commits):
            raise ValueError("fallback token is outside the exactness vocabulary")
        _apply_commits(canvas_tokens, commits)
    except Exception as error:
        return _build_step_result(
            result=result,
            canvas=canvas_tokens,
            commits=(),
            source=CommitSource.FALLBACK_FAILED,
            guarantee=CommitGuarantee.NONE,
            profiler=profiler,
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
        profiler=profiler,
        fallback_strategy=failure_fallback_strategy,
        fallback_reason=reason,
        fallback_attempted=True,
        fallback_succeeded=True,
        fallback_handler_diagnostics=selection.diagnostics,
    )


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
