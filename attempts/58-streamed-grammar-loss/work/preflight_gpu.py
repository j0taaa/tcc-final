"""Execute only the frozen synthetic V3 arithmetic packet, never a benchmark."""

import argparse
import hashlib
import json
import random
import signal
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import torch
import triton

from .gpu_head import grouped_gpu, metadata
from .torch_head import grouped_head

SHAPES = (
    (1, 3, 7, 6),
    (4, 3, 7, 6),
    (7, 5, 11, 5),
    (17, 33, 67, 7),
    (33, 65, 257, 13),
    (65, 64, 1024, 17),
    (5, 17, 17, 17),
    (2, 2, 4, 3),
)


def fixture(index):
    n, d, v, c = SHAPES[index]
    gen = torch.Generator().manual_seed(58030 + index)
    mapping = torch.arange(v) % c
    if index >= 3 and index % 2:
        mapping = torch.zeros(v, dtype=torch.long)
        mapping[-(c - 1) :] = torch.arange(1, c)
    mapping = mapping[torch.randperm(v, generator=gen)].tolist()
    if index < 2:
        mapping = [0, 0, 1, 2, 3, 4, 5]
    h, w, b = (0.2 * torch.randn(*shape, generator=gen) for shape in ((n, d), (v, d), (v,)))
    t = torch.randint(v, (n,), generator=gen)
    dz, dt = torch.randn(n, c, generator=gen), torch.randn(n, generator=gen)
    if index == 7:
        h = torch.tensor([[0.1, 0.2], [0.3, -0.1]])
        w = torch.tensor([[0.2, 0.3], [0.4, 0.2], [-0.5, 0.7], [0.1, -0.2]])
        b = torch.tensor([0.0, -torch.inf, -torch.inf, 0.1])
        mapping, t = [0, 1, 1, 2], torch.tensor([0, 3])
        dz, dt = torch.tensor([[1.0, 0.0, 1.0], [1.0, 0.0, 1.0]]), torch.ones(2)
    return h, w, b, t, mapping, dz, dt


def dense(h, w, b, t, mapping):
    logits = h @ w.T + b
    cols = []
    for cls in range(max(mapping) + 1):
        ids = [v for v, c in enumerate(mapping) if c == cls]
        if torch.isneginf(b[ids]).all():
            cols.append(h.new_full((len(h),), -torch.inf))
        else:
            cols.append(torch.logsumexp(logits[:, ids], dim=1))
    return torch.stack(cols, 1), logits.gather(1, t[:, None]).squeeze(1)


def cce(h, w, b, t, mapping):
    from cut_cross_entropy import linear_cross_entropy

    cols = []
    for cls in range(max(mapping) + 1):
        ids = torch.tensor([v for v, c in enumerate(mapping) if c == cls], device=h.device)
        if torch.isneginf(b[ids]).all():
            cols.append(h.new_full((len(h),), -torch.inf))
        else:
            _, z = linear_cross_entropy(
                h,
                w[ids],
                torch.zeros_like(t),
                bias=b[ids],
                reduction="none",
                return_lse=True,
                filter_eps=None,
                accum_e_fp32=True,
                accum_c_fp32=True,
            )
            cols.append(z)
    return torch.stack(cols, 1), (h * w[t]).sum(1) + b[t]


def evaluate(method, data):
    h0, w0, b0, t0, mapping, dz0, dt0 = data
    device = "cpu" if method == "dense64" else "cuda"
    dtype = torch.float64 if method == "dense64" else torch.float32
    h, w, b = [v.to(device=device, dtype=dtype).detach().requires_grad_() for v in (h0, w0, b0)]
    t, dz, dt = (
        t0.to(device),
        dz0.to(device=device, dtype=dtype),
        dt0.to(device=device, dtype=dtype),
    )
    if method == "candidate":
        z, target = grouped_gpu(h, w, b, t, metadata(mapping, device))
    elif method == "checkpoint":
        z, target = grouped_head(h, w, b, t, mapping, panel=32)
    elif method == "CCE":
        z, target = cce(h, w, b, t, mapping)
    else:
        z, target = dense(h, w, b, t, mapping)
    loss = (dz * torch.where(torch.isfinite(z), z, torch.zeros_like(z))).sum() + (dt * target).sum()
    loss.backward()
    if device == "cuda":
        torch.cuda.synchronize()
    return tuple(v.detach().cpu().double().numpy() for v in (z, target, h.grad, w.grad, b.grad))


