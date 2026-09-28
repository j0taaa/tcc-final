#!/usr/bin/env python3
"""Frozen M24 live policy screen. No expected answer is passed into decoding."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime
from math import fsum
from pathlib import Path

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    Proposal,
    SelectionStatus,
    select_exact_mwpc,
    select_greedy_exact_feasibility,
)
from mwpc_exact.commit_gate import select_stable_commit
from mwpc_exact.profiling import ComponentProfiler
from mwpc_research.tool_parser import catalog_byte_grammar, production_input
from mwpc_research.tool_screen import (
    execute_tool_call,
    normalize_tool_call,
    operand_preserving_indices,
    tool_catalog,
)

ROOT = Path(__file__).resolve().parents[2]
EOS, MASK = 126081, 126336
INSTRUCTION = (
    "Translate the request to a nested calculator function call. Functions: "
    "add(a,b), sub(a,b), mul(a,b), neg(a), abs(a). "
    "Literal arguments are digits 0 to 3. Calls may be nested once. "
    "Preserve every requested operation; do NOT simplify or calculate. "
    "Return ONLY the call, without spaces or explanation.\nRequest: "
)


def fallback_positions(result, proposals):
    selected = set(result.selected_proposal_ids)
    candidates = [p for p in proposals if p.proposal_id in selected]
    if candidates:
        return [max(candidates, key=lambda p: (p.weight, -p.position)).position]
    return []


def decode(*, model, tokenizer, request, calls, paths, grammar, rows, adapter, policy, config):
    import torch

    messages = [{"role": "user", "content": request}]
    prompt = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=True)
    row_tensors = [torch.tensor(row, device="cuda") for row in rows]
    canvas = [None] * config["slots"]
    trace, status, failure = [], "forward_limit", None
    forwards = 0
    torch.cuda.synchronize()
    started = time.perf_counter()
    for step in range(config["max_forwards"]):
        if time.perf_counter() - started >= config["max_generation_seconds"]:
            status = "timeout"
            break
        tokens = torch.tensor([prompt + [MASK if t is None else t for t in canvas]], device="cuda")
        torch.cuda.synchronize()
        begin = time.perf_counter()
        with torch.inference_mode():
            logits = model(tokens).logits[0, len(prompt) :].float()
        torch.cuda.synchronize()
        forward_seconds = time.perf_counter() - begin
        forwards += 1
        begin = time.perf_counter()
        candidates, distributions = [], []
        log_z = torch.logsumexp(logits, dim=-1)
        for p, row in enumerate(rows):
            values = logits[p, row_tensors[p]]
            log_probs = (values - log_z[p]).tolist()
            distributions.append(log_probs)
            if canvas[p] is not None:
                continue
            order = sorted(range(len(row)), key=lambda i: (-log_probs[i], row[i]))
            for i in order[: policy.get("top_k", 1)]:
                candidates.append((p, row[i], float(torch.exp(values[i] - log_z[p]).item())))
        candidates.sort(key=lambda c: (-c[2], c[0], c[1]))
        candidates = candidates[: policy.get("proposal_budget", len(candidates))]
        proposals = tuple(Proposal(i, p, t, w) for i, (p, t, w) in enumerate(candidates))
        candidate_seconds = time.perf_counter() - begin
        begin = time.perf_counter()
        state = replace(
            production_input(grammar, canvas, (), rows, adapter, EOS), proposals=proposals
        )
        support_seconds = time.perf_counter() - begin
        profile = ComponentProfiler(enabled=True)
        begin = time.perf_counter()
        gate_data, native = None, None
        kind = policy["kind"]
        remaining = min(
            config["selection_timeout_seconds"],
            config["max_generation_seconds"] - (begin - started),
        )
        if remaining <= 0:
            status = "timeout"
            break
        if kind == "margin":
            gate = select_stable_commit(
                state,
                tolerance=policy["relative_tolerance"] * fsum(p.weight for p in proposals),
                total_timeout_seconds=remaining,
                profiler=profile,
            )
            result = gate.optimizer
            gate_data = {
                "status": gate.status.value,
                "certified_positions": list(gate.certified_positions),
                "progress_fallback": gate.progress_fallback,
                "queries": [
                    {
                        "position": q.position,
                        "forced": q.forced_on_support,
                        "alternative_score": q.alternative_score,
                        "margin": q.margin,
                        "result": q.result.to_dict(),
                    }
                    for q in gate.queries
                ],
            }
            if gate.status is not SelectionStatus.OPTIMAL:
                status, failure = gate.status.value, gate_data
                break
            commits = list(gate.committed_positions)
            fallback = gate.progress_fallback
        elif kind == "catalog_map":
            # Explicit canonical-only MAP control, not production CFG optimization.
            feasible = [
                path
                for path in paths
                if all(t is None or t == path[p] for p, t in enumerate(canvas))
            ]
            if not feasible:
                status = "infeasible_on_support"
                break
            scores = [
                fsum(
                    distributions[p][rows[p].index(t)]
                    for p, t in enumerate(path)
                    if canvas[p] is None
                )
                for path in feasible
            ]
            witness = list(feasible[max(range(len(feasible)), key=lambda i: scores[i])])
            free = [p for p, t in enumerate(canvas) if t is None]
            free.sort(key=lambda p: (-distributions[p][rows[p].index(witness[p])], p))
            commits = free[: policy["commit_cap"]]
            result, fallback = None, False
        else:
            result = (
                select_greedy_exact_feasibility(
                    state, total_timeout_seconds=remaining, reuse_witness=True, profiler=profile
                )
                if kind == "greedy"
                else select_exact_mwpc(state, timeout_seconds=remaining, profiler=profile)
            )
            if result.score is None:
                status, failure = result.status.value, result.to_dict()
                break
            selected = set(result.selected_proposal_ids)
            accepted = [p for p in proposals if p.proposal_id in selected]
            if kind == "confidence":
                accepted = [p for p in accepted if p.weight >= policy["threshold"]]
            accepted.sort(key=lambda p: (-p.weight, p.position))
            commits = list(dict.fromkeys(p.position for p in accepted))[
                : policy.get("commit_cap", len(canvas))
            ]
            fallback = not commits
            if fallback:
                commits = fallback_positions(result, proposals) or [canvas.index(None)]
        if result is not None:
            native = result.to_dict()
            witness = list(result.witness_token_ids)
        selection_seconds = time.perf_counter() - begin
        if time.perf_counter() - started >= config["max_generation_seconds"]:
            status = "timeout"
            break
        begin = time.perf_counter()
        before = list(canvas)
        for p in commits:
            assert canvas[p] is None
            canvas[p] = witness[p]
        update_seconds = time.perf_counter() - begin
        trace.append(
            {
                "step": step,
                "canvas_before": before,
                "proposals": candidates,
                "domain_log_probabilities": distributions,
                "witness_token_ids": witness,
                "production_result": native,
                "gate": gate_data,
                "committed_positions": commits,
                "fallback": fallback,
                "ordinary_commits": sum(witness[p] != EOS for p in commits),
                "forward_seconds": forward_seconds,
                "candidate_seconds": candidate_seconds,
                "support_seconds": support_seconds,
                "selector_seconds": selection_seconds,
                "update_seconds": update_seconds,
                "profile": profile.snapshot().to_dict(),
            }
        )
        if all(t is not None for t in canvas):
            status = "complete"
            break
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    return {
        "status": status,
        "failure": failure,
        "forwards": forwards,
        "output": tokenizer.decode(
            [MASK if t is None else t for t in canvas], skip_special_tokens=True
        ),
        "token_ids": canvas,
        "trace": trace,
        "elapsed_seconds": elapsed,
        "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated(),
        "solver_status_counts": dict(
            Counter(
                t["production_result"]["status"] if t["production_result"] else "catalog_map"
                for t in trace
            )
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    raw_config = args.config.read_bytes()
    config = json.loads(raw_config)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise SystemExit("Freeze source/config in a clean commit before measurement")
    import torch
    from epic_tool_runner import run_epic
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    torch.set_num_threads(config["cpu_threads"])
    torch.manual_seed(config["seed"])
    torch.cuda.manual_seed_all(config["seed"])
    tokenizer = AutoTokenizer.from_pretrained(
        config["model_id"], revision=config["revision"], local_files_only=True
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
    catalog = tool_catalog("nested")
    paths = []
    for call in catalog:
        tokens = tokenizer.encode(call, add_special_tokens=False)
        assert len(tokens) < config["slots"]
        paths.append(tokens + [EOS] * (config["slots"] - len(tokens)))
    emissions = {
        t: tokenizer.decode([t], clean_up_tokenization_spaces=False).encode()
        for path in paths
        for t in path
        if t != EOS
    }
    adapter = CompositionalByteLevelAdapter(
        tuple(emissions.get(i) for i in range(model.config.vocab_size))
    )
    for call, path in zip(catalog, paths, strict=True):
        assert b"".join(emissions[t] for t in path if t != EOS).decode() == call
    output = ROOT / config["output_root"] / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output.mkdir(parents=True, exist_ok=False)
    metadata = {
        "git_commit": commit,
        "seed": config["seed"],
        "model_id": config["model_id"],
        "model_revision": config["revision"],
        "tokenizer_revision": config["revision"],
        "config_sha256": hashlib.sha256(raw_config).hexdigest(),
        "hardware": torch.cuda.get_device_name(0),
        "quantization": config["quantization"],
        "python": platform.python_version(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "bitsandbytes", "tokenizers")
        },
        "upstream_epic_commit": subprocess.check_output(
            ["git", "-C", "vendor/EPIC-Decoding", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "phase": config["phase"],
        "grammar_hash": hashlib.sha256(json.dumps(catalog).encode()).hexdigest(),
        "support_sha256": hashlib.sha256(json.dumps(paths).encode()).hexdigest(),
    }
    for name, value in (
        ("metadata", metadata),
        ("support", {"catalog": catalog, "paths": paths}),
        ("token_emissions", {t: list(b) for t, b in emissions.items()}),
    ):
        (output / f"{name}.json").write_text(json.dumps(value) + "\n")
    (output / "config.json").write_bytes(raw_config)
    warmup = tokenizer.apply_chat_template(
        [{"role": "user", "content": INSTRUCTION + "Add 1 and 2."}],
        add_generation_prompt=True,
        tokenize=True,
    )
    with torch.inference_mode():
        for _ in range(2):
            model(torch.tensor([warmup + [MASK] * config["slots"]], device="cuda"))
    torch.cuda.synchronize()
    for task_index, task in enumerate(config["tasks"]):
        begin = time.perf_counter()
        indices = list(operand_preserving_indices(catalog, task["instruction"]))
        active_paths = [paths[i] for i in indices]
        calls = [catalog[i] for i in indices]
        rows = [sorted({path[p] for path in active_paths}) for p in range(config["slots"])]
        grammar = catalog_byte_grammar(calls)
        setup = time.perf_counter() - begin
        request = INSTRUCTION + task["instruction"]
        policies = config["policies"]
        offset = task_index % len(policies)
        for policy in policies[offset:] + policies[:offset]:
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
            method_started = time.perf_counter()
            if policy["kind"] == "epic":
                prompt = tokenizer.apply_chat_template(
                    [{"role": "user", "content": request}],
                    add_generation_prompt=True,
                    tokenize=True,
                )
                outcome = run_epic(
                    model=model,
                    tokenizer=tokenizer,
                    prompt=prompt,
                    grammar=grammar,
                    rows=rows,
                    calls=calls,
                    config=config,
                    method=policy["method"],
                )
                outcome["elapsed_seconds"] = outcome["elapsed_excluding_shadow_seconds"]
                outcome["gpu_peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
                scope = "EPIC native vocabulary and abstract gaps; official recovery included"
            else:
                common = dict(
                    model=model,
                    tokenizer=tokenizer,
                    calls=calls,
                    paths=active_paths,
                    grammar=grammar,
                    rows=rows,
                    adapter=adapter,
                    policy=policy,
                    config=config,
                )
                outcome = decode(request=request, **common)
                if policy.get("review", False) and outcome["status"] == "complete":
                    draft = outcome
                    revised_request = (
                        request
                        + "\nCandidate call: "
                        + draft["output"]
                        + "\nCheck the candidate against every requested operation and argument. "
                        "Return the corrected call only, or the same call if already correct."
                    )
                    remaining_config = {
                        **config,
                        "max_forwards": config["max_forwards"] - draft["forwards"],
                        "max_generation_seconds": config["max_generation_seconds"]
                        - draft["elapsed_seconds"],
                    }
                    outcome = decode(
                        request=revised_request, **{**common, "config": remaining_config}
                    )
                    outcome["draft"] = draft
                    outcome["elapsed_seconds"] += draft["elapsed_seconds"]
                    outcome["forwards"] += draft["forwards"]
                scope = (
                    "canonical token paths only; exhaustive mean-field MAP control"
                    if policy["kind"] == "catalog_map"
                    else "exact_on_support: positional domains, byte CFG, finite EOS/PAD slots"
                )
            torch.cuda.synchronize()
            total_seconds = time.perf_counter() - method_started + setup
            normalized = normalize_tool_call(outcome["output"])
            complete = outcome["status"] == "complete"
            record = {
                **metadata,
                **outcome,
                "task": task,
                "policy": policy,
                "method": policy["name"],
                "active_catalog_indices": indices,
                "support_policy": scope,
                "exactness_scope": scope,
                "active_grammar_hash": hashlib.sha256(json.dumps(calls).encode()).hexdigest(),
                "grammar_setup_seconds": setup,
                "total_seconds_including_setup": total_seconds,
                "normalized_output": normalized,
                "correct": complete and normalized == task["expected"],
                "syntax_valid": complete and normalized in calls,
                "numeric_correct": complete
                and normalized in calls
                and execute_tool_call(normalized) == execute_tool_call(task["expected"]),
            }
            with (output / "results.jsonl").open("a") as stream:
                stream.write(json.dumps(record, allow_nan=False) + "\n")
            print(
                json.dumps(
                    {
                        k: record[k]
                        for k in (
                            "method",
                            "output",
                            "correct",
                            "forwards",
                            "elapsed_seconds",
                            "status",
                        )
                    }
                ),
                flush=True,
            )
    print(f"ARTIFACT_DIR={output}", flush=True)


if __name__ == "__main__":
    main()
