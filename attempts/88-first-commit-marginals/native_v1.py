"""One frozen A88 development capture; no training and no automatic retry."""

# Synchronous, immediately called timing closures cannot escape their iteration.
# ruff: noqa: B023
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import struct
import subprocess
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODEL = Path.home() / (
    ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots/"
    "08b83a6feb34df1a6011b80c3c00c7563e963b07"
)
REV = "c30699e8356da336a370243923dbaf21066bb9fe"
URL = f"https://huggingface.co/datasets/cais/mmlu/resolve/{REV}/all/dev-00000-of-00001.parquet"
INPUTS = HERE / "native-inputs-v1.json"
SOURCES = ROOT / "artifacts/a88-v1-sources"
MASK, EOT, PAD, VOCAB = 126336, 126348, 126081, 126464
OWN = (
    "native_v1.py",
    "analyze_v1.py",
    "test_native_v1.py",
    "implementation-v1.md",
    "native-inputs-v1.json",
    "native-protocol-v1.md",
    "budgeted-family.md",
    "README.md",
    "oracle.py",
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def model_hashes():
    names = sorted(p.name for p in MODEL.iterdir() if p.is_file())
    return {
        name: {"sha256": file_sha(MODEL / name), "bytes": (MODEL / name).stat().st_size}
        for name in names
    }


def state_hash(canvas, step):
    return sha(
        b"A88-clean-v1\0" + struct.pack("<I", step) + struct.pack(f"<{len(canvas)}I", *canvas)
    )


def group_assignment(tokenizer):
    # Keep all original IDs, including aliases and specials. MASK is explicitly zero.
    emissions = [
        tokenizer.decode([v], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        for v in range(VOCAB)
    ]
    assignment = [
        "ABCD".index(s.strip()) if s.strip() in ("A", "B", "C", "D") else 4 for s in emissions
    ]
    return assignment, {str(i): emissions[i] for i, g in enumerate(assignment) if g < 4}


def prepare():
    import pyarrow.parquet as pq
    from transformers import AutoTokenizer

    started = time.perf_counter()
    SOURCES.mkdir(parents=True, exist_ok=True)
    parquet = SOURCES / "dev.parquet"
    if not parquet.exists():
        with urllib.request.urlopen(URL, timeout=60) as response, parquet.open("xb") as out:
            while block := response.read(1024 * 1024):
                out.write(block)
    rows = pq.read_table(parquet).to_pylist()
    selected = sorted(range(len(rows)), key=lambda i: sha(f"A88-dev-v1:{i}".encode()))[:8]
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=True)
    groups, aliases = group_assignment(tokenizer)
    delimiter = tokenizer.encode("\nAnswer:", add_special_tokens=False)
    cases = []
    for row in selected:
        item = rows[row]
        question, choices = item["question"], item["choices"]
        prompt = (
            "Answer the multiple-choice question. Give a brief explanation "
            "in the reasoning region, "
            "then put exactly one letter A, B, C, or D in the reserved answer region.\n\n"
            + question
            + "\n"
            + "\n".join(
                f"{letter}. {choice}" for letter, choice in zip("ABCD", choices, strict=True)
            )
        )
        prompt_ids = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], add_generation_prompt=True, tokenize=True
        )
        f = len(prompt_ids) + 31 + len(delimiter)
        canvas = prompt_ids + [MASK] * 31 + delimiter + [MASK, EOT]
        cases.append(
            {
                "row": row,
                "selection_sha256": sha(f"A88-dev-v1:{row}".encode()),
                "question": question,
                "choices": choices,
                "subject": item["subject"],
                "answer": item["answer"],
                "prompt": prompt,
                "offset": len(prompt_ids),
                "observed": f,
                "eligible": [*list(range(len(prompt_ids), len(prompt_ids) + 31)), f],
                "input_ids": canvas,
            }
        )
    data = {
        "schema": "A88-native-inputs-v1",
        "dataset_revision": REV,
        "dataset": {"url": URL, "sha256": file_sha(parquet), "rows": len(rows)},
        "attribution": (
            "MMLU, Hendrycks et al., cais/mmlu pinned all/dev; "
            "questions and choices unchanged; see pinned dataset card."
        ),
        "selection": "eight smallest SHA256(A88-dev-v1:<zero-based-row>)",
        "model": str(MODEL),
        "model_files": model_hashes(),
        "groups": groups,
        "aliases": aliases,
        "group_order": ["A", "B", "C", "D", "OUTSIDE"],
        "delimiter_ids": delimiter,
        "mask": MASK,
        "eot": EOT,
        "pad": PAD,
        "vocab": VOCAB,
        "cases": cases,
        "prepare_wall_seconds": time.perf_counter() - started,
    }
    validate_inputs(data)
    with INPUTS.open("x") as stream:
        json.dump(data, stream, ensure_ascii=False, separators=(",", ":"))
        stream.write("\n")
    print(
        json.dumps(
            {
                "inputs": str(INPUTS),
                "sha256": file_sha(INPUTS),
                "rows": selected,
                "aliases": aliases,
                "prepare_seconds": data["prepare_wall_seconds"],
            }
        )
    )