def main(output, source):
    output.mkdir(parents=True, exist_ok=False)
    pin = json.loads((Path(__file__).parent / "cce-source-v3.json").read_text())
    assert (
        subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        == pin["commit"]
    )
    for rel, digest in pin["sha256"].items():
        assert hashlib.sha256((source / rel).read_bytes()).hexdigest() == digest
    sys.path.insert(0, str(source))
    producer = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    source_hashes = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path(__file__).parent.glob("*.py")
    }
    config = {
        "producer": producer,
        "source_sha256": source_hashes,
        "CCE_commit": pin["commit"],
        "torch": torch.__version__,
        "triton": triton.__version__,
        "packaging": version("packaging"),
        "CUDA": torch.version.cuda,
        "device": torch.cuda.get_device_name(0),
        "dtype": "float32",
        "dot_precision": "ieee",
        "gradient_filtering": False,
        "shapes": SHAPES,
        "new_model_forwards": 0,
        "new_model_parameter_reads": 0,
        "optimizer_updates": 0,
        "competitive_timing": False,
    }
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    start, initial = time.monotonic(), torch.cuda.memory_allocated()
    precision = torch.get_float32_matmul_precision()
    python_state, numpy_state = random.getstate(), np.random.get_state()
    cpu_rng, cuda_rng = torch.get_rng_state(), torch.cuda.get_rng_state_all()
    previous_threads = torch.get_num_threads()
    records = []

    def timed_out(signum, frame):
        raise TimeoutError("frozen120s fixture resource cap")

    previous_handler = signal.signal(signal.SIGALRM, timed_out)
    try:
        torch.set_float32_matmul_precision("highest")
        for index in range(len(SHAPES)):
            signal.alarm(120)
            data = fixture(index)
            h, w, b, t, mapping, dz, dt = data
            np.savez_compressed(
                output / f"input-{index}.npz",
                H=h.numpy(),
                W=w.numpy(),
                bias=b.numpy(),
                targets=t.numpy(),
                mapping=np.asarray(mapping),
                dz=dz.numpy(),
                dt=dt.numpy(),
            )
            reference = evaluate("dense64", data)
            for method in ("candidate", "dense32", "checkpoint", "CCE"):
                record = {"fixture": index, "method": method}
                try:
                    if time.monotonic() - start > 900:
                        raise TimeoutError("frozen900s total resource cap")
                    actual = evaluate(method, data)
                    largest, scaled, checked = 0.0, 0.0, 0
                    for a, ref in zip(actual, reference, strict=True):
                        finite = np.isfinite(ref)
                        assert np.array_equal(np.isneginf(a), np.isneginf(ref))
                        assert np.isfinite(a[finite]).all()
                        error = np.abs(a[finite] - ref[finite])
                        largest = max(largest, float(error.max(initial=0)))
                        scaled = max(
                            scaled,
                            float((error / (5e-5 + 5e-5 * np.abs(ref[finite]))).max(initial=0)),
                        )
                        checked += a.size
                    assert scaled <= 1, (largest, scaled)
                    assert torch.cuda.max_memory_allocated() - initial <= 2 * 1024**3
                    assert time.monotonic() - start <= 900
                    record.update(
                        status="PASS",
                        max_abs_error=largest,
                        max_scaled_error=scaled,
                        checked=checked,
                    )
                except Exception as exc:
                    record.update(status="ERROR", exception=type(exc).__name__, message=str(exc))
                records.append(record)
                with (output / "records.jsonl").open("a") as stream:
                    stream.write(json.dumps(record) + "\n")
                print(json.dumps(record), flush=True)
                if record.get("exception") == "TimeoutError":
                    break
            signal.alarm(0)
        h, w, b, t, mapping, _, _ = fixture(2)
        h, w, b, t = [v.cuda() for v in (h, w, b, t)]
        meta = metadata(mapping, "cuda")
        bad = h.clone()
        bad[0, 0] = torch.nan
        guards = (
            (h[:0], w, b, t[:0]),
            (bad, w, b, t),
            (h, w, b, torch.full_like(t, len(w))),
            (h, w, b * 0 - torch.inf, t),
        )
        refusals = []
        for ordinal, args in enumerate(guards):
            try:
                grouped_gpu(*args, meta)
            except ValueError:
                refusals.append({"refusal": ordinal, "status": "PASS"})
                print(json.dumps(refusals[-1]), flush=True)
            else:
                raise AssertionError(f"missing refusal{ordinal}")
        (output / "refusals.json").write_text(json.dumps(refusals, indent=2) + "\n")
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.set_rng_state(cpu_rng)
        torch.cuda.set_rng_state_all(cuda_rng)
        torch.set_float32_matmul_precision(precision)
    summary = {
        "status": "PASS"
        if len(records) == 32 and all(r["status"] == "PASS" for r in records)
        else "ERROR",
        "records": len(records),
        "checked": sum(r.get("checked", 0) for r in records),
        "refusals": len(refusals),
        "new_model_forwards": 0,
        "new_model_parameter_reads": 0,
        "optimizer_updates": 0,
        "competitive_timing": False,
        "RNG_restored": bool(
            torch.equal(cpu_rng, torch.get_rng_state())
            and all(
                torch.equal(a, b)
                for a, b in zip(cuda_rng, torch.cuda.get_rng_state_all(), strict=True)
            )
        ),
        "Python_RNG_restored": random.getstate() == python_state,
        "NumPy_RNG_restored": all(
            np.array_equal(a, b) for a, b in zip(numpy_state, np.random.get_state(), strict=True)
        ),
        "matmul_precision_restored": torch.get_float32_matmul_precision() == precision,
        "threads_unchanged": torch.get_num_threads() == previous_threads,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)
    return summary["status"] == "PASS"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cce-source", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if main(args.output, args.cce_source) else 1)
