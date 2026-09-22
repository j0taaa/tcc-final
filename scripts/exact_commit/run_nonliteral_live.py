#!/usr/bin/env python3
"""Supervised, matched-budget LLaDA study; every failed job remains a row.

The supervisor can kill only its own worker. Model loading, grammar setup,
warmup and state capture are outside timed generation. An unresponsive native
baseline is killed and the remaining jobs resume in a fresh worker.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from contextlib import nullcontext
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

from scripts.exact_commit.run_q5_end_to_end import (
    _configuration_parameters,
    _prepare_exact_call,
    _prepare_upstream_call,
)

from mwpc_exact.epic_adapter.llada import (
    PINNED_LLADA_PROFILE,
    _permitted_token_ids,
    _ranked_support_from_model_logits,
    build_llada_byte_adapter,
)
from mwpc_exact.experiments import capture_run_metadata, load_experiment_config
from mwpc_exact.experiments.metadata import canonical_json_sha256
from mwpc_exact.proposal_policy import ProposalWeightMode, build_schedule_proposals
from mwpc_research.live_evidence import (
    checked_generation,
    declared_schedule,
    live_jobs,
    summarize_live_rows,
)
from mwpc_research.recursive_tasks import RecursiveTask, epic_grammar_spec, recursive_grammar

ROOT = Path(__file__).resolve().parents[2]


def observed_forward(torch, model, tokens, *args, **kwargs):
    # Baseline resampling modifies logits after this call. Inference tensors
    # cannot be modified there; no_grad preserves the baseline's own contract.
    with torch.no_grad():
        return model(tokens, *args, **kwargs)


def write_json(path, value, *, exclusive=True):
    with path.open("x" if exclusive else "w", encoding="utf-8") as output:
        json.dump(value, output, allow_nan=False, sort_keys=True)
        output.write("\n")


def progress(directory, job, phase):
    temporary = directory / "progress.tmp"
    write_json(
        temporary, {"job": job, "phase": phase, "started": time.monotonic()}, exclusive=False
    )
    temporary.replace(directory / "progress.json")


def capture_state(directory, job, index, tokens, logits, adapter, prompt_length, config):
    import torch

    slots = int(config.parameters["slots"])
    permitted = _permitted_token_ids(adapter, PINNED_LLADA_PROFILE.eos_policy)
    ranked = _ranked_support_from_model_logits(
        logits[0],
        prompt_length=prompt_length,
        generation_length=slots,
        vocabulary_size=adapter.vocabulary_size,
        permitted_token_ids=permitted,
        max_k=config.support_k_max,
    )
    canvas = tuple(
        None if token == PINNED_LLADA_PROFILE.mask_token_id else token
        for token in tokens[0, prompt_length:].tolist()
    )
    predictions = logits[0, prompt_length:].argmax(dim=-1)
    probabilities = torch.softmax(logits[0, prompt_length:].to(torch.float64), dim=-1)
    confidence = probabilities.gather(1, predictions[:, None]).squeeze(1)
    budget = declared_schedule(slots, int(config.parameters["steps"]))["proposal_budgets"][index]
    batch = build_schedule_proposals(
        predicted_token_ids=tuple(predictions.tolist()),
        confidence_values=tuple(confidence.tolist()),
        schedule_mask=tuple(token is None for token in canvas),
        k_s=budget,
        weight_mode=ProposalWeightMode.CONFIDENCE,
    )
    rankings = ranked.token_ids_by_position
    policy = PINNED_LLADA_PROFILE.eos_policy
    represented = {
        *(token for row in rankings for token in row),
        *(p.token_id for p in batch.proposals),
        *(token for token in canvas if token is not None),
        *policy.termination_token_ids,
        policy.pad_token_id,
    }
    rank_tensor = torch.tensor(rankings, device=logits.device)
    snapshot = {
        "snapshot_id": f"{job['job_id']}-forward{index}",
        "family": job["task"]["family"],
        "task_id": job["task"]["task_id"],
        "seed": job["seed"],
        "source_strategy": "unconstrained",
        "forward_index": index,
        "canvas": canvas,
        "rankings": rankings,
        "proposals": [asdict(p) for p in batch.proposals],
        "ranked_logits": logits[0, prompt_length:].gather(1, rank_tensor).tolist(),
        "ranked_probabilities": probabilities.gather(1, rank_tensor).tolist(),
        "emissions": {
            str(token): None if adapter.emissions[token] is None else adapter.emissions[token].hex()
            for token in represented
        },
        "termination_token_ids": policy.termination_token_ids,
        "pad_token_id": policy.pad_token_id,
        "model_revision": config.model_revision,
        "tokenizer_revision": config.tokenizer_revision,
        "target_injected": False,
    }
    write_json(directory / "snapshots" / f"{snapshot['snapshot_id']}.json", snapshot)


def worker(directory, config):
    import psutil
    import torch
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    jobs = json.loads((directory / "jobs.json").read_text())
    pending = [job for job in jobs if not (directory / "rows" / f"{job['job_id']}.json").exists()]
    if not pending:
        return
    progress(directory, pending[0], "model_load")
    torch.set_num_threads(config.cpu_threads)
    tokenizer = AutoTokenizer.from_pretrained(
        config.tokenizer_id,
        revision=config.tokenizer_revision,
        trust_remote_code=True,
        local_files_only=True,
    )
    model = AutoModel.from_pretrained(
        config.model_id,
        revision=config.model_revision,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        local_files_only=True,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
    ).eval()
    if model.config._commit_hash != config.model_revision:
        raise RuntimeError("resolved model revision differs from frozen config")
    adapter = build_llada_byte_adapter(
        tuple(tokenizer.convert_ids_to_tokens(i) for i in range(tokenizer.vocab_size)),
        model_vocabulary_size=model.config.vocab_size,
    )
    parameters = _configuration_parameters(
        load_experiment_config(
            ROOT / "configs/experiments/q5_structured_publication_v4.toml"
        ).parameters,
        publication_mode=True,
    )
    slots, steps = int(config.parameters["slots"]), int(config.parameters["steps"])
    parameters = replace(
        parameters,
        generation_length=slots,
        block_length=slots,
        steps=steps,
        schedule_budget=slots,
        max_resamples=32,
    )
    grammar_cache = {}
    process = psutil.Process()
    for job in pending:
        progress(directory, job, "setup")
        task = RecursiveTask(
            **{**job["task"], "required_leaves": tuple(job["task"]["required_leaves"])}
        )
        prompt_text = tokenizer.apply_chat_template(
            [{"role": "user", "content": task.prompt}],
            tokenize=False,
            add_generation_prompt=True,
        )
        prompt_ids = tuple(tokenizer(prompt_text)["input_ids"])
        prompt = torch.tensor([prompt_ids], device="cuda:0")
        grammar = recursive_grammar(task.family)
        row = {
            **job,
            "grammar_sha256": canonical_json_sha256(grammar.to_dict()),
            "schedule": declared_schedule(slots, steps),
        }
        started = None
        try:
            if job["strategy"] in {"serial", "epic"} and task.family not in grammar_cache:
                from constrained_diffusion.constrain_utils import compile_lex_map
                from constrained_diffusion.eval.dllm.models.llada.generate_constrained import (
                    preprocessed_generate_stuff,
                )
                from rustformlang.cfg import CFG

                text, lexemes = epic_grammar_spec(task.family)
                cfg = CFG.from_text(text, "S").to_normal_form()
                lex_map = compile_lex_map(lexemes, subtokens={})
                preprocessed = preprocessed_generate_stuff(tokenizer, cfg, lex_map, trace=False)
                grammar_cache[task.family] = cfg, lex_map, preprocessed
            torch.manual_seed(job["seed"])
            torch.cuda.manual_seed_all(job["seed"])
            warmup_tokens = torch.tensor(
                [list(prompt_ids) + [PINNED_LLADA_PROFILE.mask_token_id] * slots], device="cuda:0"
            )
            for _ in range(int(config.parameters["warmup_forwards"])):
                with torch.inference_mode():
                    model(warmup_tokens)
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()

            class ObservedModel:
                def __init__(self, active_job, prefix_length):
                    self.job = active_job
                    self.prefix_length = prefix_length
                    self.count = 0
                    self.forward_seconds = 0.0

                def __getattr__(self, name):
                    return getattr(model, name)

                def __call__(self, tokens, *args, **kwargs):
                    torch.cuda.synchronize()
                    begin = time.perf_counter()
                    output = observed_forward(torch, model, tokens, *args, **kwargs)
                    torch.cuda.synchronize()
                    self.forward_seconds += time.perf_counter() - begin
                    if (
                        self.job["strategy"] == "capture"
                        and self.count in config.parameters["capture_forward_indices"]
                    ):
                        capture_state(
                            directory,
                            self.job,
                            self.count,
                            tokens,
                            output.logits,
                            adapter,
                            self.prefix_length,
                            config,
                        )
                    self.count += 1
                    return output

            observed = ObservedModel(job, len(prompt_ids))
            if job["strategy"] == "exact":
                context = nullcontext(
                    _prepare_exact_call(
                        torch=torch,
                        model=observed,
                        tokenizer=tokenizer,
                        prompt_ids=prompt_ids,
                        tokenizer_adapter=adapter,
                        grammar=grammar,
                        parameters=parameters,
                        support_initial_k=config.support_top_k,
                        support_k_max=config.support_k_max,
                        solver_timeout_seconds=config.solver_timeout_seconds,
                    )
                )
            else:
                baseline_strategy = (
                    "unconstrained" if job["strategy"] == "capture" else job["strategy"]
                )
                cfg, lex_map, preprocessed = grammar_cache.get(task.family, (None, None, None))
                context = _prepare_upstream_call(
                    baseline_strategy,
                    model=observed,
                    tokenizer=tokenizer,
                    prompt=prompt,
                    grammar=cfg,
                    lex_map=lex_map,
                    preprocessed=preprocessed,
                    parameters=parameters,
                )
            with context as call:
                progress(directory, job, "generation")
                torch.cuda.synchronize()
                started = time.perf_counter()
                payload = call()
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - started
            checked = checked_generation(
                task,
                payload["generated_token_ids"],
                adapter,
                PINNED_LLADA_PROFILE.eos_policy.termination_token_ids,
                PINNED_LLADA_PROFILE.mask_token_id,
            )
            row.update(
                {
                    **checked,
                    "runtime_seconds": elapsed,
                    "execution_status": "complete" if checked["complete"] else "incomplete",
                    "model_forward_count": observed.count,
                    "model_forward_seconds": observed.forward_seconds,
                    "solver_status": payload.get("solver_status"),
                    "payload": payload,
                    "peak_cuda_bytes": torch.cuda.max_memory_allocated(),
                    "process_rss_bytes": process.memory_info().rss,
                }
            )
            if job["strategy"] == "exact" and payload.get("solver_status") == "timeout":
                row["execution_status"] = "timeout"
        except Exception as error:
            row.update(
                {
                    "execution_status": "error",
                    "error": f"{type(error).__name__}: {error}",
                    "runtime_seconds": None if started is None else time.perf_counter() - started,
                }
            )
        write_json(directory / "rows" / f"{job['job_id']}.json", row)
        print(json.dumps({"job": job["job_id"], "status": row["execution_status"]}), flush=True)


def supervise(directory, config_path, config):
    jobs = json.loads((directory / "jobs.json").read_text())
    deadline = time.monotonic() + config.run_timeout_seconds
    while any(not (directory / "rows" / f"{job['job_id']}.json").exists() for job in jobs):
        if time.monotonic() >= deadline:
            for job in jobs:
                path = directory / "rows" / f"{job['job_id']}.json"
                if not path.exists():
                    write_json(
                        path,
                        {**job, "execution_status": "not_run_run_budget", "runtime_seconds": None},
                    )
            break
        (directory / "progress.json").unlink(missing_ok=True)
        with (directory / "worker.log").open("a") as log:
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "scripts.exact_commit.run_nonliteral_live",
                    "--worker",
                    "--config",
                    str(config_path),
                    "--run-directory",
                    str(directory),
                ],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1"},
            )
            began = time.monotonic()
            observation = None
            while child.poll() is None:
                path = directory / "progress.json"
                if path.exists():
                    observation = json.loads(path.read_text())
                limit = float(
                    config.parameters["generation_timeout_seconds"]
                    if observation and observation["phase"] == "generation"
                    else config.parameters["setup_timeout_seconds"]
                )
                origin = observation["started"] if observation else began
                if time.monotonic() - origin >= limit or time.monotonic() >= deadline:
                    child.kill()
                    child.wait()
                    if observation:
                        job = observation["job"]
                        destination = directory / "rows" / f"{job['job_id']}.json"
                        if not destination.exists():
                            write_json(
                                destination,
                                {
                                    **job,
                                    "execution_status": "timeout",
                                    "runtime_seconds": None,
                                    "censoring_seconds": limit,
                                    "timeout_phase": observation["phase"],
                                    "solver_status": "timeout"
                                    if job["strategy"] == "exact"
                                    else None,
                                },
                            )
                    break
                time.sleep(0.2)
            if child.returncode and observation:
                path = directory / "rows" / f"{observation['job']['job_id']}.json"
                if not path.exists():
                    write_json(
                        path,
                        {
                            **observation["job"],
                            "execution_status": "error",
                            "runtime_seconds": None,
                            "worker_exit_code": child.returncode,
                        },
                    )
            elif child.returncode and observation is None:
                raise RuntimeError("worker failed before startup; inspect worker.log")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/experiments/m17_nonliteral_pilot_v1.toml"
    )
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    config = load_experiment_config(args.config)
    directory = args.run_directory or ROOT / str(
        config.parameters["raw_output_root"]
    ) / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    if args.worker:
        worker(directory, config)
        return
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "rows").mkdir()
    (directory / "snapshots").mkdir()
    hashes = [
        canonical_json_sha256(recursive_grammar(f).to_dict())
        for f in ("brackets", "arithmetic", "nested_json")
    ]
    import importlib.metadata

    import torch

    metadata = capture_run_metadata(
        config,
        run_id=directory.name,
        repository_root=ROOT,
        grammar_sha256=hashes,
        require_rust=True,
        require_ml_stack=True,
        software_overrides={"cuda_runtime": torch.version.cuda},
        additional={
            "live_dependency_versions": {
                name: importlib.metadata.version(name) for name in ("bitsandbytes", "tokenizers")
            }
        },
    )
    if metadata["git_dirty"]:
        raise RuntimeError("commit the generating code/config before live measurements")
    write_json(directory / "metadata.json", metadata)
    (directory / "config.toml").write_bytes(args.config.read_bytes())
    jobs = live_jobs(str(config.parameters["split"]), config.seeds, config.repetitions)
    write_json(directory / "jobs.json", jobs)
    supervise(directory, args.config.resolve(), config)
    rows = [json.loads((directory / "rows" / f"{job['job_id']}.json").read_text()) for job in jobs]
    metadata["solver_status_counts"] = dict(Counter(str(row.get("solver_status")) for row in rows))
    with (directory / "rows.jsonl").open("x") as output:
        for row in rows:
            output.write(json.dumps({**row, "run_metadata": metadata}, allow_nan=False) + "\n")
    write_json(directory / "summary.json", summarize_live_rows(rows))
    print(json.dumps({"run_directory": str(directory), "rows": len(rows)}))


if __name__ == "__main__":
    main()
