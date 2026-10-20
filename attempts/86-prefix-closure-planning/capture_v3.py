"""Frozen native B1 capture for A86 offline replay; this runs no accelerated decoder."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = Path.home() / (
    ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots/"
    "08b83a6feb34df1a6011b80c3c00c7563e963b07"
)
MASK, TERMINALS = 126336, {126081, 126348}
TOTAL, GENERATION, BLOCK = 256, 128, 32
PROMPTS = {
    "train": (
        "Write a Python function that merges two sorted lists. Include a short explanation.",
        "Write a Python function that returns the longest common prefix of a list of strings. "
        "Explain its complexity.",
        "Explain why hash tables can have collisions and how chaining resolves them. "
        "Give a concrete example.",
        "Explain the difference between a stack and a queue, with one practical example for each.",
    ),
    "validation": (
        "Write a Python function that removes duplicates from a list while preserving order. "
        "Explain its complexity.",
        "Write a Python function that rotates a list to the right by k positions. "
        "Include an example.",
        "Explain what a deadlock is and give a concrete example with two resources.",
        "Explain why merge sort has O(n log n) time complexity.",
    ),
    "test": (
        "Write a Python function that checks whether a string is a palindrome. "
        "Explain how it handles spaces.",
        "Write a Python function that flattens a nested list of integers. Include a short example.",
        "Write a Python function for binary search in a sorted list. State the time complexity.",
        "Write a Python function that counts word frequencies in a string, ignoring case.",
        "Explain why binary search requires sorted input. Show a small worked example.",
        "Explain how breadth-first search differs from depth-first search. "
        "Give an appropriate use for each.",
        "Explain the difference between a process and a thread, with one example.",
        "Explain why a database index can speed up a query but slow down updates.",
    ),
}


class Refusal(RuntimeError):
    """Resource refusal leaves the partial capture inconclusive."""


def processes():
    raw = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"], text=True
    )
    return [int(p) for p in raw.splitlines() if p.strip().isdigit() and int(p) != os.getpid()]


def run(record):
    # Resolve all provenance dependencies before importing or initializing CUDA.
    hashes = {
        name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        for name in (
            "capture_v3.py",
            "protocol-v3.md",
            "planner.py",
            "policies_v3.py",
            "profile-v1.jsonl",
            "fidelity-v2.jsonl",
        )
    }
    record(
        {
            "type": "producer",
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "model": str(MODEL),
            "hashes": hashes,
            "seed": 86003,
            "total": TOTAL,
            "generation": GENERATION,
            "block": BLOCK,
            "batch": 1,
            "use_cache": False,
            "quantization": "NF4-double-BF16",
        }
    )
    import torch
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    torch.set_num_threads(4)
    torch.manual_seed(86003)
    foreign = processes()
    record(
        {
            "type": "hardware",
            "pid": os.getpid(),
            "python": platform.python_version(),
            "packages": {
                p: importlib.metadata.version(p)
                for p in (
                    "torch",
                    "transformers",
                    "bitsandbytes",
                    "accelerate",
                )
            },
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
            "free_total_bytes": torch.cuda.mem_get_info(),
            "foreign_compute_pids": foreign,
            "nvidia_smi": subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=driver_version,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
            ).strip(),
            "threads": 4,
        }
    )
    if foreign or torch.cuda.mem_get_info()[0] < 7 * 2**30:
        raise Refusal("foreign CUDA process or less than 7 GiB free before load")
    load_wall, load_cpu = time.perf_counter(), time.process_time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        MODEL,
        local_files_only=True,
        trust_remote_code=True,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
    ).eval()
    torch.cuda.synchronize()
    record(
        {
            "type": "load",
            "wall_seconds": time.perf_counter() - load_wall,
            "cpu_process_seconds": time.process_time() - load_cpu,
        }
    )
    selection = None

    def select_head(_module, args):
        if selection is None:
            return None
        hidden = args[0]
        if hidden.shape != (1, TOTAL, 4096):
            raise RuntimeError(f"unsupported hidden shape: {tuple(hidden.shape)}")
        return (hidden.gather(1, selection.unsqueeze(-1).expand(-1, -1, 4096)), *args[1:])

    def inspect(phase, info):
        foreign = processes()
        record(
            {
                "type": "inspection",
                "phase": phase,
                **info,
                "foreign_compute_pids": foreign,
                "free_total_bytes": torch.cuda.mem_get_info(),
                "allocated_bytes": torch.cuda.memory_allocated(),
                "reserved_bytes": torch.cuda.memory_reserved(),
            }
        )
        if foreign:
            raise Refusal(f"foreign CUDA process at {phase}: {foreign}")

    handle = model.get_output_embeddings().register_forward_pre_hook(select_head)

    @torch.inference_mode()
    def query(cpu_canvas, start):
        nonlocal selection
        torch.cuda.synchronize()
        began, cpu_began = time.perf_counter(), time.process_time()
        cuda_start = torch.cuda.Event(enable_timing=True)
        cuda_end = torch.cuda.Event(enable_timing=True)
        cuda_start.record()
        canvas = cpu_canvas[None].to("cuda")
        indices = torch.tensor([start], device="cuda")[:, None] + torch.arange(BLOCK, device="cuda")
        selection = indices
        try:
            logits = model(canvas, use_cache=False).logits.float()
            if not bool(torch.isfinite(logits).all()):
                raise FloatingPointError("nonfinite selected B1 logits")
            logits[:, :, MASK] = -float("inf")
            probabilities = logits.softmax(-1)
            if not bool(torch.isfinite(probabilities).all()):
                raise FloatingPointError("nonfinite selected B1 probabilities")
            confidence, tokens = probabilities.max(-1)
            scores = confidence.masked_fill(canvas.gather(1, indices) != MASK, -float("inf"))
            order = torch.argsort(scores, dim=-1, descending=True, stable=True)
            head = {
                "top1_ids": tokens[0].tolist(),
                "confidence": confidence[0].tolist(),
                "order": order[0].tolist(),
                "action": [
                    indices[0, order[0, 0]].item(),
                    tokens[0, order[0, 0]].item(),
                ],
            }
            del logits, probabilities, confidence, tokens, scores, order, canvas, indices
            cuda_end.record()
            torch.cuda.synchronize()
            costs = {
                "seconds": time.perf_counter() - began,
                "cpu_process_seconds": time.process_time() - cpu_began,
                "cuda_event_seconds": cuda_start.elapsed_time(cuda_end) / 1000,
            }
        finally:
            selection = None
        return head, costs

    completed, total_events = 0, 0
    try:
        for split, prompts in PROMPTS.items():
            limit = 64 if split == "train" else 128
            for case, prompt in enumerate(prompts):
                info = {
                    "split": split,
                    "family": "code" if case < len(prompts) // 2 else "explanation",
                    "id": f"{split}-{case}",
                    "case": case,
                }
                began, cpu_began = time.perf_counter(), time.process_time()
                inspect("before_case", info)
                torch.cuda.reset_peak_memory_stats()
                text = tokenizer.apply_chat_template(
                    [{"role": "user", "content": prompt}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
                prompt_ids = tokenizer(text, return_tensors="pt")["input_ids"][0]
                offset = len(prompt_ids)
                if offset + GENERATION > TOTAL:
                    raise RuntimeError("prompt + 128 does not fit fixed canvas; no truncation")
                canvas = torch.full((TOTAL,), MASK, dtype=torch.long)
                canvas[:offset] = prompt_ids
                record(
                    {
                        "type": "input",
                        **info,
                        "prompt": prompt,
                        "prompt_ids": prompt_ids.tolist(),
                        "offset": offset,
                        "event_limit": limit,
                    }
                )
                sums = {"seconds": 0.0, "cpu_process_seconds": 0.0, "cuda_event_seconds": 0.0}
                reason, events = "event_limit", 0
                for step in range(limit):
                    remaining = (canvas[offset : offset + GENERATION] == MASK).nonzero().flatten()
                    if not len(remaining):
                        reason = "generation_complete"
                        break
                    start = offset + (remaining[0].item() // BLOCK) * BLOCK
                    head, costs = query(canvas, start)
                    for key in sums:
                        sums[key] += costs[key]
                    position, token = head["action"]
                    if not (start <= position < start + BLOCK) or canvas[position].item() != MASK:
                        raise RuntimeError("action must reveal a masked position in active block")
                    if token == MASK:
                        raise RuntimeError("MASK is not an admissible revealed token")
                    canvas[position] = token
                    terminal = None
                    for local, value in enumerate(canvas[offset : offset + GENERATION].tolist()):
                        prefix_complete = not bool((canvas[offset : offset + local] == MASK).any())
                        if value in TERMINALS and prefix_complete:
                            terminal = [offset + local, value]
                            break
                    complete = not bool((canvas[offset : offset + GENERATION] == MASK).any())
                    reason = (
                        "safe_terminal"
                        if terminal
                        else (
                            "generation_complete"
                            if complete
                            else ("event_limit" if step + 1 == limit else "continue")
                        )
                    )
                    record(
                        {
                            "type": "serial_step",
                            **info,
                            "step": step,
                            "block_start": start,
                            "stop_reason": reason,
                            "terminal": terminal,
                            **head,
                            **costs,
                        }
                    )
                    events += 1
                    if terminal or complete:
                        break
                record(
                    {
                        "type": "serial_final",
                        **info,
                        "stop_reason": reason,
                        "events": events,
                        "canvas_ids": canvas.tolist(),
                        "generated_text": tokenizer.decode(
                            canvas[offset : offset + GENERATION].tolist(), skip_special_tokens=False
                        ),
                    }
                )
                inspect("after_case", info)
                record(
                    {
                        "type": "case_cost",
                        **info,
                        "capture_wall_seconds": time.perf_counter() - began,
                        "capture_cpu_process_seconds": time.process_time() - cpu_began,
                        "scope": "before_case inspection through final data/after_case flush; "
                        "excludes this cost record",
                        "head_cost_sums": sums,
                        "events": events,
                        "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                        "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                    }
                )
                completed += 1
                total_events += events
        record(
            {
                "type": "result",
                "status": "COMPLETE",
                "completed_cases": completed,
                "total_events": total_events,
                "expected_cases": 16,
            }
        )
    finally:
        handle.remove()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8") as output:

        def record(value):
            output.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
            output.flush()

        try:
            run(record)
        except Refusal as exc:
            record({"type": "refusal", "status": "INCONCLUSIVE", "reason": str(exc)})
        except BaseException as exc:
            kind = "refusal" if type(exc).__name__ == "OutOfMemoryError" else "error"
            record(
                {
                    "type": kind,
                    "status": "INCONCLUSIVE" if kind == "refusal" else "FAIL",
                    "reason": repr(exc),
                }
            )
            if kind != "refusal":
                raise


if __name__ == "__main__":
    main()