def validate_inputs(data):
    if (
        data["schema"] != "A88-native-inputs-v1"
        or data["dataset_revision"] != REV
        or len(data["cases"]) != 8
    ):
        raise ValueError("unsupported manifest")
    if (data["mask"], data["eot"], data["pad"], data["vocab"]) != (MASK, EOT, PAD, VOCAB):
        raise ValueError("special token contract changed")
    if len(data["groups"]) != VOCAB or any(
        type(g) is not int or g not in range(5) for g in data["groups"]
    ):
        raise ValueError("incomplete alias partition")
    expected = sorted(
        range(data["dataset"]["rows"]), key=lambda i: sha(f"A88-dev-v1:{i}".encode())
    )[:8]
    if [x["row"] for x in data["cases"]] != expected:
        raise ValueError("case selection changed")
    for item in data["cases"]:
        canvas, off, f = item["input_ids"], item["offset"], item["observed"]
        eligible = [*list(range(off, off + 31)), f]
        if (
            len(canvas) > 2048
            or off <= 0
            or f != off + 31 + len(data["delimiter_ids"])
            or item["eligible"] != eligible
            or canvas[off:] != [MASK] * 31 + data["delimiter_ids"] + [MASK, EOT]
            or MASK in canvas[:off]
            or any(type(v) is not int or not 0 <= v < VOCAB for v in canvas)
        ):
            raise ValueError("unsupported context/scaffold; no truncation")


def stable_free_order(scores, positions):
    """Positions must already be ascending; stable sort implements physical ties."""
    import torch

    if positions != sorted(positions):
        raise ValueError("ascending physical positions required")
    return torch.argsort(scores, descending=True, stable=True)


def select_ids(cdf, uniforms):
    import torch

    # right=True skips zero-probability plateaus, including the suppressed MASK.
    values = torch.searchsorted(
        cdf.contiguous(), uniforms.unsqueeze(-1).contiguous(), right=True
    ).squeeze(-1)
    if bool((values >= cdf.shape[-1]).any()):
        raise ValueError("floating CDF failed to cover a proposal uniform")
    return values


class Refusal(RuntimeError):
    """A resource refusal is inconclusive, never scientific failure."""


def foreign_processes():
    raw = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"], text=True
    )
    return [int(x) for x in raw.splitlines() if x.strip().isdigit() and int(x) != os.getpid()]


