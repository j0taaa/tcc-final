"""Bounded, input-only Tiny-A2D/Mosaic masked-loop resource/variance screen."""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import platform
import resource
import signal
import subprocess
import time
import traceback
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from masked_adapter import LastProposal, bit_digest, load_masked
from masked_controls import SparseEdges
from native_adapter import local_rng, render, restore_rng, rng_digest, rng_state
from reference import normalized

HERE = Path(__file__).resolve().parent
MODEL = "dllm-hub/Qwen3-0.6B-diffusion-mdlm-v0.1"


class Refusal(RuntimeError):
    pass


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


@contextlib.contextmanager
def bounded(seconds):
    def timeout(signum, frame):
        raise Refusal("Frozen operation/whole-run time guard exceeded")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@contextlib.contextmanager
def measured(target, name):
    torch.cuda.synchronize()
    wall, cpu = time.perf_counter(), time.process_time()
    try:
        yield
    finally:
        torch.cuda.synchronize()
        target[name] = {
            "wall_seconds": time.perf_counter() - wall,
            "cpu_seconds": time.process_time() - cpu,
        }


def messages(item):
    source = HERE / "jevbench_source_v6/jevbench/adapters/openai_compat.py"
    tree = ast.parse(source.read_text())
    system = next(
        n.value
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "_SYSTEM" for t in n.targets)
    )
    cls = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "OpenAICompatAdapter"
    )
    method = next(
        n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "build_request"
    )
    namespace = {"json": json, "_SYSTEM": ast.literal_eval(system)}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), namespace)
    return namespace["build_request"](SimpleNamespace(model=MODEL), SimpleNamespace(**item))[
        "messages"
    ]


def message_checks():
    for kind, labels, criteria, expected in [
        (
            "choice",
            ["a", "b"],
            {"a": "first", "b": "second"},
            "Options:\n- a: first\n- b: second\n\n"
            'Output probabilities over exactly these keys: ["a", "b"].',
        ),
        (
            "noul",
            ["no", "yes"],
            {"false": "absent", "true": "present"},
            "Options:\n- no: absent\n- yes: present\n\n"
            'Output probabilities over exactly these keys: ["no", "yes"].',
        ),
        (
            "score",
            ["0", "1"],
            ["low", "high"],
            "Levels:\n0: low\n1: high\n\nRate the state. "
            'Output probabilities over the level indices: ["0", "1"].',
        ),
    ]:
        result = messages(
            {
                "state": "example",
                "labels": labels,
                "question": {"type": kind, "instructions": "Decide.", "criteria": criteria},
            }
        )
        assert result[1] == {"role": "user", "content": "State:\nexample\n\nDecide.\n\n" + expected}
        assert result[0]["role"] == "system" and "calibration engine" in result[0]["content"]


def verify(folder):
    protocol = json.loads((HERE / "runner-source-v8.json").read_text())
    for name, digest in protocol["source_sha256"].items():
        assert sha(HERE / name) == digest, name
    runtime = {
        p: importlib.metadata.version(p)
        for p in ("torch", "transformers", "numpy", "automata-lib", "safetensors")
    }
    assert runtime == protocol["runtime"], runtime
    manifest = json.loads((HERE / "model_source_v7/manifest.json").read_text())
    for name, digest in manifest["files_sha256"].items():
        assert sha(folder / name) == digest, name
    assert sha(folder / manifest["weights"]["file"]) == manifest["weights"]["sha256"]
    for name in ("masked_source_v6", "jevbench_source_v6"):
        manifest = json.loads((HERE / name / "manifest.json").read_text())
        for row in manifest["files"]:
            assert sha(HERE / name / row["file"]) == row["sha256"]
    return protocol, runtime


def preflight(folder, output):
    from transformers import AutoTokenizer

    output.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "RUNNING",
        "new_neural_forwards": 0,
        "model_instance_loaded": False,
        "rows": [],
    }
    try:
        protocol, runtime = verify(folder)
        message_checks()
        tokenizer = AutoTokenizer.from_pretrained(
            folder, local_files_only=True, trust_remote_code=False
        )
        assert len(tokenizer) == 151670
        assert [
            tokenizer.convert_tokens_to_ids(t) for t in ("<|im_end|>", "<|endoftext|>", "<|mask|>")
        ] == [151645, 151643, 151669]
        inputs = json.loads((HERE / "inputs-v6.json").read_text())["selected"]
        for row in inputs:
            prompt = messages(row["input"])
            ids = tokenizer.apply_chat_template(
                prompt, tokenize=True, add_generation_prompt=True, enable_thinking=False
            )
            if hasattr(ids, "keys"):
                ids = ids["input_ids"]
            status = "READY" if len(ids) <= 1024 and 151669 not in ids else "RESOURCE_REFUSAL"
            report["rows"].append(
                {
                    "input_id": row["input"]["id"],
                    "input_sha256": row["input_sha256"],
                    "status": status,
                    "messages": prompt,
                    "prompt_ids": ids,
                    "prompt_tokens": len(ids),
                }
            )
        assert len(report["rows"]) == 8
        report.update(
            status="PREFLIGHT_PASS",
            runtime=runtime,
            source_sha256=protocol["source_sha256"],
            ready=sum(r["status"] == "READY" for r in report["rows"]),
        )
    except Exception as error:
        report.update(status="ERROR", error=repr(error))
        (output / "traceback.txt").write_text(traceback.format_exc())
        raise
    finally:
        write(output / "summary.json", report)
    print(json.dumps({k: v for k, v in report.items() if k not in ("rows", "source_sha256")}))


