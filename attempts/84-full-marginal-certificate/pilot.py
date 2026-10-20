"""Frozen, small discard pilot. No modification of maintained APIs or vendor."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import os
import platform
import re
import subprocess
import time
import urllib.request
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MODEL = (
    Path.home()
    / ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots"
    / "08b83a6feb34df1a6011b80c3c00c7563e963b07"
)
SOURCES = {
    "gsm8k": "https://raw.githubusercontent.com/openai/grade-school-math/3101c7d5072418e28b9008a6636bde82a006892c/grade_school_math/data/test.jsonl",
    "word_sorting": "https://raw.githubusercontent.com/suzgunmirac/BIG-Bench-Hard/9ee07bd481feebf959a6b59d61ea57bdcf30964d/bbh/word_sorting.json",
}
NUMBER = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")


def prefix(confidences, seconds, margin=Fraction(1, 4)):
    """Given descending confidence order, return certified prefix cardinality."""
    error = 0
    upper = 0
    count = 0
    for k, (confidence, runner_up) in enumerate(zip(confidences, seconds, strict=True), 1):
        error += 1 - confidence
        upper = max(upper, runner_up)
        if error + upper < 1 - margin:
            count = k
    return count


def audit():
    """Finite exact oracle for bound, sharpness and the one-item ceiling."""
    rows = [
        tuple(Fraction(x, 5) for x in xs)
        for xs in itertools.product(range(6), repeat=3)
        if sum(xs) == 5
    ]
    cases = 0
    for distributions in itertools.chain(
        itertools.product(rows, repeat=2), itertools.product(rows, repeat=3)
    ):
        dimensions = len(distributions)
        zero = (0,) * dimensions
        ranked = [sorted(row, reverse=True) for row in distributions]
        errors = [1 - row[0] for row in ranked]
        runners = [row[1] for row in ranked]
        if sum(errors) <= 1:
            joint = {zero: 1 - sum(errors)}
            for i, row in enumerate(ranked):
                for value in (1, 2):
                    word = [0] * dimensions
                    word[i] = value
                    joint[tuple(word)] = row[value]
            assert sum(joint.values()) == 1
            for i, row in enumerate(ranked):
                assert all(
                    sum(p for word, p in joint.items() if word[i] == value) == row[value]
                    for value in range(3)
                )
            assert joint[zero] - max(p for word, p in joint.items() if word != zero) == 1 - sum(
                errors
            ) - max(runners)
        order = sorted(range(dimensions), key=lambda i: (errors[i], i))
        cs = [ranked[i][0] for i in order]
        qs = [runners[i] for i in order]
        f = prefix(cs, [1 - c for c in cs])
        r = prefix(cs, qs)
        assert f <= r <= f + 1
        direct = max(
            (
                k
                for k in range(1, dimensions + 1)
                if sum(1 - c for c in cs[:k]) + max(qs[:k]) < Fraction(3, 4)
            ),
            default=0,
        )
        assert r == direct
        cases += 1
    # Enumerate joint integer tables independently; do not assume independence.
    joint_cases = 0
    for counts in itertools.product(range(5), repeat=4):
        if sum(counts) != 4:
            continue
        table = dict(
            zip(
                itertools.product(range(2), repeat=2),
                map(lambda x: Fraction(x, 4), counts),
                strict=True,
            )
        )
        marginals = [
            [sum(p for word, p in table.items() if word[i] == value) for value in range(2)]
            for i in range(2)
        ]
        y = tuple(max(range(2), key=lambda value: marginals[i][value]) for i in range(2))
        lower = max(0, 1 - sum(1 - marginals[i][y[i]] for i in range(2))) - max(
            marginals[i][1 - y[i]] for i in range(2)
        )
        gap = table[y] - max(p for word, p in table.items() if word != y)
        assert gap >= lower
        joint_cases += 1
    # E>1 can leave the marginal-greedy tuple with zero joint mass.
    table3 = {
        word: Fraction(4 if sum(word) == 1 else 1, 15)
        for word in itertools.product(range(2), repeat=3)
        if sum(word) in (1, 2)
    }
    assert sum(table3.values()) == 1
    assert all(
        sum(p for word, p in table3.items() if word[i] == 0) == Fraction(3, 5) for i in range(3)
    )
    assert (0, 0, 0) not in table3
    return {"type": "audit", "marginal_cases": cases, "joint_tables": joint_cases}


def cases(record):
    result = []
    cache = ROOT / ".cache/a84-data"
    cache.mkdir(parents=True, exist_ok=True)
    for family, url in SOURCES.items():
        path = cache / (family + ".json")
        raw = urllib.request.urlopen(url, timeout=30).read()
        path.write_bytes(raw)
        data = (
            [json.loads(line) for line in raw.splitlines()]
            if family == "gsm8k"
            else json.loads(raw)["examples"]
        )
        selected = sorted(
            enumerate(data),
            key=lambda item: (
                hashlib.sha256(
                    item[1]["question" if family == "gsm8k" else "input"].encode()
                ).hexdigest(),
                item[0],
            ),
        )[:8]
        record(
            {
                "type": "dataset",
                "family": family,
                "url": url,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "indices": [i for i, _ in selected],
            }
        )
        for index, item in selected:
            question = item["question" if family == "gsm8k" else "input"]
            gold = item["answer"] if family == "gsm8k" else item["target"]
            instruction = (
                "\nExplain your calculation concisely, then end with Final answer: NUMBER."
                if family == "gsm8k"
                else "\nReturn only the sorted list, separated by spaces, with no explanation."
            )
            case = {
                "family": family,
                "index": index,
                "question": question,
                "gold": gold,
                "prompt": question + instruction,
            }
            record({"type": "case", **case})
            result.append(case)
    return result


def score(case, output):
    if case["family"] == "word_sorting":
        return " ".join(output.split()) == " ".join(case["gold"].split())
    tail = output.rsplit("Final answer:", 1)[-1]
    guesses = NUMBER.findall(tail)
    targets = NUMBER.findall(case["gold"].rsplit("####", 1)[-1])
    try:
        return bool(
            guesses
            and targets
            and Decimal(guesses[-1].replace(",", "")) == Decimal(targets[-1].replace(",", ""))
        )
    except InvalidOperation:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if args.audit:
        print(json.dumps(audit()))
        return
    if args.output is None or args.output.exists():
        raise SystemExit("Specify a NEW --output file; no overwrites")

    def record(data):
        with args.output.open("a") as stream:
            stream.write(json.dumps(data, ensure_ascii=False) + "\n")
        if data["type"] != "case":
            summary = {
                key: value
                for key, value in data.items()
                if key not in ("ids", "output", "selections")
            }
            print(json.dumps(summary, ensure_ascii=False), flush=True)

    try:
        run(record)
    except BaseException as exc:
        record({"type": "fatal", "error": repr(exc)})
        raise


def foreign_gpu_processes():
    raw = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
        text=True,
    )
    return [
        int(line)
        for line in raw.splitlines()
        if line.strip().isdigit() and int(line) != os.getpid()
    ]


def run(record):
    record(
        {
            "type": "producer",
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "protocol_sha256": hashlib.sha256((HERE / "README.md").read_bytes()).hexdigest(),
        }
    )
    record(audit())
    dataset = cases(record)
    import torch
    import transformers
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    torch.set_num_threads(4)
    torch.manual_seed(84001)
    record(
        {
            "type": "hardware",
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "python": platform.python_version(),
            "cuda": torch.version.cuda,
            "packages": {
                name: importlib.metadata.version(name) for name in ("bitsandbytes", "accelerate")
            },
            "driver": subprocess.check_output(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], text=True
            ).strip(),
            "gpu": torch.cuda.get_device_name(0),
            "memory_free_total": torch.cuda.mem_get_info(),
            "model_snapshot": MODEL.name,
            "processes": subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-compute-apps=pid,process_name,used_gpu_memory",
                    "--format=csv,noheader",
                ],
                text=True,
            ).strip(),
        }
    )
    if torch.cuda.mem_get_info()[0] < 7 * 2**30:
        record({"type": "refusal", "reason": "less_than_7GiB_free"})
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
    record(
        {
            "type": "load",
            "seconds": time.perf_counter() - start,
            "allocated_bytes": torch.cuda.memory_allocated(),
        }
    )
    mask = 126336
    terminals = {126081, tokenizer.convert_tokens_to_ids("<|eot_id|>")}
    partial = {}

    @torch.inference_mode()
    def decode(prompt, method, length=256):
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        started = time.perf_counter()
        partial.clear()
        partial.update(started=started, nfe=0, attempted_forwards=0)
        text = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
        )
        input_ids = tokenizer(text, return_tensors="pt")["input_ids"].to("cuda")
        offset = input_ids.shape[1]
        canvas = torch.full((1, offset + length), mask, dtype=torch.long, device="cuda")
        canvas[:, :offset] = input_ids
        partial.update(canvas=canvas, offset=offset)
        selections = []
        nfe = 0
        ended = False
        for block in range(0, length, 32):
            stop = min(length, block + 32)
            while bool((canvas[0, offset + block : offset + stop] == mask).any()):
                partial["attempted_forwards"] = nfe + 1
                logits = model(canvas).logits[0, offset + block : offset + stop].float()
                nfe += 1
                partial["nfe"] = nfe
                logits[:, mask] = -float("inf")
                probabilities = logits.softmax(-1)
                confidence, tokens = probabilities.max(-1)
                positions = torch.nonzero(
                    canvas[0, offset + block : offset + stop] == mask
                ).flatten()
                order = torch.argsort(confidence[positions], descending=True, stable=True)
                positions = positions[order]
                values = confidence[positions]
                errors = 1 - values
                if method == "runner_up":
                    seconds = probabilities[positions].topk(2, dim=-1).values[:, 1]
                    uppers = torch.cummax(seconds, 0).values
                else:
                    uppers = errors
                accepted = torch.nonzero(errors.cumsum(0) + uppers < 0.75).flatten()
                count = int(accepted[-1]) + 1 if accepted.numel() else 1
                selected = positions[:count]
                canvas[0, offset + block + selected] = tokens[selected]
                selections.append(
                    {
                        "block": block,
                        "masked": len(positions),
                        "count": count,
                        "certified": bool(accepted.numel()),
                    }
                )
                tail = canvas[0, offset:]
                terminal_positions = torch.nonzero(
                    (tail == 126081) | (tail == tokenizer.convert_tokens_to_ids("<|eot_id|>"))
                ).flatten()
                if terminal_positions.numel():
                    endpoint = int(terminal_positions[0])
                    if not bool((tail[:endpoint] == mask).any()):
                        ended = True
                        break
                del logits, probabilities
                if nfe >= length:
                    break
            if ended or nfe >= length:
                break
        ids = canvas[0, offset:].tolist()
        endpoint = next((i for i, token in enumerate(ids) if token in terminals), len(ids))
        output_ids = ids[:endpoint]
        incomplete = mask in output_ids
        output = tokenizer.decode(output_ids, skip_special_tokens=False)
        torch.cuda.synchronize()
        return {
            "seconds": time.perf_counter() - started,
            "nfe": nfe,
            "ids": ids,
            "output": output,
            "ended": ended,
            "incomplete": incomplete,
            "truncated": not ended,
            "selections": selections,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
        }

    for method in ("frechet", "runner_up"):
        warm = decode("Say hello.", method, 32)
        record({"type": "warmup", "method": method, "seconds": warm["seconds"], "nfe": warm["nfe"]})
    for repeat in range(2):
        for ordinal, case in enumerate(dataset):
            methods = (
                ("frechet", "runner_up")
                if (ordinal + repeat) % 2 == 0
                else ("runner_up", "frechet")
            )
            for method in methods:
                try:
                    foreign_before = foreign_gpu_processes()
                    result = decode(case["prompt"], method)
                    foreign_after = foreign_gpu_processes()
                    record(
                        {
                            "type": "decode",
                            "family": case["family"],
                            "index": case["index"],
                            "repeat": repeat,
                            "method": method,
                            "correct": score(case, result["output"]) and not result["incomplete"],
                            "foreign_before": foreign_before,
                            "foreign_after": foreign_after,
                            **result,
                        }
                    )
                except Exception as exc:
                    progress = {key: value for key, value in partial.items() if key != "canvas"}
                    if "started" in progress:
                        progress["elapsed_seconds"] = time.perf_counter() - progress.pop("started")
                    try:
                        progress["ids"] = partial["canvas"][0, partial["offset"] :].tolist()
                    except Exception:
                        progress["ids_unavailable"] = True
                    record(
                        {
                            "type": "error",
                            "family": case["family"],
                            "index": case["index"],
                            "repeat": repeat,
                            "method": method,
                            "error": repr(exc),
                            "partial": progress,
                        }
                    )
                    raise


if __name__ == "__main__":
    main()
