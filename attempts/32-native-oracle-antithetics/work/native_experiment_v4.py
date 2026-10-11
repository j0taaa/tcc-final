"""Opt-in frozen GSM questions: complete EPIC, all statuses and strong controls."""

import argparse
import functools
import hashlib
import json
import os
import random
import subprocess
import time
import urllib.request
from fractions import Fraction
from pathlib import Path

import torch
from constrained_diffusion.constrain_utils import compile_lex_map, preprocessed_generate_stuff
from rustformlang.cfg import CFG

from .native_decode_v4 import CachedModel, decode
from .native_noise_v4 import PairBook, coupled_noise
from .numeric_partition import NumericPartition
from .numeric_task import correct, task
from .raw_anchored_ledger import AnchoredLedger
from .raw_noise import coupled_noise as raw_noise

HERE = Path(__file__).parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_sources(commit):
    """Require every current producer/config/input to match one committed tree."""
    files = [
        *HERE.glob("*.py"),
        *(
            HERE / f
            for f in (
                "protocol-v4.json",
                "protocol-v4.md",
                "protocol-v4-inputs.md",
                "gsm-inputs-v4.json",
            )
        ),
    ]
    result = {}
    for path in files:
        relative = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        content = subprocess.check_output(["git", "show", f"{commit}:{relative}"])
        if content != path.read_bytes():
            raise ValueError(f"not frozen at source commit: {path}")
        result[path.name] = digest(path)
    return result


def gold_answers(manifest, split):
    """Only called after source freeze; test branch needs signed-off decision."""
    source = manifest["files"][split]
    data = urllib.request.urlopen(source["url"], timeout=30).read()
    if hashlib.sha256(data).hexdigest() != source["sha256"]:
        raise ValueError("pinned public gold file hash mismatch")
    lines = data.splitlines()
    selected = {}
    for record in manifest["selections"][split]:
        raw = json.loads(lines[int(record["id"].split(":")[1])])
        if raw["question"] != record["question"]:
            raise ValueError("question identity mismatch")
        selected[record["id"]] = raw["answer"]
    return selected


def fingerprint(sample):
    return tuple(
        sample[k]
        for k in (
            "original_ids_sha256",
            "output",
            "status",
            "native_complete",
            "rejections",
            "recovery",
            "queries",
        )
    )


def specification(config, phase, decision):
    seeds = config["development_seeds"]
    methods = config["methods"]
    if phase == "pilot":
        seeds = seeds[:1]
    if phase == "confirmation":
        if decision is None:
            raise ValueError("confirmation requires development decision file")
        approved = json.loads(decision.read_text())
        if not approved.get("approved") or approved["protocol_sha256"] != digest(
            HERE / "protocol-v4.json"
        ):
            raise ValueError("independent branch not activated by frozen development gate")
        chosen = approved["method"]
        if chosen not in {m["id"] for m in methods if m.get("candidate")}:
            raise ValueError("unknown selected candidate")
        methods = [m for m in methods if not m.get("candidate") or m["id"] == chosen]
        seeds = config["confirmation_seeds"]
    return seeds, methods


