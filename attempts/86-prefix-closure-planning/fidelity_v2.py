"""Frozen A86 B1/B8 trajectory-fidelity gate; no decoder acceleration claims."""

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
TOTAL, GENERATION, BLOCK, BATCH, EVENTS = 256, 128, 32, 8, 64
PROMPTS = (
    "Write a Python function that merges two sorted lists. Include a short explanation.",
    "Write a Python function that returns the longest common prefix of a list of strings. "
    "Explain its complexity.",
    "Explain why hash tables can have collisions and how chaining resolves them. "
    "Give a concrete example.",
    "Explain the difference between a stack and a queue, with one practical example for each.",
)


class Refusal(RuntimeError):
    """Resource interference makes this run inconclusive."""


def processes():
    raw = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"], text=True
    )
    return [int(p) for p in raw.splitlines() if p.strip().isdigit() and int(p) != os.getpid()]


def difference(left, right):
    return {
        "action_equal": left["action"] == right["action"],
        "all_top1_equal": left["top1_ids"] == right["top1_ids"],
        "order_equal": left["order"] == right["order"],
        "max_abs_confidence_difference": max(
            abs(a - b) for a, b in zip(left["confidence"], right["confidence"], strict=True)
        ),
    }


def run(record):
    import torch
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    record(
        {
            "type": "producer",
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "profile_source_commit": "220be2ff",
            "model": str(MODEL),
            "hashes": {
                name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                for name in (
                    "fidelity_v2.py",
                    "fidelity-protocol-v2.md",
                    "profile_v1.py",
                    "profile-protocol-v1.md",
                    "README.md",
                )
            },
        }
    )
    torch.set_num_threads(4)
    torch.manual_seed(86002)

    def inspect(phase):
        foreign = processes()
        record({"type": "inspection", "phase": phase, "foreign_compute_pids": foreign})
        if foreign:
            raise Refusal(f"foreign CUDA process at {phase}: {foreign}")

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
            "nvidia_smi": subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=driver_version,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
            ).strip(),
            "seed": 86002,
            "threads": 4,
        }
    )
    inspect("before_load")
    if torch.cuda.mem_get_info()[0] < 7 * 2**30:
        raise Refusal("less than 7 GiB free before model load")
    started = time.perf_counter()
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
    record({"type": "load", "seconds": time.perf_counter() - started})
    selection = None

    def select_head(_module, args):
        if selection is None:
            return None
        hidden = args[0]
        if hidden.shape != (selection.shape[0], TOTAL, 4096):
            raise RuntimeError(f"unsupported hidden shape: {tuple(hidden.shape)}")
        return (hidden.gather(1, selection.unsqueeze(-1).expand(-1, -1, 4096)), *args[1:])

    handle = model.get_output_embeddings().register_forward_pre_hook(select_head)

    @torch.inference_mode()
    def query(cpu_canvas, starts, phase, full=False):
        nonlocal selection
        inspect(f"before_{phase}")
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        began = time.perf_counter()
        canvas = cpu_canvas.to("cuda")
        indices = torch.tensor(starts, device="cuda")[:, None] + torch.arange(BLOCK, device="cuda")
        selection = None if full else indices
        try:
            logits = model(canvas, use_cache=False).logits
            if full:
                logits = logits[torch.arange(len(starts), device="cuda")[:, None], indices]
            logits = logits.float()
            if not bool(torch.isfinite(logits).all()):
                raise FloatingPointError(f"nonfinite logits at {phase}")
            logits[:, :, MASK] = -float("inf")
            probabilities = logits.softmax(-1)
            if not bool(torch.isfinite(probabilities).all()):
                raise FloatingPointError(f"nonfinite probabilities at {phase}")
            confidence, tokens = probabilities.max(-1)
            scores = confidence.masked_fill(canvas.gather(1, indices) != MASK, -float("inf"))
            order = torch.argsort(scores, dim=-1, descending=True, stable=True)
            rows = [
                {
                    "top1_ids": tokens[i].tolist(),
                    "confidence": confidence[i].tolist(),
                    "order": order[i].tolist(),
                    "action": [
                        indices[i, order[i, 0]].item(),
                        tokens[i, order[i, 0]].item(),
                    ],
                }
                for i in range(len(starts))
            ]
            del logits, probabilities, confidence, tokens, scores, order, canvas, indices
            torch.cuda.synchronize()
            seconds = time.perf_counter() - began
            peak = torch.cuda.max_memory_allocated()
        finally:
            selection = None
        inspect(f"after_{phase}")
        return rows, seconds, peak

    states, projection_mismatches = [], 0
    try:
        for case, prompt in enumerate(PROMPTS):
            text = tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
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
                    "case": case,
                    "prompt": prompt,
                    "prompt_ids": prompt_ids.tolist(),
                    "offset": offset,
                }
            )
            reason = "event_limit"
            for step in range(EVENTS):
                remaining = (canvas[offset : offset + GENERATION] == MASK).nonzero().flatten()
                if not len(remaining):
                    reason = "generation_complete"
                    break
                start = offset + (remaining[0].item() // BLOCK) * BLOCK
                full = None
                if step == 0:
                    full_rows, seconds, peak = query(canvas[None], [start], f"full_{case}", True)
                    full = full_rows[0]
                    record(
                        {
                            "type": "full_reference",
                            "case": case,
                            "seconds": seconds,
                            "peak_allocated_bytes": peak,
                            **full,
                        }
                    )
                before = canvas.clone()
                rows, seconds, peak = query(before[None], [start], f"serial_{case}_{step}")
                head = rows[0]
                if full is not None:
                    check = difference(head, full)
                    projection_mismatches += not check["action_equal"]
                    record({"type": "projection_check", "case": case, **check})
                states.append((case, step, before, start, head))
                position, token = head["action"]
                if canvas[position].item() != MASK or token == MASK:
                    raise RuntimeError("selected action must reveal a masked eligible position")
                canvas[position] = token
                terminal = None
                for local, value in enumerate(canvas[offset : offset + GENERATION].tolist()):
                    prefix_complete = not bool((canvas[offset : offset + local] == MASK).any())
                    if value in TERMINALS and prefix_complete:
                        terminal = [offset + local, value]
                        break
                reason = (
                    "safe_terminal"
                    if terminal
                    else ("event_limit" if step + 1 == EVENTS else "continue")
                )
                record(
                    {
                        "type": "serial_step",
                        "case": case,
                        "step": step,
                        "block_start": start,
                        "seconds": seconds,
                        "peak_allocated_bytes": peak,
                        "stop_reason": reason,
                        "terminal": terminal,
                        **head,
                    }
                )
                if terminal:
                    break
            record(
                {
                    "type": "serial_final",
                    "case": case,
                    "stop_reason": reason,
                    "canvas_ids": canvas.tolist(),
                }
            )

        action_mismatches = top1_mismatches = order_mismatches = 0
        for batch_start in range(0, len(states), BATCH):
            real = states[batch_start : batch_start + BATCH]
            padded = real + [real[-1]] * (BATCH - len(real))
            rows, seconds, peak = query(
                torch.stack([row[2] for row in padded]),
                [row[3] for row in padded],
                f"batch_{batch_start // BATCH}",
            )
            for row, (case, step, _, start, reference) in zip(rows[: len(real)], real, strict=True):
                check = difference(row, reference)
                action_mismatches += not check["action_equal"]
                top1_mismatches += not check["all_top1_equal"]
                order_mismatches += not check["order_equal"]
                record(
                    {
                        "type": "batch_row",
                        "case": case,
                        "step": step,
                        "block_start": start,
                        **row,
                        **check,
                    }
                )
            record(
                {
                    "type": "batch",
                    "index": batch_start // BATCH,
                    "real_rows": len(real),
                    "padding_rows": BATCH - len(real),
                    "seconds": seconds,
                    "peak_allocated_bytes": peak,
                }
            )
        record(
            {
                "type": "result",
                "gate": "PASS" if not (action_mismatches or projection_mismatches) else "FAIL",
                "completed_cases": len(PROMPTS),
                "compared_rows": len(states),
                "action_mismatches": action_mismatches,
                "projection_mismatches": projection_mismatches,
                "all_top1_mismatch_rows": top1_mismatches,
                "order_mismatch_rows": order_mismatches,
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
            record({"type": "refusal", "gate": "INCONCLUSIVE", "reason": str(exc)})
        except BaseException as exc:
            kind = "refusal" if type(exc).__name__ == "OutOfMemoryError" else "error"
            record(
                {
                    "type": kind,
                    "gate": "INCONCLUSIVE" if kind == "refusal" else "FAIL",
                    "reason": repr(exc),
                }
            )
            if kind != "refusal":
                raise


if __name__ == "__main__":
    main()
