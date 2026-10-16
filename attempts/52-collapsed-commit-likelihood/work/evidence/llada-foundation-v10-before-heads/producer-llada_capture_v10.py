"""V10 bounded LLaDA suffix RESOURCE capture. No labels or model updates."""

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import resource
import subprocess
import time
from pathlib import Path

import numpy as np

from .capture_occupancy_v10 import CaptureOccupancy
from .consumer_resource import (
    HERE,
    INPUT_SHA,
    ResourceRefusal,
    bounded,
    serial,
    sha,
    write_json,
)
from .llada_suffix_v10 import PREFIX, NumericSuffixJSON, full_text, terminal_prefix
from .llada_tokenizer_v10 import EOS, FILES, MASK, REVISION, VOCABULARY, emissions, verify_files
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_runtime import assemble, extent, release
from .prefix_torch import PrefixTorch
from .preflight_floating import compare
from .two_stage import bf16_probabilities

WIDTH = 64
INSTRUCTION = (
    "Solve the problem and return exactly one JSON object with the key answer "
    "and its numeric value. No explanation, units, or markdown in the output. "
    "The JSON prefix is already supplied; continue it without repeating it.\nProblem:\n"
)


def seed_for(case, replica, step):
    return int.from_bytes(
        hashlib.sha256(f"52100:{case}:{replica}:{step}:joint".encode()).digest()[:8], "little"
    )


def padded_score(score):
    return {
        "alpha": np.pad(np.asarray(score["alpha"]), (0, WIDTH - len(score["alpha"]))),
        "beta": float(score["beta"]),
        "anchor": np.pad(np.asarray(score["anchor"]), (0, WIDTH - len(score["anchor"]))),
    }


