"""Opt-in bounded DEVELOPMENT resource screen; no labels, updates or speed gate."""

import argparse
import contextlib
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import resource
import signal
import subprocess
import time
from pathlib import Path

import numpy as np

from .floating import FloatPlan, TorchPlan
from .numeric_json import STATE_COUNT, NumericJSON
from .preflight_floating import compare
from .test_numeric_json import independent_accepts
from .tokenizer_audit import FILES, emissions, verify_files

HERE = Path(__file__).resolve().parent
INPUT_SHA = "bfdfabc9fb0fad256ad8f44f9a43acd8c171ebc265235d56c861a962b03d5b49"
WEIGHT_SHA = "3485d18016ce6c302e8973809b47aa6369d6612ef9978d0690b4575d1193e932"
PROMPT = (
    'Solve the following problem. Return only a JSON object with one field named "answer", '
    "whose value is a JSON number.\nProblem: {question}"
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def serial(value):
    if isinstance(value, dict):
        return {k: serial(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [serial(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


class ResourceRefusal(RuntimeError):
    pass


@contextlib.contextmanager
def bounded(seconds=60):
    def timeout(signum, frame):
        raise ResourceRefusal(f"operation exceeded {seconds}s cap")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def auxiliary_statistics(plan, weights, word, anchor, action):
    """Valid full-triple and known-anchor controls, same observed draw."""
    n = len(weights)
    gates = weights / (weights + 0.01)
    keep = np.asarray([i in dict(action) for i in range(n)], dtype=np.float64)
    sampled_gates = gates[np.arange(n), word]
    full_alpha = keep - sampled_gates
    full_alpha[anchor] = 0
    anchor_score = np.eye(n)[anchor] - 1 / n
    full = {
        "alpha": full_alpha,
        "beta": np.sum(full_alpha * np.log(weights[np.arange(n), word])),
        "anchor": anchor_score,
    }
    filtered = weights * (1 - gates)
    for i, v in action:
        filtered[i] = 0
        filtered[i, v] = weights[i, v] * gates[i, v]
    filtered[anchor] = 0
    filtered[anchor, word[anchor]] = weights[anchor, word[anchor]]
    _, posterior = plan.posterior(filtered)
    gate_score = posterior * (keep[:, None] - gates)
    gate_score[anchor] = 0
    intermediate = {
        "alpha": gate_score.sum(axis=1),
        "beta": np.sum(gate_score * np.log(weights)),
        "anchor": anchor_score,
    }
    return {"full_triple": full, "known_anchor": intermediate}


def run(folder, output, protocol_path):
    import torch
    from transformers import AutoTokenizer

    output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads(protocol_path.read_text())
    report = {
        "scope": "KNOWN_DEVELOPMENT_RESOURCE_ONLY",
        "model_forward_attempts": 0,
        "model_forward_completions": 0,
        "updates": 0,
        "competitive_timing": False,
        "native_rng_exactness_claimed": False,
        "cases": [],
    }
    events = (output / "events.jsonl").open("x", buffering=1)
    rows = (output / "rows.jsonl").open("x", buffering=1)

    def event(kind, **fields):
        events.write(json.dumps({"event": kind, "utc_seconds": time.time(), **fields}) + "\n")

    started = time.monotonic()

    def budget():
        left = 1200 - (time.monotonic() - started)
        if left <= 0:
            raise ResourceRefusal("whole-screen20min cap")
        return min(60, left)

    try:
        verify_files(folder)
        if sha(folder / "model.safetensors") != WEIGHT_SHA:
            raise ValueError("checkpoint SHA mismatch")
        if sha(HERE / "consumer-inputs-v4.json") != INPUT_SHA:
            raise ValueError("input manifest SHA mismatch")
        for name, expected in protocol["source_sha256"].items():
            if sha(HERE / name) != expected:
                raise ValueError(f"frozen consumer source mismatch: {name}")
        runtime = {
            p: importlib.metadata.version(p)
            for p in ("torch", "transformers", "tokenizers", "numpy", "safetensors")
        }
        if runtime != protocol["runtime"]:
            raise ValueError("runtime differs from frozen protocol")
        torch.set_num_threads(4)
        torch.manual_seed(52040)
        torch.cuda.manual_seed_all(52040)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        write_json(output / "protocol.json", protocol)
        write_json(
            output / "provenance.json",
            {
                "producer_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "source_sha256": protocol["source_sha256"],
                "runtime": runtime,
                "python": platform.python_version(),
                "cuda": torch.version.cuda,
                "gpu": torch.cuda.get_device_name(),
                "checkpoint_sha256": WEIGHT_SHA,
                "tokenizer_file_sha256": FILES,
                "prompt": PROMPT,
                "chat_template": (folder / "chat_template.jinja").read_text(),
            },
        )
        tokenizer = AutoTokenizer.from_pretrained(folder, local_files_only=True)
        inputs = json.loads((HERE / "consumer-inputs-v4.json").read_text())["questions"]
        prompts = []
        for item in inputs:
            prompt = tokenizer.apply_chat_template(
                [{"role": "user", "content": PROMPT.format(question=item["question"])}],
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            prompts.append(prompt)
        write_json(output / "prompt-ids.json", prompts)
        if len(prompts) != 8 or any(len(p) > 1024 for p in prompts):
            raise ResourceRefusal("input count or1024prompt-token cap")
        compile_start = time.monotonic()
        with bounded(budget()):
            table = emissions(folder)
            language = NumericJSON(table, 151645, 151643)
            plan = FloatPlan(language)
            arcs = int(np.sum(plan.effects >= 0)) * 32
            if arcs > 2_000_000:
                raise ResourceRefusal("symbolic arc cap")
        np.savez_compressed(
            output / "token-effects.npz",
            effects=plan.effects,
            mapping=plan.mapping,
            emission_bytes=np.frombuffer(b"".join(table), dtype=np.uint8),
            emission_lengths=np.asarray([len(b) for b in table], dtype=np.int64),
        )
        report["compiler"] = {
            "classes": plan.class_count,
            "states": STATE_COUNT,
            "arcs": arcs,
            "diagnostic_seconds": time.monotonic() - compile_start,
        }
        spec = importlib.util.spec_from_file_location(
            "a52_pinned_resource_model", folder / "modeling_qwen3.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        config = module.A2DQwen3Config.from_pretrained(folder, local_files_only=True)
        config.use_cache = False
        load_start = time.monotonic()
        with bounded(1200 - (time.monotonic() - started)):
            model = (
                module.A2DQwen3LMHeadModel.from_pretrained(
                    folder,
                    config=config,
                    local_files_only=True,
                    dtype=torch.bfloat16,
                    attn_implementation="sdpa",
                )
                .to("cuda")
                .eval()
            )
        model.requires_grad_(False)
        report["diagnostic_model_load_seconds"] = time.monotonic() - load_start
        backend = TorchPlan(plan)
        persistent_bytes = backend.mapping.nbytes + backend.routes.nbytes

        def forward(prompt, name):
            if report["model_forward_attempts"] >= 9:
                raise ResourceRefusal("nine model-forward cap")
            ids = torch.tensor([prompt + [151669] * 32], device="cuda")
            mask = torch.ones_like(ids)
            report["model_forward_attempts"] += 1
            event("forward_attempt", name=name, ordinal=report["model_forward_attempts"])
            with bounded(budget()), torch.no_grad():
                logits = model(ids, attention_mask=mask, use_cache=False, logits_to_keep=32).logits
                torch.cuda.synchronize()
            report["model_forward_completions"] += 1
            event("forward_complete", name=name)
            raw = (
                {"logits_bf16": logits[0].view(torch.uint16).cpu().numpy()}
                if logits.dtype == torch.bfloat16
                else {"unexpected_logits": logits.detach().cpu().numpy()}
            )
            np.savez_compressed(output / f"head-{name}.npz", **raw)
            if logits.shape != (1, 32, 151936) or logits.dtype != torch.bfloat16:
                raise ValueError("original-V32-slot BF16 head contract mismatch")
            return logits[0]

        # The warmup's original bits are retained too; it is never a ninth case.
        warmup = forward(prompts[0], "warmup")
        del warmup
        for case, (item, prompt) in enumerate(zip(inputs, prompts, strict=True)):
            case_start = time.monotonic()
            row = {"case": case, "input_id": item["id"], "draws": []}
            try:
                budget()
                stage_start = time.monotonic()
                logits = forward(prompt, f"{case:02d}")
                row["diagnostic_head_and_archive_seconds"] = time.monotonic() - stage_start
                torch.cuda.synchronize()
                baseline = torch.cuda.memory_allocated()
                torch.cuda.reset_peak_memory_stats()
                stage_start = time.monotonic()
                with bounded(budget()):
                    device_weights = torch.softmax(logits.to(torch.float64), dim=-1)
                    if not bool(torch.isfinite(device_weights).all()) or not bool(
                        (device_weights > 0).all()
                    ):
                        raise ResourceRefusal("full-V positive probability range")
                    weights = device_weights.cpu().numpy()
                    gates = weights / (weights + 0.01)
                    row["log_grammar_mass"] = plan.forwards(plan.matrices(weights)[0])[0]
                row["diagnostic_softmax_transfer_base_seconds"] = time.monotonic() - stage_start
                for draw in range(4):
                    seed = int.from_bytes(
                        hashlib.sha256(f"52040:{case}:{draw}".encode()).digest()[:8], "little"
                    )
                    rng = np.random.default_rng(seed)
                    draw_row = {"draw": draw, "seed": seed}
                    row["draws"].append(draw_row)
                    with bounded(budget()):
                        stage_start = time.monotonic()
                        word = plan.sample(weights, rng)
                        anchor = int(rng.integers(32))
                        bits = rng.random(32) < gates[np.arange(32), word]
                        bits[anchor] = True
                        action = tuple((i, v) for i, v in enumerate(word) if bits[i])
                        draw_row.update({"word": word, "anchor": anchor, "action": action})
                        valid = language.accepts(word) and independent_accepts(language, word)
                        if not valid or word[anchor] != dict(action)[anchor]:
                            raise AssertionError(
                                "original IDs, termination or JSON validation failed"
                            )
                        text = b"".join(table[v] for v in word[: word.index(151645)]).decode("utf8")
                        draw_row["json"] = text
                        draw_row["diagnostic_sample_and_validation_seconds"] = (
                            time.monotonic() - stage_start
                        )
                        stage_start = time.monotonic()
                        expected = plan.action_statistics(weights, action)
                        draw_row["diagnostic_cpu_reference_seconds"] = (
                            time.monotonic() - stage_start
                        )
                        stage_start = time.monotonic()
                        actual = backend.action_statistics(device_weights, action)
                        draw_row["diagnostic_gpu_collapsed_seconds"] = (
                            time.monotonic() - stage_start
                        )
                        errors = compare(actual, expected)
                        if errors["log_probability"] > 1e-7:
                            raise AssertionError("real-head log probability tolerance")
                        stage_start = time.monotonic()
                        controls = auxiliary_statistics(plan, weights, word, anchor, action)
                        draw_row["diagnostic_auxiliary_controls_seconds"] = (
                            time.monotonic() - stage_start
                        )
                        draw_row.update(
                            {
                                "scores": {
                                    "collapsed": actual,
                                    **controls,
                                },
                                "cpu_reference": expected,
                                "errors": errors,
                                "status": "PASS",
                            }
                        )
                peak = (
                    torch.cuda.max_memory_allocated() - baseline + persistent_bytes + logits.nbytes
                )
                row["sampler_workspace_allocated_bytes"] = peak
                if peak > 2 * 1024**3:
                    raise ResourceRefusal("sampler workspace2GiB cap")
                row["status"] = "COMPLETE"
            except ResourceRefusal as error:
                row.update({"status": "RESOURCE_REFUSAL", "exception": repr(error)})
            except Exception as error:
                row.update({"status": "ERROR", "exception": repr(error)})
            finally:
                row["diagnostic_seconds"] = time.monotonic() - case_start
                row = serial(row)
                rows.write(json.dumps(row, allow_nan=False) + "\n")
                report["cases"].append(
                    {k: row[k] for k in ("case", "input_id", "status", "diagnostic_seconds")}
                )
                write_json(output / "progress.json", report)
                print(json.dumps(report["cases"][-1]), flush=True)
                # Avoid retaining a previous autograd graph/head between cases.
                if "device_weights" in locals():
                    del device_weights
                if "logits" in locals():
                    del logits
        complete = sum(r["status"] == "COMPLETE" for r in report["cases"])
        report.update(
            {
                "status": "RESOURCE_PASS" if complete >= 6 else "RESOURCE_GATE_NEGATIVE",
                "complete_cases": complete,
            }
        )
    except Exception as error:
        report.update(
            {
                "status": "RESOURCE_REFUSAL" if isinstance(error, ResourceRefusal) else "ERROR",
                "exception": repr(error),
            }
        )
        event("screen_exception", exception=repr(error))
        raise
    finally:
        report["diagnostic_seconds_including_load"] = time.monotonic() - started
        report["process_max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        write_json(output / "summary.json", report)
        events.close()
        rows.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    args = ap.parse_args()
    run(args.tokenizer_dir, args.output, args.protocol)
