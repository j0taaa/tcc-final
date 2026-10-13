"""One actual target prediction per admitted canvas; preserve full logits and hashes."""

import argparse
import json
import subprocess
from pathlib import Path
from time import perf_counter, process_time

import numpy as np
import torch
from scripts.exact_commit.mdlm_cpu import load_cpu_model

from .native import ROOT, digest, dump, frame, metadata


def run(output):
    if subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode:
        raise ValueError("freeze tracked source before neural capture")
    meta = metadata()
    initial = json.loads((output / "initial-rows.json").read_text())
    assert len(initial) == 30
    admitted = [row for row in initial if row["status"] == "ADMITTED"]
    summary = dict(
        scope="FUNCTIONAL_RESOURCE_ONLY; no training, latency or semantic superiority",
        producer=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        initial_rows_sha256=digest(output / "initial-rows.json"),
        admitted=len(admitted),
        actual_forwards=0,
        heads=[],
    )
    if not admitted:
        dump(output / "capture-summary.json", summary)
        return
    config = meta["config"]
    torch.set_num_threads(4)
    torch.set_flush_denormal(False)
    torch.manual_seed(202610135013)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    started = perf_counter(), process_time()
    model, hashes, adapted = load_cpu_model(config, ROOT / ".cache/mdlm")
    model.to("cuda").eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    summary.update(
        config=config,
        model_hashes=hashes,
        adapted_model_sha256=adapted,
        model_loader_sha256=digest(ROOT / "scripts/exact_commit/mdlm_cpu.py"),
        torch_version=torch.__version__,
        gpu=torch.cuda.get_device_name(),
    )
    with torch.inference_mode():
        model(
            input_ids=torch.full((1, 32), config["mask_token_id"], device="cuda"),
            timesteps=torch.zeros(1, device="cuda"),
        )
    torch.cuda.synchronize()
    summary["actual_forwards"] = 1
    summary["startup_wall_cpu"] = [perf_counter() - started[0], process_time() - started[1]]
    cached = {}
    for initial_row in admitted:
        name, kind = initial_row["frame"], initial_row["support"]
        data, _ = frame(name)
        canvas = initial_row["canvas"]
        key = tuple(canvas)
        if key not in cached:
            torch.cuda.synchronize()
            started = perf_counter(), process_time()
            ids = [config["mask_token_id"] if t is None else t for t in canvas]
            with torch.inference_mode():
                logits = model(
                    input_ids=torch.tensor([ids], device="cuda"),
                    timesteps=torch.zeros(1, device="cuda"),
                )[0]
                original = logits[data["positions"]].to(device="cpu", dtype=torch.float64)
                assert original.shape == (data["mask_count"], 50258)
                scores = original.clone()
                scores[:, config["mask_token_id"]] = float("-inf")
                probabilities = scores.softmax(-1).numpy().copy()
            torch.cuda.synchronize()
            costs = [perf_counter() - started[0], process_time() - started[1]]
            stem = f"{name}-{kind}-target"
            np.save(output / (stem + ".npy"), probabilities, allow_pickle=False)
            np.save(output / (stem + ".logits.npy"), original.numpy(), allow_pickle=False)
            cached[key] = dict(
                probabilities_file=stem + ".npy",
                probabilities_sha256=digest(output / (stem + ".npy")),
                logits_sha256=digest(output / (stem + ".logits.npy")),
                source_frame=name,
                canvas=canvas,
                diagnostic_forward_softmax_wall_cpu=costs,
            )
            summary["actual_forwards"] += 1
        dump(output / f"{name}-{kind}-head.json", cached[key])
        summary["heads"].append(dict(frame=name, support=kind, **cached[key]))
        dump(output / "capture-summary.json", summary)
    print(
        json.dumps(dict(actual_forwards=summary["actual_forwards"], consumers=len(admitted))),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
