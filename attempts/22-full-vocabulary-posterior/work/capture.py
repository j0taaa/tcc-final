"""Opt-in actual frozen full-vocabulary model predictions, no reference injection."""

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from random import Random
from time import perf_counter, process_time

from .corpus import select_documents

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    import numpy as np
    import torch
    from scripts.exact_commit.mdlm_cpu import load_cpu_model
    from transformers import AutoTokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--phase", choices=("development", "heldout", "fresh"), required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("freeze source/protocol before model capture")
    if args.output.exists():
        raise FileExistsError(args.output)
    protocol = json.loads((WORK / "protocol.json").read_text())
    config = json.loads((ROOT / protocol["model_config"]).read_text())
    torch.set_num_threads(config["torch_cpu_threads"])
    torch.set_flush_denormal(False)
    torch.manual_seed(protocol["seed"])
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    start, cpu = perf_counter(), process_time()
    tokenizer = AutoTokenizer.from_pretrained(
        config["tokenizer_id"],
        revision=config["tokenizer_revision"],
        cache_dir=str(ROOT / ".cache/mdlm"),
        local_files_only=True,
    )
    docs = select_documents(args.source, tokenizer, protocol)
    selected = docs[("development", "heldout", "fresh").index(args.phase)]
    model, hashes, adapted = load_cpu_model(config, ROOT / ".cache/mdlm")
    model.to(args.device)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    args.output.mkdir(parents=True)
    vocabulary = [
        tokenizer.convert_ids_to_tokens(i) if i not in tokenizer.all_special_ids else None
        for i in range(len(tokenizer))
    ] + [None]
    (args.output / "vocabulary.json").write_text(json.dumps(vocabulary) + "\n")
    with torch.inference_mode():
        model(
            input_ids=torch.full((1, 32), config["mask_token_id"], device=args.device),
            timesteps=torch.zeros(1, device=args.device),
        )
    if args.device == "cuda":
        torch.cuda.synchronize()
    metadata = dict(
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        protocol_sha256=digest((WORK / "protocol.json").read_bytes()),
        phase=args.phase,
        device=args.device,
        config=config,
        model_hashes=hashes,
        adapted_model_sha256=adapted,
        vocabulary_sha256=digest((args.output / "vocabulary.json").read_bytes()),
        selected=selected,
        versions=dict(
            torch=torch.__version__, python=platform.python_version(), cuda=torch.version.cuda
        ),
        gpu=torch.cuda.get_device_name() if args.device == "cuda" else None,
        startup=dict(
            wall=perf_counter() - start,
            cpu=process_time() - cpu,
            scope=(
                "common model/tokenizer load, corpus tokenization and warmup; "
                "recorded outside frozen query"
            ),
        ),
        source_sha256={p.name: digest(p.read_bytes()) for p in WORK.glob("*.py")},
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    for example in selected:
        for masks in protocol["mask_counts"]:
            positions = sorted(
                Random(protocol["seed"] + int(example["key"][:12], 16) + masks).sample(
                    range(len(example["tokens"])), masks
                )
            )
            canvas = [None if p in positions else t for p, t in enumerate(example["tokens"])]
            ids = [config["mask_token_id"] if t is None else t for t in canvas]
            if args.device == "cuda":
                torch.cuda.synchronize()
            begin, cpu_begin = perf_counter(), process_time()
            with torch.inference_mode():
                logits = model(
                    input_ids=torch.tensor([ids], device=args.device),
                    timesteps=torch.zeros(1, device=args.device),
                )[0]
                scores = logits[positions].to(device="cpu", dtype=torch.float64).clone()
                scores[:, config["mask_token_id"]] = float("-inf")
                probabilities = scores.softmax(-1).numpy().copy()
            if args.device == "cuda":
                torch.cuda.synchronize()
            measured = dict(wall=perf_counter() - begin, cpu=process_time() - cpu_begin)
            name = f"{example['key']}-{masks}"
            np.save(args.output / (name + ".npy"), probabilities, allow_pickle=False)
            result = dict(
                case=example["key"],
                mask_count=masks,
                canvas=canvas,
                positions=positions,
                forward_and_softmax=measured,
                probabilities_sha256=digest((args.output / (name + ".npy")).read_bytes()),
                vocabulary=len(vocabulary),
                status="captured",
            )
            (args.output / (name + ".json")).write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps({k: result[k] for k in ("case", "mask_count", "status")}), flush=True)


if __name__ == "__main__":
    main()
