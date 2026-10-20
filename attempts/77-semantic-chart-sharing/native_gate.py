"""A77 frozen original-head delta gate; lock/preflight precede clocks/CUDA."""

from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
import re
import resource
import signal
import subprocess
import time
from fractions import Fraction as F
from pathlib import Path

MODEL = Path("/home/jota/projects/tcc-final/.cache/a52-model-metadata")
PROMPTS = (
    "Return an unordered pool of pure arithmetic expression AST candidates. "
    "Each module uses only a, b, (, ), +, and *. Modules are interchangeable; "
    "retain duplicates. Fill every masked module, separated by #.\nPool: ",
    "Propose a bag of candidate symbolic expressions for a pure commutative "
    "sum. Use grammar E ::= a | b | (E+E) | (E*E) in each module. Module order is "
    "ignored; internal AST order is retained. Separate modules by #.\nPool: ",
)
CASES = tuple((p, m, n) for p in range(2) for m, n in ((2, 13), (8, 13), (8, 253)))
LOCK = "/tmp/tcc-final-candidate-tests-gpu.lock"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def preflight(initial):
    command = [
        "nvidia-smi",
        "--query-compute-apps=pid,process_name,used_memory",
        "--format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=True, timeout=10)
    foreign = [
        line
        for line in result.stdout.splitlines()
        if line.strip() and int(line.split(",")[0]) != os.getpid()
    ]
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=utilization.gpu,memory.free", "--format=csv,noheader,nounits"],
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
    )
    readings = [tuple(map(int, line.split(","))) for line in result.stdout.splitlines()]
    return {
        "foreign_compute": foreign,
        "gpu_utilization_free_mib": readings,
        "ready": not foreign and (not initial or all(util <= 5 for util, _ in readings)),
    }


def timeout(_signum, _frame):
    raise TimeoutError("frozen_phase_deadline")


