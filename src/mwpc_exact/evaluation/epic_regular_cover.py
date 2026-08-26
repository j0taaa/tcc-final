"""Read-only adapter from frozen common inputs to EPIC's pinned heuristic.

The adapter delegates selection to the upstream regular-cover implementation;
it does not copy or redefine EPIC's recursive cover/exact-shrink algorithm.
EPIC's candidate ranking remains based on saved model confidence, while the
common comparison score is independently recomputed from MWPC proposal
weights.  Because EPIC does not return a finite-slot completion certificate,
successful results are explicitly ``HEURISTIC`` and carry no witness.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from math import fsum, isfinite
from time import perf_counter
from typing import Protocol, cast

from mwpc_exact.evaluation.selection import (
    SelectionInput,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
)
from mwpc_exact.types import Proposal

EPIC_UPSTREAM_COMMIT = "5b1b31098f34ed3691d2a9f4aae14fdf5839d072"


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


class _EpicCandidate(Protocol):
    index: int
    token_id: int
    word: object
    score: float


class _CandidateFactory(Protocol):
    def __call__(
        self,
        index: int,
        token_id: int,
        word: object,
        score: float = 0.0,
    ) -> _EpicCandidate: ...


class _BatchSelector(Protocol):
    def __call__(
        self,
        *,
        words_full: Sequence[object],
        candidates: Sequence[_EpicCandidate],
        prompt_len: int,
        cfg: object,
        lex_map: object,
        terminals: list[str],
        prelex: str | None,
        single_token_lexing: object,
        inject_gap_size: int,
        max_total_injections: int,
        subtokens: object,
        supertokens: object,
        strip_chars: str | None,
        trace: bool = False,
    ) -> Sequence[_EpicCandidate]: ...


@dataclass(frozen=True, slots=True)
class _EpicRuntime:
    candidate_factory: _CandidateFactory
    select_batch: _BatchSelector
    minimum_batch_size: Callable[[], int]
    exact_shrink_enabled: Callable[[], bool]
    profiler_enabled: Callable[[], bool]
    profiler_snapshot: Callable[[], Mapping[str, object]]


@dataclass(frozen=True, slots=True)
class EpicSelectionContext:
    """EPIC lexical state paired with one common generated-canvas input.

    ``words_full`` is the upstream decoded tracking row, including its prompt.
    Common proposal positions are generated-canvas-relative and are translated
    to EPIC indices by adding ``prompt_length``.
    """

    words_full: tuple[object, ...]
    prompt_length: int
    cfg: object
    decode_token: Callable[[int], object]
    lex_map: object = None
    terminals: tuple[str, ...] = ()
    prelex: str | None = None
    single_token_lexing: object = None
    inject_gap_size: int = 0
    max_total_injections: int = 0
    subtokens: object = None
    supertokens: object = None
    strip_chars: str | None = None
    trace: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.words_full, (str, bytes)) or not isinstance(
            self.words_full,
            Sequence,
        ):
            raise TypeError("words_full must be a finite decoded tracking sequence")
        words = tuple(self.words_full)
        prompt_length = _non_negative_integer(self.prompt_length, "prompt_length")
        if prompt_length > len(words):
            raise ValueError("prompt_length cannot exceed words_full length")
        if self.cfg is None:
            raise ValueError("cfg must contain the upstream EPIC grammar")
        if not callable(self.decode_token):
            raise TypeError("decode_token must be callable")
        terminals = tuple(self.terminals)
        if not all(isinstance(terminal, str) for terminal in terminals):
            raise TypeError("terminals must contain only strings")
        _non_negative_integer(self.inject_gap_size, "inject_gap_size")
        _non_negative_integer(self.max_total_injections, "max_total_injections")
        if self.prelex is not None and not isinstance(self.prelex, str):
            raise TypeError("prelex must be a string or None")
        if self.strip_chars is not None and not isinstance(self.strip_chars, str):
            raise TypeError("strip_chars must be a string or None")
        if not isinstance(self.trace, bool):
            raise TypeError("trace must be a boolean")
        object.__setattr__(self, "words_full", words)
        object.__setattr__(self, "terminals", terminals)


def _load_pinned_epic_runtime() -> _EpicRuntime:
    regular_cover = import_module("constrained_diffusion.regular_cover")
    profiler = import_module("constrained_diffusion.fast_enfa_profiler")
    return _EpicRuntime(
        candidate_factory=cast(_CandidateFactory, regular_cover.BatchCandidate),
        select_batch=cast(_BatchSelector, regular_cover.select_batch_with_regular_cover),
        minimum_batch_size=cast(Callable[[], int], regular_cover.regular_cover_min_batch),
        exact_shrink_enabled=cast(
            Callable[[], bool],
            regular_cover.regular_cover_exact_enabled,
        ),
        profiler_enabled=cast(Callable[[], bool], profiler.enabled),
        profiler_snapshot=cast(Callable[[], Mapping[str, object]], profiler.snapshot),
    )


def _profile_count(
    snapshot: Mapping[str, object],
    *,
    group_name: str,
    metric_name: str,
) -> int:
    group = snapshot.get(group_name)
    if not isinstance(group, Mapping):
        return 0
    metric = group.get(metric_name)
    if group_name == "timers":
        if not isinstance(metric, Mapping):
            return 0
        metric = metric.get("count")
    if isinstance(metric, bool) or not isinstance(metric, int):
        return 0
    return metric


def _profile_delta(
    before: Mapping[str, object] | None,
    after: Mapping[str, object] | None,
    *,
    group_name: str,
    metric_name: str,
) -> int | None:
    if before is None or after is None:
        return None
    delta = _profile_count(
        after,
        group_name=group_name,
        metric_name=metric_name,
    ) - _profile_count(
        before,
        group_name=group_name,
        metric_name=metric_name,
    )
    return delta if delta >= 0 else None


def _base_diagnostics(
    selection_input: SelectionInput,
    *,
    minimum_batch_size: int | None,
    exact_shrink_enabled: bool | None,
) -> dict[str, object]:
    return {
        "implementation": "pinned_upstream_epic_regular_cover",
        "upstream_commit": EPIC_UPSTREAM_COMMIT,
        "optimization_guarantee": "none_heuristic",
        "finite_slot_witness_available": False,
        "input_support_sha256": selection_input.support.fingerprint,
        "input_proposal_ids": [proposal.proposal_id for proposal in selection_input.proposals],
        "input_proposal_weights": [proposal.weight for proposal in selection_input.proposals],
        "candidate_ranking_score": "model_confidence",
        "comparison_score": "sum_of_selected_positive_mwpc_weights",
        "minimum_batch_size": minimum_batch_size,
        "exact_shrink_enabled": exact_shrink_enabled,
    }


def _non_success_result(
    selection_input: SelectionInput,
    *,
    status: SelectionStatus,
    started: float,
    diagnostics: Mapping[str, object],
) -> SelectionResult:
    if status in {
        SelectionStatus.OPTIMAL,
        SelectionStatus.FEASIBLE_ON_SUPPORT,
        SelectionStatus.HEURISTIC,
    }:
        raise ValueError("non-success conversion requires an inconclusive status")
    return SelectionResult(
        selector=SelectorKind.EPIC_REGULAR_COVER,
        status=status,
        exactness_scope=selection_input.support.exactness_scope,
        runtime_seconds=perf_counter() - started,
        diagnostics=diagnostics,
    )


def _validate_current_words(
    selection_input: SelectionInput,
    context: EpicSelectionContext,
) -> None:
    expected_length = context.prompt_length + len(selection_input.canvas)
    if len(context.words_full) != expected_length:
        raise ValueError("words_full must contain the prompt followed by the complete canvas")
    for position, token_id in enumerate(selection_input.canvas):
        word = context.words_full[context.prompt_length + position]
        if (token_id is None) != (word is None):
            raise ValueError(
                f"current words and canvas disagree about masked/fixed state at position {position}"
            )


def _recompute_selected_score(
    selection_input: SelectionInput,
    selected_ids: frozenset[int],
) -> tuple[tuple[int, ...], float]:
    selected = tuple(
        proposal
        for proposal in selection_input.proposals
        if proposal.proposal_id in selected_ids and proposal.weight > 0.0
    )
    try:
        score = fsum(proposal.weight for proposal in selected)
    except OverflowError as error:
        raise ValueError("selected EPIC proposal score must be finite") from error
    if not isfinite(score):
        raise ValueError("selected EPIC proposal score must be finite")
    return tuple(proposal.proposal_id for proposal in selected), score


def select_epic_regular_cover(
    selection_input: SelectionInput,
    context: EpicSelectionContext,
) -> SelectionResult:
    """Run the pinned EPIC heuristic on one common frozen proposal set."""

    if not isinstance(selection_input, SelectionInput):
        raise TypeError("selection_input must be a SelectionInput")
    if not isinstance(context, EpicSelectionContext):
        raise TypeError("context must be an EpicSelectionContext")
    _validate_current_words(selection_input, context)
    started = perf_counter()

    try:
        runtime = _load_pinned_epic_runtime()
    except (ImportError, ModuleNotFoundError) as error:
        return _non_success_result(
            selection_input,
            status=SelectionStatus.UNSUPPORTED,
            started=started,
            diagnostics={
                **_base_diagnostics(
                    selection_input,
                    minimum_batch_size=None,
                    exact_shrink_enabled=None,
                ),
                "error_stage": "upstream_import",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

    try:
        minimum_batch_size = runtime.minimum_batch_size()
        exact_shrink_enabled = runtime.exact_shrink_enabled()
        profiler_enabled = runtime.profiler_enabled()
        if (
            isinstance(minimum_batch_size, bool)
            or not isinstance(minimum_batch_size, int)
            or minimum_batch_size <= 0
        ):
            raise ValueError("EPIC minimum batch size must be a positive integer")
        if not isinstance(exact_shrink_enabled, bool):
            raise TypeError("EPIC exact-shrink setting must be a boolean")
        if not isinstance(profiler_enabled, bool):
            raise TypeError("EPIC profiler enabled flag must be a boolean")
    except Exception as error:
        return _non_success_result(
            selection_input,
            status=SelectionStatus.ERROR,
            started=started,
            diagnostics={
                **_base_diagnostics(
                    selection_input,
                    minimum_batch_size=None,
                    exact_shrink_enabled=None,
                ),
                "error_stage": "upstream_configuration",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

    base_diagnostics = _base_diagnostics(
        selection_input,
        minimum_batch_size=minimum_batch_size,
        exact_shrink_enabled=exact_shrink_enabled,
    )
    positions = tuple(proposal.position for proposal in selection_input.proposals)
    if len(set(positions)) != len(positions):
        return _non_success_result(
            selection_input,
            status=SelectionStatus.UNSUPPORTED,
            started=started,
            diagnostics={
                **base_diagnostics,
                "unsupported_reason": "EPIC schedule candidates require unique positions",
            },
        )
    if any(selection_input.canvas[position] is not None for position in positions):
        return _non_success_result(
            selection_input,
            status=SelectionStatus.UNSUPPORTED,
            started=started,
            diagnostics={
                **base_diagnostics,
                "unsupported_reason": "EPIC candidates must target masked positions",
            },
        )
    if any(proposal.model_confidence is None for proposal in selection_input.proposals):
        return _non_success_result(
            selection_input,
            status=SelectionStatus.UNSUPPORTED,
            started=started,
            diagnostics={
                **base_diagnostics,
                "unsupported_reason": "EPIC candidate ranking requires model_confidence",
            },
        )

    special_ids = set(selection_input.eos_policy.termination_token_ids)
    if selection_input.eos_policy.pad_token_id is not None:
        special_ids.add(selection_input.eos_policy.pad_token_id)
    excluded_special_ids: list[int] = []
    excluded_unrepresented_ids: list[int] = []
    candidate_pairs: list[tuple[_EpicCandidate, Proposal]] = []
    try:
        for proposal in selection_input.proposals:
            if proposal.token_id in special_ids:
                excluded_special_ids.append(proposal.proposal_id)
                continue
            if proposal.token_id not in selection_input.support.rows[proposal.position]:
                excluded_unrepresented_ids.append(proposal.proposal_id)
                continue
            confidence = proposal.model_confidence
            if confidence is None:
                raise AssertionError("EPIC confidence validation lost a proposal")
            word = context.decode_token(proposal.token_id)
            if word is None:
                raise ValueError(f"decode_token returned None for proposal {proposal.proposal_id}")
            candidate = runtime.candidate_factory(
                context.prompt_length + proposal.position,
                proposal.token_id,
                word,
                confidence,
            )
            candidate_pairs.append((candidate, proposal))
    except Exception as error:
        return _non_success_result(
            selection_input,
            status=SelectionStatus.ERROR,
            started=started,
            diagnostics={
                **base_diagnostics,
                "error_stage": "candidate_conversion",
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

    candidate_ids = [proposal.proposal_id for _, proposal in candidate_pairs]
    if len(candidate_pairs) < minimum_batch_size:
        return SelectionResult(
            selector=SelectorKind.EPIC_REGULAR_COVER,
            status=SelectionStatus.HEURISTIC,
            exactness_scope=selection_input.support.exactness_scope,
            runtime_seconds=perf_counter() - started,
            score=0.0,
            diagnostics={
                **base_diagnostics,
                "eligible_candidate_proposal_ids": candidate_ids,
                "excluded_special_proposal_ids": excluded_special_ids,
                "excluded_unrepresented_proposal_ids": excluded_unrepresented_ids,
                "regular_cover_selector_calls": 0,
                "regular_cover_check_calls": 0,
                "exact_shrink_check_calls": 0,
                "upstream_selected_proposal_ids": [],
                "minimum_batch_filter_applied": True,
                "serial_fallback_required": True,
                "score_recomputed_from_proposal_weights": True,
            },
        )

    candidate_by_identity = {id(candidate): proposal for candidate, proposal in candidate_pairs}
    before = runtime.profiler_snapshot() if profiler_enabled else None
    try:
        raw_selected = tuple(
            runtime.select_batch(
                words_full=context.words_full,
                candidates=[candidate for candidate, _ in candidate_pairs],
                prompt_len=context.prompt_length,
                cfg=context.cfg,
                lex_map=context.lex_map,
                terminals=list(context.terminals),
                prelex=context.prelex,
                single_token_lexing=context.single_token_lexing,
                inject_gap_size=context.inject_gap_size,
                max_total_injections=context.max_total_injections,
                subtokens={} if context.subtokens is None else context.subtokens,
                supertokens={} if context.supertokens is None else context.supertokens,
                strip_chars=context.strip_chars,
                trace=context.trace,
            )
        )
    except Exception as error:
        after = runtime.profiler_snapshot() if profiler_enabled else None
        return _non_success_result(
            selection_input,
            status=SelectionStatus.ERROR,
            started=started,
            diagnostics={
                **base_diagnostics,
                "error_stage": "upstream_selector",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "regular_cover_selector_calls": 1,
                "regular_cover_check_calls": _profile_delta(
                    before,
                    after,
                    group_name="timers",
                    metric_name="regular_cover.generated_language",
                ),
                "exact_shrink_check_calls": _profile_delta(
                    before,
                    after,
                    group_name="counts",
                    metric_name="regular_cover.exact.calls",
                ),
            },
        )
    after = runtime.profiler_snapshot() if profiler_enabled else None

    raw_identities = tuple(id(candidate) for candidate in raw_selected)
    if len(set(raw_identities)) != len(raw_identities) or any(
        identity not in candidate_by_identity for identity in raw_identities
    ):
        return _non_success_result(
            selection_input,
            status=SelectionStatus.ERROR,
            started=started,
            diagnostics={
                **base_diagnostics,
                "error_stage": "upstream_result_validation",
                "error_message": ("EPIC returned an unknown or duplicate candidate object"),
            },
        )

    upstream_selected = tuple(
        candidate_by_identity[identity].proposal_id for identity in raw_identities
    )
    minimum_batch_filter_applied = len(raw_selected) < minimum_batch_size
    effective_ids = (
        frozenset[int]() if minimum_batch_filter_applied else frozenset(upstream_selected)
    )
    selected_ids, score = _recompute_selected_score(selection_input, effective_ids)
    return SelectionResult(
        selector=SelectorKind.EPIC_REGULAR_COVER,
        status=SelectionStatus.HEURISTIC,
        exactness_scope=selection_input.support.exactness_scope,
        runtime_seconds=perf_counter() - started,
        selected_proposal_ids=selected_ids,
        score=score,
        diagnostics={
            **base_diagnostics,
            "eligible_candidate_proposal_ids": candidate_ids,
            "excluded_special_proposal_ids": excluded_special_ids,
            "excluded_unrepresented_proposal_ids": excluded_unrepresented_ids,
            "regular_cover_profiler_enabled": profiler_enabled,
            "regular_cover_selector_calls": 1,
            "regular_cover_check_calls": _profile_delta(
                before,
                after,
                group_name="timers",
                metric_name="regular_cover.generated_language",
            ),
            "regular_cover_intersection_calls": _profile_delta(
                before,
                after,
                group_name="timers",
                metric_name="regular_cover.intersection",
            ),
            "exact_shrink_check_calls": _profile_delta(
                before,
                after,
                group_name="counts",
                metric_name="regular_cover.exact.calls",
            ),
            "upstream_selected_proposal_ids": list(upstream_selected),
            "minimum_batch_filter_applied": minimum_batch_filter_applied,
            "serial_fallback_required": not effective_ids,
            "score_recomputed_from_proposal_weights": True,
        },
    )


# Compatibility alias retained for version-1 callers and artifacts.
select_epic = select_epic_regular_cover


__all__ = [
    "EPIC_UPSTREAM_COMMIT",
    "EpicSelectionContext",
    "select_epic",
    "select_epic_regular_cover",
]
