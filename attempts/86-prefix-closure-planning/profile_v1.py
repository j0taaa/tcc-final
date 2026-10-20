"""Prospective hardware feasibility probe; no text generation or cache changes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import statistics
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = (
    Path.home()
    / ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots"
    / "08b83a6feb34df1a6011b80c3c00c7563e963b07"
)
MASK = 126336


def processes():
    raw = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
        text=True,
    )
    return [int(p) for p in raw.splitlines() if p.strip().isdigit() and int(p) != os.getpid()]


def run(record):
    import torch
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    record(
        {
            "type": "producer",
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "hashes": {
                name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                for name in ("profile_v1.py", "profile-protocol-v1.md", "README.md")
            },
        }
    )
    torch.set_num_threads(4)
    torch.manual_seed(86001)
    foreign = processes()
    record(
        {
            "type": "hardware",
            "pid": os.getpid(),
            "python": platform.python_version(),
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("torch", "transformers", "bitsandbytes", "accelerate")
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
        }
    )
    if foreign or torch.cuda.mem_get_info()[0] < 7 * 2**30:
        record({"type": "refusal", "reason": "foreign_process_or_low_memory"})
        return
    start = time.perf_counter()
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
    record({"type": "load", "seconds": time.perf_counter() - start})
    prompt = tokenizer.apply_chat_template(
        [
            {
                "role": "user",
                "content": "Write a Python function that returns the running sum of a list.",
            }
        ],
        tokenize=False,
        add_generation_prompt=True,
    )
    ids = tokenizer(prompt, return_tensors="pt")["input_ids"].to("cuda")
    offset = ids.shape[1]
    record({"type": "input", "prompt_ids": ids[0].tolist(), "offset": offset})

    @torch.inference_mode()
    def forward(canvas, selected):
        logits = model(canvas, use_cache=False).logits
        if not selected:
            logits = logits[:, offset : offset + 32]
        logits = logits.float()
        finite_logits = torch.isfinite(logits).all()
        logits[:, :, MASK] = -float("inf")
        probabilities = logits.softmax(-1)
        finite_probabilities = torch.isfinite(probabilities).all()
        confidence, tokens = probabilities.max(-1)
        order = torch.argsort(confidence, dim=-1, descending=True, stable=True)
        action = torch.stack((order[:, 0], tokens.gather(1, order[:, :1])[:, 0]), dim=1)
        return (
            logits,
            tokens,
            confidence,
            action,
            torch.stack((finite_logits, finite_probabilities)),
        )

    with torch.inference_mode():
        for length in (128, 256):
            foreign = processes()
            record(
                {"type": "reference_inspection", "length": length, "foreign_compute_pids": foreign}
            )
            if foreign:
                record({"type": "refusal", "reason": "foreign_process_before_reference"})
                return
            if offset + 32 > length:
                raise RuntimeError("Protocol prompt does not fit; do not truncate")
            canvas = torch.full((1, length), MASK, dtype=torch.long, device="cuda")
            canvas[:, :offset] = ids
            try:
                full, _, _, full_action, full_valid = forward(canvas, False)
            except torch.OutOfMemoryError as exc:
                record(
                    {
                        "type": "refusal",
                        "length": length,
                        "batch": 1,
                        "phase": "full_reference",
                        "reason": "OOM",
                        "error": repr(exc),
                    }
                )
                torch.cuda.empty_cache()
                continue
            if not bool(full_valid.all()):
                raise FloatingPointError("Nonfinite full reference logits/probabilities")
            handle = model.get_output_embeddings().register_forward_pre_hook(
                lambda _module, args: (args[0][:, offset : offset + 32],)
            )
            try:
                reference, ref_tokens, ref_confidence, ref_action, ref_valid = forward(canvas, True)
            except torch.OutOfMemoryError as exc:
                handle.remove()
                record(
                    {
                        "type": "refusal",
                        "length": length,
                        "batch": 1,
                        "phase": "selected_reference",
                        "reason": "OOM",
                        "error": repr(exc),
                    }
                )
                del full
                torch.cuda.empty_cache()
                continue
            if not bool(ref_valid.all()):
                raise FloatingPointError("Nonfinite selected reference logits/probabilities")
            finite = torch.isfinite(reference) & torch.isfinite(full)
            record(
                {
                    "type": "projection_check",
                    "length": length,
                    "full_finite": full_valid.tolist(),
                    "selected_finite": ref_valid.tolist(),
                    "max_abs_logit_difference": (reference[finite] - full[finite])
                    .abs()
                    .max()
                    .item(),
                    "action_equal": bool(torch.equal(ref_action, full_action)),
                    "reference_action": ref_action[0].tolist(),
                    "full_action": full_action[0].tolist(),
                }
            )
            del full
            reference = reference.cpu()
            for batch in (1, 2, 4, 8):
                foreign = processes()
                record(
                    {
                        "type": "inspection",
                        "length": length,
                        "batch": batch,
                        "foreign_compute_pids": foreign,
                    }
                )
                if foreign:
                    record({"type": "refusal", "reason": "foreign_process_mid_probe"})
                    handle.remove()
                    return
                repeated = canvas.repeat(batch, 1)
                torch.cuda.reset_peak_memory_stats()
                timings = []
                checks = []
                try:
                    for repeat in range(7):
                        torch.cuda.synchronize()
                        started = time.perf_counter()
                        logits, tokens, confidence, action, valid = forward(repeated, True)
                        torch.cuda.synchronize()
                        elapsed = time.perf_counter() - started
                        timings.append(elapsed)
                        differences = logits.cpu() - reference
                        differences[:, :, MASK] = 0
                        checks.append(
                            {
                                "repeat": repeat,
                                "finite_logits_probabilities": valid.tolist(),
                                "action_equal": bool(
                                    torch.equal(action, ref_action.repeat(batch, 1))
                                ),
                                "all_top1_equal": bool(
                                    torch.equal(tokens, ref_tokens.repeat(batch, 1))
                                ),
                                "max_abs_confidence_difference": (confidence - ref_confidence)
                                .abs()
                                .max()
                                .item(),
                                "max_abs_logit_difference": differences.abs().max().item(),
                            }
                        )
                        del logits, tokens, confidence, action
                        if not bool(valid.all()):
                            record(
                                {
                                    "type": "invalid_numeric",
                                    "length": length,
                                    "batch": batch,
                                    "repeat": repeat,
                                    "completed_seconds": timings,
                                    "completed_checks": checks,
                                }
                            )
                            raise FloatingPointError("Nonfinite measured logits/probabilities")
                except torch.OutOfMemoryError as exc:
                    record(
                        {
                            "type": "refusal",
                            "length": length,
                            "batch": batch,
                            "reason": "OOM",
                            "error": repr(exc),
                            "completed_seconds": timings,
                            "completed_checks": checks,
                        }
                    )
                    torch.cuda.empty_cache()
                    break
                foreign_after = processes()
                record(
                    {
                        "type": "profile",
                        "length": length,
                        "batch": batch,
                        "warmup_seconds": timings[:2],
                        "seconds": timings[2:],
                        "median_seconds": statistics.median(timings[2:]),
                        "checks": checks,
                        "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                        "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                        "nvidia_memory_mib": subprocess.check_output(
                            [
                                "nvidia-smi",
                                "--query-gpu=memory.used",
                                "--format=csv,noheader,nounits",
                            ],
                            text=True,
                        ).strip(),
                        "foreign_compute_pids_after": foreign_after,
                    }
                )
                if foreign_after:
                    record({"type": "refusal", "reason": "foreign_process_after_batch"})
                    handle.remove()
                    return
            handle.remove()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.output.open("x") as stream:

        def record(row):
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            print(json.dumps({k: v for k, v in row.items() if k != "checks"}), flush=True)

        try:
            run(record)
        except BaseException as exc:
            record({"type": "fatal", "error": repr(exc)})
            raise


if __name__ == "__main__":
    main()
