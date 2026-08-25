"""Parent-side exact-step hook for the pinned EPIC LLaDA decoder.

The vendor loop remains read-only.  Its single-batch tensor rows are passed to
this boundary immediately after primary tokens/confidences and the baseline
``k_s`` budget have been computed.  Tensor snapshots are converted to finite
CPU-side tuples before model-independent exact orchestration begins.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import exp, inf, isfinite, isnan
from types import MappingProxyType
from typing import Protocol

from mwpc_exact.adaptive import solve_exact_commit_adaptive_validated
from mwpc_exact.decoder import apply_exact_commit_result
from mwpc_exact.decoder_types import (
    DecoderStepResult,
    FailureFallbackHandler,
)
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.profiling import ComponentProfiler
from mwpc_exact.proposal_policy import (
    ProposalWeightMode,
    ScheduleProposalBatch,
    build_schedule_proposals,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.strategy import ExactStrategyConfig
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import ExactCommitResult, SolveStatus
from mwpc_exact.validated import ValidatedExactCommit

LLADA_MODEL_ID = "GSAI-ML/LLaDA-8B-Instruct"
LLADA_TOKENIZER_REVISION = "08b83a6feb34df1a6011b80c3c00c7563e963b07"
LLADA_MASK_TOKEN_ID = 126336
LLADA_EOS_TOKEN_ID = 126081
LLADA_EOT_TOKEN_ID = 126348


class MutableTokenRow(Protocol):
    """Minimum mutation surface implemented by a one-dimensional torch row."""

    def __setitem__(self, position: int, token_id: int, /) -> None: ...


class DecodedTracking(Protocol):
    """Minimum surface of EPIC's per-position ``generated_words`` list."""

    def __len__(self) -> int: ...

    def __setitem__(self, position: int, value: object, /) -> None: ...


@dataclass(frozen=True, slots=True)
class LLaDAAdapterProfile:
    """Immutable model/tokenizer special-token profile for one adapter."""

    model_id: str
    tokenizer_revision: str
    mask_token_id: int
    eos_policy: EOSPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id:
            raise ValueError("model_id must be a non-empty string")
        if not isinstance(self.tokenizer_revision, str) or not self.tokenizer_revision:
            raise ValueError("tokenizer_revision must be a non-empty string")
        if isinstance(self.mask_token_id, bool) or not isinstance(self.mask_token_id, int):
            raise TypeError("mask_token_id must be an integer")
        if self.mask_token_id < 0:
            raise ValueError("mask_token_id must be non-negative")
        if not isinstance(self.eos_policy, EOSPolicy):
            raise TypeError("eos_policy must be an EOSPolicy")
        if self.mask_token_id in self.eos_policy.termination_token_ids:
            raise ValueError("the diffusion mask cannot also be a termination token")
        if self.mask_token_id == self.eos_policy.pad_token_id:
            raise ValueError("the diffusion mask cannot also be PAD")

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "tokenizer_revision": self.tokenizer_revision,
            "mask_token_id": self.mask_token_id,
            "eos_policy": self.eos_policy.to_dict(),
        }


PINNED_LLADA_PROFILE = LLaDAAdapterProfile(
    model_id=LLADA_MODEL_ID,
    tokenizer_revision=LLADA_TOKENIZER_REVISION,
    mask_token_id=LLADA_MASK_TOKEN_ID,
    eos_policy=EOSPolicy(
        EOSMode.REQUIRED,
        termination_token_ids=(LLADA_EOS_TOKEN_ID, LLADA_EOT_TOKEN_ID),
        pad_token_id=LLADA_EOS_TOKEN_ID,
    ),
)


