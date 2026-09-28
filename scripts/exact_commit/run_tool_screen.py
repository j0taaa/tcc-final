#!/usr/bin/env python3
"""Opt-in CUDA discovery experiment: actual LLaDA, exhaustive finite catalog.

This is not an EPIC benchmark or a production-parser latency measurement.
Every call is retained, and expected answers are used only after decoding.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from mwpc_research.tool_screen import (
    operand_preserving_indices,
    screen_tasks,
    select_catalog,
    tool_catalog,
)

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    raw_config = args.config.read_bytes()
    config = json.loads(raw_config)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    if dirty:
        raise SystemExit("Freeze source/config in a clean local commit before measurement")
    output = ROOT / config["output_root"] / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output.mkdir(parents=True, exist_ok=False)
    (output / "config.json").write_bytes(raw_config)

    import torch
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    torch.set_num_threads(config["cpu_threads"])
    torch.manual_seed(config["seed"])
    torch.cuda.manual_seed_all(config["seed"])
    tokenizer = AutoTokenizer.from_pretrained(
        config["model_id"],
        revision=config["revision"],
        local_files_only=True,
    )
    model = AutoModel.from_pretrained(
        config["model_id"],
        revision=config["revision"],
        local_files_only=True,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        ),
    ).eval()
    assert model.config._commit_hash == config["revision"]
    eos, mask = 126081, 126336
    family = config.get("family", "simple")
    catalog = tool_catalog(family)
    paths = []
    for call in catalog:
        tokens = tokenizer.encode(call, add_special_tokens=False)
        assert len(tokens) < config["slots"]
        paths.append(tuple(tokens + [eos] * (config["slots"] - len(tokens))))
    rows = [sorted({path[p] for path in paths}) for p in range(config["slots"])]
    row_tensors = [torch.tensor(row, device="cuda") for row in rows]
    support_hash = hashlib.sha256(json.dumps(paths).encode()).hexdigest()
    metadata = {
        "git_commit": commit,
        "seed": config["seed"],
        "model_id": config["model_id"],
        "model_revision": config["revision"],
        "tokenizer_revision": config["revision"],
        "quantization": config["quantization"],
        "config_sha256": hashlib.sha256(raw_config).hexdigest(),
        "grammar_hash": hashlib.sha256(json.dumps(catalog).encode()).hexdigest(),
        "support_sha256": support_hash,
        "support_policy": config["support"],
        "exactness_scope": f"exact_on_support: {len(paths)} canonical legal token paths",
        "hardware": torch.cuda.get_device_name(0),
        "python": platform.python_version(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "bitsandbytes", "tokenizers")
        },
        "implementation": "exhaustive_catalog_oracle_not_production_CFG_parser",
        "limitations": [
            "exploratory",
            "small synthetic tool requests",
            "no EPIC baseline",
            "one quantized model",
            "canonical tokenizations only",
        ],
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (output / "support.json").write_text(json.dumps({"catalog": catalog, "paths": paths}) + "\n")
    all_paths = paths
    instruction = (
        "You control a calculator using function calls. Available functions: "
        "add(a,b), sub(a,b), mul(a,b), neg(a), abs(a). "
        "Arguments are single digits 0 to 9. "
        "Return ONLY the requested function call, without spaces or explanation. "
        "Do not calculate its result.\nRequest: "
    )
    if family == "nested":
        instruction = (
            "Translate the request to a nested calculator function call. Functions: "
            "add(a,b), sub(a,b), mul(a,b), neg(a), abs(a). "
            "Literal arguments are digits 0 to 3. Calls may be nested once. "
            "Preserve every requested operation; do NOT simplify or calculate. "
            "Return ONLY the call, without spaces or explanation.\nRequest: "
        )
    warmup_prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": instruction + "Add 1 and 2."}],
        add_generation_prompt=True,
        tokenize=True,
    )
    with torch.inference_mode():
        for _ in range(2):
            model(torch.tensor([warmup_prompt + [mask] * config["slots"]], device="cuda"))
    torch.cuda.synchronize()
    for budget in config["proposal_budgets"]:
        for task_index, task in enumerate(
            screen_tasks(config["seed"], config["task_count"], family)
        ):
            active_indices = list(range(len(catalog)))
            if config.get("preserve_operands", False):
                active_indices = list(operand_preserving_indices(catalog, task["instruction"]))
            paths = [all_paths[i] for i in active_indices]
            rows = [sorted({path[p] for path in paths}) for p in range(config["slots"])]
            row_tensors = [torch.tensor(row, device="cuda") for row in rows]
            prompt = tokenizer.apply_chat_template(
                [{"role": "user", "content": instruction + task["instruction"]}],
                add_generation_prompt=True,
                tokenize=True,
            )
            methods = config["methods"]
            offset = task_index % len(methods)
            for method in methods[offset:] + methods[:offset]:
                generator = torch.Generator(device="cuda")
                generator.manual_seed(config["seed"] + task_index + 1000 * budget)
                canvas: list[int | None] = [None] * config["slots"]
                trace = []
                status = "forward_limit"
                torch.cuda.synchronize()
                start = time.perf_counter()
                for step in range(config["max_forwards"]):
                    if time.perf_counter() - start >= config["max_generation_seconds"]:
                        status = "timeout"
                        break
                    x = torch.tensor(
                        [prompt + [mask if t is None else t for t in canvas]], device="cuda"
                    )
                    torch.cuda.synchronize()
                    forward_start = time.perf_counter()
                    with torch.inference_mode():
                        logits = model(x).logits[0, len(prompt) :].float()
                    torch.cuda.synchronize()
                    forward_seconds = time.perf_counter() - forward_start
                    candidate_start = time.perf_counter()
                    proposals = []
                    for p, row in enumerate(rows):
                        # Draw even for fixed positions: equal step/position shares randomness.
                        temperature = config.get("temperature", 0.0)
                        noise = None
                        if temperature > 0:
                            uniform = torch.rand(len(row), device="cuda", generator=generator)
                            noise = -torch.log(-torch.log(uniform.clamp(1e-7, 1 - 1e-7)))
                        if canvas[p] is not None:
                            continue
                        values = logits[p, row_tensors[p]]
                        sampled = values if noise is None else values / temperature + noise
                        best = int(sampled.argmax().item())
                        probability = float(
                            torch.exp(values[best] - torch.logsumexp(logits[p], dim=-1)).item()
                        )
                        proposals.append((p, row[best], probability))
                    proposals.sort(key=lambda item: (-item[2], item[0]))
                    proposals = proposals[:budget]
                    candidate_seconds = time.perf_counter() - candidate_start
                    selection_start = time.perf_counter()
                    selection = select_catalog(paths, canvas, proposals, method=method)
                    selector_seconds = time.perf_counter() - selection_start
                    # Paired counterfactual at identical logits/state, excluded from main timing.
                    diagnostic_start = time.perf_counter()
                    other = select_catalog(
                        paths, canvas, proposals, method="greedy" if method == "exact" else "exact"
                    )
                    diagnostic_seconds = time.perf_counter() - diagnostic_start
                    witness = paths[selection.witness_index]
                    before = list(canvas)
                    commits = list(selection.selected_positions)
                    fallback = not commits
                    if fallback:
                        # Same deterministic progress rule for both methods, explicitly unscored.
                        commits = [next(p for p, token in enumerate(canvas) if token is None)]
                    for p in commits:
                        canvas[p] = witness[p]
                    assert any(
                        all(t is None or t == path[p] for p, t in enumerate(canvas))
                        for path in paths
                    )
                    trace.append(
                        {
                            "step": step,
                            "canvas_before": before,
                            "proposals": proposals,
                            "witness_index": selection.witness_index,
                            "selected_positions": selection.selected_positions,
                            "objective": selection.objective,
                            "other_objective": other.objective,
                            "other_witness_index": other.witness_index,
                            "committed_positions": commits,
                            "fallback": fallback,
                            "ordinary_commits": sum(witness[p] != eos for p in commits),
                            "forward_seconds": forward_seconds,
                            "candidate_seconds": candidate_seconds,
                            "selector_seconds": selector_seconds,
                            "diagnostic_seconds": diagnostic_seconds,
                        }
                    )
                    if all(t is not None for t in canvas):
                        status = "complete"
                        break
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - start
                complete = status == "complete"
                decoded = tokenizer.decode(
                    [mask if t is None else t for t in canvas], skip_special_tokens=True
                )
                record = {
                    **metadata,
                    "task": task,
                    "method": method,
                    "budget": budget,
                    "active_catalog_indices": active_indices,
                    "status": status,
                    "solver_status_counts": {
                        "optimal_on_catalog" if method == "exact" else "feasible_on_catalog": len(
                            trace
                        )
                    },
                    "output": decoded,
                    "correct": complete and decoded == task["expected"],
                    "syntax_valid": complete and decoded in catalog,
                    "forwards": len(trace),
                    "elapsed_with_diagnostics_seconds": elapsed,
                    "elapsed_excluding_shadow_seconds": elapsed
                    - sum(t["diagnostic_seconds"] for t in trace),
                    "trace": trace,
                }
                with (output / "results.jsonl").open("a") as stream:
                    stream.write(json.dumps(record, allow_nan=False) + "\n")
                print(
                    json.dumps(
                        {
                            k: record[k]
                            for k in ("method", "budget", "output", "correct", "forwards")
                        }
                    ),
                    flush=True,
                )
    print(f"ARTIFACT_DIR={output}", flush=True)


if __name__ == "__main__":
    main()