def run(folder, protocol_path, output):
    output.mkdir(parents=True, exist_ok=False)
    (output / "heads").mkdir()
    (output / "root-features").mkdir()
    protocol = json.loads(protocol_path.read_text())
    started = time.monotonic()
    report = {
        "status": "RUNNING",
        "scope": "KNOWN_STOPPED_RESOURCE_SIGNAL_ONLY",
        "new_forward_attempts": 0,
        "new_forward_completions": 0,
        "old_root_heads": 0,
        "new_root_heads": 0,
        "declared_root_heads": 8,
        "model_parameter_updates": 0,
        "cases": [],
    }
    stream = (output / "rows.jsonl").open("x", buffering=1)
    events = (output / "events.jsonl").open("x", buffering=1)
    occupancy = CaptureOccupancy(output / "gpu-occupancy.jsonl")

    def event(kind, **fields):
        events.write(json.dumps({"event": kind, "utc_seconds": time.time(), **fields}) + "\n")

    def budget(maximum=60):
        left = 1800 - (time.monotonic() - started)
        if left <= 0:
            raise ResourceRefusal("30min capture cap")
        return min(maximum, left)

    try:
        occupancy.start()
        import torch
        from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

        with bounded(budget(300)):
            source_files = verify_files(folder, weights=True)
        if sha(HERE / "consumer-inputs-v4.json") != INPUT_SHA:
            raise ValueError("input pin mismatch")
        for name, expected in protocol["source_sha256"].items():
            if sha(HERE / name) != expected:
                raise ValueError(f"source hash mismatch: {name}")
        runtime = {
            p: importlib.metadata.version(p)
            for p in (
                "torch",
                "transformers",
                "tokenizers",
                "numpy",
                "safetensors",
                "bitsandbytes",
                "accelerate",
            )
        }
        if runtime != protocol["runtime"]:
            raise ValueError("runtime mismatch")
        write_json(output / "protocol.json", protocol)
        write_json(
            output / "provenance.json",
            {
                "producer_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "runtime": runtime,
                "gpu": torch.cuda.get_device_name(),
                "cuda": torch.version.cuda,
                "model_revision": REVISION,
                "source_sha256": protocol["source_sha256"],
                "model_source_files": source_files,
                "labels_read_by_capture": False,
                "known_development_not_blinded": True,
            },
        )
        torch.set_num_threads(4)
        torch.manual_seed(52100)
        torch.cuda.manual_seed_all(52100)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        inputs = json.loads((HERE / "consumer-inputs-v4.json").read_text())["questions"]
        tokenizer = AutoTokenizer.from_pretrained(
            folder, local_files_only=True, trust_remote_code=False
        )
        prefix_ids = tokenizer.encode(PREFIX.decode(), add_special_tokens=False)
        if tokenizer.decode(prefix_ids, skip_special_tokens=False) != PREFIX.decode():
            raise ValueError("supplied prefix original IDs do not decode literally")
        prompts = [
            tokenizer.apply_chat_template(
                [{"role": "user", "content": INSTRUCTION + item["question"]}],
                add_generation_prompt=True,
                tokenize=True,
            )
            + prefix_ids
            for item in inputs
        ]
        write_json(output / "prompt-ids.json", prompts)
        write_json(output / "supplied-prefix.json", {"bytes": PREFIX.hex(), "ids": prefix_ids})
        if prompts != protocol["prompt_ids"] or prefix_ids != protocol["supplied_prefix_ids"]:
            raise ValueError("actual official prompt tokenization differs from the frozen inputs")
        if any(len(prompt) + WIDTH > 4096 for prompt in prompts):
            raise ResourceRefusal("declared native model context exceeded without truncation")
        with bounded(budget()):
            plan = PrefixFloatPlan(NumericSuffixJSON(emissions(folder), EOS, EOS))
        if int(np.sum(plan.effects >= 0)) * WIDTH > 2000000:
            raise ResourceRefusal("symbolic arc cap")
        occupancy.check()
        loading = time.monotonic()
        with bounded(budget(300)):
            model = AutoModel.from_pretrained(
                folder,
                local_files_only=True,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,
                device_map={"": 0},
                quantization_config=BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                ),
            ).eval()
        report["model_setup_diagnostic_seconds"] = time.monotonic() - loading
        model.requires_grad_(False)
        for kind, cls, filename in (
            ("model", type(model), "modeling_llada.py"),
            ("config", type(model.config), "configuration_llada.py"),
        ):
            actual_source = Path(inspect.getfile(cls))
            if sha(actual_source) != FILES[filename]:
                raise ValueError(f"actual imported {kind} source differs from pinned checkpoint")
            report[f"imported_{kind}_source_sha256"] = sha(actual_source)
        if model.config.vocab_size != VOCABULARY:
            raise ValueError("actual loaded head domain mismatch")
        report["trainable_model_parameters"] = sum(
            p.numel() for p in model.parameters() if p.requires_grad
        )
        torch.cuda.synchronize()
        occupancy.check()
        baseline = torch.cuda.memory_allocated()
        report["model_allocated_bytes"] = baseline
        report["setup_gpu_peak_allocated_bytes"] = torch.cuda.max_memory_allocated()
        report["setup_gpu_peak_reserved_bytes"] = torch.cuda.max_memory_reserved()
        torch.cuda.reset_peak_memory_stats()
        backend = PrefixTorch(plan)

        def head(case, fixed, positions, name):
            occupancy.check()
            if report["new_forward_attempts"] >= 1017:
                raise ResourceRefusal("1017 new-forward cap")
            canvas = [fixed.get(i, MASK) for i in range(WIDTH)]
            context = {
                "case": case,
                "prompt": prompts[case],
                "canvas": canvas,
                "fixed": sorted(fixed.items()),
                "queried_positions": positions,
            }
            write_json(output / "heads" / f"{name}.json", context)
            ids = torch.tensor([prompts[case] + canvas], device="cuda")
            indices = torch.tensor([len(prompts[case]) + i for i in positions], device="cuda")
            report["new_forward_attempts"] += 1
            event("forward_attempt", name=name, ordinal=report["new_forward_attempts"])
            with torch.no_grad(), bounded(budget()):
                logits = model(
                    ids,
                    attention_mask=torch.ones_like(ids),
                    use_cache=False,
                ).logits
                torch.cuda.synchronize()
            report["new_forward_completions"] += 1
            if name.startswith("root-"):
                report["new_root_heads"] += 1
            shape = list(logits.shape)
            event("forward_complete", name=name, full_native_output_shape=shape)
            if logits.dtype != torch.bfloat16:
                np.savez_compressed(
                    output / "heads" / f"{name}.npz",
                    unexpected_logits=logits.detach().cpu().numpy(),
                )
                raise ValueError("BF16 original head required")
            if shape != [1, len(prompts[case]) + WIDTH, VOCABULARY]:
                np.savez_compressed(
                    output / "heads" / f"{name}.npz",
                    unexpected_logits_bf16=logits.view(torch.uint16).cpu().numpy(),
                    full_native_output_shape=np.asarray(shape),
                )
                raise ValueError("full native projection shape mismatch")
            bits = logits[0].index_select(0, indices).view(torch.uint16).cpu().numpy()
            np.savez_compressed(
                output / "heads" / f"{name}.npz",
                logits_bf16=bits,
                positions=np.asarray(positions),
                full_native_output_shape=np.asarray(shape),
            )
            if bits.shape != (len(positions), VOCABULARY):
                raise ValueError("gathered original-V shape mismatch")
            occupancy.check()
            return bits

        warmup = head(0, {}, tuple(range(WIDTH)), "warmup")
        features = []
        for case in range(8):
            item = {"case": case}
            try:
                bits = head(case, {}, tuple(range(WIDTH)), f"root-{case:02d}")
                if case == 0:
                    report["warmup_matches_new_root_bits"] = bool(np.array_equal(warmup, bits))
                with bounded(budget()):
                    weights = bf16_probabilities(bits)
                    item.update({"status": "READY", "feature": plan.root_feature(weights)})
                occupancy.check()
                del weights, bits
            except (ResourceRefusal, ValueError) as error:
                item.update({"status": "RESOURCE_REFUSAL", "exception": repr(error)})
            except Exception as error:
                item.update({"status": "ERROR", "exception": repr(error)})
            features.append(item)
            write_json(output / "root-features" / f"{case:02d}.json", item)
            print(
                json.dumps({"phase": "new-root-feature", "case": case, "status": item["status"]}),
                flush=True,
            )
        del warmup
        for case, item in enumerate(inputs):
            with bounded(budget()):
                root_weights = (
                    bf16_probabilities(
                        np.load(output / "heads" / f"root-{case:02d}.npz")["logits_bf16"]
                    )
                    if features[case]["status"] == "READY"
                    else None
                )
            for replica in range(2):
                began = time.monotonic()
                row = {"case": case, "replica": replica, "input_id": item["id"], "transitions": []}
                fixed = {}
                try:
                    occupancy.check()
                    if features[case]["status"] == "ERROR":
                        raise RuntimeError("root preparation correctness error")
                    if features[case]["status"] != "READY":
                        raise ResourceRefusal("root calibration refused")
                    feature = features[case]["feature"]["alpha"]
                    row["root_feature"] = feature
                    for step in range(WIDTH):
                        end = extent(WIDTH, fixed, plan.language.eos)
                        positions = tuple(i for i in range(end) if i not in fixed)
                        transition = {
                            "step": step,
                            "fixed_before": sorted(fixed.items()),
                            "prefix_extent": end,
                            "queried_positions": positions,
                            "seed": seed_for(case, replica, step),
                        }
                        row["transitions"].append(transition)
                        if step == 0:
                            transition["head"] = f"root-{case:02d}"
                            new_bits = None
                        else:
                            name = f"c{case:02d}-r{replica}-s{step:02d}"
                            transition["head"] = name
                            new_bits = head(case, fixed, positions, name)
                        with bounded(budget()):
                            probabilities = (
                                root_weights if step == 0 else bf16_probabilities(new_bits)
                            )
                            weights = assemble(probabilities, positions, fixed, end, VOCABULARY)
                            planner = PrefixPlanner(plan, weights, fixed, feature)
                            word, anchor, action, following = release(
                                plan, planner, np.random.default_rng(transition["seed"])
                            )
                            transition.update(
                                {"proposal_prefix": word, "anchor": anchor, "action": action}
                            )
                            if step == 0:
                                row["paired_one_shot_ids"] = word
                                row["paired_one_shot_json"] = full_text(plan.language, word)
                            expected = planner.statistics(action)
                            occupancy.check()
                            actual = backend.statistics(
                                torch.as_tensor(weights, device="cuda"), fixed, feature, action
                            )
                            errors = compare(actual, expected)
                            if errors["log_probability"] > 1e-7:
                                raise AssertionError("prefix log probability tolerance")
                            controls = planner.controls(word, anchor, action, expected)
                            transition.update(
                                {
                                    "score_errors": errors,
                                    "log_probability": actual["log_probability"],
                                    "scores": {
                                        "collapsed": padded_score(actual),
                                        **{name: padded_score(s) for name, s in controls.items()},
                                    },
                                    "fixed_after": sorted(following.items()),
                                    "status": "PASS",
                                }
                            )
                            payload = sum(
                                a.nbytes
                                for a in (
                                    root_weights,
                                    weights,
                                    planner.logc,
                                    planner.gates,
                                    planner.u,
                                    planner.da,
                                    planner.db,
                                )
                            )
                            peak = torch.cuda.max_memory_allocated() - baseline
                            report["tracked_sampler_payload_bytes"] = max(
                                report.get("tracked_sampler_payload_bytes", 0), payload + peak
                            )
                            report["gpu_sampler_peak_allocated_bytes"] = peak
                            if peak > 2 * 1024**3 or payload + peak > 2 * 1024**3:
                                raise ResourceRefusal("2GiB tracked sampler payload cap")
                        fixed = following
                        occupancy.check()
                        complete = terminal_prefix(plan.language, WIDTH, fixed)
                        if complete is not None:
                            if any(
                                i >= len(complete) or complete[i] != v for i, v in fixed.items()
                            ):
                                raise AssertionError(
                                    "a committed original ID vanished from terminal output"
                                )
                            row.update(
                                {
                                    "status": "COMPLETE",
                                    "terminal_ids": complete,
                                    "json": full_text(plan.language, complete),
                                    "fixed_terminal": sorted(fixed.items()),
                                    "transition_count": step + 1,
                                }
                            )
                            break
                    else:
                        raise AssertionError("64-transition progress bound failed")
                except Exception as error:
                    row.update(
                        {
                            "status": "RESOURCE_REFUSAL"
                            if isinstance(error, ResourceRefusal)
                            else "ERROR",
                            "exception": repr(error),
                        }
                    )
                finally:
                    row["diagnostic_seconds"] = time.monotonic() - began
                    stream.write(json.dumps(serial(row), allow_nan=False) + "\n")
                    report["cases"].append(
                        {
                            k: row[k]
                            for k in ("case", "replica", "input_id", "status", "diagnostic_seconds")
                        }
                    )
                    write_json(output / "progress.json", report)
                    print(json.dumps(report["cases"][-1]), flush=True)
        complete_cases = sum(
            all(
                any(
                    r["case"] == case and r["replica"] == replica and r["status"] == "COMPLETE"
                    for r in report["cases"]
                )
                for replica in range(2)
            )
            for case in range(8)
        )
        errors = sum(r["status"] == "ERROR" for r in report["cases"])
        report.update(
            {
                "complete_cases": complete_cases,
                "correctness_errors": errors,
                "status": "RESOURCE_PASS_AWAIT_KNOWN_LABEL_SIGNAL"
                if complete_cases >= 6
                and errors == 0
                and occupancy.report()["whole_capture_isolation_satisfied"]
                and time.monotonic() - started < 1800
                else "RESOURCE_GATE_NEGATIVE",
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
        report["process_max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        try:
            occupancy.close()
        except Exception as error:
            report.update({"status": "RESOURCE_REFUSAL", "observer_close_exception": repr(error)})
        report.update(occupancy.report())
        if "torch" in locals() and torch.cuda.is_initialized():
            report["whole_process_cuda_peak_allocated_bytes"] = max(
                report.get("setup_gpu_peak_allocated_bytes", 0), torch.cuda.max_memory_allocated()
            )
            report["whole_process_cuda_peak_reserved_bytes"] = max(
                report.get("setup_gpu_peak_reserved_bytes", 0), torch.cuda.max_memory_reserved()
            )
        if report["status"] == "RESOURCE_PASS_AWAIT_KNOWN_LABEL_SIGNAL" and (
            not report["whole_capture_isolation_satisfied"] or time.monotonic() - started >= 1800
        ):
            report["status"] = "RESOURCE_GATE_NEGATIVE"
        present = {(r["case"], r["replica"]) for r in report["cases"]}
        for case in range(8):
            for replica in range(2):
                if (case, replica) not in present:
                    row = {
                        "case": case,
                        "replica": replica,
                        "status": "NOT_RUN_CAPTURE_STOPPED",
                        "reason": report["status"],
                        "transitions": [],
                    }
                    stream.write(json.dumps(row) + "\n")
                    report["cases"].append(row)
        stream.flush()
        events.flush()
        report["diagnostic_seconds_including_setup"] = time.monotonic() - started
        write_json(output / "summary.json", report)
        stream.close()
        events.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.model_dir, args.protocol, args.output)