@dataclass(frozen=True, slots=True)
class LLaDAExactStepRequest:
    """Frozen generated-region input supplied to one validated exact solve."""

    canvas: tuple[int | None, ...]
    logits: tuple[tuple[float, ...], ...]
    proposal_batch: ScheduleProposalBatch
    schedule_mask: tuple[bool, ...]
    prompt_token_ids: tuple[int, ...]
    prompt_length: int
    generation_length: int
    active_block_end: int
    profile: LLaDAAdapterProfile
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.profile, LLaDAAdapterProfile):
            raise TypeError("profile must be an LLaDAAdapterProfile")
        if len(self.canvas) != self.generation_length:
            raise ValueError("canvas length must equal generation_length")
        if len(self.logits) != self.generation_length:
            raise ValueError("logits length must equal generation_length")
        if len(self.schedule_mask) != self.generation_length:
            raise ValueError("schedule_mask length must equal generation_length")
        if len(self.prompt_token_ids) != self.prompt_length:
            raise ValueError("prompt token count must equal prompt_length")
        if (
            not self.prompt_length
            <= self.active_block_end
            <= (self.prompt_length + self.generation_length)
        ):
            raise ValueError("active_block_end must lie inside the generated region")
        expected_eligible = tuple(
            position
            for position, (token_id, included) in enumerate(
                zip(self.canvas, self.schedule_mask, strict=True)
            )
            if included and token_id is None
        )
        if expected_eligible != self.proposal_batch.eligible_positions:
            raise ValueError("proposal eligibility must match the frozen schedule mask")
        if any(
            included and token_id is not None
            for token_id, included in zip(self.canvas, self.schedule_mask, strict=True)
        ):
            raise ValueError("the schedule mask cannot include fixed generated positions")
        frozen = MappingProxyType(dict(self.diagnostics))
        object.__setattr__(self, "diagnostics", frozen)

    def to_dict(self) -> dict[str, object]:
        return {
            "canvas": list(self.canvas),
            "proposal_batch": self.proposal_batch.to_dict(),
            "schedule_mask": list(self.schedule_mask),
            "prompt_token_ids": list(self.prompt_token_ids),
            "prompt_length": self.prompt_length,
            "generation_length": self.generation_length,
            "active_block_end": self.active_block_end,
            "profile": self.profile.to_dict(),
            "diagnostics": dict(self.diagnostics),
        }


class LLaDAUpdateReason(StrEnum):
    """Why one physical model-tensor slot changed during the hook."""

    DECODER_COMMIT = "decoder_commit"
    EOS_PAD_CANONICALIZATION = "eos_pad_canonicalization"


@dataclass(frozen=True, slots=True)
class LLaDATokenUpdate:
    """One generated-canvas update mapped back to the full model row."""

    canvas_position: int
    model_position: int
    token_id: int
    reason: LLaDAUpdateReason

    def to_dict(self) -> dict[str, object]:
        return {
            "canvas_position": self.canvas_position,
            "model_position": self.model_position,
            "token_id": self.token_id,
            "reason": self.reason.value,
        }


@dataclass(frozen=True, slots=True)
class LLaDAExactStepResult:
    """Exact scientific result plus every physical LLaDA state mutation."""

    request: LLaDAExactStepRequest
    decoder_step: DecoderStepResult
    updated_canvas: tuple[int | None, ...]
    model_updates: tuple[LLaDATokenUpdate, ...]
    complete: bool

    def __post_init__(self) -> None:
        if self.decoder_step.input_canvas != self.request.canvas:
            raise ValueError("decoder input must equal the adapter's frozen canvas")
        if len(self.updated_canvas) != self.request.generation_length:
            raise ValueError("updated canvas length must remain finite and unchanged")
        positions = tuple(update.canvas_position for update in self.model_updates)
        if len(set(positions)) != len(positions):
            raise ValueError("model updates must not repeat a generated position")
        for update in self.model_updates:
            if update.model_position != self.request.prompt_length + update.canvas_position:
                raise ValueError("model update offset does not match prompt_length")
            if self.updated_canvas[update.canvas_position] != update.token_id:
                raise ValueError("model update token disagrees with updated_canvas")

    @property
    def solver_result(self) -> ExactCommitResult:
        return self.decoder_step.solver_result

    def to_dict(self) -> dict[str, object]:
        return {
            "request": self.request.to_dict(),
            "decoder_step": self.decoder_step.to_dict(),
            "updated_canvas": list(self.updated_canvas),
            "model_updates": [update.to_dict() for update in self.model_updates],
            "complete": self.complete,
        }


def _snapshot(value: object) -> object:
    """Return ordinary CPU data from a tensor-like value without importing torch."""

    current = value
    for method_name in ("detach", "cpu"):
        method = getattr(current, method_name, None)
        if method is not None:
            if not callable(method):
                raise TypeError(f"{method_name} must be callable on tensor-like inputs")
            current = method()
    tolist = getattr(current, "tolist", None)
    if tolist is not None:
        if not callable(tolist):
            raise TypeError("tolist must be callable on tensor-like inputs")
        current = tolist()
    return current


def _sequence(value: object, field_name: str) -> Sequence[object]:
    snapshot = _snapshot(value)
    if isinstance(snapshot, (str, bytes)) or not isinstance(snapshot, Sequence):
        raise TypeError(f"{field_name} must be a finite sequence or tensor row")
    return snapshot


def _integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _token_vector(value: object, field_name: str) -> tuple[int, ...]:
    return tuple(
        _integer(item, f"{field_name} item at position {position}")
        for position, item in enumerate(_sequence(value, field_name))
    )


