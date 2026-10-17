"""Frozen head-primitive feasibility screen; NO backbone/model/optimizer run."""

import argparse
import gc
import hashlib
import json
import math
import os
import random
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

from .bucket_head_v8 import bucket_head, prepare_bucket
from .resource_analysis_v7 import analyze
from .strong_head import SortedHeadPlan
from .tiled_head_v6 import finite_domain_head, prepare

NS = (16, 32, 64, 128, 256, 512, 1024, 2048)
TILES = ((16, 32), (32, 64), (64, 64), (64, 128))
CANDIDATES = [f"{kind}{a}x{b}" for kind in ("tile", "bucket") for a, b in TILES]
CONTROLS = (
    ["dense"]
    + [f"CCE{t}" for t in (0, 8, 32, 128)]
    + [f"checkpoint{t}p{p}" for t in (0, 8, 32, 128) for p in (2048, 8192)]
    + ["CCE_out128"]
)
FIRST_CONTROLS = ["dense", "CCE128", "checkpoint128p8192", "CCE_out128"]


def sha(tensor):
    return hashlib.sha256(memoryview(tensor.detach().numpy()).cast("B")).hexdigest()


def reference64(h0, w0, b0, t, mapping, dz0, dt0):
    """Dense FP64 autodiff with ONE permutation and native segmented reduction."""
    perm = torch.tensor(sorted(range(len(mapping)), key=lambda v: mapping[v]))
    inv = torch.empty_like(perm)
    inv[perm] = torch.arange(len(perm))
    lengths = torch.bincount(torch.tensor(mapping))
    h, w, b = [x.double().detach().requires_grad_() for x in (h0, w0, b0)]
    logits = h @ w[perm].T + b[perm]
    sizes = lengths[None, :].expand(len(h), -1)
    maximum = torch.segment_reduce(logits, "max", lengths=sizes, axis=1)
    expanded = torch.repeat_interleave(maximum, lengths, dim=1, output_size=len(w))
    total = torch.segment_reduce(torch.exp(logits - expanded), "sum", lengths=sizes, axis=1)
    z = maximum + total.log()
    target = logits.gather(1, inv[t][:, None]).squeeze(1)
    loss = (dz0.double() * z).sum() + (dt0.double() * target).sum()
    loss.backward()
    return tuple(x.detach() for x in (loss, z, target, h.grad, w.grad, b.grad))


def make_state(name, data, mapping):
    h0, w0, b0, t0, dz0, dt0 = data
    if name.startswith(("tile", "bucket")):
        bucketed = name.startswith("bucket")
        tile = tuple(map(int, name[6 if bucketed else 4 :].split("x")))
        meta = (prepare_bucket if bucketed else prepare)(mapping, "cuda", tile)
        head_fn = bucket_head if bucketed else finite_domain_head
        h, w, b = [x.cuda().detach().requires_grad_() for x in (h0, w0, b0)]
        inv = None

        def call(hh, ww, bb, tt):
            return head_fn(hh, ww, bb, tt, meta)
    else:
        if name == "dense":
            backend, threshold, panel = "dense", 0, 8192
        elif name.startswith("CCE_out"):
            backend, threshold, panel = "CCE_out", int(name[len("CCE_out") :]), 8192
        elif name.startswith("CCE"):
            backend, threshold, panel = "CCE", int(name[3:]), 8192
        else:
            threshold, panel = map(int, name[len("checkpoint") :].split("p"))
            backend = "checkpoint"
        plan = SortedHeadPlan(
            mapping, device="cuda", threshold=threshold, panel=panel, backend=backend
        )
        plan.blocked_classes = frozenset()  # Validated finite, immutable synthetic bias.
        perm_cpu = plan.perm.cpu()
        h = h0.cuda().detach().requires_grad_()
        w = w0[perm_cpu].cuda().detach().requires_grad_()
        b = b0[perm_cpu].cuda().detach().requires_grad_()
        inv = plan.inv.cpu()
        call = plan
    t, dz, dt = [x.cuda() for x in (t0, dz0, dt0)]
    state = {"h": h, "w": w, "b": b, "t": t, "dz": dz, "dt": dt, "call": call, "inverse_cpu": inv}
    state["input_bytes"] = sum(
        state[k].numel() * state[k].element_size() for k in ("h", "w", "b", "t", "dz", "dt")
    )
    return state


