"""Frozen A74 envelope refusal screen. No sampler or decoder speed claim."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import linecache
import math
import signal
import subprocess
import sys
import types
from contextlib import nullcontext
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from safetensors.torch import load_file
from scripts.exact_commit.mdlm_cpu import attention, rearrange, rotary
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path("/home/jota/projects/tcc-final/.cache/mdlm")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norms(values, bits):
    """Outward Euclidean norms, only exact int64 sums after dyadic rounding."""
    scaled = np.abs(values.astype(np.float64)) * 2**bits
    assert np.isfinite(scaled).all()
    assert scaled.max() + 1 < math.isqrt((2**63 - 1) // scaled.shape[-1])
    lo = np.floor(scaled).astype(np.int64)
    hi = np.ceil(scaled).astype(np.int64)
    lower2 = (lo * lo).sum(axis=-1, dtype=np.int64)
    upper2 = (hi * hi).sum(axis=-1, dtype=np.int64)
    lower = [F(math.isqrt(int(v)), 2**bits) for v in lower2]
    upper = [
        F(math.isqrt(int(v)) + int(math.isqrt(int(v)) ** 2 != int(v)), 2**bits) for v in upper2
    ]
    return lower, upper


def load_model(config):
    """Same maintained audited port, transformed in memory; cache stays read-only."""
    snapshot = CACHE / "models--kuleshov-group--mdlm-owt/snapshots" / config["model_revision"]
    files = {name: snapshot / name for name in config["checkpoint_sha256"]}
    assert {name: digest(path) for name, path in files.items()} == config["checkpoint_sha256"]
    configuration = types.ModuleType("a74_mdlm_configuration")
    configuration.__file__ = str(files["configuration_mdlm.py"])
    exec(
        compile(files["configuration_mdlm.py"].read_text(), configuration.__file__, "exec"),
        configuration.__dict__,
    )
    source = files["modeling_mdlm.py"].read_text()
    for line in (
        "import flash_attn\n",
        "import flash_attn.layers.rotary\n",
        "from einops import rearrange\n",
        "from .configuration_mdlm import MDLMConfig\n",
    ):
        assert source.count(line) == 1
        source = source.replace(line, "")
    source = source.replace(
        "torch.cuda.amp.autocast(enabled=False)", 'torch.autocast(device_type="cpu", enabled=False)'
    )
    source = source.replace(
        "torch.cuda.amp.autocast(dtype=torch.bfloat16)",
        'torch.autocast(device_type="cpu", enabled=False)',
    )
    module = types.ModuleType("a74_mdlm_model")
    module.__file__ = str(ROOT / ".cache/a74-audited-mdlm.py")
    # TorchScript inspects the transformed source, whose line numbers differ
    # from the original. Supply it in memory; never write the shared cache.
    linecache.cache[module.__file__] = (
        len(source),
        None,
        source.splitlines(keepends=True),
        module.__file__,
    )
    module.__dict__.update(
        MDLMConfig=configuration.MDLMConfig,
        rearrange=rearrange,
        flash_attn=types.SimpleNamespace(
            layers=types.SimpleNamespace(
                rotary=types.SimpleNamespace(apply_rotary_emb_qkv_=rotary)
            ),
            flash_attn_interface=types.SimpleNamespace(flash_attn_varlen_qkvpacked_func=attention),
        ),
    )
    sys.modules[module.__name__] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    model = module.MDLM(configuration.MDLMConfig(**json.loads(files["config.json"].read_text())))
    model.load_state_dict(load_file(str(files["model.safetensors"]), device="cpu"), strict=True)
    return model.eval(), hashlib.sha256(source.encode()).hexdigest()


def run(output, device):
    if subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT).returncode:
        raise ValueError("freeze protocol and source before capture")
    cpu = device == "cpu"
    clock = (lambda: 0.0) if cpu else perf_counter
    lock = nullcontext() if cpu else open("/tmp/tcc-final-candidate-tests-gpu.lock", "a")
    if not cpu:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("GPU_LOCK_BUSY: no GPU query, capture or timing started", flush=True)
            return 75
    # File opened exclusively: old data cannot be overwritten.
    with lock, output.open("x") as stream:

        def emit(**row):
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            print(json.dumps(row), flush=True)

        def interrupted(signum, _frame):
            emit(type="interruption", signal=signum, status="INCONCLUSIVE")
            raise SystemExit(128 + signum)

        signal.signal(signal.SIGTERM, interrupted)

        def elapsed(begin):
            return None if cpu else clock() - begin

        started = clock()
        smi = (
            None
            if cpu
            else subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.free", "--format=csv,noheader,nounits"],
                text=True,
            ).strip()
        )
        processes = (
            None
            if cpu
            else subprocess.check_output(
                ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
                text=True,
            ).strip()
        )
        producer = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        emit(
            type="environment",
            producer=producer,
            device=device,
            gpu=smi,
            compute_processes=processes,
            torch=torch.__version__,
            numpy=np.__version__,
            seed=740203,
            lock=None if cpu else "/tmp/tcc-final-candidate-tests-gpu.lock",
            scope="envelope_screen_only",
        )
        if not cpu and (
            processes or int(smi.rsplit(",", 1)[1]) < 2048 or not torch.cuda.is_available()
        ):
            emit(type="resource", status="RESOURCE_REFUSAL_INCONCLUSIVE")
            return 2
        torch.set_num_threads(4)
        torch.manual_seed(740203)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        config = json.loads(
            (ROOT / "configs/experiments/m31_probability_scaling_cpu_v1.json").read_text()
        )
        model, adapted = load_model(config)
        # The output head is the only Linear with this original vocabulary size.
        heads = [
            m for m in model.modules() if isinstance(m, torch.nn.Linear) and m.out_features == 50258
        ]
        assert len(heads) == 1
        head = heads[0]
        weight = head.weight.detach().numpy()[:50256].astype(np.float64)
        token_snapshot = (
            CACHE / "models--openai-community--gpt2/snapshots" / config["tokenizer_revision"]
        )
        tokenizer = AutoTokenizer.from_pretrained(str(token_snapshot), local_files_only=True)
        emit(
            type="model",
            model_id=config["model_id"],
            revision=config["model_revision"],
            hashes=config["checkpoint_sha256"],
            adapted_sha256=adapted,
            tokenizer_revision=config["tokenizer_revision"],
            eligible_ids="0..50255",
            original_head_shape=list(head.weight.shape),
            bias="unchanged_exact",
            tokenizer_hashes={p.name: digest(p) for p in token_snapshot.iterdir() if p.is_file()},
        )
        proxy_started = clock()
        scales = np.exp2(np.ceil(np.log2(np.maximum(np.abs(weight).max(axis=1), 2.0**-100) / 127)))
        quantized = np.rint(weight / scales[:, None]) * scales[:, None]
        assert (np.abs(quantized / scales[:, None]) <= 127).all()
        _, quant_upper = norms(weight - quantized, 24)
        rank_residual = weight.copy()
        rank_residual[:, 0] = 0
        _, rank_upper = norms(rank_residual, 24)
        proxies = {"int8_row_power2": min(quant_upper), "rank1_first_column": min(rank_upper)}
        # Independent exact Fraction checks of rows attaining the minima.
        for name, residual, upper in (
            ("int8_row_power2", weight - quantized, quant_upper),
            ("rank1_first_column", rank_residual, rank_upper),
        ):
            index = upper.index(min(upper))
            assert sum(F(float(v)) ** 2 for v in residual[index]) <= upper[index] ** 2
            emit(
                type="proxy",
                proxy=name,
                min_rho=str(proxies[name]),
                min_row_id=index,
                residual_coordinate_count=int(residual.size),
                norm_grid_bits=24,
            )
        emit(
            type="preparation",
            model_load_hash_tokenizer_seconds=None if cpu else proxy_started - started,
            proxy_norm_seconds=elapsed(proxy_started),
            reference_weight_bytes=head.weight.numel() * head.weight.element_size(),
            int8_storage_bytes=int(weight.size + 8 * len(scales)),
            diagnostic_host_work_arrays_bytes_lower_bound=int(weight.nbytes * 3),
            rank1_storage_bytes=int(len(weight) * 4),
            residual_norms_storage_bytes=len(weight) * 8,
        )
        model.to(device).eval()
        hidden = []

        class Captured(Exception):
            pass

        def capture(_module, inputs):
            hidden.append(inputs[0].detach().to(device="cpu", dtype=torch.float32).numpy().copy())
            raise Captured

        hook = head.register_forward_pre_hook(capture)
        for p, prefix in enumerate(
            ("Return a balanced sequence of A and B:", "Complete the structured payload:")
        ):
            for n in (8, 32):
                prefix_ids = tokenizer.encode(prefix, add_special_tokens=False)
                ids = torch.tensor([prefix_ids + [config["mask_token_id"]] * n], device=device)
                if not cpu:
                    torch.cuda.synchronize()
                capture_started = clock()
                try:
                    with torch.inference_mode():
                        model(input_ids=ids, timesteps=torch.zeros(1, device=device))
                except Captured:
                    pass
                else:
                    raise AssertionError("reference head executed")
                if not cpu:
                    torch.cuda.synchronize()
                capture_seconds = elapsed(capture_started)
                h = hidden.pop()[0, len(prefix_ids) :]
                assert h.shape == (n, weight.shape[1])
                norms_started = clock()
                _, eta = norms(h, 16)
                for row, upper in zip(h, eta, strict=True):
                    assert sum(F(float(v)) ** 2 for v in row) <= upper**2
                for name, rho in proxies.items():
                    a = 2 * rho * sum(eta)
                    term = F(1)
                    lower_exp = F(1)
                    for k in range(1, 17):
                        term *= a / k
                        lower_exp += term
                    emit(
                        type="case",
                        prompt=p,
                        prefix=prefix,
                        n=n,
                        proxy=name,
                        status="ENVELOPE_GATE_REFUSAL"
                        if lower_exp > 4
                        else "NEEDS_EXACT_MASS_AND_CONSUMER",
                        log_R_lower=str(a),
                        log_R_lower_display=float(a),
                        R_lower_taylor16=str(lower_exp),
                        eta_upper=[str(v) for v in eta],
                        hidden_sha256=hashlib.sha256(h.tobytes()).hexdigest(),
                        input_ids=prefix_ids + [config["mask_token_id"]] * n,
                        backbone_capture_seconds=capture_seconds,
                        norm_seconds=elapsed(norms_started),
                        cuda_peak_allocated_bytes=None
                        if cpu
                        else torch.cuda.max_memory_allocated(),
                        reference_head_rows=0,
                        projected_proxy_rows=0,
                        chart_bytes=0,
                        sampler_rng_bits=0,
                        output_tokens=0,
                    )
        hook.remove()
        emit(
            type="complete",
            states=4,
            proxy_cases=8,
            diagnostic_total_seconds=elapsed(started),
            host_peak_rss_kib=__import__("resource")
            .getrusage(__import__("resource").RUSAGE_SELF)
            .ru_maxrss,
            scope="no_decoder_timing_no_output_law_claim",
        )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    raise SystemExit(run(args.output, args.device))
