"""Frozen six-case MAP gate. Own lock before clocks, imports, or CUDA use."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import resource
import signal
import subprocess
import time
import traceback
from itertools import product
from pathlib import Path

from contraction import Node, compile_forest, word_forest

HERE = Path(__file__).resolve().parent
MODEL = Path("/home/jota/projects/tcc-final/.cache/a52-model-metadata")
METHODS = ("dense", "sparse", "manual", "a73")
CASES = (
    ("copy", 4, 0),
    ("copy", 16, 0),
    ("copy", 32, 1),
    ("independent", 4, 0),
    ("independent", 16, 1),
    ("balance", 4, 1),
)
PROMPTS = (
    "Fill the comma-separated fields with a valid identifier. "
    "Repeated fields must agree.\nFields: ",
    "Complete this identifier record using short names. "
    "Respect the declared joint constraints.\nRecord: ",
)


def sha_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_forest(family, n, ids, sentinel):
    if family == "copy":
        return word_forest([(v,) * n for v in ids])
    if family == "balance":
        patterns = [p for p in product(range(2), repeat=4) if p[0] + p[1] == p[2] + p[3]]
        words = [(sentinel,) * 4]
        words.extend(tuple(v if x else sentinel for x in p) for p in patterns[1:] for v in ids)
        return word_forest(words)
    nodes, choices = [], []
    for position in range(n):
        children = []
        for v in ids:
            children.append(len(nodes))
            nodes.append(Node("leaf", position=position, token=v))
        choices.append(len(nodes))
        nodes.append(Node("or", tuple(children)))
    nodes.append(Node("and", tuple(choices)))
    return nodes, len(nodes) - 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Retain descriptor through every measurement and until CUDA context exits.
    lock = open("/tmp/tcc-final-candidate-tests-gpu.lock", "a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("GPU/timing lock occupied; no GPU use or timing performed", flush=True)
        return 75
    started, cpu_started = time.perf_counter(), time.process_time()
    args.output.mkdir(parents=True, exist_ok=True)
    stream = (args.output / "records.jsonl").open("x")

    def emit(kind, **fields):
        stream.write(json.dumps({"kind": kind, **fields}, sort_keys=True) + "\n")
        stream.flush()
        if kind != "measurement":
            print(json.dumps({"kind": kind, **fields}, sort_keys=True), flush=True)

    def timeout_handler(signum, frame):
        raise TimeoutError("predeclared 1200-second process cap")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(1200)
    emit(
        "start",
        producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        dirty=subprocess.check_output(["git", "status", "--porcelain"], text=True),
        protocol_sha256=sha_file(HERE / "protocol.md"),
        source_sha256={p.name: sha_file(p) for p in HERE.glob("*.py")},
        pid=os.getpid(),
    )
    try:
        inventory = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader",
            ],
            text=True,
        ).strip()
        processes = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader",
            ],
            text=True,
        ).strip()
        emit("gpu_preflight", inventory=inventory, compute_processes=processes)
        utilization = int(inventory.split(",")[-1].strip().split()[0])
        if processes or utilization > 5:
            emit("resource_refusal", reason="foreign compute process or utilization above 5%")
            return 76
        os.environ.update(
            HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false"
        )
        import re

        import numpy as np
        import torch
        import transformers
        from tokenizers import Tokenizer

        torch.set_num_threads(4)
        torch.manual_seed(730019)
        torch.cuda.manual_seed_all(730019)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        expected = {
            "tokenizer.json": "6d55810de1daf81d1d1259355b4b85810385022ab745be68029295935a4eacf0",
            "model.safetensors": "3485d18016ce6c302e8973809b47aa6369d6612ef9978d0690b4575d1193e932",
        }
        for filename, digest in expected.items():
            if sha_file(MODEL / filename) != digest:
                raise ValueError(f"hash mismatch: {filename}")
        tokenizer = Tokenizer.from_file(str(MODEL / "tokenizer.json"))
        ordinary = json.loads((MODEL / "tokenizer.json").read_text())["model"]["vocab"]
        ids = sorted(
            v for text, v in ordinary.items() if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text)
        )
        identifier_set = set(ids)
        texts = {v: text for text, v in ordinary.items() if v in identifier_set}
        assert len(ids) == len(set(texts.values())) == 32804
        assert all(tokenizer.decode([v], skip_special_tokens=False) == texts[v] for v in ids)
        sentinel, comma = tokenizer.token_to_id("#"), tokenizer.token_to_id(",")
        assert sentinel not in ids and comma not in ids
        assert tokenizer.token_to_id("<|mask|>") == 151669
        texts[sentinel] = "#"
        spec = importlib.util.spec_from_file_location(
            "a73_local_qwen3", MODEL / "modeling_qwen3.py"
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
        startup_wall, startup_cpu = time.perf_counter() - started, time.process_time() - cpu_started
        emit(
            "startup",
            wall_s=startup_wall,
            cpu_s=startup_cpu,
            torch=torch.__version__,
            transformers=transformers.__version__,
            model_path=str(MODEL),
            model_bytes=torch.cuda.memory_allocated(),
            peak_cuda_bytes=torch.cuda.max_memory_allocated(),
            rss_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            model_source_sha256=sha_file(MODEL / "modeling_qwen3.py"),
            config_sha256=sha_file(MODEL / "config.json"),
        )
        patterns = [p for p in product(range(2), repeat=4) if p[0] + p[1] == p[2] + p[3]]
        forward_count = 0

        def run_case(case_index, family, n, prompt_index):
            case = f"{family}{n}-p{prompt_index}"
            emit("case_start", case=case)
            prefix = tokenizer.encode(PROMPTS[prompt_index], add_special_tokens=False).ids
            canvas = [151669 if i % 2 == 0 else comma for i in range(2 * n - 1)]
            inputs = torch.tensor([prefix + canvas], device="cuda")
            positions = torch.tensor([len(prefix) + 2 * i for i in range(n)], device="cuda")
            legal = ids + ([sentinel] if family == "balance" else [])
            legal_set = set(legal)
            legal_tensor = torch.tensor(legal, device="cuda")
            routes = {}
            for method in METHODS:
                torch.cuda.synchronize()
                prep_wall, prep_cpu = time.perf_counter(), time.process_time()
                basis_tensor, pivots, stats = None, tuple(range(n)), None
                if method == "dense":
                    weight = model.lm_head.weight.float()
                else:
                    weight = model.lm_head.weight.index_select(0, legal_tensor).float()
                if method == "a73":
                    nodes, root = make_forest(family, n, ids, sentinel)
                    if len(nodes) > 2000000:
                        raise MemoryError("predeclared 2-million-node cap")
                    plan = compile_forest(nodes, root, n)
                    if len(plan.groups) != 1:
                        raise ValueError("bounded V1 runtime requires one common B group")
                    basis = next(iter(plan.groups))
                    pivots, stats = basis.pivots, plan.stats
                    basis_tensor = torch.tensor(
                        [[float(x) for x in row] for row in basis.rows],
                        device="cuda",
                        dtype=torch.float32,
                    )
                    del nodes, plan
                torch.cuda.synchronize()
                prep_wall, prep_cpu = (
                    time.perf_counter() - prep_wall,
                    time.process_time() - prep_cpu,
                )
                routes[method] = weight, basis_tensor, pivots
                emit(
                    "preparation",
                    case=case,
                    method=method,
                    wall_s=prep_wall,
                    cpu_s=prep_cpu,
                    stats=stats,
                    weight_shape=list(weight.shape),
                    transform_shape=None if basis_tensor is None else list(basis_tensor.shape),
                    peak_cuda_bytes=torch.cuda.max_memory_allocated(),
                    rss_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                )
                if prep_wall > 120:
                    raise TimeoutError("predeclared 120-second case preparation cap")

            def backbone():
                nonlocal forward_count
                forward_count += 1
                if forward_count > 150:
                    raise RuntimeError("predeclared 150-forward cap")
                return (
                    model.model(inputs, use_cache=False)
                    .last_hidden_state[0]
                    .index_select(0, positions)
                )

            def solve(projected, compressed_pivots):
                if family == "copy":
                    scores = projected.sum(dim=0)
                    best = int(scores.argmax().item())
                    return [ids[best]] * n, scores
                if family == "independent":
                    best = projected.argmax(dim=1).tolist()
                    return [ids[j] for j in best], projected
                pattern_matrix = torch.tensor(
                    [[p[j] for j in compressed_pivots] for p in patterns[1:]],
                    dtype=projected.dtype,
                    device="cuda",
                )
                delta = projected[:, :-1] - projected[:, -1:]
                scores = torch.cat(
                    (
                        torch.zeros(1, dtype=projected.dtype, device="cuda"),
                        (pattern_matrix @ delta).flatten(),
                    )
                )
                best = int(scores.argmax().item())
                if best == 0:
                    return [sentinel] * 4, scores
                p, v = divmod(best - 1, len(ids))
                return [ids[v] if x else sentinel for x in patterns[p + 1]], scores

            torch.cuda.synchronize()
            oracle_wall, oracle_cpu = time.perf_counter(), time.process_time()
            with torch.inference_mode():
                hidden = backbone()
                reference_weight = routes["sparse"][0].double()
                reference_logits = hidden.double() @ reference_weight.T
                reference_word, reference_scores = solve(reference_logits, tuple(range(n)))
                top = reference_scores.topk(2, dim=-1).values
                gap = float((top[..., 0] - top[..., 1]).min().item())
                bound = (
                    16
                    * torch.finfo(torch.float64).eps
                    * config.hidden_size
                    * n
                    * float(reference_weight.abs().max().item())
                    * float(hidden.double().abs().sum().item())
                )
                torch.cuda.synchronize()
                h_cpu = hidden.float().cpu().numpy()
                np.savez(args.output / f"{case}-hidden.npz", hidden=h_cpu)
                h_hash = hashlib.sha256(h_cpu.tobytes()).hexdigest()
                certified = gap > 2 * bound
                emit(
                    "reference",
                    case=case,
                    status="certified" if certified else "inconclusive",
                    word=reference_word,
                    gap=gap,
                    fp64_error_bound=bound,
                    wall_s=time.perf_counter() - oracle_wall,
                    cpu_s=time.process_time() - oracle_cpu,
                    hidden_sha256=h_hash,
                    prefix=prefix,
                    canvas=canvas,
                    hidden_shape=list(hidden.shape),
                    forward_count=forward_count,
                )
                del reference_weight, reference_logits, reference_scores

            def query(method, repetition):
                weight, transform, pivots = routes[method]
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats()
                base_memory = torch.cuda.memory_allocated()
                begin_wall, begin_cpu = time.perf_counter(), time.process_time()
                with torch.inference_mode():
                    actual_h = backbone()
                    torch.cuda.synchronize()
                    backbone_wall = time.perf_counter() - begin_wall
                    h = actual_h.float()
                    selected = tuple(range(n))
                    if method == "a73":
                        h, selected = transform @ h, pivots
                    elif method == "manual" and family == "copy":
                        h = h.sum(dim=0, keepdim=True)
                    projected = h @ weight.T
                    if method == "dense":
                        projected = projected.index_select(1, legal_tensor)
                    word, _ = solve(projected, selected)
                    output = canvas.copy()
                    output[::2] = word
                    valid = all(v in legal_set for v in word)
                    valid = valid and output[1::2] == [comma] * (n - 1)
                    if family == "copy":
                        valid = valid and len(set(word)) == 1
                    elif family == "balance":
                        active = [v for v in word if v != sentinel]
                        valid = valid and len(set(active)) <= 1
                        valid = valid and sum(v != sentinel for v in word[:2]) == sum(
                            v != sentinel for v in word[2:]
                        )
                    decoded = tokenizer.decode(output, skip_special_tokens=False)
                    valid = valid and decoded == ",".join(texts[v] for v in word)
                    stable_h = bool(torch.equal(actual_h, hidden))
                    optimal = certified and stable_h and word == reference_word
                    serialized = json.dumps({"ids": output, "text": decoded}, ensure_ascii=False)
                    torch.cuda.synchronize()
                total_wall, total_cpu = (
                    time.perf_counter() - begin_wall,
                    time.process_time() - begin_cpu,
                )
                emit(
                    "measurement",
                    case=case,
                    method=method,
                    repetition=repetition,
                    wall_s=total_wall,
                    cpu_s=total_cpu,
                    backbone_wall_s=backbone_wall,
                    boundary_wall_s=total_wall - backbone_wall,
                    status="OPTIMAL" if valid and optimal else "inconclusive_or_error",
                    valid=valid,
                    hidden_stable=stable_h,
                    matches_reference=word == reference_word,
                    output_ids=output,
                    output_sha256=hashlib.sha256(serialized.encode()).hexdigest(),
                    output_bytes=len(serialized.encode()),
                    rng_calls=0,
                    projected_shape=list(projected.shape),
                    peak_cuda_bytes=torch.cuda.max_memory_allocated(),
                    incremental_cuda_bytes=torch.cuda.max_memory_allocated() - base_memory,
                    rss_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                )

            for repetition in range(-1, 5):
                shift = (case_index + max(repetition, 0)) % len(METHODS)
                for method in METHODS[shift:] + METHODS[:shift]:
                    query(method, repetition)

        for case_index, (family, n, prompt_index) in enumerate(CASES):
            run_case(case_index, family, n, prompt_index)
            torch.cuda.empty_cache()
        emit("complete", forward_count=forward_count, wall_s=time.perf_counter() - started)
        return 0
    except BaseException as exc:
        emit(
            "interrupted_or_error",
            exception=type(exc).__name__,
            reason=str(exc),
            traceback=traceback.format_exc(),
        )
        return 1
    finally:
        signal.alarm(0)
        stream.close()
        # Descriptor intentionally remains open until process exit: CUDA teardown is protected.


if __name__ == "__main__":
    raise SystemExit(main())