def _score_vector(value: object, field_name: str) -> tuple[float, ...]:
    scores: list[float] = []
    for position, item in enumerate(_sequence(value, field_name)):
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError(f"{field_name} item at position {position} must be real")
        score = float(item)
        if isnan(score):
            raise ValueError(f"{field_name} item at position {position} must not be NaN")
        scores.append(score)
    return tuple(scores)


def _logit_matrix(value: object) -> tuple[tuple[float, ...], ...]:
    rows = _sequence(value, "logits")
    matrix = tuple(
        _score_vector(row, f"logits row {position}") for position, row in enumerate(rows)
    )
    if not matrix or not matrix[0]:
        raise ValueError("logits must contain at least one position and vocabulary score")
    vocabulary_size = len(matrix[0])
    if any(len(row) != vocabulary_size for row in matrix):
        raise ValueError("all logit rows must have the same vocabulary size")
    return matrix


def prepare_llada_exact_step(
    *,
    token_ids: object,
    logits: object,
    predicted_token_ids: object,
    confidence_values: object,
    prompt_length: int,
    generation_length: int,
    active_block_end: int,
    k_s: int,
    weight_mode: ProposalWeightMode,
    profile: LLaDAAdapterProfile = PINNED_LLADA_PROFILE,
) -> LLaDAExactStepRequest:
    """Freeze one EPIC LLaDA step using its existing schedule budget.

    Inputs are single-batch rows (``x[0]``, ``logits[0]``, ``x0[0]``, and
    ``confidence[0]``).  Exact canvas positions are generation-relative;
    ``model_position = prompt_length + canvas_position`` is retained explicitly.
    """

    if not isinstance(profile, LLaDAAdapterProfile):
        raise TypeError("profile must be an LLaDAAdapterProfile")
    prompt_count = _integer(prompt_length, "prompt_length")
    generated_count = _integer(generation_length, "generation_length")
    if generated_count == 0:
        raise ValueError("generation_length must be positive")
    block_end = _integer(active_block_end, "active_block_end")
    schedule_budget = _integer(k_s, "k_s")
    if schedule_budget == 0:
        raise ValueError("the LLaDA exact hook requires a positive baseline k_s budget")
    model_tokens = _token_vector(token_ids, "token_ids")
    model_logits = _logit_matrix(logits)
    model_predictions = _token_vector(predicted_token_ids, "predicted_token_ids")
    model_confidences = _score_vector(confidence_values, "confidence_values")
    expected_length = prompt_count + generated_count
    if not (
        len(model_tokens)
        == len(model_logits)
        == len(model_predictions)
        == len(model_confidences)
        == expected_length
    ):
        raise ValueError(
            "single-batch token, logit, prediction, and confidence rows must equal "
            "prompt_length + generation_length"
        )
    if not prompt_count <= block_end <= expected_length:
        raise ValueError("active_block_end must lie inside the generated region")
    vocabulary_size = len(model_logits[0])
    if profile.mask_token_id >= vocabulary_size:
        raise ValueError("mask_token_id is outside the model vocabulary")
    if any(token_id >= vocabulary_size for token_id in model_tokens):
        raise ValueError("token_ids contains a token outside the model vocabulary")
    if any(token_id >= vocabulary_size for token_id in model_predictions):
        raise ValueError("predicted_token_ids contains a token outside the model vocabulary")

    generation_slice = slice(prompt_count, expected_length)
    generated_tokens = model_tokens[generation_slice]
    canvas = tuple(
        None if token_id == profile.mask_token_id else token_id for token_id in generated_tokens
    )
    schedule_mask = tuple(
        token_id is None and prompt_count + position < block_end
        for position, token_id in enumerate(canvas)
    )
    if not any(schedule_mask):
        raise ValueError("the LLaDA exact hook requires a masked position in the active block")
    proposal_batch = build_schedule_proposals(
        predicted_token_ids=model_predictions[generation_slice],
        confidence_values=model_confidences[generation_slice],
        schedule_mask=schedule_mask,
        k_s=schedule_budget,
        weight_mode=weight_mode,
    )
    generation_logits = model_logits[generation_slice]
    return LLaDAExactStepRequest(
        canvas=canvas,
        logits=generation_logits,
        proposal_batch=proposal_batch,
        schedule_mask=schedule_mask,
        prompt_token_ids=model_tokens[:prompt_count],
        prompt_length=prompt_count,
        generation_length=generated_count,
        active_block_end=block_end,
        profile=profile,
        diagnostics={
            "adapter": "pinned_epic_llada_exact_step_v1",
            "tensor_batch_size": 1,
            "canvas_position_mapping": "model_position_minus_prompt_length",
            "active_block_limit_applied_to_proposals": True,
            "support_covers_full_generated_canvas": True,
            "logit_shape": [generated_count, vocabulary_size],
            "exactness_scope": "exact_on_support",
        },
    )