def run(output, raw):
    with output.open("x") as stream, open(LOCK, "a") as lock:

        def emit(kind, **fields):
            stream.write(json.dumps({"type": kind, **fields}, sort_keys=True) + "\n")
            stream.flush()

        def refuse(status, cases=CASES, **fields):
            for p, m, n in cases:
                emit("case", case=f"p{p}-m{m}-n{n}", status=status, **fields)

        emit(
            "protocol",
            producer_commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            epsilon="1/100",
            coordinator_ready=True,
            scope="exact_on_support",
            eos_pad="absent",
            lock=LOCK,
        )
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            refuse("RESOURCE_REFUSAL_LOCK_BUSY")
            return
        try:
            initial = preflight(True)
            emit("preflight", **initial)
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            refuse("RESOURCE_PREFLIGHT_UNAVAILABLE", error=repr(error))
            return
        if not initial["ready"]:
            refuse("RESOURCE_REFUSAL_FOREIGN_COMPUTE_OR_UTILIZATION")
            return
        # No clocks, Torch import or CUDA calls occurred before this point.
        started = time.perf_counter()
        signal.signal(signal.SIGALRM, timeout)
        signal.alarm(180)
        try:
            import torch
            import transformers
            from tokenizers import Tokenizer

            torch.set_num_threads(4)
            torch.manual_seed(770301)
            torch.cuda.manual_seed_all(770301)
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            for name, expected in {
                "tokenizer.json": (
                    "6d55810de1daf81d1d1259355b4b85810385022ab745be68029295935a4eacf0"
                ),
                "model.safetensors": (
                    "3485d18016ce6c302e8973809b47aa6369d6612ef9978d0690b4575d1193e932"
                ),
            }.items():
                if sha(MODEL / name) != expected:
                    raise ValueError(f"frozen_hash_mismatch:{name}")
            tokenizer = Tokenizer.from_file(str(MODEL / "tokenizer.json"))
            metadata = json.loads((MODEL / "tokenizer.json").read_text())
            specials = {row["id"] for row in metadata["added_tokens"] if row["special"]}
            vocab = {v: text for text, v in metadata["model"]["vocab"].items()}
            vocab.update(
                {
                    row["id"]: row["content"]
                    for row in metadata["added_tokens"]
                    if not row["special"]
                }
            )
            support = {
                v: text
                for v, text in sorted(vocab.items())
                if v not in specials and re.fullmatch(r"[ab()+*]+", text)
            }
            assert support and all(
                tokenizer.decode([v], skip_special_tokens=False) == text
                for v, text in support.items()
            )
            assert all(c in support.values() for c in "ab()+*")
            mask, separator = tokenizer.token_to_id("<|mask|>"), tokenizer.token_to_id("#")
            assert mask == 151669 and separator is not None
            assert tokenizer.decode([separator], skip_special_tokens=False) == "#"
            assert not {151643, 151645, mask, separator} & support.keys()
            emit(
                "support",
                original_ids_bytes=support,
                size=len(support),
                aliases=len(support) - len(set(support.values())),
                omitted_tail="explicit_not_renormalized",
                separator_id=separator,
                mask_id=mask,
                eos_id=151645,
                pad_id=151643,
            )
            spec = importlib.util.spec_from_file_location(
                "a77_local_qwen", MODEL / "modeling_qwen3.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            config = module.A2DQwen3Config.from_pretrained(MODEL, local_files_only=True)
            config.use_cache = False
            with torch.inference_mode():
                model = (
                    module.A2DQwen3LMHeadModel.from_pretrained(
                        MODEL,
                        config=config,
                        local_files_only=True,
                        dtype=torch.bfloat16,
                        attn_implementation="sdpa",
                    )
                    .to("cuda")
                    .eval()
                )
            model.requires_grad_(False)
            torch.cuda.synchronize()
            signal.alarm(0)
            emit(
                "startup",
                wall_seconds=time.perf_counter() - started,
                torch=torch.__version__,
                transformers=transformers.__version__,
                model_source_sha256=sha(MODEL / "modeling_qwen3.py"),
                config_sha256=sha(MODEL / "config.json"),
                cuda_allocated_bytes=torch.cuda.memory_allocated(),
                rss_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            )
        except (TimeoutError, MemoryError) as error:
            signal.alarm(0)
            refuse("RESOURCE_REFUSAL_STARTUP", error=repr(error))
            return
        except Exception as error:
            signal.alarm(0)
            refuse(
                "RESOURCE_REFUSAL_STARTUP"
                if type(error).__name__ == "OutOfMemoryError"
                else "ERROR_STARTUP",
                error=repr(error),
            )
            return

        raw.mkdir(parents=True, exist_ok=False)
        for i, (p, m, n) in enumerate(CASES):
            current = preflight(False)
            emit("preflight_case", case=f"p{p}-m{m}-n{n}", **current)
            if not current["ready"]:
                refuse("RESOURCE_REFUSAL_FOREIGN_COMPUTE", cases=CASES[i:])
                return
            name = f"p{p}-m{m}-n{n}"
            signal.alarm(120)
            try:
                prefix = tokenizer.encode(PROMPTS[p], add_special_tokens=False).ids
                canvas, positions = [], []
                for j in range(m):
                    positions.extend(
                        range(len(prefix) + len(canvas), len(prefix) + len(canvas) + n)
                    )
                    canvas.extend([mask] * n)
                    if j + 1 < m:
                        canvas.append(separator)
                inputs = torch.tensor([prefix + canvas], device="cuda")
                legal = torch.tensor(list(support), device="cuda")
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
                begin = time.perf_counter()
                with torch.inference_mode():
                    hidden = model.model(input_ids=inputs, use_cache=False).last_hidden_state
                    torch.cuda.synchronize()
                    backbone_s = time.perf_counter() - begin
                    begin = time.perf_counter()
                    selected = []
                    for offset in range(0, len(positions), 32):
                        indices = torch.tensor(positions[offset : offset + 32], device="cuda")
                        logits = model.lm_head(hidden[0].index_select(0, indices)).to(torch.float64)
                        probs = torch.exp(
                            logits.index_select(1, legal)
                            - torch.logsumexp(logits, dim=1, keepdim=True)
                        )
                        selected.extend(probs.cpu().tolist())
                    torch.cuda.synchronize()
                    head_transfer_s = time.perf_counter() - begin
                del hidden, logits, probs, indices, inputs
                weights = [
                    [tuple(F(value) for value in selected[j * n + k]) for k in range(n)]
                    for j in range(m)
                ]
                if any(value <= 0 for rows in weights for row in rows for value in row):
                    raise ValueError("unsupported_nonpositive_represented_weight")
                delta, witness = F(-1), None
                for k in range(n):
                    for v, token in enumerate(support):
                        values = [weights[j][k][v] for j in range(m)]
                        mean = sum(values, F()) / m
                        for j, value in enumerate(values):
                            difference = abs(value / mean - 1)
                            if difference > delta:
                                delta = difference
                                witness = {
                                    "j": j,
                                    "k": k,
                                    "token_id": token,
                                    "bytes": support[token],
                                    "weights": list(map(str, values)),
                                    "mean": str(mean),
                                }
                d = (
                    None
                    if delta >= 1
                    else m * n * delta**2 / (2 * (1 - delta))
                    + 2 * (m - 1) * n**2 * delta**2 / (1 - delta) ** 2
                )
                raw_path = raw / f"{name}.json.gz"
                with (
                    raw_path.open("xb") as binary,
                    gzip.GzipFile(fileobj=binary, mode="wb", mtime=0) as compressed,
                ):
                    compressed.write(
                        json.dumps(
                            {
                                "case": name,
                                "support": support,
                                "probabilities_hex": [
                                    [value.hex() for value in row] for row in selected
                                ],
                            },
                            sort_keys=True,
                        ).encode()
                    )
                masses = [sum(row, F()) for rows in weights for row in rows]
                emit(
                    "case",
                    case=name,
                    status="CERTIFICATE_COVERED"
                    if d is not None and d <= F(1, 25)
                    else "CERTIFICATE_NOT_COVERED",
                    delta=str(delta),
                    delta_float=float(delta),
                    D_over_4=None if d is None else str(d / 4),
                    witness=witness,
                    support_mass_min=str(min(masses)),
                    support_mass_max=str(max(masses)),
                    raw_path=str(raw_path.resolve()),
                    raw_sha256=sha(raw_path),
                    backbone_seconds=backbone_s,
                    original_head_transfer_seconds=head_transfer_s,
                    cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                    rss_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    weight_max_bits=max(
                        max(v.numerator.bit_length(), v.denominator.bit_length())
                        for rows in weights
                        for row in rows
                        for v in row
                    ),
                    forwards=1,
                )
            except (TimeoutError, torch.cuda.OutOfMemoryError, MemoryError) as error:
                emit("case", case=name, status="RESOURCE_REFUSAL_CASE", error=repr(error))
                # No replacement/second forward. Remaining fixed cases stay visible.
                refuse("RESOURCE_NOT_RUN_AFTER_REFUSAL", cases=CASES[i + 1 :])
                return
            except Exception as error:
                emit("case", case=name, status="ERROR_CASE", error=repr(error))
                refuse("NOT_RUN_AFTER_ERROR", cases=CASES[i + 1 :])
                return
            finally:
                signal.alarm(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--coordinator-ready", action="store_true", required=True)
    args = parser.parse_args()
    run(args.output, args.raw)


if __name__ == "__main__":
    main()
