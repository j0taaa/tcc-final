"""Replay frozen V3 inputs for ALL V5 layout/backend/threshold controls."""

import argparse
import hashlib
import json
import signal
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

from .preflight_gpu import evaluate
from .strong_head import SortedHeadPlan


def main(output, source, inputs):
    output.mkdir(parents=True, exist_ok=False)
    pin = json.loads((Path(__file__).parent / "cce-source-v3.json").read_text())
    assert (
        subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        == pin["commit"]
    )
    for rel, sha in pin["sha256"].items():
        assert hashlib.sha256((source / rel).read_bytes()).hexdigest() == sha
    sys.path.insert(0, str(source))
    producer = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    config = {
        "producer": producer,
        "inputs": str(inputs),
        "CCE_commit": pin["commit"],
        "torch": torch.__version__,
        "dot_precision": "ieee",
        "filtering": False,
        "source_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*.py")
        },
        "thresholds": [0, 8, 32, 128],
        "backends": ["dense", "checkpoint", "CCE"],
        "competitive_timing": False,
        "new_model_forwards": 0,
        "model_parameter_reads": 0,
    }
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    old_precision = torch.get_float32_matmul_precision()
    cpu_rng, cuda_rng = torch.get_rng_state(), torch.cuda.get_rng_state_all()
    records = []

    def timeout(signum, frame):
        raise TimeoutError("V5 fixture120s resource bound")

    handler = signal.signal(signal.SIGALRM, timeout)
    try:
        torch.set_float32_matmul_precision("highest")
        for index in range(8):
            signal.alarm(120)
            path = inputs / f"input-{index}.npz"
            with np.load(path) as packet:
                data = tuple(
                    torch.from_numpy(packet[key].copy()) for key in ("H", "W", "bias", "targets")
                )
                mapping = packet["mapping"].tolist()
                dz, dt = [torch.from_numpy(packet[key].copy()) for key in ("dz", "dt")]
            full_data = (*data, mapping, dz, dt)
            reference = evaluate("dense64", full_data)
            for backend in ("dense", "checkpoint", "CCE"):
                for threshold in (0, 8, 32, 128):
                    row = {
                        "fixture": index,
                        "backend": backend,
                        "threshold": threshold,
                        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                    try:
                        h0, w0, b0, t0 = [v.cuda() for v in data]
                        plan = SortedHeadPlan(
                            mapping, device="cuda", threshold=threshold, panel=32, backend=backend
                        )
                        h = h0.detach().requires_grad_()
                        w, b = [x[plan.perm].detach().requires_grad_() for x in (w0, b0)]
                        z, t = plan(h, w, b, t0)
                        loss = (
                            dz.cuda() * torch.where(torch.isfinite(z), z, torch.zeros_like(z))
                        ).sum() + (dt.cuda() * t).sum()
                        loss.backward()
                        actual = tuple(
                            v.detach().cpu().double().numpy()
                            for v in (z, t, h.grad, w.grad[plan.inv], b.grad[plan.inv])
                        )
                        largest, scaled, checked = 0.0, 0.0, 0
                        for a, ref in zip(actual, reference, strict=True):
                            assert np.array_equal(np.isneginf(a), np.isneginf(ref))
                            mask = np.isfinite(ref)
                            assert np.isfinite(a[mask]).all()
                            error = np.abs(a[mask] - ref[mask])
                            largest = max(largest, float(error.max(initial=0)))
                            scaled = max(
                                scaled,
                                float((error / (5e-5 + 5e-5 * np.abs(ref[mask]))).max(initial=0)),
                            )
                            checked += a.size
                        assert scaled <= 1, (largest, scaled)
                        row.update(
                            status="PASS",
                            checked=checked,
                            max_abs_error=largest,
                            max_scaled_error=scaled,
                        )
                    except Exception as exc:
                        row.update(status="ERROR", exception=type(exc).__name__, message=str(exc))
                    records.append(row)
                    with (output / "records.jsonl").open("a") as stream:
                        stream.write(json.dumps(row) + "\n")
                    print(json.dumps(row), flush=True)
                    if row.get("exception") == "TimeoutError":
                        break
            signal.alarm(0)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, handler)
        torch.set_float32_matmul_precision(old_precision)
        torch.set_rng_state(cpu_rng)
        torch.cuda.set_rng_state_all(cuda_rng)
    report = {
        "status": "PASS"
        if len(records) == 96 and all(r["status"] == "PASS" for r in records)
        else "ERROR",
        "records": len(records),
        "checked": sum(r.get("checked", 0) for r in records),
        "new_model_forwards": 0,
        "model_parameter_reads": 0,
        "optimizer_model_updates": 0,
        "competitive_timing": False,
        "RNG_restored": True,
        "matmul_precision_restored": True,
    }
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)
    return report["status"] == "PASS"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cce-source", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if main(args.output, args.cce_source, args.inputs) else 1)