def _permitted_token_ids(
    adapter: CompositionalByteLevelAdapter,
    eos_policy: EOSPolicy,
) -> tuple[int, ...]:
    permitted = {
        token_id for token_id, emission in enumerate(adapter.emissions) if emission is not None
    }
    permitted.update(eos_policy.termination_token_ids)
    if eos_policy.pad_token_id is not None:
        permitted.add(eos_policy.pad_token_id)
    if any(token_id >= adapter.vocabulary_size for token_id in permitted):
        raise ValueError("EOS/PAD token is outside the tokenizer adapter vocabulary")
    return tuple(sorted(permitted))


def _witness_probabilities(
    logits: tuple[tuple[float, ...], ...],
    witness_token_ids: tuple[int, ...],
) -> tuple[float, ...]:
    probabilities: list[float] = []
    for position, (row, witness_token_id) in enumerate(zip(logits, witness_token_ids, strict=True)):
        maximum = max(row)
        if maximum == inf:
            positive_infinity_count = sum(score == inf for score in row)
            probabilities.append(
                1.0 / positive_infinity_count if row[witness_token_id] == inf else 0.0
            )
            continue
        if maximum == -inf:
            raise ValueError(f"all logits are -infinity at generated position {position}")
        denominator = sum(exp(score - maximum) for score in row if score != -inf)
        probability = (
            0.0
            if row[witness_token_id] == -inf
            else exp(row[witness_token_id] - maximum) / denominator
        )
        if not isfinite(probability):
            raise ValueError("witness probability must be finite")
        probabilities.append(probability)
    return tuple(probabilities)


def _termination_position(
    canvas: Sequence[int | None],
    eos_policy: EOSPolicy,
) -> int | None:
    termination_ids = frozenset(eos_policy.termination_token_ids)
    return next(
        (position for position, token_id in enumerate(canvas) if token_id in termination_ids),
        None,
    )


def _complete_model_updates(
    request: LLaDAExactStepRequest,
    decoder_step: DecoderStepResult,
    eos_policy: EOSPolicy,
) -> tuple[tuple[int | None, ...], tuple[LLaDATokenUpdate, ...], int | None]:
    eligible = frozenset(request.proposal_batch.eligible_positions)
    for commit in decoder_step.commits:
        if commit.position not in eligible:
            raise ValueError("decoder commit escaped the current LLaDA active block")

    updated = list(decoder_step.updated_canvas)
    updates = [
        LLaDATokenUpdate(
            canvas_position=commit.position,
            model_position=request.prompt_length + commit.position,
            token_id=commit.token_id,
            reason=LLaDAUpdateReason.DECODER_COMMIT,
        )
        for commit in decoder_step.commits
    ]
    eos_position = _termination_position(updated, eos_policy)
    if eos_position is None:
        return tuple(updated), tuple(updates), None
    pad_token_id = eos_policy.pad_token_id
    if pad_token_id is None:
        raise AssertionError("a configured termination path omitted its PAD token")
    already_updated = {update.canvas_position for update in updates}
    for position in range(eos_position + 1, len(updated)):
        token_id = updated[position]
        if token_id is not None and token_id != pad_token_id:
            raise ValueError("a fixed token after EOS is not the canonical LLaDA PAD")
        if token_id is None:
            updated[position] = pad_token_id
            if position not in already_updated:
                updates.append(
                    LLaDATokenUpdate(
                        canvas_position=position,
                        model_position=request.prompt_length + position,
                        token_id=pad_token_id,
                        reason=LLaDAUpdateReason.EOS_PAD_CANONICALIZATION,
                    )
                )
    updates.sort(key=lambda update: update.canvas_position)
    return tuple(updated), tuple(updates), eos_position


