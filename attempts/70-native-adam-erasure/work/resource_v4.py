"""Frozen optimistic resource screen; NOT an A70 optimizer or complete NNCP port."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
import traceback
from pathlib import Path

METHODS = ("native_single", "native_foreach", "ideal_single", "ideal_foreach")
FRAMES = ("empty", "full160")
WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]
SOURCE = WORK / "consumer_v4"
TORCH_GIT = "a1cb3cc05d46d198467bebbb6e8fba50a325d4e7"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def memory():
    keys = {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}
    return {
        name: value.strip()
        for line in Path("/proc/meminfo").read_text().splitlines()
        for name, value in [line.split(":", 1)]
        if name in keys
    }


def load_original(name):
    spec = importlib.util.spec_from_file_location("a70_v4_" + name, SOURCE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RetainedBuffer(io.BytesIO):
    """Allow inspection after the original BitOutputStream closes its sink."""

    def close(self):
        self.flush()


def tensor_digest(named):
    digest = hashlib.sha256()
    for name, tensor in named:
        digest.update(name.encode() + b"\0")
        if tensor is None:
            digest.update(b"NONE")
            continue
        array = tensor.detach().contiguous().cpu().numpy()
        digest.update(str((array.dtype.str, array.shape)).encode() + b"\0")
        digest.update(memoryview(array).cast("B"))
    return digest.hexdigest()


def native_digest(named_params, optimizer):
    tensors = []
    for name, param in named_params:
        tensors.append((name + "/weight", param))
        for key, value in sorted(optimizer.state[param].items()):
            tensors.append((name + "/" + key, value))
    return tensor_digest(tensors)


def frozen_sources():
    paths = [Path(__file__).resolve(), WORK / "protocol-v4-resource.md", SOURCE / "provenance.json"]
    provenance = json.loads((SOURCE / "provenance.json").read_text())
    for entry in provenance["files"]:
        path = SOURCE / entry["path"]
        if len(path.read_bytes()) != entry["bytes"] or sha(path.read_bytes()) != entry["sha256"]:
            raise RuntimeError("Original source mismatch: " + entry["path"])
        paths.append(path)
    hashes = {}
    for path in paths:
        relative = str(path.relative_to(ROOT))
        committed = subprocess.check_output(["git", "show", "HEAD:" + relative], cwd=ROOT)
        actual = path.read_bytes()
        if actual != committed:
            raise RuntimeError("Source not frozen at HEAD: " + relative)
        hashes[relative] = sha(actual)
    return hashes


def gate(records):
    output = {}
    for frame in FRAMES:
        cells = {
            (r["method"], r["repetition"]): r
            for r in records
            if r["phase"] == "measured" and r["frame"] == frame and r["status"] == "COMPLETE"
        }
        comparisons = []
        passing = []
        for ideal in METHODS[2:]:
            ok = len(cells) == 28
            for native in METHODS[:2]:
                entry = {"ideal": ideal, "native": native, "metrics": {}}
                for metric in ("wall_ns", "cpu_ns"):
                    ratios = [
                        cells[ideal, rep][metric] / cells[native, rep][metric] for rep in range(7)
                    ]
                    median = statistics.median(ratios)
                    favorable = all(ratio < 1 for ratio in ratios)
                    entry["metrics"][metric] = {
                        "paired_ratios": ratios,
                        "median_ratio": median,
                        "every_repetition_favorable": favorable,
                    }
                    ok = ok and median <= 0.8 and favorable
                comparisons.append(entry)
            if ok:
                passing.append(ideal)
        output[frame] = {"passing_ideal_methods": passing, "comparisons": comparisons}
    return output


def screen(output):
    original_affinity = sorted(os.sched_getaffinity(0))
    physical_cores = {}
    for cpu in original_affinity:
        topology = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        identity = (
            (topology / "physical_package_id").read_text().strip(),
            (topology / "core_id").read_text().strip(),
        )
        physical_cores.setdefault(identity, cpu)
    if len(physical_cores) != 8:
        raise RuntimeError("Fixed eight-physical-core screen unavailable")
    os.sched_setaffinity(0, set(physical_cores.values()))
    manifest = {
        "producer_commit": git("rev-parse", "HEAD"),
        "protocol_commit": "30480f37",
        "sources": frozen_sources(),
        "python": sys.version,
        "platform": platform.platform(),
        "cpu_model": next(
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        ),
        "memory_before_import": memory(),
        "original_cpu_affinity": original_affinity,
        "screen_cpu_affinity": sorted(os.sched_getaffinity(0)),
        "scope": "Modern CPU/FP32 NNCPv2 component RESOURCE screen; constructed frames; no A70",
    }
    save(output / "manifest.json", manifest)
    import_start = time.perf_counter_ns()
    import numpy as np
    import torch
    import torch.nn.functional as functional

    if torch.__version__ != "2.8.0+cpu" or torch.version.git_version != TORCH_GIT:
        raise RuntimeError("Unexpected Torch runtime")
    torch.set_num_threads(8)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(1111)
    np.random.seed(1111)
    model_source = load_original("mem_transformer")
    coder_source = load_original("arithmetic_coder")
    manifest.update(
        torch=torch.__version__,
        torch_git=torch.version.git_version,
        numpy=np.__version__,
        threads=torch.get_num_threads(),
        interop=torch.get_num_interop_threads(),
        deterministic=torch.are_deterministic_algorithms_enabled(),
        import_wall_ns=time.perf_counter_ns() - import_start,
        torch_config=torch.__config__.show(),
        adam_python_sha256=sha((Path(torch.__file__).parent / "optim/adam.py").read_bytes()),
    )
    init_start = time.perf_counter_ns()
    model = model_source.MemTransformerLM(
        16388,
        12,
        8,
        512,
        64,
        2048,
        0.25,
        0.0,
        d_embed=512,
        tie_projs=[False],
        pre_lnorm=False,
        tgt_len=1,
        ext_len=0,
        mem_len=160,
        cutoffs=[],
        same_length=False,
        attn_type=1,
        clamp_len=-1,
        tied_r_bias=True,
        use_gelu=True,
    )
    # Literal initialization rules from nncp.py, without executing its CLI/main.
    for name, module in model.named_modules():
        classname = module.__class__.__name__
        if "Linear" in classname:
            if getattr(module, "weight", None) is not None:
                scale = 0.013 * math.sqrt(512 / 2048) if "ff2" in name else 0.013
                torch.nn.init.normal_(module.weight, 0.0, scale)
            if getattr(module, "bias", None) is not None:
                torch.nn.init.constant_(module.bias, 0.0)
        elif "Embedding" in classname:
            torch.nn.init.normal_(module.weight, 0.0, 0.013)
        elif "LayerNorm" in classname:
            torch.nn.init.normal_(module.weight, 1.0, 0.013)
            torch.nn.init.constant_(module.bias, 0.0)
        elif "TransformerLM" in classname:
            for key in ("r_emb", "r_w_bias", "r_r_bias"):
                if hasattr(module, key):
                    torch.nn.init.normal_(getattr(module, key), 0.0, 0.013)
            if hasattr(module, "r_bias"):
                torch.nn.init.constant_(module.r_bias, 0.0)
    model.eval()
    named_params = list(model.named_parameters())
    params = [param for _, param in named_params]
    embedding = model.word_emb.weight
    other_params = [param for param in params if param is not embedding]
    optimizer = torch.optim.Adam(
        params,
        lr=7.9e-5,
        betas=(0.0, 0.9999),
        eps=1e-9,
        weight_decay=0,
        foreach=False,
        fused=False,
        capturable=False,
        differentiable=False,
        maximize=False,
    )
    generator = torch.Generator().manual_seed(1111)
    data_list = torch.randint(16388, (32, 64), generator=generator).tolist()
    target_list = torch.randint(16388, (64,), generator=generator).tolist()
    memory_generator = torch.Generator().manual_seed(1112)
    memories = {
        "empty": (),
        "full160": tuple(
            torch.randn((160, 64, 512), generator=memory_generator) * 0.013 for _ in range(13)
        ),
    }
    fixture_hashes = {
        "input_ids": sha(json.dumps(data_list).encode()),
        "target_ids": sha(json.dumps(target_list).encode()),
        "full_memory": tensor_digest([(str(i), t) for i, t in enumerate(memories["full160"])]),
    }
    manifest.update(
        initialization_wall_ns=time.perf_counter_ns() - init_start,
        parameter_count=sum(p.numel() for p in params),
        embedding_parameter_count=embedding.numel(),
        initial_weights_digest=tensor_digest(named_params),
        fixture_hashes=fixture_hashes,
        memory_after_initialization=memory(),
    )
    save(output / "manifest.json", manifest)
    calls = {"forwards": 0, "backwards": 0, "optimizer_steps": 0}
    records = []
    observations = {}
    native_states = {}
    checkpoint = None
    rng_state = None

    def restore(method):
        start = time.perf_counter_ns()
        with torch.no_grad():
            for param, old_weight, old_state in checkpoint:
                param.copy_(old_weight)
                for key, value in old_state.items():
                    optimizer.state[param][key].copy_(value)
        torch.set_rng_state(rng_state)
        optimizer.param_groups[0]["params"] = other_params if method.startswith("ideal") else params
        optimizer.param_groups[0]["foreach"] = method.endswith("foreach")
        return time.perf_counter_ns() - start

    def cycle(frame, method, phase, repetition):
        row = {"frame": frame, "method": method, "phase": phase, "repetition": repetition}
        row["restore_wall_ns"] = restore(method) if checkpoint is not None else 0
        sink = RetainedBuffer()
        bit_output = coder_source.BitOutputStream(sink)
        encoder = coder_source.ArithmeticEncoder(32, bit_output)
        before_cpu, before_wall = time.process_time_ns(), time.perf_counter_ns()
        # Full prescribed amortized cycle. Every model parameter's gradient is cleared.
        model.zero_grad(set_to_none=False)
        data = torch.LongTensor(data_list)
        calls["forwards"] += 1
        result = model(data, 1, *memories[frame])
        logits = result[0]
        probabilities = functional.softmax(logits.detach(), -1)
        frequencies = torch.round(probabilities * 10000000).int()
        frequencies = torch.max(frequencies, frequencies.new_ones(frequencies.size()))
        frequencies = torch.cumsum(frequencies, -1).cpu()
        for index, symbol in enumerate(target_list):
            encoder.write(frequencies[0][index], symbol)
        target = torch.LongTensor(target_list)
        log_probability = functional.log_softmax(logits, -1).reshape(64, 16388)
        loss = functional.nll_loss(log_probability, target, reduction="none")
        output_bits = loss.float().sum().item() / math.log(2)
        loss = loss.float().mean().type_as(loss)
        calls["backwards"] += 1
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 0.25)
        optimizer.param_groups[0]["lr"] = 7.9e-5
        calls["optimizer_steps"] += 1
        optimizer.step()
        row.update(
            wall_ns=time.perf_counter_ns() - before_wall, cpu_ns=time.process_time_ns() - before_cpu
        )
        validation_start = time.perf_counter_ns()
        encoder.finish()
        bit_output.close()
        encoded = sink.getvalue()
        decoder = coder_source.ArithmeticDecoder(
            32, coder_source.BitInputStream(io.BytesIO(encoded))
        )
        decoded = [decoder.read(frequencies[0][index]) for index in range(64)]
        if decoded != target_list:
            raise AssertionError("Original coder round-trip failed")
        if not math.isfinite(loss.item()) or not math.isfinite(grad_norm.item()):
            raise AssertionError("Nonfinite loss or gradient norm")
        grad_hash = tensor_digest([(name, param.grad) for name, param in named_params])
        observation = {
            "loss_bits": tensor_digest([("loss", loss)]),
            "logits": tensor_digest([("logits", logits)]),
            "cdf": tensor_digest([("cdf", frequencies)]),
            "gradients": grad_hash,
            "output_memories": tensor_digest([(str(i), t) for i, t in enumerate(result[1:])]),
            "encoded_sha256": sha(encoded),
        }
        # No extra forward is used to check identical paired inputs/outputs.
        if phase != "setup":
            if frame in observations and observations[frame] != observation:
                raise AssertionError("Common frame loss/CDF/gradient/memory differs")
            observations[frame] = observation
        state_hash = native_digest(named_params, optimizer)
        if phase != "setup":
            key = frame + "/" + method
            if key in native_states and native_states[key] != state_hash:
                raise AssertionError("Restored identical method has different native state")
            native_states[key] = state_hash
        row.update(
            status="COMPLETE",
            loss=loss.item(),
            output_bits=output_bits,
            clipped_from_norm=grad_norm.item(),
            observation=observation,
            output_bytes=len(encoded),
            state_digest=state_hash,
            validation_flush_roundtrip_hash_wall_ns=time.perf_counter_ns() - validation_start,
            max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            memory_after=memory(),
            cumulative_calls=dict(calls),
        )
        records.append(row)
        with (output / "records.jsonl").open("a") as stream:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
        save(output / "calls.json", calls)
        print(
            json.dumps(
                {
                    key: row[key]
                    for key in ("phase", "frame", "method", "repetition", "wall_ns", "cpu_ns")
                }
            ),
            flush=True,
        )

    try:
        cycle("empty", "native_single", "setup", -1)
        snapshot_start = time.perf_counter_ns()
        checkpoint = [
            (
                param,
                param.detach().clone(),
                {key: value.clone() for key, value in optimizer.state[param].items()},
            )
            for param in params
        ]
        rng_state = torch.get_rng_state().clone()
        manifest.update(
            snapshot_wall_ns=time.perf_counter_ns() - snapshot_start,
            snapshot_native_digest=native_digest(named_params, optimizer),
            snapshot_clock_values=sorted({float(optimizer.state[p]["step"]) for p in params}),
            snapshot_memory_bytes=sum(
                weight.numel() * weight.element_size()
                + sum(t.numel() * t.element_size() for t in state.values())
                for _, weight, state in checkpoint
            ),
        )
        save(output / "manifest.json", manifest)
        for frame in FRAMES:
            for method in METHODS:
                cycle(frame, method, "warmup", -1)
        for rep in range(7):
            order = METHODS[rep % 4 :] + METHODS[: rep % 4]
            for frame in FRAMES:
                for method in order:
                    cycle(frame, method, "measured", rep)
        if calls != {"forwards": 65, "backwards": 65, "optimizer_steps": 65}:
            raise AssertionError("Unexpected actual call count")
        summary = {
            "status": "COMPLETE",
            "measured_records": 56,
            "warmups": 8,
            "setup_records": 1,
            "calls": calls,
            "gates": gate(records),
            "observations": observations,
            "native_single_foreach_state_equal_on_frames": {
                frame: native_states[frame + "/native_single"]
                == native_states[frame + "/native_foreach"]
                for frame in FRAMES
            },
            "memory_end": memory(),
            "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "claim": (
                "Only optimistic resource feasibility; no candidate, "
                "real-text or whole-codec advantage"
            ),
        }
        save(output / "summary.json", summary)
        print(json.dumps(summary, allow_nan=False), flush=True)
    finally:
        save(output / "calls.json", calls)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        screen(args.output)
    except BaseException as error:
        save(
            args.output / "error.json",
            {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            },
        )
        raise


if __name__ == "__main__":
    main()