def clear_grad(state):
    for k in ("h", "w", "b"):
        state[k].grad = None


def step(state):
    clear_grad(state)
    z, t = state["call"](state["h"], state["w"], state["b"], state["t"])
    loss = (state["dz"] * z).sum() + (state["dt"] * t).sum()
    loss.backward()
    return loss.detach(), z.detach(), t.detach()


def check(state, outputs, reference):
    actual = [
        *outputs,
        state["h"].grad.detach().cpu(),
        state["w"].grad.detach().cpu(),
        state["b"].grad.detach().cpu(),
    ]
    if state["inverse_cpu"] is not None:
        actual[4] = actual[4][state["inverse_cpu"]]
        actual[5] = actual[5][state["inverse_cpu"]]
    largest, scaled, count = 0.0, 0.0, 0
    for a, r in zip(actual, reference, strict=True):
        a = a.detach().cpu().double()
        assert a.shape == r.shape and torch.isfinite(a).all() and torch.isfinite(r).all()
        error = (a - r).abs()
        largest = max(largest, float(error.max()))
        scaled = max(scaled, float((error / (5e-5 + 5e-5 * r.abs())).max()))
        count += a.numel()
    assert scaled <= 1, (largest, scaled)
    return {"checked": count, "max_abs_error": largest, "max_scaled_error": scaled}


def append(output, rows, row):
    rows.append(row)
    with (output / "records.jsonl").open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    print(json.dumps(row), flush=True)