def main():
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument(
        "--phase", choices=("pilot", "development", "confirmation"), default="pilot"
    )
    parser.add_argument("--decision", type=Path)
    args = parser.parse_args()
    metadata_path = args.output.with_suffix(".metadata.json")
    io_path = args.output.with_suffix(".io.jsonl")
    if args.output.exists() or metadata_path.exists() or io_path.exists():
        raise SystemExit("refuse to overwrite any prior evidence")
    sources = frozen_sources(args.source_commit)
    config = json.loads((HERE / "protocol-v4.json").read_text())
    manifest = json.loads((HERE / "gsm-inputs-v4.json").read_text())
    if digest(HERE / "gsm-inputs-v4.json") != config["inputs_sha256"]:
        raise ValueError("frozen input mismatch")
    seeds, methods = specification(config, args.phase, args.decision)
    split = "test" if args.phase == "confirmation" else "train"
    # This is the first access to selected labels by the evaluation producer.
    gold = gold_answers(manifest, split)
    os.environ.update(config["native_env"])
    torch.set_num_threads(config["cpu_threads"])
    loading = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        config["model_id"], revision=config["revision"], local_files_only=True
    )
    actual = AutoModel.from_pretrained(
        config["model_id"],
        revision=config["revision"],
        local_files_only=True,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
    ).eval()
    torch.cuda.synchronize()
    model_load_wall = time.perf_counter() - loading
    if actual.config._commit_hash != config["revision"]:
        raise ValueError("model revision mismatch")
    model = CachedModel(actual, config["cache_bytes"])
    setup = time.perf_counter(), time.process_time()
    t = task("")
    grammar = CFG.from_text(t["grammar"], "S").to_normal_form()
    lex = compile_lex_map(t["lexical"])
    additional_stuff = preprocessed_generate_stuff(tokenizer, grammar, lex)
    grammar_wall, grammar_cpu = time.perf_counter() - setup[0], time.process_time() - setup[1]
    setup = time.perf_counter(), time.process_time()
    pieces = [
        tokenizer.decode([i], clean_up_tokenization_spaces=False)
        for i in range(actual.config.vocab_size)
    ]
    partition = NumericPartition(pieces)
    partition.tensor(model.device)
    torch.cuda.synchronize()
    class_wall, class_cpu = time.perf_counter() - setup[0], time.process_time() - setup[1]
    records = manifest["selections"][split]
    deployment_count = len(records) * len(seeds)
    metadata = dict(
        phase=args.phase,
        source_commit=args.source_commit,
        sources=sources,
        config=config,
        torch=torch.__version__,
        hardware=torch.cuda.get_device_name(),
        model_load_wall_excluded_common=model_load_wall,
        grammar_setup_wall=grammar_wall,
        grammar_setup_cpu=grammar_cpu,
        class_setup_wall=class_wall,
        class_setup_cpu=class_cpu,
        partition_ids=len(partition.ids),
        partition_sha256=partition.signature,
        native_prelex="pinned early return: no full lexical-token table",
        costs="first-use and campaign amortization; all native recovery and new forwards",
        scope="full original native ranking rows; approximate known_p law disclosed",
        conditions="no heavy simultaneous checks/model work intended during timings",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    references = {}
    with torch.no_grad(), args.output.open("x") as stream, io_path.open("x") as io_stream:
        for record in records:
            prompt_start = time.perf_counter(), time.process_time()
            spec = task(record["question"])
            chat = tokenizer.apply_chat_template(
                [{"role": "user", "content": spec["instruction"]}],
                add_generation_prompt=True,
                tokenize=True,
            )
            all_ids = chat + tokenizer.encode(spec["prefix"], add_special_tokens=False)
            ids = torch.tensor([all_ids], device=model.device)
            torch.cuda.synchronize()
            prompt_wall = time.perf_counter() - prompt_start[0]
            prompt_cpu = time.process_time() - prompt_start[1]
            runs = [
                (seed, temperature, method)
                for seed in seeds
                for temperature in config["temperatures"]
                for method in methods
            ]
            runs.append((seeds[0], 0.0, dict(id="deterministic", kind="iid", K=1)))
            shuffle = random.Random(
                config["method_shuffle_offset"] + int(record["selection_sha256"][:12], 16)
            )
            shuffle.shuffle(runs)
            for seed, temperature, method in runs:
                row = dict(
                    id=record["id"],
                    method=method["id"],
                    temperature=temperature,
                    seed=seed,
                    prompt_tokens=len(all_ids),
                    pair=[],
                    pass2=False,
                )
                if len(all_ids) > config["max_prompt_tokens"]:
                    row.update(
                        status="prompt_budget_refusal",
                        full_wall=prompt_wall,
                        full_cpu=prompt_cpu,
                        first_equal=None,
                    )
                else:
                    pair_start = time.perf_counter(), time.process_time()
                    model.clear()
                    torch.cuda.reset_peak_memory_stats()
                    book, hook = None, None
                    uses_class = method["kind"] in ("walk", "pool", "pool_batch", "known_p")
                    auxiliary_seed = seed + config["auxiliary_seed_offset"]
                    if uses_class:
                        book = PairBook(
                            auxiliary_seed, budget=method["budget"], strategy=method["kind"]
                        )
                        hook = functools.partial(coupled_noise, partition=partition)
                    elif method["kind"] == "raw":
                        book = AnchoredLedger(2, random.Random(auxiliary_seed))
                        hook = raw_noise
                    namespace = (
                        record["id"],
                        spec["grammar_sha256"],
                        config["revision"],
                        tuple(config["native_env"].items()),
                        temperature,
                    )
                    samples = []
                    for label in range(method["K"]):
                        actual_temperature = (
                            0.0 if method["kind"] == "mixed" and label else temperature
                        )
                        sample = decode(
                            model,
                            tokenizer,
                            ids,
                            len(chat),
                            grammar,
                            lex,
                            spec["lexical"],
                            config,
                            actual_temperature,
                            seed + label * config["torch_seed_label_offset"],
                            book=book,
                            label=label,
                            mode=method.get("mode"),
                            coordinate=config["coordinate"],
                            namespace=namespace,
                            hook=hook,
                            additional_stuff=additional_stuff,
                        )
                        verifying = time.perf_counter(), time.process_time()
                        parsed = sample.pop("parsed")
                        sample["typed_valid"] = (
                            isinstance(parsed, dict)
                            and set(parsed) == {"answer"}
                            and isinstance(parsed["answer"], Fraction)
                        )
                        try:
                            sample["correct"] = correct(parsed, gold[record["id"]])
                        except (ValueError, TypeError, ZeroDivisionError) as exc:
                            sample["correct"] = False
                            sample["verifier_error"] = str(exc)
                        sample["verifier_wall"] = time.perf_counter() - verifying[0]
                        sample["verifier_cpu"] = time.process_time() - verifying[1]
                        samples.append(sample)
                    key = (record["id"], seed, temperature)
                    first = fingerprint(samples[0])
                    first_equal = first == references.setdefault(key, first)
                    row.update(
                        pair=samples,
                        pass2=any(s["correct"] for s in samples),
                        first_equal=first_equal,
                        shared_nodes=book.shared if uses_class else None,
                        auxiliary_rows=book.extra_draws if uses_class else 0,
                        forward_seconds=model.forward_wall,
                        head_digests=model.head_digests,
                        peak_cuda_bytes=torch.cuda.max_memory_allocated(),
                    )
                    model.clear()
                    measured_wall = time.perf_counter() - pair_start[0]
                    measured_cpu = time.process_time() - pair_start[1]
                    setup_wall = grammar_wall + (class_wall if uses_class else 0.0)
                    setup_cpu = grammar_cpu + (class_cpu if uses_class else 0.0)
                    divisor = len(records) if temperature == 0 else deployment_count
                    row.update(
                        batch_wall=measured_wall,
                        batch_cpu=measured_cpu,
                        prompt_wall=prompt_wall,
                        prompt_cpu=prompt_cpu,
                        first_use_wall=setup_wall + prompt_wall + measured_wall,
                        first_use_cpu=setup_cpu + prompt_cpu + measured_cpu,
                        full_wall=setup_wall / divisor + prompt_wall + measured_wall,
                        full_cpu=setup_cpu / divisor + prompt_cpu + measured_cpu,
                    )
                serializing = time.perf_counter(), time.process_time()
                json.dumps(row, ensure_ascii=False)
                row["serialization_wall"] = time.perf_counter() - serializing[0]
                row["serialization_cpu"] = time.process_time() - serializing[1]
                # Include measured JSON construction; buffered output flushed below.
                row["full_wall"] += row["serialization_wall"]
                row["full_cpu"] += row["serialization_cpu"]
                writing = time.perf_counter(), time.process_time()
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                print(
                    json.dumps(
                        {
                            k: row[k]
                            for k in ("id", "method", "temperature", "seed", "pass2", "first_equal")
                        }
                    ),
                    flush=True,
                )
                io_stream.write(
                    json.dumps(
                        dict(
                            id=row["id"],
                            method=row["method"],
                            temperature=temperature,
                            seed=seed,
                            output_wall=time.perf_counter() - writing[0],
                            output_cpu=time.process_time() - writing[1],
                        )
                    )
                    + "\n"
                )
                io_stream.flush()


if __name__ == "__main__":
    main()
