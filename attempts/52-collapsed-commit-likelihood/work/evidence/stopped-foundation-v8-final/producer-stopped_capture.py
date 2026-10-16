"""V8 bounded stopped iterative RESOURCE capture. No labels or model updates."""

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import resource
import subprocess
import time
from pathlib import Path

import numpy as np

from .consumer_resource import (
    HERE,
    INPUT_SHA,
    WEIGHT_SHA,
    ResourceRefusal,
    bounded,
    serial,
    sha,
    write_json,
)
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_runtime import assemble, extent, release, terminal
from .prefix_torch import PrefixTorch
from .preflight_floating import compare
from .stopping import StoppedNumericJSON
from .tokenizer_audit import MODEL_REVISION, emissions, verify_files
from .two_stage import bf16_probabilities, json_text


def seed_for(case, replica, step):
    return int.from_bytes(
        hashlib.sha256(f"52080:{case}:{replica}:{step}:joint".encode()).digest()[:8], "little"
    )


def padded_score(score):
    return {
        "alpha": np.pad(np.asarray(score["alpha"]), (0, 32 - len(score["alpha"]))),
        "beta": float(score["beta"]),
        "anchor": np.pad(np.asarray(score["anchor"]), (0, 32 - len(score["anchor"]))),
    }


def run(folder, initial, protocol_path, output):
    import torch

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
        "old_root_heads": 8,
        "model_parameter_updates": 0,
        "cases": [],
    }
    stream = (output / "rows.jsonl").open("x", buffering=1)
    events = (output / "events.jsonl").open("x", buffering=1)

    def event(kind, **fields):
        events.write(json.dumps({"event": kind, "utc_seconds": time.time(), **fields}) + "\n")

    def budget():
        left = 1200 - (time.monotonic() - started)
        if left <= 0:
            raise ResourceRefusal("20min capture cap")
        return min(60, left)

    try:
        verify_files(folder)
        if (
            sha(folder / "model.safetensors") != WEIGHT_SHA
            or sha(HERE / "consumer-inputs-v4.json") != INPUT_SHA
        ):
            raise ValueError("model/input pin mismatch")
        for name, expected in protocol["source_sha256"].items():
            if sha(HERE / name) != expected:
                raise ValueError(f"source hash mismatch: {name}")
        if sha(initial / "manifest.json") != protocol["initial_manifest_sha256"]:
            raise ValueError("old initial head inventory mismatch")
        for name, entry in json.loads((initial / "manifest.json").read_text()).items():
            if sha(initial / name) != entry["sha256"]:
                raise ValueError(f"old packet mismatch: {name}")
        runtime = {
            p: importlib.metadata.version(p)
            for p in ("torch", "transformers", "tokenizers", "numpy", "safetensors")
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
                "model_revision": MODEL_REVISION,
                "source_sha256": protocol["source_sha256"],
                "old_root_producer": json.loads((initial / "provenance.json").read_text())[
                    "producer_commit"
                ],
                "labels_read_by_capture": False,
                "known_development_not_blinded": True,
            },
        )
        torch.set_num_threads(4)
        torch.manual_seed(52080)
        torch.cuda.manual_seed_all(52080)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        prompts = json.loads((initial / "prompt-ids.json").read_text())
        inputs = json.loads((HERE / "consumer-inputs-v4.json").read_text())["questions"]
        with bounded(budget()):
            plan = PrefixFloatPlan(StoppedNumericJSON(emissions(folder), 151645, 151643))
        if int(np.sum(plan.effects >= 0)) * 32 > 2000000:
            raise ResourceRefusal("symbolic arc cap")
        features = []
        for case in range(8):
            item = {"case": case}
            try:
                with bounded(budget()):
                    weights = bf16_probabilities(
                        np.load(initial / f"head-{case:02d}.npz")["logits_bf16"]
                    )
                    item.update({"status": "READY", "feature": plan.root_feature(weights)})
            except (ResourceRefusal, ValueError) as error:
                item.update({"status": "RESOURCE_REFUSAL", "exception": repr(error)})
            except Exception as error:
                item.update({"status": "ERROR", "exception": repr(error)})
            features.append(item)
            write_json(output / "root-features" / f"{case:02d}.json", item)
            print(
                json.dumps({"phase": "root-feature", "case": case, "status": item["status"]}),
                flush=True,
            )
        spec = importlib.util.spec_from_file_location(
            "a52_stopped_pinned", folder / "modeling_qwen3.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        config = module.A2DQwen3Config.from_pretrained(folder, local_files_only=True)
        config.use_cache = False
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
        torch.cuda.synchronize()
        baseline = torch.cuda.memory_allocated()
        torch.cuda.reset_peak_memory_stats()
        backend = PrefixTorch(plan)

        def head(case, fixed, positions, name):
            if report["new_forward_attempts"] >= 497:
                raise ResourceRefusal("497 new-forward cap")
            canvas = [fixed.get(i, 151669) for i in range(32)]
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
                    logits_to_keep=indices,
                ).logits
                torch.cuda.synchronize()
            report["new_forward_completions"] += 1
            event("forward_complete", name=name)
            if logits.dtype != torch.bfloat16:
                np.savez_compressed(
                    output / "heads" / f"{name}.npz",
                    unexpected_logits=logits.detach().cpu().numpy(),
                )
                raise ValueError("BF16 original head required")
            bits = logits[0].view(torch.uint16).cpu().numpy()
            np.savez_compressed(
                output / "heads" / f"{name}.npz", logits_bf16=bits, positions=np.asarray(positions)
            )
            if bits.shape != (len(positions), 151936):
                raise ValueError("projected original-V shape mismatch")
            return bits

        warmup = head(0, {}, tuple(range(32)), "warmup")
        report["warmup_matches_old_root_bits"] = bool(
            np.array_equal(warmup, np.load(initial / "head-00.npz")["logits_bf16"])
        )
        del warmup
        for case, item in enumerate(inputs):
            root_weights = bf16_probabilities(
                np.load(initial / f"head-{case:02d}.npz")["logits_bf16"]
            )
            for replica in range(2):
                began = time.monotonic()
                row = {"case": case, "replica": replica, "input_id": item["id"], "transitions": []}
                fixed = {}
                try:
                    if features[case]["status"] == "ERROR":
                        raise RuntimeError("root preparation correctness error")
                    if features[case]["status"] != "READY":
                        raise ResourceRefusal("root calibration refused")
                    feature = features[case]["feature"]["alpha"]
                    row["root_feature"] = feature
                    for step in range(32):
                        end = extent(32, fixed, plan.language.eos)
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
                            transition["head"] = "OLD_ROOT"
                            new_bits = None
                        else:
                            name = f"c{case:02d}-r{replica}-s{step:02d}"
                            transition["head"] = name
                            new_bits = head(case, fixed, positions, name)
                        with bounded(budget()):
                            probabilities = (
                                root_weights if step == 0 else bf16_probabilities(new_bits)
                            )
                            weights = assemble(probabilities, positions, fixed, end, 151936)
                            planner = PrefixPlanner(plan, weights, fixed, feature)
                            word, anchor, action, following = release(
                                plan, planner, np.random.default_rng(transition["seed"])
                            )
                            transition.update(
                                {"proposal_prefix": word, "anchor": anchor, "action": action}
                            )
                            if step == 0:
                                row["paired_one_shot_ids"] = word
                                row["paired_one_shot_json"] = json_text(plan.language, word)
                            expected = planner.statistics(action)
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
                        complete = terminal(plan.language, 32, fixed)
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
                                    "json": json_text(plan.language, complete),
                                    "fixed_terminal": sorted(fixed.items()),
                                    "transition_count": step + 1,
                                }
                            )
                            break
                    else:
                        raise AssertionError("32-transition progress bound failed")
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
                if complete_cases >= 6 and errors == 0
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
        report["diagnostic_seconds_including_setup"] = time.monotonic() - started
        report["process_max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        write_json(output / "summary.json", report)
        stream.close()
        events.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer-dir", type=Path, required=True)
    ap.add_argument("--initial-packet", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.tokenizer_dir, args.initial_packet, args.protocol, args.output)