def capture(record):
    started = time.perf_counter()
    data = json.loads(INPUTS.read_text())
    validate_inputs(data)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    hashes = {name: file_sha(HERE / name) for name in OWN}
    for name, digest in hashes.items():
        frozen = subprocess.check_output(
            ["git", "show", f"HEAD:{(HERE / name).relative_to(ROOT)}"], cwd=ROOT
        )
        if sha(frozen) != digest:
            raise ValueError(f"freeze exact source before capture: {name}")
    record(
        {
            "type": "producer",
            "commit": commit,
            "source_hashes": hashes,
            "pid": os.getpid(),
            "inputs_sha256": file_sha(INPUTS),
            "prepare_seconds": data["prepare_wall_seconds"],
        }
    )
    hash_started = time.perf_counter()
    actual_hashes = model_hashes()
    if actual_hashes != data["model_files"]:
        raise ValueError("local checkpoint files changed after prepare")
    record(
        {
            "type": "model_verification",
            "wall_seconds": time.perf_counter() - hash_started,
            "model_files": actual_hashes,
        }
    )
    import torch
    from transformers import AutoModel, BitsAndBytesConfig

    torch.set_num_threads(4)
    if not torch.cuda.is_available():
        raise Refusal("CUDA unavailable")
    foreign = foreign_processes()
    record(
        {
            "type": "hardware",
            "gpu": torch.cuda.get_device_name(0),
            "free_total_bytes": torch.cuda.mem_get_info(),
            "foreign_compute_pids": foreign,
            "python": platform.python_version(),
            "cuda": torch.version.cuda,
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("torch", "transformers", "bitsandbytes", "numpy", "pyarrow", "accelerate")
            },
            "threads": 4,
            "rng": (
                "torch CUDA float64 uniform; independent free and observed generators; "
                "seeds recorded"
            ),
            "numeric_contract": (
                "nominal categorical law; floating CDF/ranking/reductions, NOT finite-bit exact"
            ),
        }
    )
    if foreign or torch.cuda.mem_get_info()[0] < 7 * 2**30:
        raise Refusal("foreign CUDA process or less than 7 GiB free before load")
    load_started = time.perf_counter()
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
            "wall_seconds": time.perf_counter() - load_started,
            "allocated_bytes": torch.cuda.memory_allocated(),
            "reserved_bytes": torch.cuda.memory_reserved(),
            "host_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        }
    )
    selection = None
    calls, logical, completed = 0, 0, 0
    group_indices = [
        torch.tensor([i for i, g in enumerate(data["groups"]) if g == b], device="cuda")
        for b in range(5)
    ]

    def crop(_module, args):
        if selection is None or args[0].ndim != 3 or args[0].shape[0] != 1:
            raise ValueError("output head outside selected B1 query")
        return (args[0].index_select(1, selection), *args[1:])

    handle = model.get_output_embeddings().register_forward_pre_hook(crop)

    def timer(fn):
        torch.cuda.synchronize()
        wall = time.perf_counter()
        value = fn()
        torch.cuda.synchronize()
        return value, time.perf_counter() - wall

    def check_budget():
        if time.perf_counter() - started >= 1800 or calls >= 968:
            raise Refusal("cooperative 30-minute or 968-new-forward ceiling")
        if foreign_processes():
            raise Refusal("foreign CUDA process appeared; no process killed")

    @torch.inference_mode()
    def query(canvas, positions, state, case, replica, step):
        nonlocal selection, calls
        check_budget()
        selection = torch.tensor(positions, device="cuda")
        tensor = torch.tensor([canvas], device="cuda")
        calls += 1
        record(
            {
                "type": "query_begin",
                "call": calls,
                "case": case,
                "replica": replica,
                "step": step,
                "state_hash": state,
            }
        )
        try:
            logits, model_seconds = timer(lambda: model(tensor, use_cache=False).logits[0])
            if tuple(logits.shape) != (len(positions), VOCAB) or logits.dtype != torch.bfloat16:
                raise ValueError(f"unsupported logits {tuple(logits.shape)}, {logits.dtype}")

            def prepare_categorical():
                if not bool(torch.isfinite(logits).all()):
                    raise ValueError("nonfinite BF16 logits")
                clean = logits.double()
                clean[:, MASK] = -float("inf")
                q = clean.softmax(-1)
                cdf = q.cumsum(-1)
                return q, cdf

            (q, cdf), prep_seconds = timer(prepare_categorical)
            facts = {
                "call": calls,
                "model_seconds": model_seconds,
                "categorical_seconds": prep_seconds,
                "max_q_sum_error": (q.sum(-1) - 1).abs().max().item(),
                "max_cdf_end_error": (cdf[:, -1] - 1).abs().max().item(),
                "zero_clean_probabilities": int((q == 0).sum().item()) - len(positions),
            }
            return q, cdf, facts
        finally:
            selection = None

    def reduce5(row):
        return torch.stack([row.index_select(0, ids).sum() for ids in group_indices])

    try:
        for case, item in enumerate(data["cases"]):
            root_canvas = item["input_ids"]
            root_positions = item["eligible"]
            root_state = state_hash(root_canvas, 0)
            root_q, root_cdf, root_facts = query(
                root_canvas, root_positions, root_state, case, -1, 0
            )
            record({"type": "root", "case": case, "state_hash": root_state, **root_facts})
            for replica in range(8):
                seed = 880001 + 1000 * case + replica
                free_rng = torch.Generator(device="cuda").manual_seed(seed)
                f_rng = torch.Generator(device="cuda").manual_seed(seed + 1000000000)
                canvas = root_canvas.copy()
                f, w, y, native_hit = item["observed"], 1.0, [0.0] * 5, None
                for step in range(16):
                    logical += 1
                    state_started = time.perf_counter()
                    positions = [p for p in root_positions if canvas[p] == MASK]
                    free = [p for p in positions if p != f]
                    state = state_hash(canvas, step)
                    state_seconds = time.perf_counter() - state_started
                    cache_started = time.perf_counter()
                    if step == 0:
                        q, cdf, facts = root_q, root_cdf, root_facts
                        cache_seconds = time.perf_counter() - cache_started
                    else:
                        q, cdf, facts = query(canvas, positions, state, case, replica, step)
                        cache_seconds = 0.0
                    fi = positions.index(f)
                    free_rows = [i for i, p in enumerate(positions) if p != f]
                    forced = len(free) < 2
                    if forced:
                        proposals, selected, cutoff, cutoff_pos = [], [], None, None
                        rng_seconds, rank_seconds = 0.0, 0.0
                    else:

                        def sample_free():
                            uniforms = torch.rand(
                                len(free), dtype=torch.float64, device="cuda", generator=free_rng
                            )
                            return select_ids(cdf[free_rows], uniforms)

                        proposals, rng_seconds = timer(sample_free)

                        def rank_free():
                            scores = q[free_rows].gather(1, proposals[:, None]).squeeze(1)
                            order = stable_free_order(scores, free)
                            return scores, order

                        (scores, order), rank_seconds = timer(rank_free)
                        rank_post_started = time.perf_counter()
                        chosen = order[:2].tolist()
                        selected = [(free[i], int(proposals[i])) for i in chosen]
                        cutoff, cutoff_pos = float(scores[chosen[-1]]), free[chosen[-1]]
                        rank_seconds += time.perf_counter() - rank_post_started

                    def observed_proposal():
                        uniform = torch.rand(1, dtype=torch.float64, device="cuda", generator=f_rng)
                        return int(select_ids(cdf[fi : fi + 1], uniform)[0])

                    ftoken, f_rng_seconds = timer(observed_proposal)
                    fscore_started = time.perf_counter()
                    fscore = float(q[fi, ftoken])
                    f_rng_seconds += time.perf_counter() - fscore_started
                    hit = forced or fscore > cutoff or (fscore == cutoff and f < cutoff_pos)
                    if ftoken == MASK or any(token == MASK for _, token in selected):
                        raise ValueError("suppressed MASK sampled")
                    q5, q5_seconds = timer(lambda: reduce5(q[fi]))

                    def integrate():
                        if forced:
                            return q5, 1.0, 0
                        keep = (q[fi] > cutoff) | ((q[fi] == cutoff) & (f < cutoff_pos))
                        a5 = reduce5(torch.where(keep, q[fi], 0.0))
                        return a5, float(a5.sum()), int((q[fi] == cutoff).sum())

                    (a5_tensor, a, ties), reduction_seconds = timer(integrate)
                    copy_started = time.perf_counter()
                    a5 = a5_tensor.tolist()
                    reduction_seconds += time.perf_counter() - copy_started
                    if forced:
                        reduction_seconds += q5_seconds
                        q5_seconds = 0.0
                    if not -1e-12 <= a <= 1 + 1e-12:
                        raise ValueError("invalid selected probability mass")
                    b = 0.0 if forced else max(0.0, 1.0 - a)
                    update_started = time.perf_counter()
                    before = w
                    y = [old + before * value for old, value in zip(y, a5, strict=True)]
                    w = before * b
                    update_seconds = time.perf_counter() - update_started
                    canvas_started = time.perf_counter()
                    for pos, token in selected:
                        canvas[pos] = token
                    canvas_seconds = time.perf_counter() - canvas_started
                    if native_hit is None and hit:
                        native_hit = {
                            "step": step,
                            "token": ftoken,
                            "group": data["groups"][ftoken],
                            "R5": [v / a for v in a5],
                            "not_full_native_output": True,
                        }
                    output_started = time.perf_counter()
                    json.dumps(y)
                    vector_output_seconds = time.perf_counter() - output_started
                    output_started = time.perf_counter()
                    json.dumps(ftoken)
                    token_output_seconds = time.perf_counter() - output_started
                    row = {
                        "type": "step",
                        "case": case,
                        "replica": replica,
                        "seed": seed,
                        "f_seed": seed + 1000000000,
                        "step": step,
                        "state_hash": state,
                        "new_forward": step > 0,
                        "query_call": facts["call"],
                        "eligible_positions": positions,
                        "free_commit_positions": [p for p, _ in selected],
                        "free_commit_ids": [v for _, v in selected],
                        "cutoff": cutoff,
                        "cutoff_position": cutoff_pos,
                        "qf5": q5.tolist(),
                        "a5": a5,
                        "A": a,
                        "b": b,
                        "W_before": before,
                        "W_after": w,
                        "forced": forced,
                        "f_proposal": ftoken,
                        "f_proposal_score": fscore,
                        "f_selected": hit,
                        "qf_cutoff_ties": ties,
                        "b_rounding_clamp": max(0.0, a - 1.0),
                        "profile": {
                            "model_seconds": facts["model_seconds"],
                            "categorical_seconds": facts["categorical_seconds"],
                            "free_rng_seconds": rng_seconds,
                            "rank_seconds": rank_seconds,
                            "f_rng_seconds": f_rng_seconds,
                            "a5_seconds": reduction_seconds,
                            "qf5_diagnostic_seconds": q5_seconds,
                            "update_seconds": update_seconds,
                            "canvas_seconds": canvas_seconds,
                            "state_seconds": state_seconds,
                            "cache_seconds": cache_seconds,
                            "vector_output_seconds": vector_output_seconds,
                            "token_output_seconds": token_output_seconds,
                        },
                        "numeric": {
                            k: facts[k]
                            for k in (
                                "max_q_sum_error",
                                "max_cdf_end_error",
                                "zero_clean_probabilities",
                            )
                        },
                        "memory": {
                            "allocated_bytes": torch.cuda.memory_allocated(),
                            "reserved_bytes": torch.cuda.memory_reserved(),
                            "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                            "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                            "host_peak_rss_bytes": resource.getrusage(
                                resource.RUSAGE_SELF
                            ).ru_maxrss
                            * 1024,
                        },
                    }
                    record(row)
                    if forced or w == 0:
                        break
                    if step > 0:
                        del q, cdf
                if abs(sum(y) - 1.0) > 1e-10 or native_hit is None:
                    raise ValueError("path lost tail mass or native hit")
                record(
                    {
                        "type": "replica_complete",
                        "case": case,
                        "replica": replica,
                        "Y5": y,
                        "native_first_hit": native_hit,
                        "calls": calls,
                        "logical_steps": logical,
                    }
                )
                if step > 0:
                    del q, cdf
            completed += 1
            record(
                {
                    "type": "case_complete",
                    "case": case,
                    "calls": calls,
                    "logical_steps": logical,
                    "wall_seconds": time.perf_counter() - started,
                }
            )
            del root_q, root_cdf
    finally:
        handle.remove()
        record(
            {
                "type": "capture_progress",
                "completed_cases": completed,
                "calls": calls,
                "logical_steps": logical,
                "wall_seconds": time.perf_counter() - started,
            }
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--capture", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.prepare:
        if args.output:
            parser.error("--prepare uses only the fixed new input manifest")
        prepare()
        return
    if args.output is None or not args.output.resolve().is_relative_to(ROOT / "artifacts"):
        parser.error("--capture requires exclusive new --output under artifacts/")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        output_seconds = 0.0

        def record(value):
            nonlocal output_seconds
            tick = time.perf_counter()
            stream.write(json.dumps(value, sort_keys=True) + "\n")
            stream.flush()
            output_seconds += time.perf_counter() - tick

        started = time.perf_counter()
        try:
            capture(record)
        except (Exception, KeyboardInterrupt) as error:
            refused = (
                isinstance(error, (Refusal, MemoryError))
                or type(error).__name__ == "OutOfMemoryError"
            )
            status = (
                "REFUSED"
                if refused
                else ("INTERRUPTED" if isinstance(error, KeyboardInterrupt) else "ERROR")
            )
            record(
                {
                    "type": "terminal",
                    "status": status,
                    "error": repr(error),
                    "wall_seconds": time.perf_counter() - started,
                    "capture_output_seconds": output_seconds,
                }
            )
            raise
        record(
            {
                "type": "terminal",
                "status": "COMPLETE",
                "wall_seconds": time.perf_counter() - started,
                "capture_output_seconds": output_seconds,
            }
        )


if __name__ == "__main__":
    main()
