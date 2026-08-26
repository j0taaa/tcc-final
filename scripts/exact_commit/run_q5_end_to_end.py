#!/usr/bin/env python3
"""Run the paired Q5 unconstrained/serial/EPIC/exact LLaDA smoke."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any

from mwpc_exact import (
    AdaptiveSupportConfig,
    ExactBackend,
    ExactStrategyConfig,
    ProposalWeightMode,
    SolveStatus,
)
from mwpc_exact.epic_adapter.llada import (
    PINNED_LLADA_PROFILE,
    build_llada_byte_adapter,
    run_llada_exact_step,
)
from mwpc_exact.experiments import (
    ExperimentConfig,
    ExperimentKind,
    load_experiment_config,
    save_resolved_config,
)
from mwpc_exact.profiling import ComponentProfiler
from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal, TerminalProduction
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_research.q5_end_to_end import (
    Q5_STRATEGIES,
    Q5ExecutionStatus,
    Q5ExperimentResult,
    Q5MethodRecord,
    upstream_selection_batch_size,
    write_q5_artifacts,
)
from mwpc_research.robust_timing import (
    QUARTILE_POLICY,
    cyclic_method_order,
    measure_call,
)

sys.dont_write_bytecode = True

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q5_end_to_end_v1.toml"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _command_output(command: Sequence[str], *, cwd: Path = REPOSITORY_ROOT) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256_bytes(
        json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()
    )


def _package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not_recorded_by_distribution"


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _integer(value: object, field_name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return value


def _real(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    return float(value)


def _string_sequence(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a sequence")
    result = tuple(_string(item, f"{field_name} item") for item in value)
    if not result:
        raise ValueError(f"{field_name} must not be empty")
    return result


def _integer_sequence(value: object, field_name: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a sequence")
    return tuple(_integer(item, f"{field_name} item") for item in value)


def _relative_path(value: object, field_name: str) -> str:
    raw = _string(value, field_name)
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field_name} must be repository-relative")
    return raw


@dataclass(frozen=True, slots=True)
class Q5Parameters:
    strategies: tuple[str, ...]
    task_ids: tuple[str, ...]
    prompt_id: str
    prompt_instruction: str
    target_utf8: str
    functional_checker: str
    generation_length: int
    block_length: int
    steps: int
    temperature: float
    cfg_scale: float
    remasking: str
    max_resamples: int
    weight_mode: ProposalWeightMode
    exact_backend: ExactBackend
    schedule_budget: int
    eos_mode: str
    termination_token_ids: tuple[int, ...]
    pad_token_id: int
    epic_regular_cover_min_batch: int
    epic_regular_cover_exact: bool
    quantization: str
    expected_model_vocabulary_size: int
    expected_tokenizer_base_vocabulary_size: int
    expected_tokenizer_total_vocabulary_size: int
    live_profile_source_sha256: str
    warmup_runs: int
    method_order: str
    raw_output_root: str
    rss_sample_interval_seconds: float | None
    quartile_policy: str | None


def _configuration_parameters(parameters: Mapping[str, object]) -> Q5Parameters:
    required = {
        "strategies",
        "task_ids",
        "prompt_id",
        "prompt_instruction",
        "target_utf8",
        "functional_checker",
        "generation_length",
        "block_length",
        "steps",
        "temperature",
        "cfg_scale",
        "remasking",
        "max_resamples",
        "weight_mode",
        "exact_backend",
        "schedule_budget",
        "eos_mode",
        "termination_token_ids",
        "pad_token_id",
        "epic_regular_cover_min_batch",
        "epic_regular_cover_exact",
        "quantization",
        "expected_model_vocabulary_size",
        "expected_tokenizer_base_vocabulary_size",
        "expected_tokenizer_total_vocabulary_size",
        "live_profile_source_sha256",
        "warmup_runs",
        "method_order",
        "raw_output_root",
    }
    timing_fields = {"rss_sample_interval_seconds", "quartile_policy"}
    if set(parameters) not in (required, required | timing_fields):
        raise ValueError(
            "Q5 parameters must contain the base fields and either both or neither timing field"
        )
    strategies = _string_sequence(parameters["strategies"], "parameters.strategies")
    if strategies != Q5_STRATEGIES:
        raise ValueError(f"Q5 strategies must be {Q5_STRATEGIES!r}")
    task_ids = _string_sequence(parameters["task_ids"], "parameters.task_ids")
    if task_ids != ("t904_literal_zero",):
        raise ValueError("Q5 v1 must use only the frozen T904 literal-zero task")
    exact_backend = ExactBackend(_string(parameters["exact_backend"], "exact_backend"))
    if exact_backend is not ExactBackend.RUST:
        raise ValueError("Q5 v1 must exercise the Rust production exact backend")
    epic_exact = parameters["epic_regular_cover_exact"]
    if epic_exact is not True:
        raise ValueError("Q5 EPIC regular-cover verification must remain exact")
    return Q5Parameters(
        strategies=strategies,
        task_ids=task_ids,
        prompt_id=_string(parameters["prompt_id"], "parameters.prompt_id"),
        prompt_instruction=_string(
            parameters["prompt_instruction"], "parameters.prompt_instruction"
        ),
        target_utf8=_string(parameters["target_utf8"], "parameters.target_utf8"),
        functional_checker=_string(
            parameters["functional_checker"], "parameters.functional_checker"
        ),
        generation_length=_integer(
            parameters["generation_length"], "parameters.generation_length", minimum=1
        ),
        block_length=_integer(parameters["block_length"], "parameters.block_length", minimum=1),
        steps=_integer(parameters["steps"], "parameters.steps", minimum=1),
        temperature=_real(parameters["temperature"], "parameters.temperature"),
        cfg_scale=_real(parameters["cfg_scale"], "parameters.cfg_scale"),
        remasking=_string(parameters["remasking"], "parameters.remasking"),
        max_resamples=_integer(parameters["max_resamples"], "parameters.max_resamples", minimum=1),
        weight_mode=ProposalWeightMode(
            _string(parameters["weight_mode"], "parameters.weight_mode")
        ),
        exact_backend=exact_backend,
        schedule_budget=_integer(
            parameters["schedule_budget"], "parameters.schedule_budget", minimum=1
        ),
        eos_mode=_string(parameters["eos_mode"], "parameters.eos_mode"),
        termination_token_ids=_integer_sequence(
            parameters["termination_token_ids"], "parameters.termination_token_ids"
        ),
        pad_token_id=_integer(parameters["pad_token_id"], "parameters.pad_token_id"),
        epic_regular_cover_min_batch=_integer(
            parameters["epic_regular_cover_min_batch"],
            "parameters.epic_regular_cover_min_batch",
            minimum=1,
        ),
        epic_regular_cover_exact=True,
        quantization=_string(parameters["quantization"], "parameters.quantization"),
        expected_model_vocabulary_size=_integer(
            parameters["expected_model_vocabulary_size"],
            "parameters.expected_model_vocabulary_size",
            minimum=1,
        ),
        expected_tokenizer_base_vocabulary_size=_integer(
            parameters["expected_tokenizer_base_vocabulary_size"],
            "parameters.expected_tokenizer_base_vocabulary_size",
            minimum=1,
        ),
        expected_tokenizer_total_vocabulary_size=_integer(
            parameters["expected_tokenizer_total_vocabulary_size"],
            "parameters.expected_tokenizer_total_vocabulary_size",
            minimum=1,
        ),
        live_profile_source_sha256=_string(
            parameters["live_profile_source_sha256"],
            "parameters.live_profile_source_sha256",
        ),
        warmup_runs=_integer(parameters["warmup_runs"], "parameters.warmup_runs"),
        method_order=_string(parameters["method_order"], "parameters.method_order"),
        raw_output_root=_relative_path(parameters["raw_output_root"], "parameters.raw_output_root"),
        rss_sample_interval_seconds=(
            None
            if "rss_sample_interval_seconds" not in parameters
            else _real(
                parameters["rss_sample_interval_seconds"],
                "parameters.rss_sample_interval_seconds",
            )
        ),
        quartile_policy=(
            None
            if "quartile_policy" not in parameters
            else _string(parameters["quartile_policy"], "parameters.quartile_policy")
        ),
    )


def _literal_grammar(target: bytes) -> CnfGrammar:
    _require(len(target) == 1, "Q5 v1 target must be exactly one byte")
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, target[0]),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )


def _check_generated_tokens(
    token_ids: Sequence[int],
    *,
    tokenizer_adapter: Any,
    grammar: CnfGrammar,
    target: bytes,
) -> tuple[dict[str, object], bool, bool]:
    termination_ids = frozenset(PINNED_LLADA_PROFILE.eos_policy.termination_token_ids)
    termination_position = next(
        (position for position, token_id in enumerate(token_ids) if token_id in termination_ids),
        None,
    )
    content_ids = tuple(
        token_ids if termination_position is None else token_ids[:termination_position]
    )
    suffix_ids = tuple(
        () if termination_position is None else token_ids[termination_position + 1 :]
    )
    content_bytes: bytes | None
    detokenization_error: str | None = None
    try:
        content_bytes = tokenizer_adapter.detokenize_bytes(content_ids)
    except (TypeError, ValueError) as error:
        content_bytes = None
        detokenization_error = f"{type(error).__name__}: {error}"
    grammar_valid = (
        False if content_bytes is None else recognizes_cnf(grammar, tuple(content_bytes))
    )
    termination_suffix_valid = termination_position is not None and all(
        token_id in termination_ids for token_id in suffix_ids
    )
    canonical_pad_suffix = termination_position is not None and all(
        token_id == PINNED_LLADA_PROFILE.eos_policy.pad_token_id for token_id in suffix_ids
    )
    syntactic_valid = bool(grammar_valid and termination_suffix_valid)
    functional_success = content_bytes == target
    checker = {
        "checker_id": "independent_cnf_plus_exact_target_v1",
        "termination_position": termination_position,
        "termination_token_id": (
            None if termination_position is None else token_ids[termination_position]
        ),
        "suffix_token_ids": list(suffix_ids),
        "termination_suffix_valid": termination_suffix_valid,
        "canonical_exact_pad_suffix": canonical_pad_suffix,
        "content_token_ids": list(content_ids),
        "content_bytes_hex": None if content_bytes is None else content_bytes.hex(),
        "content_utf8": (
            None if content_bytes is None else content_bytes.decode("utf-8", errors="replace")
        ),
        "independent_grammar_valid": grammar_valid,
        "target_bytes_hex": target.hex(),
        "exact_target_match": functional_success,
        "detokenization_error": detokenization_error,
    }
    return checker, syntactic_valid, functional_success


def _cached_checkpoint_metadata(source: Mapping[str, Any]) -> list[dict[str, object]]:
    from huggingface_hub import try_to_load_from_cache

    names = [str(value) for value in source["checkpoint_shard_names"]]
    expected_sizes = [int(value) for value in source["checkpoint_shard_sizes_bytes"]]
    _require(len(names) == len(expected_sizes), "checkpoint shard metadata length mismatch")
    shards: list[dict[str, object]] = []
    for name, expected_size in zip(names, expected_sizes, strict=True):
        cached = try_to_load_from_cache(
            str(source["model_id"]),
            name,
            revision=str(source["model_revision"]),
        )
        _require(isinstance(cached, str), f"pinned checkpoint shard is not cached: {name}")
        actual_size = Path(cached).stat().st_size
        _require(actual_size == expected_size, f"checkpoint shard size mismatch: {name}")
        shards.append({"name": name, "size_bytes": actual_size})
    return shards


def _restore_environment(name: str, old_value: str | None) -> None:
    if old_value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = old_value


@contextmanager
def _prepare_upstream_call(
    strategy: str,
    *,
    model: Any,
    tokenizer: Any,
    prompt: Any,
    grammar: Any,
    lex_map: Any,
    preprocessed: Any,
    parameters: Q5Parameters,
) -> Iterator[Callable[[], Mapping[str, object]]]:
    """Prepare upstream environment and observers outside the timed region."""

    from constrained_diffusion.eval.dllm.models.llada import generate_constrained

    constrain = strategy != "unconstrained"
    regular_cover = strategy == "epic"
    environment = {
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH": "1" if regular_cover else "0",
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH": str(
            parameters.epic_regular_cover_min_batch
        ),
        "CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT": (
            "1" if parameters.epic_regular_cover_exact else "0"
        ),
    }
    old_environment = {name: os.environ.get(name) for name in environment}
    os.environ.update(environment)

    selector_calls = 0
    regular_cover_batch_sizes: list[int] = []
    original_selector = generate_constrained.select_batch_with_regular_cover
    original_try_batch = generate_constrained._try_regular_cover_batch_commit_llada

    def observing_selector(*args: object, **kwargs: object) -> object:
        nonlocal selector_calls
        selector_calls += 1
        return original_selector(*args, **kwargs)

    def observing_try_batch(*args: object, **kwargs: object) -> object:
        selected = original_try_batch(*args, **kwargs)
        if selected:
            regular_cover_batch_sizes.append(len(selected))
        return selected

    generate_constrained.select_batch_with_regular_cover = observing_selector
    generate_constrained._try_regular_cover_batch_commit_llada = observing_try_batch
    event_count = 0
    commit_batch_sizes: list[int] = []
    physical_update_batch_sizes: list[int] = []
    observed_regular_batches = 0
    generation_length = parameters.generation_length
    previous = [PINNED_LLADA_PROFILE.mask_token_id] * generation_length

    def run() -> Mapping[str, object]:
        nonlocal event_count, observed_regular_batches, previous
        final_event: tuple[Any, list[Any], bool] | None = None
        for event in generate_constrained.generate(
            model,
            prompt,
            tokenizer,
            grammar,
            lex_map,
            prompt_len=int(prompt.shape[1]),
            steps=parameters.steps,
            gen_length=generation_length,
            block_length=parameters.block_length,
            temperature=parameters.temperature,
            cfg_scale=parameters.cfg_scale,
            remasking=parameters.remasking,
            mask_id=PINNED_LLADA_PROFILE.mask_token_id,
            trace=False,
            constrain=constrain,
            max_resamples=parameters.max_resamples,
            additional_stuff=preprocessed if constrain else (None, None, {}),
        ):
            event_count += 1
            final_event = event
            current = [int(value) for value in event[0][0, -generation_length:].tolist()]
            committed = sum(
                before == PINNED_LLADA_PROFILE.mask_token_id
                and after != PINNED_LLADA_PROFILE.mask_token_id
                for before, after in zip(previous, current, strict=True)
            )
            if committed:
                physical_update_batch_sizes.append(committed)
                new_regular_batches = regular_cover_batch_sizes[observed_regular_batches:]
                _require(
                    len(new_regular_batches) <= 1,
                    "multiple regular-cover selections occurred before one emitted event",
                )
                regular_selected = new_regular_batches[0] if new_regular_batches else 0
                commit_batch_sizes.append(
                    upstream_selection_batch_size(committed, regular_selected)
                )
                observed_regular_batches += len(new_regular_batches)
            previous = current
        _require(final_event is not None, f"{strategy} emitted no generation event")
        output, resamples, complete = final_event
        generated_ids = tuple(int(value) for value in output[0, -generation_length:].tolist())
        regular_commits = sum(regular_cover_batch_sizes)
        return {
            "complete": bool(complete),
            "generated_token_ids": generated_ids,
            "decoded_with_specials": tokenizer.decode(
                list(generated_ids),
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False,
            ),
            "commit_batch_sizes": tuple(commit_batch_sizes),
            "physical_update_batch_sizes": tuple(physical_update_batch_sizes),
            "fallback_count": (
                sum(commit_batch_sizes) - regular_commits if strategy == "epic" else 0
            ),
            "diagnostics": {
                "implementation": (
                    "upstream_llada_unconstrained_loop"
                    if strategy == "unconstrained"
                    else "upstream_llada_serial_constrained_loop"
                    if strategy == "serial"
                    else "upstream_llada_regular_cover_enabled_loop"
                ),
                "constraint_enabled": constrain,
                "regular_cover_batch_enabled": regular_cover,
                "regular_cover_selector_calls": selector_calls,
                "regular_cover_batch_sizes": regular_cover_batch_sizes,
                "regular_cover_commit_count": regular_commits,
                "serial_path_selection_count": sum(commit_batch_sizes) - regular_commits,
                "physical_update_count": sum(physical_update_batch_sizes),
                "event_count": event_count,
                "resample_count": len(resamples),
                "upstream_complete": bool(complete),
                "baseline_eos_suffix_semantics": "repeat_detected_termination_token",
            },
        }

    try:
        yield run
    finally:
        generate_constrained.select_batch_with_regular_cover = original_selector
        generate_constrained._try_regular_cover_batch_commit_llada = original_try_batch
        for name, old_value in old_environment.items():
            _restore_environment(name, old_value)


def _prepare_exact_call(
    *,
    torch: Any,
    model: Any,
    tokenizer: Any,
    prompt_ids: Sequence[int],
    tokenizer_adapter: Any,
    grammar: CnfGrammar,
    parameters: Q5Parameters,
    solver_timeout_seconds: float,
) -> Callable[[], Mapping[str, object]]:
    """Allocate exact per-call state outside the measured region."""

    generation_length = parameters.generation_length
    token_row = torch.tensor(
        [list(prompt_ids) + [PINNED_LLADA_PROFILE.mask_token_id] * generation_length],
        device="cuda:0",
        dtype=torch.long,
    )
    tracking: list[object] = [
        tokenizer.decode(
            [int(token_id)],
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
        for token_id in prompt_ids
    ] + [None] * generation_length
    strategy_config = ExactStrategyConfig(
        adaptive_support=AdaptiveSupportConfig(
            initial_k=1,
            k_max=4,
            total_timeout_seconds=solver_timeout_seconds,
        ),
        weight_mode=parameters.weight_mode,
        eos_policy=PINNED_LLADA_PROFILE.eos_policy,
        backend=parameters.exact_backend,
        failure_fallback_strategy=None,
    )
    profiler = ComponentProfiler(enabled=True)

    def run() -> Mapping[str, object]:
        with torch.inference_mode():
            logits = model(token_row).logits
        _require(bool(torch.isfinite(logits).all().item()), "live model emitted non-finite logits")
        predictions = logits.argmax(dim=-1)
        probabilities = torch.softmax(logits.to(torch.float64), dim=-1)
        confidence = probabilities.gather(-1, predictions.unsqueeze(-1)).squeeze(-1)
        outcome = run_llada_exact_step(
            grammar,
            token_ids=token_row[0],
            logits=logits[0],
            predicted_token_ids=predictions[0],
            confidence_values=confidence[0],
            decoded_tracking=tracking,
            decode_token=lambda token_id: tokenizer.decode(
                [token_id],
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False,
            ),
            eos_marker="<EOS>",
            prompt_length=len(prompt_ids),
            generation_length=generation_length,
            active_block_end=len(prompt_ids) + generation_length,
            k_s=parameters.schedule_budget,
            tokenizer_adapter=tokenizer_adapter,
            config=strategy_config,
            profile=PINNED_LLADA_PROFILE,
            profiler=profiler,
        )
        result = outcome.solver_result
        adaptive = result.diagnostics.get("adaptive_support")
        attempted_k = (
            tuple(int(value) for value in adaptive.get("attempted_k", ()))
            if isinstance(adaptive, Mapping)
            else ()
        )
        certificate_validation = result.diagnostics.get("certificate_validation")
        certificate_valid = (
            isinstance(certificate_validation, Mapping)
            and certificate_validation.get("is_valid") is True
        )
        certificate = (
            {
                "witness_token_ids": list(result.witness_token_ids),
                "witness_terminal_labels": list(result.witness_terminal_labels),
                "witness_graph_edge_ids": list(result.witness_graph_edge_ids),
                "selected_proposal_ids": list(result.selected_proposal_ids),
                "objective_value": result.objective_value,
                "witness_eos_position": result.witness_eos_position,
                "witness_content_endpoint_slot": result.witness_content_endpoint_slot,
            }
            if result.status is SolveStatus.OPTIMAL
            else None
        )
        profile_event = profiler.snapshot()
        generated_ids = tuple(int(value) for value in token_row[0, -generation_length:].tolist())
        fallback_class = outcome.decoder_step.diagnostics.get("fallback_class")
        return {
            "complete": outcome.complete,
            "generated_token_ids": generated_ids,
            "decoded_with_specials": tokenizer.decode(
                list(generated_ids),
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False,
            ),
            "commit_batch_sizes": (
                (len(outcome.decoder_step.commits),) if outcome.decoder_step.commits else ()
            ),
            "physical_update_batch_sizes": (
                (len(outcome.model_updates),) if outcome.model_updates else ()
            ),
            "fallback_count": int(fallback_class != "none"),
            "support_expansion_count": max(0, len(attempted_k) - 1),
            "empty_optimal_batch_count": int(
                result.status is SolveStatus.OPTIMAL and not result.selected_proposal_ids
            ),
            "solver_status": result.status,
            "exactness_scope": {
                "claim": "exact_on_support",
                **result.exactness_scope.to_dict(),
            },
            "objective_value": result.objective_value,
            "certificate_valid": certificate_valid,
            "certificate": certificate,
            "diagnostics": {
                "implementation": "parent_llada_exact_step_with_rust_backend_v1",
                "solver_backend": parameters.exact_backend.value,
                "support_attempted_k": list(attempted_k),
                "commit_source": outcome.decoder_step.commit_source.value,
                "commit_guarantee": outcome.decoder_step.commit_guarantee.value,
                "fallback_class": fallback_class,
                "eos_pad_canonicalization_count": sum(
                    update.reason.value == "eos_pad_canonicalization"
                    for update in outcome.model_updates
                ),
                "component_profile": (None if profile_event is None else profile_event.to_dict()),
                "outcome": outcome.to_dict(),
            },
        }

    return run


@dataclass(frozen=True, slots=True)
class _MeasuredCall:
    payload: Mapping[str, object] | None
    error: Exception | None
    elapsed_seconds: float
    model_forward_count: int
    process_rss_before_bytes: int
    process_rss_after_bytes: int
    process_high_water_rss_bytes: int
    process_sampled_peak_rss_bytes: int
    process_rss_sample_count: int
    cuda_peak_allocated_bytes: int
    cuda_peak_reserved_bytes: int


def _high_water_rss_bytes() -> int:
    raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return raw if sys.platform == "darwin" else raw * 1024


def _measure_call(
    *,
    torch: Any,
    model: Any,
    process: Any,
    remaining_seconds: float,
    rss_sample_interval_seconds: float,
    run: Callable[[], Mapping[str, object]],
) -> _MeasuredCall:
    forward_count = 0

    def count_forward(_module: object, _inputs: object) -> None:
        nonlocal forward_count
        forward_count += 1

    hook = model.register_forward_pre_hook(count_forward)
    try:
        measured = measure_call(
            run,
            synchronize_accelerator=torch.cuda.synchronize,
            reset_accelerator_peak=torch.cuda.reset_peak_memory_stats,
            read_accelerator_peak=lambda: (
                int(torch.cuda.max_memory_allocated()),
                int(torch.cuda.max_memory_reserved()),
            ),
            read_process_rss=lambda: int(process.memory_info().rss),
            maximum_elapsed_seconds=max(0.0, remaining_seconds),
            rss_sample_interval_seconds=rss_sample_interval_seconds,
        )
    finally:
        hook.remove()
    return _MeasuredCall(
        payload=measured.value,
        error=measured.error,
        elapsed_seconds=measured.elapsed_seconds,
        model_forward_count=forward_count,
        process_rss_before_bytes=measured.process_rss_before_bytes,
        process_rss_after_bytes=measured.process_rss_after_bytes,
        process_high_water_rss_bytes=_high_water_rss_bytes(),
        process_sampled_peak_rss_bytes=measured.process_sampled_peak_rss_bytes,
        process_rss_sample_count=measured.process_rss_sample_count,
        cuda_peak_allocated_bytes=measured.accelerator_peak_allocated_bytes,
        cuda_peak_reserved_bytes=measured.accelerator_peak_reserved_bytes,
    )


def _record_from_measurement(
    strategy: str,
    *,
    measured: _MeasuredCall,
    comparison_fingerprint: str,
    seed: int,
    repetition: int,
    parameters: Q5Parameters,
    tokenizer_adapter: Any,
    grammar: CnfGrammar,
    target: bytes,
) -> Q5MethodRecord:
    payload = measured.payload
    is_exact = strategy == "exact"
    if measured.error is not None or payload is None:
        error = measured.error or RuntimeError("Q5 method returned no payload")
        execution_status = (
            Q5ExecutionStatus.TIMEOUT
            if isinstance(error, TimeoutError)
            else Q5ExecutionStatus.ERROR
        )
        return Q5MethodRecord(
            strategy=strategy,
            execution_status=execution_status,
            comparison_fingerprint=comparison_fingerprint,
            seed=seed,
            repetition=repetition,
            generated_token_ids=(),
            decoded_with_specials="",
            syntactic_valid=None,
            functional_success=None,
            checker={"error_type": type(error).__name__, "error_message": str(error)},
            configured_diffusion_steps=parameters.steps,
            model_forward_count=measured.model_forward_count,
            commit_batch_sizes=(),
            physical_update_batch_sizes=(),
            fallback_count=0,
            support_expansion_count=None,
            empty_optimal_batch_count=None,
            solver_backend=parameters.exact_backend.value if is_exact else None,
            solver_status=(
                SolveStatus.TIMEOUT
                if is_exact and isinstance(error, TimeoutError)
                else SolveStatus.ERROR
                if is_exact
                else None
            ),
            exactness_scope=None,
            objective_value=None,
            certificate_valid=None,
            certificate=None,
            elapsed_seconds=measured.elapsed_seconds,
            process_rss_before_bytes=measured.process_rss_before_bytes,
            process_rss_after_bytes=measured.process_rss_after_bytes,
            process_high_water_rss_bytes=measured.process_high_water_rss_bytes,
            cuda_peak_allocated_bytes=measured.cuda_peak_allocated_bytes,
            cuda_peak_reserved_bytes=measured.cuda_peak_reserved_bytes,
            process_sampled_peak_rss_bytes=measured.process_sampled_peak_rss_bytes,
            process_rss_sample_count=measured.process_rss_sample_count,
            diagnostics={"error_type": type(error).__name__, "error_message": str(error)},
        )

    generated_ids = tuple(int(value) for value in payload["generated_token_ids"])
    checker, syntactic_valid, functional_success = _check_generated_tokens(
        generated_ids,
        tokenizer_adapter=tokenizer_adapter,
        grammar=grammar,
        target=target,
    )
    complete = bool(payload["complete"])
    return Q5MethodRecord(
        strategy=strategy,
        execution_status=(Q5ExecutionStatus.COMPLETE if complete else Q5ExecutionStatus.INCOMPLETE),
        comparison_fingerprint=comparison_fingerprint,
        seed=seed,
        repetition=repetition,
        generated_token_ids=generated_ids,
        decoded_with_specials=str(payload["decoded_with_specials"]),
        syntactic_valid=syntactic_valid,
        functional_success=functional_success,
        checker=checker,
        configured_diffusion_steps=parameters.steps,
        model_forward_count=measured.model_forward_count,
        commit_batch_sizes=tuple(int(value) for value in payload["commit_batch_sizes"]),
        physical_update_batch_sizes=tuple(
            int(value) for value in payload["physical_update_batch_sizes"]
        ),
        fallback_count=int(payload["fallback_count"]),
        support_expansion_count=(int(payload["support_expansion_count"]) if is_exact else None),
        empty_optimal_batch_count=(int(payload["empty_optimal_batch_count"]) if is_exact else None),
        solver_backend=parameters.exact_backend.value if is_exact else None,
        solver_status=payload["solver_status"] if is_exact else None,  # type: ignore[arg-type]
        exactness_scope=payload["exactness_scope"] if is_exact else None,  # type: ignore[arg-type]
        objective_value=(
            float(payload["objective_value"])
            if is_exact and payload["objective_value"] is not None
            else None
        ),
        certificate_valid=(bool(payload["certificate_valid"]) if is_exact else None),
        certificate=payload["certificate"] if is_exact else None,  # type: ignore[arg-type]
        elapsed_seconds=measured.elapsed_seconds,
        process_rss_before_bytes=measured.process_rss_before_bytes,
        process_rss_after_bytes=measured.process_rss_after_bytes,
        process_high_water_rss_bytes=measured.process_high_water_rss_bytes,
        cuda_peak_allocated_bytes=measured.cuda_peak_allocated_bytes,
        cuda_peak_reserved_bytes=measured.cuda_peak_reserved_bytes,
        process_sampled_peak_rss_bytes=measured.process_sampled_peak_rss_bytes,
        process_rss_sample_count=measured.process_rss_sample_count,
        diagnostics=payload["diagnostics"],  # type: ignore[arg-type]
    )


def _default_run_directory(raw_output_root: str, experiment_id: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return REPOSITORY_ROOT / raw_output_root / f"{experiment_id}-{timestamp}"


def _copy_summary(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as input_file, destination.open("xb") as output_file:
        shutil.copyfileobj(input_file, output_file)


def _validate_config_against_profile(
    config: ExperimentConfig,
    parameters: Q5Parameters,
    source: Mapping[str, Any],
    source_bytes: bytes,
) -> None:
    _require(
        _sha256_bytes(source_bytes) == parameters.live_profile_source_sha256,
        "T904 live profile hash differs from Q5's frozen source hash",
    )
    _require(
        config.model_id == PINNED_LLADA_PROFILE.model_id
        and config.model_revision == PINNED_LLADA_PROFILE.tokenizer_revision
        and config.tokenizer_id == PINNED_LLADA_PROFILE.model_id
        and config.tokenizer_revision == PINNED_LLADA_PROFILE.tokenizer_revision,
        "Q5 model/tokenizer pins differ from the LLaDA adapter profile",
    )
    _require(
        config.model_id == source["model_id"]
        and config.model_revision == source["model_revision"]
        and config.tokenizer_revision == source["tokenizer_revision"],
        "Q5 model/tokenizer pins differ from the frozen T904 live profile",
    )
    _require(
        parameters.prompt_instruction == source["generation"]["instruction"]
        and parameters.target_utf8 == source["generation"]["target_utf8"],
        "Q5 task prompt/target differs from the frozen T904 task",
    )
    for name in (
        "generation_length",
        "block_length",
        "steps",
        "temperature",
        "cfg_scale",
        "remasking",
        "max_resamples",
    ):
        _require(
            getattr(parameters, name) == source["generation"][name],
            f"Q5 generation setting differs from T904: {name}",
        )
    _require(
        config.support_top_k == source["exact"]["support_initial_k"]
        and config.support_k_max == source["exact"]["support_k_max"]
        and parameters.schedule_budget == source["exact"]["schedule_budget"],
        "Q5 exact support/schedule differs from the frozen live profile",
    )
    _require(
        parameters.eos_mode == source["exact"]["eos_mode"]
        and parameters.termination_token_ids
        == tuple(PINNED_LLADA_PROFILE.eos_policy.termination_token_ids)
        and parameters.pad_token_id == PINNED_LLADA_PROFILE.eos_policy.pad_token_id,
        "Q5 EOS/PAD semantics differ from the adapter profile",
    )
    _require(
        parameters.weight_mode.value == source["exact"]["weight_mode"],
        "Q5 proposal weight mode differs from the frozen live profile",
    )
    _require(
        parameters.epic_regular_cover_min_batch == source["epic"]["regular_cover_min_batch"]
        and parameters.epic_regular_cover_exact is source["epic"]["regular_cover_exact"],
        "Q5 EPIC settings differ from the frozen live profile",
    )
    _require(
        parameters.quantization == "bitsandbytes_nf4_double_quant_bfloat16"
        and source["quantization"]["load_in_4bit"] is True
        and source["quantization"]["four_bit_quant_type"] == "nf4"
        and source["quantization"]["four_bit_compute_dtype"] == "bfloat16"
        and source["quantization"]["four_bit_use_double_quant"] is True,
        "Q5 quantization label differs from the loaded frozen profile",
    )
    _require(
        parameters.functional_checker == "exact_target_bytes_match_v1",
        "Q5 v1 functional checker must remain frozen",
    )
    _require(config.local_files_only, "Q5 v1 must not fetch model files during execution")
    if parameters.method_order == "fixed_as_configured":
        _require(
            config.repetitions == 1
            and parameters.warmup_runs == 0
            and parameters.rss_sample_interval_seconds is None
            and parameters.quartile_policy is None,
            "the original Q5 smoke requires one fixed-order repetition without warmup",
        )
    elif parameters.method_order == "balanced_cyclic_by_repetition":
        _require(
            config.repetitions >= len(Q5_STRATEGIES)
            and config.repetitions % len(Q5_STRATEGIES) == 0,
            "balanced Q5 timing requires a positive multiple of four repetitions",
        )
        _require(parameters.warmup_runs >= 1, "robust Q5 timing requires warmup")
        _require(
            parameters.rss_sample_interval_seconds is not None
            and parameters.rss_sample_interval_seconds > 0.0,
            "robust Q5 timing requires a positive RSS sample interval",
        )
        _require(
            parameters.quartile_policy == QUARTILE_POLICY,
            "robust Q5 timing requires the implemented quartile policy",
        )
    else:
        raise RuntimeError("unsupported Q5 method-order policy")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the paired Q5 live-model experiment.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--summary-output", type=Path)
    arguments = parser.parse_args(argv)

    config_path = arguments.config.resolve()
    if not config_path.is_relative_to(REPOSITORY_ROOT):
        raise ValueError("Q5 config must be stored inside the repository")
    config_relative = str(config_path.relative_to(REPOSITORY_ROOT))
    config = load_experiment_config(config_path)
    if config.question is not ExperimentKind.END_TO_END:
        raise ValueError("Q5 driver requires an end_to_end configuration")
    if config.publication_mode:
        raise ValueError("Q5 v1 is a diagnostic smoke, not publication mode")
    if config.seeds != (904,):
        raise ValueError("Q5 requires exactly seed 904")
    if config.device != "cuda" or not config.synchronize_cuda or config.cuda_device != 0:
        raise ValueError("Q5 v1 requires synchronized CUDA device 0")
    parameters = _configuration_parameters(config.parameters)
    source_relative = _relative_path(config.grammar_source, "grammar.source")
    source_path = (REPOSITORY_ROOT / source_relative).resolve()
    if not source_path.is_relative_to(REPOSITORY_ROOT):
        raise ValueError("grammar.source resolves outside the repository")
    source_bytes = source_path.read_bytes()
    source: dict[str, Any] = tomllib.loads(source_bytes.decode("utf-8"))
    _validate_config_against_profile(config, parameters, source, source_bytes)

    run_directory = (
        _default_run_directory(parameters.raw_output_root, config.experiment_id)
        if arguments.run_directory is None
        else arguments.run_directory
    )
    save_resolved_config(config, run_directory)

    try:
        import psutil
        import torch
        from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig
    except ImportError as error:
        raise SystemExit(
            "Q5 CUDA dependencies are missing; follow scripts/exact_commit/README.md"
        ) from error
    _require(torch.cuda.is_available(), "Q5 requires a CUDA device")
    torch.cuda.set_device(config.cuda_device)
    torch.manual_seed(config.seeds[0])
    torch.cuda.manual_seed_all(config.seeds[0])
    device_properties = torch.cuda.get_device_properties(config.cuda_device)
    shards = _cached_checkpoint_metadata(source)
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=str(source["quantization"]["four_bit_quant_type"]),
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=bool(source["quantization"]["four_bit_use_double_quant"]),
    )
    tokenizer = AutoTokenizer.from_pretrained(
        config.tokenizer_id,
        revision=config.tokenizer_revision,
        trust_remote_code=False,
        local_files_only=config.local_files_only,
    )
    model = AutoModel.from_pretrained(
        config.model_id,
        revision=config.model_revision,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        quantization_config=quantization,
        device_map={"": config.cuda_device},
        low_cpu_mem_usage=True,
        local_files_only=config.local_files_only,
    ).eval()
    resolved_revision = getattr(model.config, "_commit_hash", None)
    _require(resolved_revision == config.model_revision, "model resolved to an unexpected revision")
    _require(
        int(model.config.vocab_size) == parameters.expected_model_vocabulary_size,
        "unexpected model vocabulary size",
    )
    _require(
        tokenizer.vocab_size == parameters.expected_tokenizer_base_vocabulary_size
        and len(tokenizer) == parameters.expected_tokenizer_total_vocabulary_size,
        "unexpected tokenizer vocabulary shape",
    )
    base_pieces = tuple(
        tokenizer.convert_ids_to_tokens(token_id) for token_id in range(tokenizer.vocab_size)
    )
    _require(all(isinstance(piece, str) for piece in base_pieces), "missing base token piece")
    tokenizer_adapter = build_llada_byte_adapter(
        base_pieces,
        model_vocabulary_size=int(model.config.vocab_size),
        profile=PINNED_LLADA_PROFILE,
    )

    target = parameters.target_utf8.encode("utf-8")
    exact_grammar = _literal_grammar(target)
    grammar_sha256 = _canonical_sha256(exact_grammar.to_dict())
    prompt_text = tokenizer.apply_chat_template(
        [{"role": "user", "content": parameters.prompt_instruction}],
        add_generation_prompt=True,
        tokenize=False,
    )
    prompt_ids = tuple(int(value) for value in tokenizer(prompt_text)["input_ids"])
    prompt = torch.tensor([prompt_ids], device="cuda:0", dtype=torch.long)

    from constrained_diffusion.constrain_utils import compile_lex_map
    from constrained_diffusion.eval.dllm.models.llada.generate_constrained import (
        preprocessed_generate_stuff,
    )
    from rustformlang.cfg import CFG

    epic = source["epic"]
    epic_grammar = CFG.from_text(str(epic["grammar_text"]), str(epic["grammar_start"]))
    epic_grammar = epic_grammar.to_normal_form()
    lex_map = compile_lex_map(
        {str(epic["lexeme_name"]): str(epic["lexeme_regex"])},
        subtokens={},
    )
    preprocessed = preprocessed_generate_stuff(tokenizer, epic_grammar, lex_map, trace=False)

    comparison_contract = {
        "task_ids": list(parameters.task_ids),
        "prompt_id": parameters.prompt_id,
        "prompt_instruction_sha256": _sha256_bytes(parameters.prompt_instruction.encode("utf-8")),
        "chat_template_text_sha256": _sha256_bytes(prompt_text.encode("utf-8")),
        "prompt_token_ids_sha256": _canonical_sha256(list(prompt_ids)),
        "prompt_token_count": len(prompt_ids),
        "model_id": config.model_id,
        "model_revision": config.model_revision,
        "tokenizer_id": config.tokenizer_id,
        "tokenizer_revision": config.tokenizer_revision,
        "grammar_id": config.grammar_id,
        "grammar_sha256": grammar_sha256,
        "target_bytes_hex": target.hex(),
        "generation_length": parameters.generation_length,
        "block_length": parameters.block_length,
        "steps": parameters.steps,
        "temperature": parameters.temperature,
        "cfg_scale": parameters.cfg_scale,
        "remasking": parameters.remasking,
        "max_resamples": parameters.max_resamples,
        "dtype": config.dtype,
        "quantization": parameters.quantization,
        "seed": config.seeds[0],
        "method_differences": {
            "unconstrained": "grammar disabled during selection; same grammar used by checker",
            "serial": "upstream one-token constrained selection",
            "epic": "upstream regular-cover batch selection with serial path retained",
            "exact": "Rust MWPC exact_on_support selection plus canonical EOS/PAD updates",
        },
    }
    comparison_fingerprint = _canonical_sha256(comparison_contract)
    process = psutil.Process()
    run_deadline = monotonic() + config.run_timeout_seconds

    def prepared_call(
        strategy: str,
        remaining_seconds: float,
    ) -> Any:
        if strategy == "exact":
            call = _prepare_exact_call(
                torch=torch,
                model=model,
                tokenizer=tokenizer,
                prompt_ids=prompt_ids,
                tokenizer_adapter=tokenizer_adapter,
                grammar=exact_grammar,
                parameters=parameters,
                solver_timeout_seconds=min(
                    config.solver_timeout_seconds,
                    max(0.0, remaining_seconds),
                ),
            )
            return nullcontext(call)
        return _prepare_upstream_call(
            strategy,
            model=model,
            tokenizer=tokenizer,
            prompt=prompt,
            grammar=epic_grammar,
            lex_map=lex_map,
            preprocessed=preprocessed,
            parameters=parameters,
        )

    warmup_records: list[dict[str, object]] = []
    for warmup_index in range(parameters.warmup_runs):
        for strategy in Q5_STRATEGIES:
            torch.manual_seed(config.seeds[0])
            torch.cuda.manual_seed_all(config.seeds[0])
            remaining = run_deadline - monotonic()
            status = Q5ExecutionStatus.COMPLETE
            detail: dict[str, object] = {}
            try:
                if remaining <= 0.0:
                    raise TimeoutError("Q5 run deadline expired before warmup")
                with prepared_call(strategy, remaining) as call:
                    payload = call()
                    torch.cuda.synchronize()
                generated_ids = tuple(int(value) for value in payload["generated_token_ids"])
                checker, syntactic_valid, functional_success = _check_generated_tokens(
                    generated_ids,
                    tokenizer_adapter=tokenizer_adapter,
                    grammar=exact_grammar,
                    target=target,
                )
                complete = bool(payload["complete"])
                status = Q5ExecutionStatus.COMPLETE if complete else Q5ExecutionStatus.INCOMPLETE
                detail = {
                    "syntactic_valid": syntactic_valid,
                    "functional_success": functional_success,
                    "generated_token_ids_sha256": _canonical_sha256(list(generated_ids)),
                    "checker_id": checker["checker_id"],
                    "solver_status": (
                        payload["solver_status"].value if strategy == "exact" else None
                    ),
                    "certificate_valid": (
                        bool(payload["certificate_valid"]) if strategy == "exact" else None
                    ),
                }
            except Exception as error:
                status = (
                    Q5ExecutionStatus.TIMEOUT
                    if isinstance(error, TimeoutError)
                    else Q5ExecutionStatus.ERROR
                )
                detail = {
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            warmup_records.append(
                {
                    "warmup_index": warmup_index,
                    "strategy": strategy,
                    "execution_status": status.value,
                    **detail,
                }
            )

    records: list[Q5MethodRecord] = []
    for repetition in range(config.repetitions):
        method_order = (
            Q5_STRATEGIES
            if parameters.method_order == "fixed_as_configured"
            else cyclic_method_order(Q5_STRATEGIES, repetition)
        )
        for strategy in method_order:
            torch.manual_seed(config.seeds[0])
            torch.cuda.manual_seed_all(config.seeds[0])
            remaining = run_deadline - monotonic()
            with prepared_call(strategy, remaining) as call:
                measured = _measure_call(
                    torch=torch,
                    model=model,
                    process=process,
                    remaining_seconds=remaining,
                    rss_sample_interval_seconds=(parameters.rss_sample_interval_seconds or 0.001),
                    run=call,
                )
            records.append(
                _record_from_measurement(
                    strategy,
                    measured=measured,
                    comparison_fingerprint=comparison_fingerprint,
                    seed=config.seeds[0],
                    repetition=repetition,
                    parameters=parameters,
                    tokenizer_adapter=tokenizer_adapter,
                    grammar=exact_grammar,
                    target=target,
                )
            )

    git_commit = _command_output(("git", "rev-parse", "HEAD"))
    git_dirty = bool(_command_output(("git", "status", "--porcelain")))
    run_metadata = {
        "run_id": run_directory.name,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "upstream_epic_commit": _command_output(
            ("git", "rev-parse", "HEAD"), cwd=REPOSITORY_ROOT / "vendor/EPIC-Decoding"
        ),
        "config_path": config_relative,
        "config_sha256": config.config_sha256,
        "live_profile_source_path": source_relative,
        "live_profile_source_sha256": _sha256_bytes(source_bytes),
        "benchmark_claim": False,
        "publication_mode": config.publication_mode,
        "timing_scope": (
            "single_fixed_order_cuda_smoke_without_warmup; model/tokenizer/grammar and "
            "per-method runner setup excluded"
            if parameters.method_order == "fixed_as_configured"
            else "warm repeated balanced-cyclic CUDA timing; model/tokenizer/grammar and "
            "per-method runner setup excluded"
        ),
        "timing_protocol": {
            "warmup_runs_per_strategy": parameters.warmup_runs,
            "recorded_repetitions_per_strategy": config.repetitions,
            "method_order": parameters.method_order,
            "cuda_synchronized_before_and_after_each_measurement": True,
            "cuda_peak_counters_reset_before_each_measurement": True,
            "model_load_inside_measured_region": False,
            "tokenizer_grammar_and_shared_preprocessing_inside_measured_region": False,
            "method_specific_runner_setup_inside_measured_region": False,
            "rss_metric": "sampled_process_resident_set_peak_per_call",
            "rss_sample_interval_seconds": (parameters.rss_sample_interval_seconds or 0.001),
            "quartile_policy": parameters.quartile_policy or QUARTILE_POLICY,
            "failed_timeout_and_incomplete_rows_in_runtime_aggregates": False,
        },
        "warmup_records": warmup_records,
        "timeout_enforcement": (
            "native_exact_parser_deadline plus post-method and between-method run deadline; "
            "upstream generation calls are not preemptible"
        ),
        "comparison_contract": comparison_contract,
        "comparison_fingerprint": comparison_fingerprint,
        "support_policy": config.support_policy,
        "support_top_k": config.support_top_k,
        "support_k_max": config.support_k_max,
        "exactness_scope": config.exactness_scope,
        "exactness_guarantee": config.exactness_guarantee,
        "model": {
            "model_id": config.model_id,
            "requested_revision": config.model_revision,
            "resolved_revision": resolved_revision,
            "class": type(model).__name__,
            "vocabulary_size": int(model.config.vocab_size),
            "checkpoint_shards": shards,
            "model_memory_footprint_bytes": int(model.get_memory_footprint()),
        },
        "tokenizer": {
            "tokenizer_id": config.tokenizer_id,
            "revision": config.tokenizer_revision,
            "class": type(tokenizer).__name__,
            "base_vocabulary_size": tokenizer.vocab_size,
            "total_vocabulary_size": len(tokenizer),
        },
        "hardware": {
            "gpu_name": device_properties.name,
            "gpu_total_memory_bytes": int(device_properties.total_memory),
            "cuda_compute_capability": f"{device_properties.major}.{device_properties.minor}",
            "cuda_driver_version": _command_output(
                ("nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader")
            ).splitlines()[0],
            "host_total_memory_bytes": int(psutil.virtual_memory().total),
            "cpu_logical_count": psutil.cpu_count(logical=True),
            "platform": platform.platform(),
        },
        "software_versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "torch_cuda_runtime": torch.version.cuda,
            "mwpc_exact": _package_version("mwpc-exact"),
            "mwpc_parser_py": _package_version("mwpc-parser-py"),
            "rustformlang": _package_version("rustformlang"),
            "transformers": _package_version("transformers"),
            "bitsandbytes": _package_version("bitsandbytes"),
        },
    }
    result = Q5ExperimentResult(tuple(records), run_metadata)
    raw_path, summary_path = write_q5_artifacts(result, run_directory)
    if arguments.summary_output is not None:
        _copy_summary(summary_path, arguments.summary_output)

    warmup_failure_count = sum(
        warmup["execution_status"] != Q5ExecutionStatus.COMPLETE.value
        or (
            warmup["strategy"] != "unconstrained"
            and (
                warmup.get("syntactic_valid") is not True
                or warmup.get("functional_success") is not True
            )
        )
        or (
            warmup["strategy"] == "exact"
            and (
                warmup.get("solver_status") != SolveStatus.OPTIMAL.value
                or warmup.get("certificate_valid") is not True
            )
        )
        for warmup in warmup_records
    )
    contract_failure_count = result.required_contract_failure_count + warmup_failure_count
    print(
        json.dumps(
            {
                "run_directory": str(run_directory),
                "raw_rows": str(raw_path),
                "summary": str(summary_path),
                "method_count": len(records),
                "warmup_count": len(warmup_records),
                "contract_failure_count": contract_failure_count,
            },
            sort_keys=True,
        )
    )
    return 1 if contract_failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
