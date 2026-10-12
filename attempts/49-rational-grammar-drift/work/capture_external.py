"""Opt-in actual MDLM full heads for every predeclared external frame."""

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from random import Random
from time import perf_counter, process_time
from zipfile import ZipFile

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def select(archive, tokenizer, protocol):
    """Independent local selection; no imports from a mutable past attempt."""
    corpus = protocol["source_corpus"]
    found = {}
    with ZipFile(archive) as source:
        for name in sorted(source.namelist()):
            if f"JSONTestSuite-{corpus['revision']}/test_parsing/y_" not in name:
                continue
            raw = source.read(name)
            try:
                text = raw.decode("utf8")
                value = json.loads(
                    text, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x))
                )
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(value, (dict, list)):
                continue
            tokens = tokenizer.encode(text, add_special_tokens=False)
            low, high = protocol["external"]["eligible_tokens"]
            if low <= len(tokens) <= high:
                key = hashlib.sha256(f"{corpus['identity_seed']}/{text}".encode()).hexdigest()
                found[key] = dict(
                    key=key,
                    text=text,
                    tokens=tokens,
                    file=Path(name).name,
                    source_sha256=hashlib.sha256(raw).hexdigest(),
                    audit_split="seen_regression"
                    if key == protocol["seen_development_document"]
                    else "unseen_A49_document",
                )
    expected = {r["key"]: (r["file"], r["source_sha256"]) for r in corpus["cases"]}
    assert len(found) == corpus["eligible_count"]
    assert {key: (r["file"], r["source_sha256"]) for key, r in found.items()} == expected
    return [found[key] for key in sorted(found)]


def run(archive, output, device):
    import numpy as np
    import torch
    from scripts.exact_commit.mdlm_cpu import load_cpu_model
    from transformers import AutoTokenizer

    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("freeze source/protocol with a clean tree before actual forwards")
    if output.exists():
        raise FileExistsError(output)
    protocol = json.loads((WORK / "protocol-v23.json").read_text())
    config = json.loads((WORK / "model-v23.json").read_text())
    torch.set_num_threads(config["torch_cpu_threads"])
    torch.set_flush_denormal(False)
    torch.manual_seed(protocol["seed"])
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    started = perf_counter(), process_time()
    tokenizer = AutoTokenizer.from_pretrained(
        config["tokenizer_id"],
        revision=config["tokenizer_revision"],
        cache_dir=str(ROOT / ".cache/mdlm"),
        local_files_only=True,
    )
    selected = select(archive, tokenizer, protocol)
    model, hashes, adapted = load_cpu_model(config, ROOT / ".cache/mdlm")
    model.to(device).eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    output.mkdir(parents=True)
    vocabulary = [
        tokenizer.convert_ids_to_tokens(i) if i not in tokenizer.all_special_ids else None
        for i in range(len(tokenizer))
    ] + [None]
    (output / "vocabulary.json").write_text(json.dumps(vocabulary) + "\n")
    with torch.inference_mode():
        model(
            input_ids=torch.full((1, 32), config["mask_token_id"], device=device),
            timesteps=torch.zeros(1, device=device),
        )
    if device == "cuda":
        torch.cuda.synchronize()
    metadata = dict(
        producer=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        protocol_sha256=digest(WORK / "protocol-v23.json"),
        archive_sha256=digest(archive),
        config=config,
        model_hashes=hashes,
        adapted_model_sha256=adapted,
        model_loader_sha256=digest(ROOT / "scripts/exact_commit/mdlm_cpu.py"),
        selected=selected,
        vocabulary_sha256=digest(output / "vocabulary.json"),
        device=device,
        versions=dict(torch=torch.__version__, python=platform.python_version(), cuda=torch.version.cuda),
        gpu=torch.cuda.get_device_name() if device == "cuda" else None,
        startup_wall_cpu=[perf_counter() - started[0], process_time() - started[1]],
        scope="15 actual frozen heads plus ONE warmup; no training/updates or iterative decoder",
    )
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    for example in selected:
        for masks in protocol["mask_counts"]:
            positions = sorted(
                Random(protocol["seed"] + int(example["key"][:12], 16) + masks).sample(
                    range(len(example["tokens"])), masks
                )
            )
            canvas = [None if p in positions else t for p, t in enumerate(example["tokens"])]
            ids = [config["mask_token_id"] if t is None else t for t in canvas]
            if device == "cuda":
                torch.cuda.synchronize()
            began = perf_counter(), process_time()
            with torch.inference_mode():
                logits = model(
                    input_ids=torch.tensor([ids], device=device),
                    timesteps=torch.zeros(1, device=device),
                )[0]
                original_scores = logits[positions].to(device="cpu", dtype=torch.float64)
                assert original_scores.shape == (masks, len(vocabulary))
                scores = original_scores.clone()
                scores[:, config["mask_token_id"]] = float("-inf")
                probabilities = scores.softmax(-1).numpy().copy()
            if device == "cuda":
                torch.cuda.synchronize()
            forward_cost = [perf_counter() - began[0], process_time() - began[1]]
            name = f"{example['key']}-{masks}"
            np.save(output / (name + ".npy"), probabilities, allow_pickle=False)
            np.save(output / (name + ".logits.npy"), original_scores.numpy(), allow_pickle=False)
            result = dict(
                case=example["key"],
                mask_count=masks,
                audit_split=example["audit_split"],
                canvas=canvas,
                positions=positions,
                forward_and_softmax_wall_cpu=forward_cost,
                probabilities_sha256=digest(output / (name + ".npy")),
                raw_logits_sha256=digest(output / (name + ".logits.npy")),
                vocabulary=len(vocabulary),
                status="CAPTURED_ACTUAL_MODEL_HEAD",
            )
            (output / (name + ".json")).write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps({k: result[k] for k in ["case", "mask_count", "audit_split", "status"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    args = parser.parse_args()
    run(args.source, args.output, args.device)
