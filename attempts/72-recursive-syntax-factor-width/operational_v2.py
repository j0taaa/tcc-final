"""Frozen A72 V2: convolution proposal, exact audit, and native-logit capture.

The FFT proposal is approximate. Its measured joint TV is certified using
independently computed integer context masses; that audit is charged in full.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import resource
import select
import statistics
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MODEL = (
    Path.home()
    / ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/snapshots"
    / "08b83a6feb34df1a6011b80c3c00c7563e963b07"
)
PROMPTS = (
    "Return two fully nested bracket expressions separated by #. "
    "Use only (, ), [, ], and #. Do not add explanation.",
    "Complete this structured payload using two nested expressions separated by #. "
    "Round and square brackets must match. Output only the payload.",
)
EPSILON = Fraction(1, 100)


class CountedRandom(random.Random):
    def __init__(self, seed: int):
        super().__init__(seed)
        self.bits = 0

    def getrandbits(self, k: int) -> int:
        self.bits += k
        return super().getrandbits(k)


def pairs(half: int, marker: int):
    for a in range(marker):
        yield a, 2 * marker - 1 - a
    for a in range(2 * marker + 1, half + marker + 1):
        yield a, 2 * half + 2 * marker + 1 - a


def integer_masses(weights: list[list[int]]) -> list[int]:
    half = (len(weights) - 1) // 2
    result = []
    for marker in range(half + 1):
        mass = weights[2 * marker][4]
        for a, b in pairs(half, marker):
            mass *= weights[a][0] * weights[b][1] + weights[a][2] * weights[b][3]
        result.append(mass)
    return result


def rationalize(values) -> list[int]:
    ratios = [float(value).as_integer_ratio() for value in values]
    denominator = max(d for _, d in ratios)
    return [n * (denominator // d) for n, d in ratios]


def exact_tv(target: list[int], candidate: list[int]) -> Fraction:
    p_total, q_total = sum(target), sum(candidate)
    return Fraction(
        sum(abs(p * q_total - q * p_total) for p, q in zip(target, candidate, strict=True)),
        2 * p_total * q_total,
    )


def floating_rows(weights: list[list[int]]) -> np.ndarray:
    return np.array([[float(Fraction(value, max(row))) for value in row] for row in weights])


def orientation_logs(rows: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    length = len(rows)
    half = (length - 1) // 2
    opening = rows[:, 0] + rows[:, 2]
    closing = rows[:, 1] + rows[:, 3]
    prefix_a = np.r_[0.0, np.cumsum(np.log(opening))]
    prefix_c = np.r_[0.0, np.cumsum(np.log(closing))]
    j = np.arange(half + 1)
    log_u = (
        np.log(rows[2 * j, 4])
        + prefix_a[j]
        + prefix_c[2 * j]
        - prefix_c[j]
        + prefix_a[half + j + 1]
        - prefix_a[2 * j + 1]
        + prefix_c[length]
        - prefix_c[half + j + 1]
    )
    return log_u, (rows[:, 0] - rows[:, 2]) / opening, (rows[:, 1] - rows[:, 3]) / closing


def normalized(logs: np.ndarray) -> list[int]:
    values = np.exp(logs - np.max(logs))
    return rationalize(values / values.sum())


def triangular_convolution(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    size = 1 << (len(left) - 1).bit_length()
    a, b = np.zeros(size), np.zeros(size)
    a[: len(left)], b[: len(right)] = left, right
    result = np.zeros(2 * size - 1)
    block = 2
    while block <= size:
        half = block // 2
        left_blocks, right_blocks = a.reshape(-1, block), b.reshape(-1, block)
        convolution = np.fft.irfft(
            np.fft.rfft(left_blocks[:, :half], n=block, axis=1)
            * np.fft.rfft(right_blocks[:, half:], n=block, axis=1),
            n=block,
            axis=1,
        )
        indices = 2 * np.arange(0, size, block)[:, None] + half + np.arange(block - 1)
        result[indices] += convolution[:, : block - 1]
        block *= 2
    return result


def proposal(weights: list[list[int]]) -> dict:
    if any(value <= 0 for row in weights for value in row):
        return {"status": "unsupported_zero_weight"}
    rows = floating_rows(weights)
    if np.any(rows == 0):
        return {"status": "unsupported_float_underflow"}
    logs, x, y = orientation_logs(rows)
    rho = float(np.max(np.abs(x)) * np.max(np.abs(y)))
    half = (len(rows) - 1) // 2
    eta = math.log1p(float(EPSILON)) / 2
    degree = 0
    while rho < 1 and half * rho ** (degree + 1) / ((degree + 1) * (1 - rho)) > eta / 2:
        degree += 1
        if degree > 64:
            break
    if rho >= 1 or degree > 64:
        return {"status": "refused_degree", "rho": rho, "degree_lower_bound": degree}
    logs -= half * math.log(2)
    power_x, power_y = np.ones(len(x)), np.ones(len(y))
    for k in range(1, degree + 1):
        power_x *= x
        power_y *= y
        coefficients = triangular_convolution(power_x, power_y)
        j = np.arange(half + 1)
        left_indices, right_indices = 2 * j - 1, 2 * half + 2 * j + 1
        combined = np.zeros(half + 1)
        mask = left_indices >= 0
        combined[mask] += coefficients[left_indices[mask]]
        mask = right_indices < 2 * len(rows) - 1
        combined[mask] += coefficients[right_indices[mask]]
        logs += ((-1) ** (k + 1) / k) * combined
    return {
        "status": "proposed",
        "rho": rho,
        "degree": degree,
        "marker_weights": normalized(logs),
        "real_arithmetic_log_tail_bound": half * rho ** (degree + 1) / ((degree + 1) * (1 - rho)),
    }


def complete_contextual_circuit(weights: list[list[int]]) -> list[int]:
    rows = floating_rows(weights)
    half = (len(rows) - 1) // 2
    scores = np.log(rows[::2, 4])
    for j in range(half + 1):
        left = rows[:j]
        left_mirrors = rows[j : 2 * j][::-1]
        right = rows[2 * j + 1 : half + j + 1]
        right_mirrors = rows[half + j + 1 :][::-1]
        for a, b in ((left, left_mirrors), (right, right_mirrors)):
            scores[j] += np.log(a[:, 0] * b[:, 1] + a[:, 2] * b[:, 3]).sum()
    return normalized(scores)


def orientation_control(weights: list[list[int]]) -> list[int]:
    return normalized(orientation_logs(floating_rows(weights))[0])


def sample(weights: list[list[int]], masses: list[int], rng: random.Random) -> str:
    draw = rng.randrange(sum(masses))
    marker = 0
    while draw >= masses[marker]:
        draw -= masses[marker]
        marker += 1
    word = ["#"] * len(weights)
    for a, b in pairs((len(weights) - 1) // 2, marker):
        round_mass = weights[a][0] * weights[b][1]
        square_mass = weights[a][2] * weights[b][3]
        word[a], word[b] = (
            ("(", ")") if rng.randrange(round_mass + square_mass) < round_mass else ("[", "]")
        )
    return "".join(word)


def valid(word: str) -> bool:
    if word.count("#") != 1:
        return False
    closing = {"(": ")", "[": "]"}
    for block in word.split("#"):
        middle = len(block) // 2
        if len(block) % 2 or any(c not in closing for c in block[:middle]):
            return False
        if block[middle:] != "".join(closing[c] for c in reversed(block[:middle])):
            return False
    return True


def timed(function):
    function()
    elapsed = []
    result = None
    for _ in range(5):
        start = time.perf_counter_ns()
        result = function()
        elapsed.append((time.perf_counter_ns() - start) / 1e6)
    return {
        "median_ms": statistics.median(elapsed),
        "max_ms": max(elapsed),
        "repetitions_ms": elapsed,
    }, result


def library_validate(weights: list[list[int]], target: list[int]) -> dict:
    from mwpc_exact.cfg_posterior import compile_cfg_sampler
    from mwpc_exact.eos_policy import EOSMode, EOSPolicy
    from mwpc_exact.mass_certificate import ProbabilityInput
    from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
    from mwpc_exact.reference.normalization import normalize_to_cnf
    from mwpc_exact.state import SelectionInput
    from mwpc_exact.support import SupportPolicy, build_per_position_support
    from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
    from mwpc_exact.types import SupportKind

    builder = _SourceGrammarBuilder(("S", "P"), start="S")
    builder.rule("S", "P", b"#", "P")
    builder.rule("P", b"(", "P", b")")
    builder.rule("P", b"[", "P", b"]")
    builder.rule("P")
    source = builder.build()
    canvas = (None,) * len(weights)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=5),
        explicit_support={i: tuple(range(5)) for i in range(len(weights))},
    )
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        canvas,
        (),
        support,
        CompositionalByteLevelAdapter((b"(", b")", b"[", b"]", b"#")),
        EOSPolicy(EOSMode.ABSENT),
    )
    probabilities = tuple(tuple(Fraction(value, sum(row)) for value in row) for row in weights)
    start = time.perf_counter_ns()
    posterior = compile_cfg_sampler(source, state).evaluate(ProbabilityInput(state, probabilities))
    assert posterior.valid_mass == Fraction(sum(target), math.prod(sum(row) for row in weights))
    assert tuple(posterior.marginals[2 * j][4] for j in range(len(target))) == tuple(
        Fraction(value, sum(target)) for value in target
    )
    return {
        "status": "exact_mass_and_marker_marginals_agree",
        "elapsed_ms": (time.perf_counter_ns() - start) / 1e6,
    }


def synthetic_cases():
    for length in (33, 129, 513, 2049):
        for radius in (0.25, 0.75, 0.99):
            for seed in (720201, 720202, 720203):
                rng = random.Random(seed)
                limit = int(256 * radius)
                weights = []
                for _ in range(length):
                    a, c, marker = (rng.randrange(1, 17) for _ in range(3))
                    x, y = rng.randint(-limit, limit), rng.randint(-limit, limit)
                    weights.append(
                        [a * (256 + x), c * (256 + y), a * (256 - x), c * (256 - y), marker * 512]
                    )
                yield {
                    "case": f"synthetic-n{length}-r{radius}-s{seed}",
                    "kind": "synthetic",
                    "weights": weights,
                }


def measure(capture: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    capture_rows = [json.loads(line) for line in capture.read_text().splitlines()]
    cases = list(synthetic_cases())
    for record in capture_rows:
        if record.get("type") == "frame":
            cases.append(
                {
                    **record,
                    "kind": "neural",
                    "weights": [
                        rationalize([float.fromhex(v) for v in row])
                        for row in record["probabilities_hex"]
                    ],
                }
            )
    with output.open("x") as out:
        out.write(
            json.dumps(
                {
                    "type": "metadata",
                    "protocol_commit": "e763bc35",
                    "numpy": np.__version__,
                    "python": sys.version,
                    "epsilon": "1/100",
                    "capture_sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
                }
            )
            + "\n"
        )
        for case in cases:
            weights = case["weights"]
            row = {
                "type": "result",
                "case": case["case"],
                "kind": case["kind"],
                "slots": len(weights),
                "input_integer_bits": sum(v.bit_length() for r in weights for v in r),
            }
            methods = [
                ("integer_conditioning", lambda w=weights: integer_masses(w)),
                ("contextual_circuit", lambda w=weights: complete_contextual_circuit(w)),
                ("orientation_only", lambda w=weights: orientation_control(w)),
                ("convolution", lambda w=weights: proposal(w)),
            ]
            offset = int(case["case"].encode().hex(), 16) % len(methods)
            answers = {}
            for name, function in methods[offset:] + methods[:offset]:
                row[name], answers[name] = timed(function)
            target = answers["integer_conditioning"]
            row["max_context_mass_bits"] = max(v.bit_length() for v in target)
            candidate = answers["convolution"]
            row["convolution"].update({k: v for k, v in candidate.items() if k != "marker_weights"})
            for name in ("contextual_circuit", "orientation_only", "convolution"):
                marker_weights = (
                    candidate.get("marker_weights") if name == "convolution" else answers[name]
                )
                if marker_weights is None:
                    continue
                audit, distance = timed(
                    lambda q=marker_weights, w=weights: exact_tv(integer_masses(w), q)
                )
                row[name]["audit"] = audit
                row[name]["tv_exact_numerator_hex"] = hex(distance.numerator)
                row[name]["tv_exact_denominator_hex"] = hex(distance.denominator)
                row[name]["marker_weights_hex"] = [hex(v) for v in marker_weights]
                row[name]["tv_float"] = float(distance)
                row[name]["tv_pass"] = distance <= EPSILON
                sample_time, word = timed(
                    lambda q=marker_weights, w=weights: sample(w, q, random.Random(720205))
                )
                assert valid(word)
                counted = CountedRandom(720205)
                assert sample(weights, marker_weights, counted) == word
                row[name]["sample"] = sample_time
                row[name]["rng_bits_for_sample"] = counted.bits
                row[name]["output_bytes"] = len(word)
                if case["kind"] == "neural":
                    row[name]["sample_word"] = word
                row[name]["sample_sha256"] = hashlib.sha256(word.encode()).hexdigest()
                row[name]["certified_total_median_ms"] = (
                    row[name]["median_ms"] + audit["median_ms"] + sample_time["median_ms"]
                )
            sample_time, word = timed(
                lambda w=weights, p=target: sample(w, p, random.Random(720205))
            )
            assert valid(word)
            row["integer_conditioning"]["sample"] = sample_time
            counted = CountedRandom(720205)
            assert sample(weights, target, counted) == word
            row["integer_conditioning"]["rng_bits_for_sample"] = counted.bits
            row["integer_conditioning"]["output_bytes"] = len(word)
            if case["kind"] == "neural":
                row["integer_conditioning"]["sample_word"] = word
            row["integer_conditioning"]["certified_total_median_ms"] = (
                row["integer_conditioning"]["median_ms"] + sample_time["median_ms"]
            )
            if len(weights) <= 33:
                row["library"] = library_validate(weights, target)
            row["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            out.write(json.dumps(row) + "\n")
            out.flush()
            print(
                json.dumps(
                    {
                        "case": row["case"],
                        "status": candidate["status"],
                        "rho": candidate.get("rho"),
                        "degree": candidate.get("degree"),
                        "tv": row["convolution"].get("tv_float"),
                    }
                ),
                flush=True,
            )


def append_record(path: Path, record: dict) -> None:
    with path.open("a") as stream:
        stream.write(json.dumps(record) + "\n")


def capture_worker(output: Path) -> None:
    import torch
    import transformers
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    def phase(name: str, seconds: int, case: str | None = None):
        print(
            "A72_PHASE " + json.dumps({"phase": name, "seconds": seconds, "case": case}), flush=True
        )

    phase("load", 180)
    torch.set_num_threads(4)
    torch.manual_seed(720204)
    free, _ = torch.cuda.mem_get_info()
    if free < 6.5 * 2**30:
        append_record(
            output,
            {"type": "refusal", "status": "insufficient_free_gpu_memory", "free_bytes": free},
        )
        return
    start = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=True)
    ids = [tokenizer.encode(c, add_special_tokens=False) for c in "()[]#"]
    if any(len(v) != 1 or tokenizer.decode(v) != c for c, v in zip("()[]#", ids, strict=True)):
        append_record(
            output, {"type": "refusal", "status": "no_atomic_original_ids", "encoded_ids": ids}
        )
        return
    token_ids = [v[0] for v in ids]
    model = AutoModel.from_pretrained(
        MODEL,
        local_files_only=True,
        trust_remote_code=True,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16
        ),
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    ).eval()
    torch.cuda.synchronize()
    metadata = {
        "type": "model",
        "snapshot": MODEL.name,
        "quantization": "NF4",
        "token_ids": token_ids,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "load_seconds": time.perf_counter() - start,
        "initial_free_gpu_bytes": free,
        "model_allocated_gpu_bytes": torch.cuda.memory_allocated(),
        "sources": {
            name: hashlib.sha256((MODEL / name).read_bytes()).hexdigest()
            for name in (
                "config.json",
                "modeling_llada.py",
                "configuration_llada.py",
                "tokenizer.json",
            )
        },
        "weight_blobs": {p.name: p.resolve().name for p in MODEL.glob("*.safetensors")},
    }
    append_record(output, metadata)
    for prompt_index, prompt in enumerate(PROMPTS):
        prefix = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=True, add_generation_prompt=True
        )
        for length in (33, 129, 513):
            case = f"llada-p{prompt_index}-n{length}"
            phase("forward", 120, case)
            input_ids = torch.tensor(
                [prefix + [model.config.mask_token_id] * length], device="cuda"
            )
            try:
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
                start = time.perf_counter()
                with torch.inference_mode():
                    logits = model(input_ids).logits[0, len(prefix) :]
                torch.cuda.synchronize()
                forward_seconds = time.perf_counter() - start
                start = time.perf_counter()
                selected = []
                for offset in range(0, length, 32):
                    chunk = logits[offset : offset + 32].to(torch.float64)
                    probabilities = torch.exp(
                        chunk[:, token_ids] - torch.logsumexp(chunk, dim=1, keepdim=True)
                    )
                    selected.extend(probabilities.cpu().tolist())
                torch.cuda.synchronize()
                transfer_seconds = time.perf_counter() - start
                append_record(
                    output,
                    {
                        "type": "frame",
                        "case": case,
                        "prompt_index": prompt_index,
                        "slots": length,
                        "forward_seconds": forward_seconds,
                        "transfer_normalization_seconds": transfer_seconds,
                        "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                        "gpu_peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                        "selected_support_mass_min": min(map(sum, selected)),
                        "selected_support_mass_max": max(map(sum, selected)),
                        "probabilities_hex": [[v.hex() for v in row] for row in selected],
                    },
                )
                del logits, probabilities, chunk, input_ids
            except torch.cuda.OutOfMemoryError as error:
                append_record(
                    output,
                    {
                        "type": "frame_refusal",
                        "case": case,
                        "status": "cuda_oom",
                        "error": str(error),
                    },
                )
                torch.cuda.empty_cache()
            if output.stat().st_size > 2 * 2**20:
                raise RuntimeError("capture_exceeds_protocol_size_limit")


def capture(output: Path) -> None:
    with output.open("x") as stream:
        stream.write(
            json.dumps(
                {
                    "type": "launch",
                    "protocol_commit": "e763bc35",
                    "prompts": PROMPTS,
                    "pid": os.getpid(),
                    "expected_cases": [
                        f"llada-p{p}-n{n}" for p in range(2) for n in (33, 129, 513)
                    ],
                }
            )
            + "\n"
        )
    child = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "capture-worker", "--output", str(output)],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert child.stdout is not None
    deadline = time.monotonic() + 180
    phase = {"phase": "load", "case": None}
    while child.poll() is None:
        if time.monotonic() > deadline:
            child.kill()
            child.wait()
            append_record(output, {"type": "refusal", "status": "external_timeout", **phase})
            return
        ready, _, _ = select.select([child.stdout], [], [], 0.25)
        if ready:
            line = child.stdout.readline()
            print(line, end="", flush=True)
            if line.startswith("A72_PHASE "):
                phase = json.loads(line.removeprefix("A72_PHASE "))
                deadline = time.monotonic() + phase["seconds"]
    append_record(output, {"type": "exit", "returncode": child.returncode})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capture", "capture-worker", "measure"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    if args.mode == "capture":
        capture(args.output)
    elif args.mode == "capture-worker":
        capture_worker(args.output)
    else:
        assert args.capture is not None
        measure(args.capture, args.output)


if __name__ == "__main__":
    main()
