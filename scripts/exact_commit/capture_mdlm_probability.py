"""Capture fresh official MDLM CPU predictions for all frozen application probes."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from scripts.exact_commit.run_conflict_real import sha, system_data, write

from mwpc_exact.experiments.metadata import collect_system_metadata

ROOT = Path(__file__).resolve().parents[2]


def planned_case_ids(config):
    slots = config["slots"]
    if (
        not slots
        or any(type(n) is not int or n <= 0 for n in slots)
        or len(set(slots)) != len(slots)
    ):
        raise ValueError("capture slots must be distinct positive integers")
    ids = tuple(f"{probe['id']}-{n}" for probe in config["probes"] for n in slots)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("capture case IDs must be nonempty and unique")
    return ids


def capture(config_path, output):
    import numpy as np
    import torch
    from scripts.exact_commit.mdlm_cpu import load_cpu_model
    from transformers import AutoTokenizer

    config = json.loads(config_path.read_text())
    expected_ids = planned_case_ids(config)
    system = collect_system_metadata(ROOT)
    if system.git_dirty is not False:
        raise ValueError("commit producing code/config before fresh forwards")
    output.mkdir(parents=True, exist_ok=False)
    write(output / "config.json", config)
    torch.set_num_threads(config["torch_cpu_threads"])
    torch.manual_seed(config["seed"])
    tokenizer = AutoTokenizer.from_pretrained(
        config["tokenizer_id"],
        revision=config["tokenizer_revision"],
        cache_dir=str(ROOT / ".cache/mdlm"),
    )
    model, hashes, adapted_hash = load_cpu_model(config, ROOT / ".cache/mdlm")
    write(
        output / "metadata.json",
        {
            "git_commit": system.git_commit,
            "git_dirty": False,
            "hardware_software": system_data(system),
            "config_source": str(config_path.relative_to(ROOT)),
            "config_sha256": sha(config_path),
            "checkpoint_sha256": hashes,
            "adapted_model_sha256": adapted_hash,
            "model_id": config["model_id"],
            "model_revision": config["model_revision"],
            "tokenizer_revision": config["tokenizer_revision"],
            "numeric_reference": config["numeric_reference"],
            "torch_threads": torch.get_num_threads(),
            "device": "cpu",
            "recorded_forwards": len(expected_ids),
            "warmup_forwards": 1,
        },
    )
    pieces = [
        tokenizer.convert_ids_to_tokens(t) if t not in tokenizer.all_special_ids else None
        for t in range(len(tokenizer))
    ] + [None]
    write(output / "tokenizer-pieces.json.gz", pieces)
    with torch.inference_mode():
        model(
            input_ids=torch.full((1, 32), config["mask_token_id"], dtype=torch.long),
            timesteps=torch.zeros(1),
        )
        for probe in config["probes"]:
            prefix = tokenizer.encode(probe["prefix"], add_special_tokens=False)
            suffix = tokenizer.encode(probe["suffix"], add_special_tokens=False)
            for slots in config["slots"]:
                name = f"{probe['id']}-{slots}"
                canvas = prefix + [config["mask_token_id"]] * slots + suffix
                started = time.perf_counter()
                logits = model(input_ids=torch.tensor([canvas]), timesteps=torch.zeros(1))[
                    0, len(prefix) : len(prefix) + slots
                ]
                forward = time.perf_counter() - started
                normalized = logits.to(torch.float64).clone()
                normalized[:, config["mask_token_id"]] = float("-inf")
                probabilities = normalized.softmax(-1)
                np.savez_compressed(
                    output / f"{name}.npz",
                    logits=logits.numpy(),
                    probabilities=probabilities.numpy(),
                )
                write(
                    output / f"{name}.json",
                    {
                        "id": name,
                        "probe": probe,
                        "slots": slots,
                        "canvas": [None if t == config["mask_token_id"] else t for t in canvas],
                        "masked_positions": list(range(len(prefix), len(prefix) + slots)),
                        "forward_seconds": forward,
                        "model_revision": config["model_revision"],
                        "tokenizer_revision": config["tokenizer_revision"],
                        "seed": config["seed"],
                        "array_file": f"{name}.npz",
                    },
                )
                print(
                    json.dumps(
                        {"id": name, "forward_seconds": forward, "shape": list(logits.shape)}
                    ),
                    flush=True,
                )
    write(
        output / "manifest.json",
        {str(p.relative_to(output)): sha(p) for p in sorted(output.iterdir()) if p.is_file()},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/experiments/m30_probability_cpu_v1.json"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    capture(args.config.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
