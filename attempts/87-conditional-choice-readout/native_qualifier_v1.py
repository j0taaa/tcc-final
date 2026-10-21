"""BANKING77 development qualifier. Preparation runs no neural forward.

Freeze this source, the protocol and prepared inputs before --capture.
Only B1 star responses are captured; no online decoder or speed claim.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import subprocess
import time
import urllib.request
from fractions import Fraction as F
from math import prod
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REV = "57ec275d8078af65b7731c2a98be812d844a6d6b"
BASE = f"https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/{REV}"
MODEL = Path.home() / (
    ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots/"
    "08b83a6feb34df1a6011b80c3c00c7563e963b07"
)
CACHE = ROOT / "artifacts/a87-native-v1-sources"
INPUTS = HERE / "native-inputs-v1.json"
MASK, EOT, PAD = 126336, 126348, 126081
VOCAB = 126464
OWN = ("native_qualifier_v1.py", "native-qualifier-v1.md", "native-inputs-v1.json")
TOKEN_FILES = ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fraction(value):
    return [value.numerator, value.denominator]


def prepare():
    from transformers import AutoTokenizer

    sources = {}
    CACHE.mkdir(parents=True, exist_ok=True)
    for name in ("banking_data/categories.json", "banking_data/train.csv", "LICENSE"):
        path = CACHE / Path(name).name
        if not path.exists():
            with urllib.request.urlopen(f"{BASE}/{name}", timeout=60) as response:
                data = response.read()
            with path.open("xb") as stream:
                stream.write(data)
        sources[name] = {"url": f"{BASE}/{name}", "sha256": sha(path.read_bytes())}
    categories = json.loads((CACHE / "categories.json").read_text())
    if len(categories) != 77 or len(set(categories)) != 77:
        raise ValueError("expected exactly 77 distinct original categories")
    rows = list(csv.DictReader(io.StringIO((CACHE / "train.csv").read_text())))
    indices = sorted(range(len(rows)), key=lambda i: sha(f"A87-native-v1:{i}".encode()))[:8]
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=True)
    texts = [name.replace("_", " ") for name in categories]
    lexical = [tokenizer.encode(text, add_special_tokens=False) for text in texts]
    length = max(map(len, lexical)) + 1
    labels = [ids + [EOT] + [PAD] * (length - len(ids) - 1) for ids in lexical]
    if len({tuple(ids) for ids in labels}) != 77 or any(
        not ids or set(ids) & {MASK, EOT, PAD} for ids in lexical
    ):
        raise ValueError("unsupported lexical IDs or duplicate candidate strings")
    a_words = sorted({tuple(ids[:1]) for ids in labels})
    b_words = sorted({tuple(ids[1:]) for ids in labels})
    edges = [
        [a_words.index(tuple(ids[:1])), len(a_words) + b_words.index(tuple(ids[1:]))]
        for ids in labels
    ]
    cases = []
    for index in indices:
        row = rows[index]
        prompt = (
            "Classify the banking request into exactly one intent from the list below. "
            "Reply with the exact intent text only, preserving its spelling and punctuation.\n"
            "Intents: " + json.dumps(texts, ensure_ascii=False) + "\nRequest: " + row["text"]
        )
        prompt_ids = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], add_generation_prompt=True, tokenize=True
        )
        canvas = prompt_ids + [MASK] * length
        if len(canvas) > 2048:
            raise ValueError(f"context exceeds 2048 without truncation: row {index}")
        cases.append(
            {
                "row": index,
                "selection_sha256": sha(f"A87-native-v1:{index}".encode()),
                "request": row["text"],
                "gold": row["category"],
                "prompt": prompt,
                "offset": len(prompt_ids),
                "input_ids": canvas,
            }
        )
    prepared = {
        "schema": "A87-native-inputs-v1",
        "stage": "development-qualifier",
        "dataset_revision": REV,
        "sources": sources,
        "attribution": "BANKING77, PolyAI/Casanueva et al. (2020), CC BY 4.0; "
        "requests unchanged; category underscores replaced with spaces; tokenized.",
        "paper": "https://arxiv.org/abs/2003.04807",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "model": str(MODEL),
        "tokenizer_hashes": {name: sha((MODEL / name).read_bytes()) for name in TOKEN_FILES},
        "mask": MASK,
        "eot": EOT,
        "pad": PAD,
        "length": length,
        "categories": categories,
        "label_texts": texts,
        "label_ids": labels,
        "a_words": a_words,
        "b_words": b_words,
        "edges": edges,
        "training_rows": len(rows),
        "selection": "eight smallest SHA256(A87-native-v1:<zero-based-row>)",
        "calls_per_case": 1 + len(a_words) + len(b_words),
        "cases": cases,
    }
    with INPUTS.open("x") as stream:
        json.dump(prepared, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {
                "prepared": str(INPUTS),
                "length": length,
                "rows": indices,
                "calls_per_case": prepared["calls_per_case"],
            }
        )
    )


class Refusal(RuntimeError):
    """Resource/time refusal is inconclusive, including a partial capture."""


def validate_inputs(data):
    labels, length = data["label_ids"], data["length"]
    if (
        data["schema"] != "A87-native-inputs-v1"
        or len(labels) != 77
        or length < 2
        or len(data["cases"]) != 8
        or (data["mask"], data["eot"], data["pad"]) != (MASK, EOT, PAD)
    ):
        raise ValueError("unsupported input manifest")
    for ids in labels:
        if len(ids) != length or any(type(x) is not int or not 0 <= x < VOCAB for x in ids):
            raise ValueError("invalid label IDs")
        end = ids.index(EOT)
        if (
            end == 0
            or set(ids[:end]) & {MASK, EOT, PAD}
            or ids[end + 1 :] != [PAD] * (length - end - 1)
        ):
            raise ValueError("invalid lexical/EOT/PAD contract")
    a = sorted({tuple(ids[:1]) for ids in labels})
    b = sorted({tuple(ids[1:]) for ids in labels})
    edges = [[a.index(tuple(ids[:1])), len(a) + b.index(tuple(ids[1:]))] for ids in labels]
    if (
        data["a_words"] != list(map(list, a))
        or data["b_words"] != list(map(list, b))
        or data["edges"] != edges
        or len(set(map(tuple, edges))) != 77
        or data["calls_per_case"] != 1 + len(a) + len(b)
    ):
        raise ValueError("invalid block/edge manifest")
    for case in data["cases"]:
        ids, offset = case["input_ids"], case["offset"]
        if (
            not 0 < offset < len(ids) <= 2048
            or len(ids) != offset + length
            or any(type(x) is not int or not 0 <= x < VOCAB for x in ids)
            or MASK in ids[:offset]
            or ids[offset:] != [MASK] * length
        ):
            raise ValueError("invalid full context or MASK slots")


def processes():
    raw = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"], text=True
    )
    return [int(p) for p in raw.splitlines() if p.strip().isdigit() and int(p) != os.getpid()]


def rational_rows(array, labels):
    """Normalize the complete clean FP32 softmax row exactly, via exponent bins."""
    import numpy as np

    if array.dtype != np.float32 or array.ndim != 2 or array.shape[1] != VOCAB:
        raise ValueError("unsupported FP32 row/vocabulary")
    result, totals, zeros = [], [], []
    for position, row in enumerate(array):
        bits = row.view(np.uint32)
        exponents = (bits >> 23) & 255
        if bool((bits >> 31).any()) or bool((exponents == 255).any()) or row[MASK] != 0:
            raise ValueError("nonfinite, signed or unmasked probability")
        significands = (bits & 0x7FFFFF) + ((exponents > 0).astype(np.uint32) << 23)
        bins = np.bincount(exponents, weights=significands, minlength=255)
        total = sum(int(value) << max(exponent - 1, 0) for exponent, value in enumerate(bins))
        if total <= 0:
            raise ValueError("zero clean-vocabulary probability mass")
        weights = {
            token: int(significands[token]) << max(int(exponents[token]) - 1, 0)
            for token in {ids[position] for ids in labels}
        }
        result.append({token: F(weight, total) for token, weight in weights.items()})
        totals.append(total)
        zeros.append(int(np.count_nonzero(significands == 0)) - 1)  # MASK excluded.
    return result, {
        "fp32_sha256": sha(array.tobytes()),
        "total_weights": totals,
        "zero_counts_clean_vocab": zeros,
        "boundary": "CLOSED" if any(zeros) else "INTERIOR",
    }


def capture(record):
    began = time.perf_counter()
    data = json.loads(INPUTS.read_text())
    validate_inputs(data)
    hashes = {name: sha((HERE / name).read_bytes()) for name in OWN}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for name in OWN:
        frozen = subprocess.check_output(
            ["git", "show", f"HEAD:{(HERE / name).relative_to(ROOT)}"], cwd=ROOT
        )
        if sha(frozen) != hashes[name]:
            raise ValueError(f"freeze the exact source before capture: {name}")
    for name, expected in data["tokenizer_hashes"].items():
        if sha((MODEL / name).read_bytes()) != expected:
            raise ValueError(f"tokenizer changed: {name}")
    hash_wall, hash_cpu = time.perf_counter(), time.process_time()
    index_name = "model.safetensors.index.json"
    shards = sorted(set(json.loads((MODEL / index_name).read_text())["weight_map"].values()))
    if len(shards) != 6 or any(Path(name).name != name for name in shards):
        raise ValueError("expected six local indexed weight shards")
    source_names = [
        "config.json",
        "modeling_llada.py",
        "configuration_llada.py",
        index_name,
        *TOKEN_FILES,
        *shards,
    ]
    model_hashes = {name: file_sha(MODEL / name) for name in source_names}
    record(
        {
            "type": "producer",
            "commit": commit,
            "hashes": hashes,
            "model": str(MODEL),
            "model_hashes": model_hashes,
            "source_hashing_wall_seconds": time.perf_counter() - hash_wall,
            "source_hashing_cpu_seconds": time.process_time() - hash_cpu,
            "model_source_bytes": sum((MODEL / name).stat().st_size for name in source_names),
            "batch": 1,
            "use_cache": False,
            "quantization": "NF4-double-BF16",
            "seed": 87001,
        }
    )
    import torch
    from transformers import AutoModel, BitsAndBytesConfig

    torch.set_num_threads(4)
    torch.manual_seed(87001)
    if not torch.cuda.is_available():
        raise Refusal("CUDA unavailable")
    foreign = processes()
    record(
        {
            "type": "hardware",
            "python": platform.python_version(),
            "pid": os.getpid(),
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("torch", "transformers", "bitsandbytes", "accelerate", "numpy")
            },
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
            "threads": 4,
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
        raise Refusal("foreign CUDA process or less than 7 GiB free before load")
    load_wall, load_cpu = time.perf_counter(), time.process_time()
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
            "allocated_bytes": torch.cuda.memory_allocated(),
            "reserved_bytes": torch.cuda.memory_reserved(),
        }
    )
    selection = None

    def select_head(_module, args):
        if selection is None:
            raise RuntimeError("head called outside a selected query")
        hidden = args[0]
        if hidden.ndim != 3 or hidden.shape[0] != 1:
            raise RuntimeError(f"unsupported hidden shape {tuple(hidden.shape)}")
        return (hidden.index_select(1, selection), *args[1:])

    handle = model.get_output_embeddings().register_forward_pre_hook(select_head)
    labels, length = data["label_ids"], data["length"]
    completed, calls = 0, 0

    @torch.inference_mode()
    def query(canvas, offset, metadata):
        nonlocal selection, calls
        wall, cpu = time.perf_counter(), time.process_time()
        if wall - began > 1800 or processes():
            raise Refusal("30-minute cooperative budget or foreign CUDA process")
        torch.cuda.synchronize()
        event0, event1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        event0.record()
        selection = torch.arange(offset, offset + length, device="cuda")
        tensor = torch.tensor([canvas], device="cuda")
        try:
            calls += 1
            record({"type": "query_begin", "call": calls, **metadata})
            logits = model(tensor, use_cache=False).logits.float()[0]
            if tuple(logits.shape) != (length, VOCAB) or not bool(torch.isfinite(logits).all()):
                raise ValueError("unsupported/nonfinite selected L-head logits")
            logits[:, MASK] = -float("inf")
            probabilities = logits.softmax(-1)
            event1.record()
            array = probabilities.cpu().numpy()
            torch.cuda.synchronize()
            rational_start = time.perf_counter()
            rows, facts = rational_rows(array, labels)
            rational_seconds = time.perf_counter() - rational_start
            return rows, {
                **facts,
                "call": calls,
                "wall_seconds": time.perf_counter() - wall,
                "cpu_process_seconds": time.process_time() - cpu,
                "cuda_event_seconds": event0.elapsed_time(event1) / 1000,
                "rationalization_seconds": rational_seconds,
                "allocated_bytes": torch.cuda.memory_allocated(),
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                "reserved_bytes": torch.cuda.memory_reserved(),
            }
        finally:
            selection = None

    try:
        for case, item in enumerate(data["cases"]):
            offset, canvas = item["offset"], item["input_ids"]
            rows, facts = query(canvas, offset, {"case": case, "block": "root"})
            root_a = [rows[0][word[0]] for word in data["a_words"]]
            root_b = [
                prod((rows[i + 1][token] for i, token in enumerate(word)), start=F(1))
                for word in data["b_words"]
            ]
            products = [root_a[a] * root_b[b - len(root_a)] for a, b in data["edges"]]
            record(
                {
                    "type": "root",
                    "case": case,
                    "row": item["row"],
                    **facts,
                    "root_a": list(map(fraction, root_a)),
                    "root_b": list(map(fraction, root_b)),
                    "caps": list(map(fraction, [x / 2 for x in root_a + root_b])),
                    "root_products": list(map(fraction, products)),
                    "proposal": max(range(77), key=lambda e: (products[e], -e)),
                }
            )
            for block, words in (("A", data["a_words"]), ("B", data["b_words"])):
                for index, word in enumerate(words):
                    pinned = canvas.copy()
                    start = offset + (block == "B")
                    pinned[start : start + len(word)] = word
                    vertex = index if block == "A" else len(root_a) + index
                    rows, facts = query(
                        pinned, offset, {"case": case, "block": block, "vertex": vertex}
                    )
                    values = {}
                    for edge, (a, b) in enumerate(data["edges"]):
                        if vertex not in (a, b):
                            continue
                        conditional = (
                            prod((rows[i][labels[edge][i]] for i in range(1, length)), start=F(1))
                            if block == "A"
                            else rows[0][labels[edge][0]]
                        )
                        cap = root_a[index] / 2 if block == "A" else root_b[index] / 2
                        values[edge] = fraction(cap * conditional)
                    record(
                        {
                            "type": "star",
                            "case": case,
                            "block": block,
                            "vertex": vertex,
                            "components": values,
                            **facts,
                        }
                    )
            completed += 1
            record({"type": "case_complete", "case": case, "calls": calls})
    finally:
        handle.remove()
        record(
            {
                "type": "capture_progress",
                "completed": completed,
                "calls": calls,
                "wall_seconds": time.perf_counter() - began,
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
            parser.error("preparation writes only the fixed new native-inputs-v1.json")
        prepare()
        return
    if args.output is None or not args.output.resolve().is_relative_to(ROOT / "artifacts"):
        parser.error("capture requires a new --output under ignored artifacts/")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:

        def record(value):
            stream.write(json.dumps(value, sort_keys=True) + "\n")
            stream.flush()

        capture_began = time.perf_counter()
        try:
            capture(record)
        except (Exception, KeyboardInterrupt) as error:
            refused = isinstance(error, (Refusal, MemoryError)) or (
                type(error).__name__ == "OutOfMemoryError"
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
                    "wall_seconds": time.perf_counter() - capture_began,
                }
            )
            raise
        record(
            {
                "type": "terminal",
                "status": "COMPLETE",
                "wall_seconds": time.perf_counter() - capture_began,
            }
        )


if __name__ == "__main__":
    main()
