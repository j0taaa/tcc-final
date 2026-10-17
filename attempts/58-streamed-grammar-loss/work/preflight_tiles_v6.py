"""All eight old fixtures/four predeclared finite-domain launch configurations."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import torch

from .preflight_gpu import evaluate
from .tiled_head_v6 import finite_domain_head, prepare


def main(output, inputs, implementation="plain"):
    if implementation == "bucketed":
        from .bucket_head_v8 import bucket_head, prepare_bucket

        head_fn, prepare_fn = bucket_head, prepare_bucket
    else:
        head_fn, prepare_fn = finite_domain_head, prepare
    output.mkdir(parents=True, exist_ok=False)
    config = {
        "producer": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*.py")
        },
        "inputs": str(inputs),
        "tiles": [(16, 32), (32, 64), (64, 64), (64, 128)],
        "torch": torch.__version__,
        "merge_implementation": implementation,
        "competitive_timing": False,
        "new_model_forwards": 0,
    }
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    old = torch.get_float32_matmul_precision()
    records = []
    try:
        torch.set_float32_matmul_precision("highest")
        for i in range(8):
            p = inputs / f"input-{i}.npz"
            with np.load(p) as packet:
                h0, w0, b0, t0, dz0, dt0 = [
                    torch.from_numpy(packet[k].copy())
                    for k in ("H", "W", "bias", "targets", "dz", "dt")
                ]
                mapping = packet["mapping"].tolist()
            reference = evaluate("dense64", (h0, w0, b0, t0, mapping, dz0, dt0))
            for tile in ((16, 32), (32, 64), (64, 64), (64, 128)):
                row = {
                    "fixture": i,
                    "tile": tile,
                    "input_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                }
                try:
                    h, w, b = [v.cuda().detach().requires_grad_() for v in (h0, w0, b0)]
                    t, dz, dt = [v.cuda() for v in (t0, dz0, dt0)]
                    z, tt = head_fn(h, w, b, t, prepare_fn(mapping, "cuda", tile))
                    loss = (dz * torch.where(torch.isfinite(z), z, torch.zeros_like(z))).sum() + (
                        dt * tt
                    ).sum()
                    loss.backward()
                    actual = [
                        v.detach().cpu().double().numpy() for v in (z, tt, h.grad, w.grad, b.grad)
                    ]
                    largest, scaled, checked = 0.0, 0.0, 0
                    for a, r in zip(actual, reference, strict=True):
                        assert np.array_equal(np.isneginf(a), np.isneginf(r))
                        mask = np.isfinite(r)
                        assert np.isfinite(a[mask]).all()
                        error = np.abs(a[mask] - r[mask])
                        largest = max(largest, float(error.max(initial=0)))
                        scaled = max(
                            scaled, float((error / (5e-5 + 5e-5 * np.abs(r[mask]))).max(initial=0))
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
    finally:
        torch.set_float32_matmul_precision(old)
    report = {
        "status": "PASS"
        if len(records) == 32 and all(r["status"] == "PASS" for r in records)
        else "ERROR",
        "records": len(records),
        "checked": sum(r.get("checked", 0) for r in records),
        "new_model_forwards": 0,
        "model_parameter_reads": 0,
        "competitive_timing": False,
    }
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)
    return report["status"] == "PASS"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--implementation", choices=("plain", "bucketed"), default="plain")
    args = parser.parse_args()
    raise SystemExit(0 if main(args.output, args.inputs, args.implementation) else 1)