def schema(labels):
    values = {
        "type": "object",
        "properties": {s: {"type": "number", "x-prob": True} for s in labels},
        "required": labels,
    }
    return {
        "type": "object",
        "properties": {"probabilities": values},
        "required": ["probabilities"],
    }


class ForwardRecorder:
    def __init__(self, model, report, output, case, event, budget):
        self.model, self.report, self.output, self.case = model, report, output, case
        self.event, self.budget, self.trace = event, budget, []

    def __call__(self, ids):
        if self.report["forward_attempts"] >= 129:
            raise Refusal("129 total attempted-forward cap")
        ordinal = self.report["forward_attempts"]
        self.report["forward_attempts"] += 1
        self.event("forward_attempt", case=self.case, ordinal=ordinal)
        before = rng_state()
        timing = {}
        with bounded(self.budget()), measured(timing, "model_forward"):
            result = self.model(ids, use_cache=False)
        self.report["forward_completions"] += 1
        assert result.logits.shape == (1, ids.shape[1], 151936)
        assert result.logits.dtype == torch.bfloat16
        self.event("forward_complete", case=self.case, ordinal=ordinal)
        after = rng_state()
        name = f"head-{ordinal:03d}"
        with measured(timing, "packet_io"):
            np.savez_compressed(
                self.output / (name + ".npz"),
                input_ids=ids.cpu().numpy(),
                response_logits_bf16=result.logits[0, -64:]
                .detach()
                .contiguous()
                .view(torch.uint16)
                .cpu()
                .numpy(),
            )
            torch.save({"before": before, "after": after}, self.output / (name + "-rng.pt"))
        self.trace.append(
            {
                "ordinal": ordinal,
                "input_sha256": bit_digest(ids),
                "response_head_sha256": bit_digest(result.logits[:, -64:]),
                "head_packet": name + ".npz",
                "rng_packet": name + "-rng.pt",
                "rng_before": rng_digest(before),
                "rng_after": rng_digest(after),
                "timing": timing,
            }
        )
        return result