def run_phase(output, rows, methods, mapping, w, b, deadline):
    for n in NS:
        gen = torch.Generator().manual_seed(585700 + n)
        h = 0.2 * torch.randn(n, 768, generator=gen, dtype=torch.float32)
        t = torch.randint(len(mapping), (n,), generator=gen)
        dz = torch.randn(n, max(mapping) + 1, generator=gen, dtype=torch.float32) / math.sqrt(n)
        dt = torch.randn(n, generator=gen, dtype=torch.float32) / math.sqrt(n)
        data = (h, w, b, t, dz, dt)
        validation_cpu, validation_wall = time.process_time_ns(), time.perf_counter_ns()
        assert all(torch.isfinite(x).all() for x in (h, w, b, dz, dt))
        append(
            output,
            rows,
            {
                "N": n,
                "kind": "common_input_validation",
                "status": "COMPLETE",
                "wall_ns": time.perf_counter_ns() - validation_wall,
                "CPU_ns": time.process_time_ns() - validation_cpu,
                "scope": "once for immutable finite inputs; excluded from warm repetitions",
            },
        )
        packet = {
            k: sha(x) for k, x in zip(("H", "W", "bias", "targets", "dz", "dt"), data, strict=True)
        }
        (output / f"input-N{n}.json").write_text(
            json.dumps({"N": n, "seed": 585700 + n, "sha256": packet}, indent=2) + "\n"
        )
        print(json.dumps({"N": n, "status": "REFERENCE_START"}), flush=True)
        reference = reference64(h, w, b, t, mapping, dz, dt)
        print(json.dumps({"N": n, "status": "REFERENCE_COMPLETE"}), flush=True)
        valid = {}
        for rep in range(3):
            order = sorted(
                methods, key=lambda m: hashlib.sha256(f"a58-v7:{n}:{rep}:{m}".encode()).digest()
            )
            print(json.dumps({"N": n, "rep": rep, "execution_order": order}), flush=True)
            for name in order:
                if valid.get(name) is False:
                    append(
                        output,
                        rows,
                        {
                            "N": n,
                            "method": name,
                            "rep": rep,
                            "kind": "warm",
                            "status": "REFUSED",
                            "reason": "earlier correctness/resource error at this geometry",
                        },
                    )
                    continue
                state = None
                try:
                    remaining = int(deadline - time.monotonic())
                    if remaining <= 0:
                        raise TimeoutError("V7 whole3600s resource cap")
                    signal.alarm(min(180, remaining))
                    gc.collect()
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    root_alloc = torch.cuda.memory_allocated()
                    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > 16 * 1024**3:
                        raise MemoryError("V7 CPU RSS cap")
                    begin_cpu, begin_wall = time.process_time_ns(), time.perf_counter_ns()
                    state = make_state(name, data, mapping)
                    torch.cuda.synchronize()
                    prep_wall, prep_cpu = (
                        time.perf_counter_ns() - begin_wall,
                        time.process_time_ns() - begin_cpu,
                    )
                    torch.cuda.reset_peak_memory_stats()
                    begin_cpu, begin_wall = time.process_time_ns(), time.perf_counter_ns()
                    actual = step(state)
                    torch.cuda.synchronize()
                    first_wall, first_cpu = (
                        time.perf_counter_ns() - begin_wall,
                        time.process_time_ns() - begin_cpu,
                    )
                    if rep == 0:
                        accuracy = check(state, actual, reference)
                        valid[name] = True
                        append(
                            output,
                            rows,
                            {
                                "N": n,
                                "method": name,
                                "kind": "validation",
                                "status": "PASS",
                                **accuracy,
                            },
                        )
                    del actual
                    append(
                        output,
                        rows,
                        {
                            "N": n,
                            "method": name,
                            "rep": rep,
                            "kind": "preparation",
                            "status": "COMPLETE",
                            "prepare_wall_ns": prep_wall,
                            "prepare_CPU_ns": prep_cpu,
                            "first_wall_ns": first_wall,
                            "first_CPU_ns": first_cpu,
                            "cache_scope": "observed first call; NOT fresh-cache compilation",
                            "first_peak_bytes": torch.cuda.max_memory_allocated() - root_alloc,
                        },
                    )
                    for _ in range(3):
                        step(state)
                    clear_grad(state)
                    torch.cuda.synchronize()
                    torch.cuda.reset_peak_memory_stats()
                    begin_cpu, begin_wall = time.process_time_ns(), time.perf_counter_ns()
                    for _ in range(5):
                        step(state)
                    torch.cuda.synchronize()
                    wall, cpu = (
                        time.perf_counter_ns() - begin_wall,
                        time.process_time_ns() - begin_cpu,
                    )
                    peak = torch.cuda.max_memory_allocated() - root_alloc
                    if peak > 8 * 1024**3:
                        raise MemoryError("V7 incremental GPU allocated cap")
                    append(
                        output,
                        rows,
                        {
                            "N": n,
                            "method": name,
                            "rep": rep,
                            "kind": "warm",
                            "status": "COMPLETE",
                            "calls": 5,
                            "wall_ns": wall / 5,
                            "CPU_ns": cpu / 5,
                            "peak_resident_bytes": peak,
                            "common_input_bytes": state["input_bytes"],
                            "workspace_bytes": peak - state["input_bytes"],
                            "root_allocated_bytes": root_alloc,
                        },
                    )
                except Exception as exc:
                    valid[name] = False
                    append(
                        output,
                        rows,
                        {
                            "N": n,
                            "method": name,
                            "rep": rep,
                            "kind": "warm",
                            "status": "ERROR",
                            "exception": type(exc).__name__,
                            "message": str(exc),
                        },
                    )
                finally:
                    signal.alarm(0)
                    if state is not None:
                        clear_grad(state)
                    del state
                    gc.collect()
                    torch.cuda.empty_cache()
            if time.monotonic() > deadline:
                raise TimeoutError("V7 whole3600s resource cap")
        del reference
        gc.collect()