def run_llada_exact_step(
    grammar: CnfGrammar,
    *,
    token_ids: MutableTokenRow,
    logits: object,
    predicted_token_ids: object,
    confidence_values: object,
    decoded_tracking: DecodedTracking,
    decode_token: Callable[[int], object],
    eos_marker: object,
    prompt_length: int,
    generation_length: int,
    active_block_end: int,
    k_s: int,
    tokenizer_adapter: CompositionalByteLevelAdapter,
    config: ExactStrategyConfig,
    profile: LLaDAAdapterProfile = PINNED_LLADA_PROFILE,
    failure_fallback: FailureFallbackHandler | None = None,
    profiler: ComponentProfiler | None = None,
) -> LLaDAExactStepResult:
    """Run and apply one independently validated exact LLaDA commitment step."""

    if not isinstance(config, ExactStrategyConfig):
        raise TypeError("config must be an ExactStrategyConfig")
    if config.eos_policy != profile.eos_policy:
        raise ValueError("exact EOS/PAD configuration must match the LLaDA adapter profile")
    if (config.failure_fallback_strategy is None) != (failure_fallback is None):
        raise ValueError("configured failure fallback requires its matching adapter callback")
    if not callable(decode_token):
        raise TypeError("decode_token must be callable")
    request = prepare_llada_exact_step(
        token_ids=token_ids,
        logits=logits,
        predicted_token_ids=predicted_token_ids,
        confidence_values=confidence_values,
        prompt_length=prompt_length,
        generation_length=generation_length,
        active_block_end=active_block_end,
        k_s=k_s,
        weight_mode=config.weight_mode,
        profile=profile,
    )
    expected_model_length = prompt_length + generation_length
    if len(decoded_tracking) != expected_model_length:
        raise ValueError("decoded_tracking must cover the full prompt and generated row")
    if tokenizer_adapter.vocabulary_size != len(request.logits[0]):
        raise ValueError("tokenizer adapter and model logits must have equal vocabularies")

    solver_output = solve_exact_commit_adaptive_validated(
        grammar,
        canvas=request.canvas,
        logits=request.logits,
        proposals=request.proposal_batch.proposals,
        tokenizer_adapter=tokenizer_adapter,
        eos_policy=config.eos_policy,
        config=config.adaptive_support,
        backend=config.backend,
        permitted_token_ids=_permitted_token_ids(tokenizer_adapter, config.eos_policy),
        include_proposal_tokens=True,
        pruning_description=("pinned EPIC LLaDA generated-canvas top-K support; exact_on_support"),
        profiler=profiler,
    )
    solver_result = (
        solver_output.result if isinstance(solver_output, ValidatedExactCommit) else solver_output
    )
    witness_probabilities = (
        _witness_probabilities(request.logits, solver_result.witness_token_ids)
        if solver_result.status is SolveStatus.OPTIMAL and not solver_result.selected_proposal_ids
        else None
    )
    decoder_step = apply_exact_commit_result(
        solver_output,
        canvas=request.canvas,
        proposals=request.proposal_batch.proposals,
        witness_token_probabilities=witness_probabilities,
        witness_progress_positions=request.proposal_batch.eligible_positions,
        failure_fallback_strategy=config.failure_fallback_strategy,
        failure_fallback=failure_fallback,
        profiler=profiler,
    )
    updated_canvas, model_updates, eos_position = _complete_model_updates(
        request,
        decoder_step,
        config.eos_policy,
    )

    tracking_values: list[object] = []
    for update in model_updates:
        if eos_position is not None and update.canvas_position >= eos_position:
            tracking_values.append(eos_marker)
            continue
        decoded_value = decode_token(update.token_id)
        if decoded_value is None:
            raise ValueError("decode_token must not map an ordinary committed token to None")
        tracking_values.append(decoded_value)

    for update, tracking_value in zip(model_updates, tracking_values, strict=True):
        token_ids[update.model_position] = update.token_id
        decoded_tracking[update.model_position] = tracking_value

    applied_tokens = _token_vector(token_ids, "token_ids after commit")
    if applied_tokens[:prompt_length] != request.prompt_token_ids:
        raise RuntimeError("the LLaDA exact hook changed a prompt position")
    if applied_tokens[prompt_length:] != tuple(
        profile.mask_token_id if token_id is None else token_id for token_id in updated_canvas
    ):
        raise RuntimeError("model tensor updates disagree with the recorded generated canvas")
    complete = eos_position is not None and all(
        token_id is not None for token_id in updated_canvas[:eos_position]
    )
    return LLaDAExactStepResult(
        request=request,
        decoder_step=decoder_step,
        updated_canvas=updated_canvas,
        model_updates=model_updates,
        complete=complete,
    )


__all__ = [
    "LLADA_EOS_TOKEN_ID",
    "LLADA_EOT_TOKEN_ID",
    "LLADA_MASK_TOKEN_ID",
    "LLADA_MODEL_ID",
    "LLADA_TOKENIZER_REVISION",
    "PINNED_LLADA_PROFILE",
    "DecodedTracking",
    "LLaDAAdapterProfile",
    "LLaDAExactStepRequest",
    "LLaDAExactStepResult",
    "LLaDATokenUpdate",
    "LLaDAUpdateReason",
    "MutableTokenRow",
    "prepare_llada_exact_step",
    "run_llada_exact_step",
]