def capture(folder, output, preflight_path):
    from transformers import AutoTokenizer

    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    previous_rng = rng_state()
    threads, precision = torch.get_num_threads(), torch.get_float32_matmul_precision()
    tf32 = torch.backends.cuda.matmul.allow_tf32, torch.backends.cudnn.allow_tf32
    report = {
        "status": "RUNNING",
        "forward_attempts": 0,
        "forward_completions": 0,
        "rows": [],
        "updates": 0,
        "quality_labels_evaluated": False,
        "competitive_timing": False,
        "original_26b_consumer_reproduced": False,
    }
    events = (output / "events.jsonl").open("x", buffering=1)

    def event(kind, **fields):
        events.write(json.dumps({"event": kind, "utc_seconds": time.time(), **fields}) + "\n")

    def budget():
        remaining = 1800 - (time.monotonic() - started)
        if remaining <= 0:
            raise Refusal("30-minute whole-screen guard exceeded")
        return min(120, remaining)

    try:
        torch.set_num_threads(4)
        torch.set_float32_matmul_precision("highest")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        protocol, runtime = verify(folder)
        pre = json.loads(preflight_path.read_text())
        assert (
            pre["status"] == "PREFLIGHT_PASS" and pre["source_sha256"] == protocol["source_sha256"]
        )
        report.update(
            runtime=runtime,
            python=platform.python_version(),
            source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
            preflight_sha256=sha(preflight_path),
        )
        write(output / "protocol.json", protocol)
        inputs = json.loads((HERE / "inputs-v6.json").read_text())["selected"]
        tokenizer = AutoTokenizer.from_pretrained(
            folder, local_files_only=True, trust_remote_code=False
        )
        spec = importlib.util.spec_from_file_location(
            "a65_reviewed_pinned_qwen", HERE / "model_source_v7/modeling_qwen3.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        config = module.A2DQwen3Config.from_pretrained(folder, local_files_only=True)
        config.use_cache = False
        with bounded(min(1800 - (time.monotonic() - started), 600)), measured(report, "model_load"):
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
        loaded_baseline = torch.cuda.memory_allocated()
        report["loaded_model_cuda_bytes"] = loaded_baseline
        native = load_masked()
        compiler = native["matcher"].ConstraintCompiler(
            tokenizer,
            eos_token="<|endoftext|>",
            eot_token="<|im_end|>",
            device="cuda",
            matmul_dtype=torch.float64,
            cache_size=1,
            compile_workers=0,
        )
        with torch.no_grad():
            warmup = ForwardRecorder(model, report, output, "warmup", event, budget)
            ready = [r for r in pre["rows"] if r["status"] == "READY"]
            if not ready:
                raise Refusal("No input within the frozen prompt guard")
            first_ids = ready[0]["prompt_ids"]
            warmup(torch.tensor([first_ids + [151669] * 64], device="cuda"))
            report["warmup"] = warmup.trace
        for index, (selected, prompt_info) in enumerate(zip(inputs, pre["rows"], strict=True)):
            row = {
                "case": index,
                "input_id": selected["input"]["id"],
                "status": "RUNNING",
                "original_complete": False,
                "ideal_n7_removed_risk": None,
                "diagnostic_timing": {},
            }
            recorder = None
            hook = control = compiled = matcher = result = None
            try:
                budget()
                assert prompt_info["input_id"] == row["input_id"]
                if prompt_info["status"] != "READY":
                    raise Refusal("Frozen prompt1024-token/mask guard")
                labels = selected["input"]["labels"]
                torch.cuda.reset_peak_memory_stats()
                with bounded(budget()), measured(row["diagnostic_timing"], "cold_compile"):
                    compiled = compiler.compile_json_schema(schema(labels))
                row["compiler"] = {
                    "states": compiled.num_states,
                    "edges": compiled.num_edges,
                    "vocab": compiled.vocab_size,
                }
                matcher = native["matcher"].ConstraintMatcher(compiled, 64)
                hook = LastProposal(native, tokenizer, labels, 151645, 151643, 16, 4)
                recorder = ForwardRecorder(model, report, output, index, event, budget)
                ids = torch.tensor([prompt_info["prompt_ids"]], device="cuda")
                with (
                    bounded(budget()),
                    local_rng(65060 + index),
                    hook.attach(matcher),
                    torch.no_grad(),
                    measured(row["diagnostic_timing"], "original_loop_including_capture_and_io"),
                ):
                    result = native["loop"].generate(
                        recorder,
                        ids,
                        151669,
                        steps=16,
                        gen_length=64,
                        block_length=64,
                        temperature=0.0,
                        cfg_scale=0.0,
                        remasking="low_confidence",
                        vocab_size=151670,
                        matcher=matcher,
                        commit_by="constrained",
                    )
                original = tuple(result[0, ids.shape[1] :].tolist())
                assert original == hook.first and not (result == 151669).any()
                assert all(
                    t == -1 or t == original[p]
                    for p, t in enumerate(hook.snapshot.tokens[0].tolist())
                )
                raw = hook.snapshot.observe(original)
                row.update(
                    original_ids=original,
                    original_raw=None if raw is None else list(map(str, raw)),
                    original_complete=raw is not None,
                    captured_raw_head_sha256=bit_digest(hook.raw_logits),
                    captured_sampler_scores_sha256=bit_digest(hook.snapshot.scores),
                    final_free_positions=torch.nonzero(hook.snapshot.tokens[0] < 0)
                    .flatten()
                    .tolist(),
                )
                with measured(row["diagnostic_timing"], "terminal_packet_io"):
                    np.savez_compressed(
                        output / f"terminal-{index:02d}.npz",
                        scores_float32=hook.snapshot.scores.cpu().numpy(),
                        tokens=hook.snapshot.tokens.cpu().numpy(),
                        original_ids=np.asarray(original),
                    )
                    torch.save(
                        {"before": hook.before_rng, "after": hook.after_rng},
                        output / f"terminal-{index:02d}-rng.pt",
                    )
                parent = rng_state()
                try:
                    with (
                        bounded(budget()),
                        measured(row["diagnostic_timing"], "literal_terminal_replay"),
                    ):
                        restore_rng(hook.before_rng)
                        assert hook.snapshot.draw() == original
                        assert rng_digest() == rng_digest(hook.after_rng)
                finally:
                    restore_rng(parent)
                row["literal_terminal_replay"] = True
                readouts = []
                for n in (0, 1, 7):
                    with bounded(budget()), measured(row["diagnostic_timing"], f"readout_N{n}"):
                        readouts.append(
                            hook.snapshot.readout(original, n, 650600 + 100 * index + n)
                        )
                row["readouts"] = readouts
                with (
                    bounded(budget()),
                    measured(row["diagnostic_timing"], "shared_sparse_preparation"),
                ):
                    control = SparseEdges(compiled, hook.snapshot.tokenizer)
                with (
                    bounded(budget()),
                    measured(row["diagnostic_timing"], "classical_grid_DP_and_word_MAP"),
                ):
                    stats = control.evaluate(hook.snapshot)
                row["control"] = {k: v for k, v in stats.items() if k not in ("by_sum", "map_raw")}
                row["control"]["map_raw"] = (
                    None if stats["map_raw"] is None else list(map(str, stats["map_raw"]))
                )
                if stats["mean"] is not None:
                    row["control"]["rendered_normalized_float_mean"] = render(
                        normalized(stats["mean"]), tuple(labels)
                    )
                    alpha, variance = float(stats["alpha"]), float(stats["variance"])
                    assert math.isfinite(alpha) and -1e-9 <= alpha <= 1 + 1e-9 and variance >= -1e-9
                    adjusted = max(0.0, min(alpha, 1.0))
                    factor = sum((1 - adjusted) ** j for j in range(8)) / 8
                    row.update(
                        alpha_for_binomial_formula=adjusted,
                        alpha_adjustment=adjusted - alpha,
                        ideal_n7_removed_risk=variance * (1 - factor),
                    )
                peak = torch.cuda.max_memory_allocated()
                row.update(
                    peak_cuda_bytes=peak,
                    sampler_incremental_cuda_bytes=max(0, peak - loaded_baseline),
                )
                if peak > 10 * 1024**3 or peak - loaded_baseline > 2 * 1024**3:
                    raise Refusal("Frozen total/incremental GPU memory guard")
                row["status"] = "COMPLETE" if raw is not None else "INELIGIBLE"
            except Exception as error:
                refusal = isinstance(error, Refusal) or "guard" in str(error).lower()
                row.update(status="RESOURCE_REFUSAL" if refusal else "ERROR", error=repr(error))
                (output / f"case-{index:02d}-traceback.txt").write_text(traceback.format_exc())
            finally:
                if recorder is not None:
                    row["forward_trace"] = recorder.trace
                report["rows"].append(row)
                with (output / "records.jsonl").open("a") as stream:
                    stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                write(output / "progress.json", report)
                print(
                    json.dumps(
                        {
                            k: row[k]
                            for k in (
                                "case",
                                "input_id",
                                "status",
                                "original_complete",
                                "ideal_n7_removed_risk",
                            )
                        }
                    ),
                    flush=True,
                )
            # Release the previous dense head and compiled schema before the next case.
            hook = control = compiled = matcher = result = None
        compiler.close()
        valid = sum(r["original_complete"] for r in report["rows"])
        magnitude = sum(
            r["status"] == "COMPLETE"
            and r["ideal_n7_removed_risk"] is not None
            and r["ideal_n7_removed_risk"] >= 0.005
            for r in report["rows"]
        )
        assert len(report["rows"]) == 8 and report["forward_attempts"] <= 129
        report.update(
            status="NECESSITY_PASS_ONLY"
            if valid >= 6 and magnitude >= 4
            else "NECESSITY_GATE_NEGATIVE",
            complete_originals=valid,
            sufficient_ideal_variance_cases=magnitude,
            quality_campaign_triggered=False,
        )
    except Exception as error:
        report.update(
            status="RESOURCE_REFUSAL" if isinstance(error, Refusal) else "ERROR", error=repr(error)
        )
        (output / "traceback.txt").write_text(traceback.format_exc())
        raise
    finally:
        restore_rng(previous_rng)
        torch.set_num_threads(threads)
        torch.set_float32_matmul_precision(precision)
        torch.backends.cuda.matmul.allow_tf32, torch.backends.cudnn.allow_tf32 = tf32
        report.update(
            caller_rng_restored=rng_digest() == rng_digest(previous_rng),
            diagnostic_total_seconds=time.monotonic() - started,
            process_max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        )
        write(output / "summary.json", report)
        events.close()
    print(json.dumps({k: v for k, v in report.items() if k not in ("rows", "warmup")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--preflight", type=Path)
    args = parser.parse_args()
    if args.preflight_only:
        preflight(args.model_dir, args.output)
    else:
        assert args.preflight is not None
        capture(args.model_dir, args.output, args.preflight)