def main(output, source):
    output.mkdir(parents=True, exist_ok=False)
    base = Path(__file__).parent
    mapfile = base / "evidence" / "metadata-v6" / "mapping.json"
    metadata_cpu, metadata_wall = time.process_time_ns(), time.perf_counter_ns()
    mapping = json.loads(mapfile.read_text())["class_of"]
    common_metadata_wall, common_metadata_cpu = (
        time.perf_counter_ns() - metadata_wall,
        time.process_time_ns() - metadata_cpu,
    )
    pin = json.loads((base / "cce-source-v3.json").read_text())
    assert (
        subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        == pin["commit"]
    )
    for path, digest in pin["sha256"].items():
        assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest
    assert (
        json.loads((base / "evidence" / "tiles-v6-initial" / "summary.json").read_text())["status"]
        == "PASS"
    )
    assert (
        json.loads((base / "evidence" / "buckets-v8-initial" / "summary.json").read_text())[
            "status"
        ]
        == "PASS"
    )
    assert (
        json.loads((base / "evidence" / "strong-v9-out" / "summary.json").read_text())["status"]
        == "PASS"
    )
    sys.path.insert(0, str(source))
    config = {
        "producer": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in base.glob("*.py")
        },
        "mapping_sha256": hashlib.sha256(mapfile.read_bytes()).hexdigest(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "CUDA": torch.version.cuda,
        "device": torch.cuda.get_device_name(0),
        "CCE_commit": pin["commit"],
        "dtype": "FP32",
        "dot_precision": "ieee",
        "filtering": False,
        "prospective_addenda": ["bucket-addendum-v8.md", "out-control-addendum-v9.md"],
        "Ns": NS,
        "candidates": CANDIDATES,
        "controls": CONTROLS,
        "first_controls": FIRST_CONTROLS,
        "common_seed": 585700,
        "common_metadata_load_wall_ns": common_metadata_wall,
        "common_metadata_load_CPU_ns": common_metadata_cpu,
        "cpu_threads": 4,
        "BLAS_env": {
            k: os.environ.get(k)
            for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "new_model_forwards": 0,
        "model_parameter_reads": 0,
        "optimizer_model_updates": 0,
        "scope": "synthetic full HEAD PRIMITIVE, not grammar/backbone/optimizer or whole training",
    }
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    old_precision, old_threads = torch.get_float32_matmul_precision(), torch.get_num_threads()
    old_cpu, old_cuda = torch.get_rng_state(), torch.cuda.get_rng_state_all()
    old_python, old_numpy = random.getstate(), np.random.get_state()

    def timeout(signum, frame):
        raise TimeoutError("V7 configuration180s resource cap")

    old_handler = signal.signal(signal.SIGALRM, timeout)
    rows = []
    try:
        torch.set_float32_matmul_precision("highest")
        torch.set_num_threads(4)
        # Initialize the shared BLAS context before comparing allocator peaks.
        warm = torch.zeros(16, 16, device="cuda")
        warm @ warm
        torch.cuda.synchronize()
        del warm
        gen = torch.Generator().manual_seed(585700)
        w = 0.02 * torch.randn(len(mapping), 768, generator=gen, dtype=torch.float32)
        b = 0.02 * torch.randn(len(mapping), generator=gen, dtype=torch.float32)
        deadline = time.monotonic() + 3600
        run_phase(output, rows, CANDIDATES + FIRST_CONTROLS, mapping, w, b, deadline)
        initial = analyze(rows, NS, CANDIDATES, FIRST_CONTROLS)
        (output / "phase-I-decision.json").write_text(json.dumps(initial, indent=2) + "\n")
        if initial["negative_shortcut"]:
            report = {
                "status": "NEGATIVE_PREDECLARED_SHORTCUT",
                "phase_I": initial,
                "unexecuted_controls": [m for m in CONTROLS if m not in FIRST_CONTROLS],
            }
        else:
            run_phase(
                output,
                rows,
                [m for m in CONTROLS if m not in FIRST_CONTROLS],
                mapping,
                w,
                b,
                deadline,
            )
            final = analyze(rows, NS, CANDIDATES, CONTROLS)
            report = {
                "status": "PASS_NECESSITY_ONLY"
                if final["gate"]
                else "NEGATIVE"
                if final["negative_shortcut"]
                else "INCONCLUSIVE",
                "phase_I": initial,
                "final": final,
                "unexecuted_controls": [],
            }
    except Exception as exc:
        report = {"status": "ERROR", "exception": type(exc).__name__, "message": str(exc)}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        torch.set_float32_matmul_precision(old_precision)
        torch.set_num_threads(old_threads)
        torch.set_rng_state(old_cpu)
        torch.cuda.set_rng_state_all(old_cuda)
        random.setstate(old_python)
        np.random.set_state(old_numpy)
    report.update(
        records=len(rows),
        new_model_forwards=0,
        model_parameter_reads=0,
        optimizer_model_updates=0,
        whole_training_benefit=False,
        Torch_RNG_restored=bool(
            torch.equal(old_cpu, torch.get_rng_state())
            and all(
                torch.equal(a, b)
                for a, b in zip(old_cuda, torch.cuda.get_rng_state_all(), strict=True)
            )
        ),
    )
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "records": len(rows)}), flush=True)
    return report["status"] != "ERROR"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cce-source", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if main(args.output, args.cce_source) else 1)
