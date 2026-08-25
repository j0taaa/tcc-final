#!/usr/bin/env python3
"""Run the pinned T904 LLaDA serial/EPIC/exact live-model smoke.

This is a correctness/reachability smoke only. It deliberately emits no
throughput, latency, quality, or comparative benchmark conclusion.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import tomllib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
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
from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal, TerminalProduction
from mwpc_exact.reference.recognizer import recognizes_cnf

sys.dont_write_bytecode = True

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/exact_commit/t904_llada_live_smoke.toml"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _run(*arguments: str, cwd: Path = REPOSITORY_ROOT) -> str:
    return subprocess.run(
        arguments,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _package_versions(names: Sequence[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in names:
        versions[name] = importlib.metadata.version(name)
    return versions


def _json_safe(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _literal_grammar(target: bytes) -> CnfGrammar:
    _require(len(target) == 1, "T904's frozen smoke target must be exactly one byte")
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, target[0]),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )


def _validate_generated_tokens(
    token_ids: Sequence[int],
    *,
    tokenizer_adapter: Any,
    grammar: CnfGrammar,
    target: bytes,
) -> dict[str, object]:
    termination_ids = frozenset(PINNED_LLADA_PROFILE.eos_policy.termination_token_ids)
    termination_position = next(
        (position for position, token_id in enumerate(token_ids) if token_id in termination_ids),
        None,
    )
    _require(termination_position is not None, "generated row has no configured termination token")
    content_ids = tuple(token_ids[:termination_position])
    suffix_ids = tuple(token_ids[termination_position + 1 :])
    _require(
        all(token_id in termination_ids for token_id in suffix_ids),
        "generated row contains an ordinary token after termination",
    )
    content_bytes = tokenizer_adapter.detokenize_bytes(content_ids)
    grammar_valid = recognizes_cnf(grammar, content_bytes)
    _require(content_bytes == target, "generated content differs from the frozen target")
    _require(grammar_valid, "generated content failed independent CNF recognition")
    return {
        "termination_position": termination_position,
        "termination_token_id": token_ids[termination_position],
        "suffix_token_ids": list(suffix_ids),
        "content_token_ids": list(content_ids),
        "content_bytes_hex": content_bytes.hex(),
        "content_utf8": content_bytes.decode("utf-8"),
        "independent_grammar_valid": grammar_valid,
    }


def _run_upstream_baseline(
    strategy: str,
    *,
    model: Any,
    tokenizer: Any,
    prompt: Any,
    grammar: Any,
    lex_map: Any,
    config: Mapping[str, Any],
    tokenizer_adapter: Any,
    exact_grammar: CnfGrammar,
    target: bytes,
) -> dict[str, object]:
    from constrained_diffusion.eval.dllm.models.llada import generate_constrained

    enabled = strategy == "epic"
    os.environ["CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH"] = "1" if enabled else "0"
    os.environ["CONSTRAINED_DIFFUSION_REGULAR_COVER_MIN_BATCH"] = str(
        config["epic"]["regular_cover_min_batch"]
    )
    os.environ["CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT"] = (
        "1" if config["epic"]["regular_cover_exact"] else "0"
    )

    selector_calls = 0
    original_selector = generate_constrained.select_batch_with_regular_cover

    def observing_selector(*args: object, **kwargs: object) -> object:
        nonlocal selector_calls
        selector_calls += 1
        return original_selector(*args, **kwargs)

    generate_constrained.select_batch_with_regular_cover = observing_selector
    event_count = 0
    final_event: tuple[Any, list[Any], bool] | None = None
    try:
        for event in generate_constrained.generate(
            model,
            prompt,
            tokenizer,
            grammar,
            lex_map,
            prompt_len=int(prompt.shape[1]),
            steps=int(config["generation"]["steps"]),
            gen_length=int(config["generation"]["generation_length"]),
            block_length=int(config["generation"]["block_length"]),
            temperature=float(config["generation"]["temperature"]),
            cfg_scale=float(config["generation"]["cfg_scale"]),
            remasking=str(config["generation"]["remasking"]),
            mask_id=PINNED_LLADA_PROFILE.mask_token_id,
            trace=False,
            constrain=True,
            max_resamples=int(config["generation"]["max_resamples"]),
        ):
            event_count += 1
            final_event = event
    finally:
        generate_constrained.select_batch_with_regular_cover = original_selector

    _require(final_event is not None, f"{strategy} baseline emitted no event")
    output, resamples, complete = final_event
    generation_length = int(config["generation"]["generation_length"])
    generated_ids = tuple(int(value) for value in output[0, -generation_length:].tolist())
    validation = _validate_generated_tokens(
        generated_ids,
        tokenizer_adapter=tokenizer_adapter,
        grammar=exact_grammar,
        target=target,
    )
    _require(bool(complete), f"{strategy} baseline did not report a complete generation")
    return {
        "strategy": strategy,
        "implementation": (
            "upstream_llada_serial_constrained_loop"
            if strategy == "serial"
            else "upstream_llada_regular_cover_enabled_loop"
        ),
        "regular_cover_batch_enabled": enabled,
        "regular_cover_selector_calls": selector_calls,
        "serial_fallback_remains_available": True,
        "complete": bool(complete),
        "event_count": event_count,
        "resample_count": len(resamples),
        "generated_token_ids": list(generated_ids),
        "decoded_with_specials": tokenizer.decode(
            list(generated_ids),
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        ),
        "validation": validation,
    }


def _top_tokens(tokenizer: Any, logits: Any, count: int = 8) -> list[list[dict[str, object]]]:
    values, indices = logits.float().topk(k=count, dim=-1)
    rows: list[list[dict[str, object]]] = []
    for row_indices, row_values in zip(indices.tolist(), values.tolist(), strict=True):
        rows.append(
            [
                {
                    "token_id": int(token_id),
                    "token_piece": tokenizer.convert_ids_to_tokens(int(token_id)),
                    "decoded": tokenizer.decode(
                        [int(token_id)],
                        skip_special_tokens=False,
                        clean_up_tokenization_spaces=False,
                    ),
                    "logit": float(score),
                }
                for token_id, score in zip(row_indices, row_values, strict=True)
            ]
        )
    return rows


def _run_exact(
    *,
    torch: Any,
    model: Any,
    tokenizer: Any,
    prompt_ids: Sequence[int],
    config: Mapping[str, Any],
    tokenizer_adapter: Any,
    grammar: CnfGrammar,
    target: bytes,
) -> dict[str, object]:
    generation_length = int(config["generation"]["generation_length"])
    token_row = torch.tensor(
        [list(prompt_ids) + [PINNED_LLADA_PROFILE.mask_token_id] * generation_length],
        device="cuda:0",
        dtype=torch.long,
    )
    with torch.inference_mode():
        logits = model(token_row).logits
    _require(bool(torch.isfinite(logits).all().item()), "live model emitted non-finite logits")
    predictions = logits.argmax(dim=-1)
    probabilities = torch.softmax(logits.to(torch.float64), dim=-1)
    confidence = probabilities.gather(-1, predictions.unsqueeze(-1)).squeeze(-1)
    tracking: list[object] = [
        tokenizer.decode(
            [int(token_id)],
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
        for token_id in prompt_ids
    ] + [None] * generation_length
    exact = config["exact"]
    strategy_config = ExactStrategyConfig(
        adaptive_support=AdaptiveSupportConfig(
            initial_k=int(exact["support_initial_k"]),
            k_max=int(exact["support_k_max"]),
        ),
        weight_mode=ProposalWeightMode(str(exact["weight_mode"])),
        eos_policy=PINNED_LLADA_PROFILE.eos_policy,
        backend=ExactBackend(str(exact["backend"])),
        failure_fallback_strategy=None,
    )
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
        k_s=int(exact["schedule_budget"]),
        tokenizer_adapter=tokenizer_adapter,
        config=strategy_config,
        profile=PINNED_LLADA_PROFILE,
    )
    result = outcome.solver_result
    _require(result.status is SolveStatus.OPTIMAL, "exact live step was not OPTIMAL")
    _require(
        config["exact"]["exactness_scope"] == "exact_on_support"
        and result.exactness_scope.kind.value in {"top_k", "explicit", "full"},
        "exact result omitted its represented-support scope",
    )
    _require(outcome.complete, "exact live step did not complete the generated row")
    certificate_validation = result.diagnostics.get("certificate_validation")
    _require(
        isinstance(certificate_validation, Mapping)
        and certificate_validation.get("is_valid") is True,
        "exact OPTIMAL result lacks a valid independent certificate report",
    )
    generated_ids = tuple(int(value) for value in token_row[0, -generation_length:].tolist())
    validation = _validate_generated_tokens(
        generated_ids,
        tokenizer_adapter=tokenizer_adapter,
        grammar=grammar,
        target=target,
    )
    return {
        "strategy": "exact",
        "implementation": "parent_side_pinned_llada_exact_step_v1",
        "complete": outcome.complete,
        "generated_token_ids": list(generated_ids),
        "decoded_with_specials": tokenizer.decode(
            list(generated_ids),
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        ),
        "top_tokens_before_commit": _top_tokens(
            tokenizer,
            logits[0, -generation_length:],
        ),
        "validation": validation,
        "outcome": _json_safe(outcome.to_dict()),
    }


def _cached_checkpoint_metadata(config: Mapping[str, Any]) -> list[dict[str, object]]:
    from huggingface_hub import try_to_load_from_cache

    names = [str(value) for value in config["checkpoint_shard_names"]]
    expected_sizes = [int(value) for value in config["checkpoint_shard_sizes_bytes"]]
    _require(len(names) == len(expected_sizes), "checkpoint shard names/sizes differ in length")
    shards: list[dict[str, object]] = []
    for name, expected_size in zip(names, expected_sizes, strict=True):
        cached = try_to_load_from_cache(
            str(config["model_id"]),
            name,
            revision=str(config["model_revision"]),
        )
        _require(isinstance(cached, str), f"pinned checkpoint shard is not cached: {name}")
        actual_size = Path(cached).stat().st_size
        _require(actual_size == expected_size, f"checkpoint shard size mismatch: {name}")
        shards.append({"name": name, "size_bytes": actual_size})
    return shards


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="require the exact model/tokenizer revision to exist in the local HF cache",
    )
    arguments = parser.parse_args()

    config_path = arguments.config.resolve()
    config_bytes = config_path.read_bytes()
    config: dict[str, Any] = tomllib.loads(config_bytes.decode("utf-8"))
    output_path = (
        arguments.output.resolve()
        if arguments.output is not None
        else (REPOSITORY_ROOT / str(config["output"]["raw_metadata"])).resolve()
    )
    _require(config["schema_version"] == 1, "unsupported T904 config schema")
    _require(config["purpose"] == "live_model_correctness_smoke_not_a_benchmark", "bad purpose")
    _require(
        tuple(config["generation"]["strategies"]) == ("serial", "epic", "exact"),
        "T904 must retain all three configured strategies",
    )
    _require(
        config["model_id"] == PINNED_LLADA_PROFILE.model_id
        and config["model_revision"] == PINNED_LLADA_PROFILE.tokenizer_revision
        and config["tokenizer_revision"] == PINNED_LLADA_PROFILE.tokenizer_revision,
        "live-smoke model/tokenizer pin differs from the LLaDA adapter profile",
    )
    _require(
        tuple(config["exact"]["termination_token_ids"])
        == PINNED_LLADA_PROFILE.eos_policy.termination_token_ids
        and config["exact"]["pad_token_id"] == PINNED_LLADA_PROFILE.eos_policy.pad_token_id,
        "live-smoke EOS/PAD settings differ from the LLaDA adapter profile",
    )
    git_commit = _run("git", "rev-parse", "HEAD")
    git_status = _run("git", "status", "--porcelain", "--untracked-files=all")
    if config["require_clean_worktree"]:
        _require(not git_status, "T904 evidence requires a clean worktree at process start")

    try:
        import psutil
        import torch
        from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig
    except ImportError as error:
        raise SystemExit(
            "T904 CUDA dependencies are missing; follow scripts/exact_commit/README.md"
        ) from error

    _require(torch.cuda.is_available(), "T904 requires a CUDA device")
    torch.manual_seed(int(config["seed"]))
    torch.cuda.manual_seed_all(int(config["seed"]))
    torch.cuda.set_device(0)
    torch.cuda.reset_peak_memory_stats()
    device_properties = torch.cuda.get_device_properties(0)
    shards = _cached_checkpoint_metadata(config)
    checkpoint_bytes = sum(int(shard["size_bytes"]) for shard in shards)
    _require(
        checkpoint_bytes == sum(int(value) for value in config["checkpoint_shard_sizes_bytes"]),
        "checkpoint byte total differs from the frozen config",
    )

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=str(config["quantization"]["four_bit_quant_type"]),
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=bool(config["quantization"]["four_bit_use_double_quant"]),
    )
    tokenizer = AutoTokenizer.from_pretrained(
        str(config["model_id"]),
        revision=str(config["tokenizer_revision"]),
        trust_remote_code=False,
        local_files_only=arguments.local_files_only,
    )
    model = AutoModel.from_pretrained(
        str(config["model_id"]),
        revision=str(config["model_revision"]),
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        quantization_config=quantization,
        device_map={"": 0},
        low_cpu_mem_usage=True,
        local_files_only=arguments.local_files_only,
    ).eval()
    resolved_revision = getattr(model.config, "_commit_hash", None)
    _require(
        resolved_revision == config["expected_resolved_revision"],
        "loaded model did not resolve to the frozen revision",
    )
    model_vocabulary_size = int(model.config.vocab_size)
    _require(
        model_vocabulary_size == config["expected_model_vocabulary_size"],
        "unexpected live model vocabulary size",
    )
    _require(
        tokenizer.vocab_size == config["expected_tokenizer_base_vocabulary_size"]
        and len(tokenizer) == config["expected_tokenizer_total_vocabulary_size"],
        "unexpected live tokenizer vocabulary shape",
    )
    base_pieces = tuple(
        tokenizer.convert_ids_to_tokens(token_id) for token_id in range(tokenizer.vocab_size)
    )
    _require(all(isinstance(piece, str) for piece in base_pieces), "missing base token piece")
    tokenizer_adapter = build_llada_byte_adapter(
        base_pieces,
        model_vocabulary_size=model_vocabulary_size,
        profile=PINNED_LLADA_PROFILE,
    )

    generation = config["generation"]
    target = str(generation["target_utf8"]).encode("utf-8")
    exact_grammar = _literal_grammar(target)
    prompt_text = tokenizer.apply_chat_template(
        [{"role": "user", "content": str(generation["instruction"])}],
        add_generation_prompt=True,
        tokenize=False,
    )
    prompt_ids = tokenizer(prompt_text)["input_ids"]
    prompt = torch.tensor([prompt_ids], device="cuda:0", dtype=torch.long)

    from constrained_diffusion.constrain_utils import compile_lex_map
    from rustformlang.cfg import CFG

    epic = config["epic"]
    epic_grammar = CFG.from_text(str(epic["grammar_text"]), str(epic["grammar_start"]))
    epic_grammar = epic_grammar.to_normal_form()
    lex_map = compile_lex_map(
        {str(epic["lexeme_name"]): str(epic["lexeme_regex"])},
        subtokens={},
    )
    strategy_runs = [
        _run_upstream_baseline(
            strategy,
            model=model,
            tokenizer=tokenizer,
            prompt=prompt,
            grammar=epic_grammar,
            lex_map=lex_map,
            config=config,
            tokenizer_adapter=tokenizer_adapter,
            exact_grammar=exact_grammar,
            target=target,
        )
        for strategy in ("serial", "epic")
    ]
    strategy_runs.append(
        _run_exact(
            torch=torch,
            model=model,
            tokenizer=tokenizer,
            prompt_ids=prompt_ids,
            config=config,
            tokenizer_adapter=tokenizer_adapter,
            grammar=exact_grammar,
            target=target,
        )
    )
    _require(all(run["complete"] for run in strategy_runs), "a strategy did not complete")

    driver_revision = _run("git", "rev-parse", "HEAD")
    _require(driver_revision == git_commit, "repository commit changed during the smoke run")
    artifact = {
        "schema_version": 1,
        "task_id": "T904",
        "status": "PASS",
        "purpose": config["purpose"],
        "benchmark_claim": False,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "invocation": (
            "python scripts/exact_commit/run_t904_llada_live_smoke.py "
            "--config configs/exact_commit/t904_llada_live_smoke.toml --local-files-only"
        ),
        "repository": {
            "git_commit": git_commit,
            "git_clean_at_start": not bool(git_status),
            "upstream_epic_commit": _run(
                "git", "rev-parse", "HEAD", cwd=REPOSITORY_ROOT / "vendor/EPIC-Decoding"
            ),
        },
        "config": {
            "path": str(config_path.relative_to(REPOSITORY_ROOT)),
            "sha256": _sha256_bytes(config_bytes),
            "seed": config["seed"],
        },
        "model": {
            "model_id": config["model_id"],
            "requested_revision": config["model_revision"],
            "resolved_revision": resolved_revision,
            "class": type(model).__name__,
            "vocabulary_size": model_vocabulary_size,
            "checkpoint_shards": shards,
            "checkpoint_safetensors_bytes": checkpoint_bytes,
        },
        "tokenizer": {
            "requested_revision": config["tokenizer_revision"],
            "class": type(tokenizer).__name__,
            "base_vocabulary_size": tokenizer.vocab_size,
            "total_vocabulary_size": len(tokenizer),
            "model_output_padding_rows": model_vocabulary_size - len(tokenizer),
            "ordinary_byte_emission_ids": tokenizer.vocab_size,
            "unsupported_ordinary_emission_ids": len(tokenizer_adapter.unsupported_token_ids),
        },
        "execution": {
            "torch_dtype": config["torch_dtype"],
            "device": config["device"],
            "device_map": _json_safe(getattr(model, "hf_device_map", {"": 0})),
            "quantization": dict(config["quantization"]),
            "local_files_only": arguments.local_files_only,
            "model_memory_footprint_bytes": int(model.get_memory_footprint()),
            "cuda_memory_allocated_bytes": int(torch.cuda.memory_allocated()),
            "cuda_peak_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        },
        "memory_assessment": {
            "gpu_total_memory_bytes": int(device_properties.total_memory),
            "host_total_memory_bytes": int(psutil.virtual_memory().total),
            "unquantized_bf16_load_attempted": False,
            "unquantized_bf16_limitation": (
                "The pinned safetensor shard bytes exceed total GPU memory before "
                "activations and runtime overhead; the smoke therefore uses recorded NF4 "
                "4-bit quantization."
            ),
        },
        "hardware": {
            "gpu_name": device_properties.name,
            "gpu_compute_capability": (f"{device_properties.major}.{device_properties.minor}"),
            "cuda_driver_version": _run(
                "nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"
            ).splitlines()[0],
            "cpu_logical_count": psutil.cpu_count(logical=True),
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "software": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "torch_cuda_runtime": torch.version.cuda,
            "packages": _package_versions(
                (
                    "accelerate",
                    "bitsandbytes",
                    "huggingface-hub",
                    "safetensors",
                    "tokenizers",
                    "transformers",
                )
            ),
        },
        "grammar": {
            "target_bytes_hex": target.hex(),
            "target_utf8": target.decode("utf-8"),
            "exact_cnf": exact_grammar.to_dict(),
            "exact_cnf_sha256": _sha256_bytes(
                json.dumps(exact_grammar.to_dict(), sort_keys=True).encode("utf-8")
            ),
            "epic_grammar_text": epic["grammar_text"],
            "epic_lexeme_regex": epic["lexeme_regex"],
        },
        "generation": {
            key: value for key, value in generation.items() if key not in {"instruction"}
        },
        "prompt": {
            "instruction": generation["instruction"],
            "chat_template_text_sha256": _sha256_bytes(prompt_text.encode("utf-8")),
            "prompt_token_count": len(prompt_ids),
        },
        "strategy_runs": strategy_runs,
        "conclusion": (
            "All configured modes reached the pinned live model and independently valid "
            "structured output; the exact run returned an independently validated OPTIMAL "
            "certificate exact_on_support. This smoke alone supports no benchmark claim."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "artifact": str(output_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
