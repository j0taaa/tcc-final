#!/usr/bin/env python3
"""Capture compact real LLaDA selector states for the publication Q2 replay."""

from __future__ import annotations

import argparse
import json
import tomllib
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

if __package__:
    from scripts.exact_commit.run_q5_end_to_end import (
        Q5Parameters,
        Q5Task,
        _cached_checkpoint_metadata,
        _canonical_sha256,
        _check_generated_tokens,
        _configuration_parameters,
        _epic_literal_regex,
        _literal_grammar,
        _load_task_manifest,
        _package_version,
        _prepare_upstream_call,
    )
else:
    from run_q5_end_to_end import (
        Q5Parameters,
        Q5Task,
        _cached_checkpoint_metadata,
        _canonical_sha256,
        _check_generated_tokens,
        _configuration_parameters,
        _epic_literal_regex,
        _literal_grammar,
        _load_task_manifest,
        _package_version,
        _prepare_upstream_call,
    )

from mwpc_exact.epic_adapter.llada import PINNED_LLADA_PROFILE, build_llada_byte_adapter
from mwpc_exact.experiments import (
    capture_run_metadata,
    finalize_run_metadata,
    load_experiment_config,
    save_resolved_config,
)
from mwpc_research.q2_real_gap import build_real_snapshot_instance

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs/experiments/q2_real_state_capture_v2.toml"
SNAPSHOT_FILENAME = "q2-real-snapshots.jsonl"
METADATA_FILENAME = "capture-metadata.json"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _selected_parameters(parameters: Q5Parameters, task: Q5Task) -> Q5Parameters:
    _require(task.generation_length is not None, "Q2 source task requires a finite schedule")
    assert task.block_length is not None
    assert task.steps is not None
    assert task.schedule_budget is not None
    generation_length = task.generation_length
    return replace(
        parameters,
        generation_length=generation_length,
        block_length=task.block_length,
        steps=task.steps,
        schedule_budget=task.schedule_budget,
        warmup_runs=0,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-directory", type=Path)
    arguments = parser.parse_args()
    config_path = arguments.config.resolve()
    config = load_experiment_config(config_path)
    _require(config.publication_mode, "Q2 snapshot capture must use publication mode")
    parameters = config.parameters
    expected_fields = {
        "source_q5_config",
        "task_ids",
        "snapshot_selection",
        "snapshots_per_task_seed",
        "expected_snapshot_count",
        "proposal_policy",
        "support_policy",
        "weight_mode",
        "publication_bundle_id",
        "raw_output_root",
    }
    _require(set(parameters) == expected_fields, "unexpected Q2 capture parameters")
    _require(
        parameters["snapshot_selection"]
        == "last_four_successful_epic_selector_states_per_task_seed",
        "unsupported Q2 snapshot selection",
    )
    snapshots_per_pair = int(parameters["snapshots_per_task_seed"])
    _require(snapshots_per_pair == 4, "Q2 v2 requires four snapshots per task/seed")

    q5_path = REPOSITORY_ROOT / str(parameters["source_q5_config"])
    q5 = load_experiment_config(q5_path)
    q5_parameters = _configuration_parameters(q5.parameters, publication_mode=True)
    assert q5_parameters.task_manifest is not None
    tasks = _load_task_manifest(
        REPOSITORY_ROOT / q5_parameters.task_manifest,
        q5_parameters.task_ids,
    )
    _require(
        tuple(parameters["task_ids"]) == tuple(task.task_id for task in tasks),
        "Q2 capture task IDs differ from Q5 v4",
    )
    run_directory = (
        REPOSITORY_ROOT / str(parameters["raw_output_root"])
        if arguments.run_directory is None
        else arguments.run_directory.resolve()
    )
    run_directory.mkdir(parents=True, exist_ok=True)
    snapshot_path = run_directory / SNAPSHOT_FILENAME
    metadata_path = run_directory / METADATA_FILENAME
    _require(not snapshot_path.exists(), "refusing to overwrite Q2 snapshots")
    _require(not metadata_path.exists(), "refusing to overwrite Q2 capture metadata")
    save_resolved_config(config, run_directory)

    try:
        import torch
        from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig
    except ImportError as error:
        raise SystemExit("Q2 snapshot capture requires the Q5 CUDA environment") from error
    _require(torch.cuda.is_available(), "Q2 snapshot capture requires CUDA")
    torch.cuda.set_device(0)
    source_path = REPOSITORY_ROOT / "configs/exact_commit/t904_llada_live_smoke.toml"
    source = tomllib.loads(source_path.read_text(encoding="utf-8"))
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        config.tokenizer_id,
        revision=config.tokenizer_revision,
        trust_remote_code=False,
        local_files_only=True,
    )
    model = AutoModel.from_pretrained(
        config.model_id,
        revision=config.model_revision,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        quantization_config=quantization,
        device_map={"": 0},
        low_cpu_mem_usage=True,
        local_files_only=True,
    ).eval()
    _require(
        getattr(model.config, "_commit_hash", None) == config.model_revision,
        "Q2 capture model resolved to an unexpected revision",
    )
    base_pieces = tuple(
        tokenizer.convert_ids_to_tokens(token_id) for token_id in range(tokenizer.vocab_size)
    )
    tokenizer_adapter = build_llada_byte_adapter(
        base_pieces,
        model_vocabulary_size=int(model.config.vocab_size),
        profile=PINNED_LLADA_PROFILE,
    )

    from constrained_diffusion.constrain_utils import compile_lex_map
    from constrained_diffusion.eval.dllm.models.llada.generate_constrained import (
        preprocessed_generate_stuff,
    )
    from rustformlang.cfg import CFG

    grammar_hashes = tuple(
        _canonical_sha256(_literal_grammar(task.target_utf8.encode()).to_dict()) for task in tasks
    )
    metadata = capture_run_metadata(
        config,
        run_id=run_directory.name,
        repository_root=REPOSITORY_ROOT,
        grammar_sha256=grammar_hashes,
        require_rust=True,
        require_ml_stack=True,
        software_overrides={
            "pytorch": str(torch.__version__),
            "cuda_runtime": None if torch.version.cuda is None else str(torch.version.cuda),
        },
        additional={
            "source_q5_config": q5_path.relative_to(REPOSITORY_ROOT).as_posix(),
            "source_q5_config_sha256": q5.config_sha256,
            "snapshot_selection": parameters["snapshot_selection"],
            "publication_bundle_id": parameters["publication_bundle_id"],
            "loaded_checkpoint_shards": _cached_checkpoint_metadata(source),
            "bitsandbytes_version": _package_version("bitsandbytes"),
        },
    )

    captured: list[tuple[Q5Task, int, int, Mapping[str, object]]] = []
    pair_counts: dict[str, int] = {}
    for task in tasks:
        task_parameters = _selected_parameters(q5_parameters, task)
        target = task.target_utf8.encode("utf-8")
        grammar = _literal_grammar(target)
        prompt_text = tokenizer.apply_chat_template(
            [{"role": "user", "content": task.prompt_instruction}],
            add_generation_prompt=True,
            tokenize=False,
        )
        prompt_ids = tuple(int(value) for value in tokenizer(prompt_text)["input_ids"])
        prompt = torch.tensor([prompt_ids], device="cuda:0", dtype=torch.long)
        epic_grammar = CFG.from_text("S -> lexTarget", "S").to_normal_form()
        lex_map = compile_lex_map(
            {"lexTarget": _epic_literal_regex(task.target_utf8)}, subtokens={}
        )
        preprocessed = preprocessed_generate_stuff(tokenizer, epic_grammar, lex_map, trace=False)
        target_token_ids = tuple(
            int(value)
            for value in tokenizer(task.target_utf8, add_special_tokens=False)["input_ids"]
        )
        _require(
            tokenizer_adapter.detokenize_bytes(target_token_ids) == target,
            "Q2 capture target tokenization did not reproduce target bytes",
        )
        for seed in config.seeds:
            torch.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            observations: list[Mapping[str, object]] = []
            with _prepare_upstream_call(
                "epic",
                model=model,
                tokenizer=tokenizer,
                prompt=prompt,
                grammar=epic_grammar,
                lex_map=lex_map,
                preprocessed=preprocessed,
                parameters=task_parameters,
                regular_cover_observer=observations.append,
            ) as call:
                payload = call()
            _checker, syntactic_valid, functional_success = _check_generated_tokens(
                payload["generated_token_ids"],
                tokenizer_adapter=tokenizer_adapter,
                grammar=grammar,
                target=target,
            )
            _require(bool(payload["complete"]), "Q2 source EPIC generation was incomplete")
            _require(syntactic_valid and functional_success, "Q2 source output was invalid")
            _require(
                len(observations) >= snapshots_per_pair,
                "Q2 source run has too few successful EPIC selector states",
            )
            selected = observations[-snapshots_per_pair:]
            pair_counts[f"{task.task_id}:{seed}"] = len(selected)
            content_slots = len(target_token_ids)
            for rank, observation in enumerate(selected):
                captured.append((task, seed, rank, {**observation, "content_slots": content_slots}))

    _require(
        len(captured) == int(parameters["expected_snapshot_count"]),
        "Q2 capture produced the wrong snapshot count",
    )
    metadata = finalize_run_metadata(
        metadata,
        solver_status_counts={"snapshot_capture": {"complete": len(captured)}},
        publication_mode=True,
    )
    instances = []
    for task, seed, rank, observation in captured:
        content_slots = int(observation["content_slots"])
        instances.append(
            build_real_snapshot_instance(
                instance_id=f"q2-real-{task.task_id}-seed{seed}-state{rank}",
                grammar=_literal_grammar(task.target_utf8.encode("utf-8")),
                target_token_ids=tokenizer(task.target_utf8, add_special_tokens=False)["input_ids"],
                canvas_token_ids=observation["canvas_token_ids"][:content_slots],  # type: ignore[index]
                predicted_token_ids=observation["predicted_token_ids"][:content_slots],  # type: ignore[index]
                confidence_values=observation["confidence_values"][:content_slots],  # type: ignore[index]
                source_adapter=tokenizer_adapter,
                decode_actual_token=lambda token_id: tokenizer.decode(
                    [token_id],
                    skip_special_tokens=False,
                    clean_up_tokenization_spaces=False,
                ),
                metadata={
                    "task_id": task.task_id,
                    "seed": seed,
                    "selected_state_rank": rank,
                    "source_selector": "epic_regular_cover",
                    "source_run_metadata": metadata,
                    "source_selected_positions": observation["selected_positions"],
                    "source_selected_token_ids": observation["selected_token_ids"],
                },
            )
        )
    with snapshot_path.open("x", encoding="utf-8") as output:
        for instance in instances:
            output.write(instance.to_json(indent=None) + "\n")
    metadata_path.write_text(
        json.dumps(
            {
                "artifact_kind": "mwpc_q2_real_snapshot_capture_metadata",
                "schema_version": 1,
                "snapshot_count": len(instances),
                "pair_counts": dict(sorted(pair_counts.items())),
                "snapshot_sha256": [instance.fingerprint for instance in instances],
                "run_metadata": metadata,
            },
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "snapshot_path": str(snapshot_path),
                "metadata_path": str(metadata_path),
                "snapshot_count": len(instances),
                "pair_counts": pair_counts,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
