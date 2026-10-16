"""V5 bounded actual-return DEVELOPMENT capture; NEVER reads answer labels."""

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

from .compact_planner import CompactPlanner, score_vector
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
from .floating import FloatPlan
from .numeric_json import NumericJSON
from .preflight_floating import compare
from .tokenizer_audit import MODEL_REVISION, emissions, verify_files
from .two_stage import bf16_probabilities, clamped_weights, json_text


def seed_for(case, phase, draw, purpose):
    return int.from_bytes(
        hashlib.sha256(f"52050:{case}:{phase}:{draw}:{purpose}".encode()).digest()[:8], "little"
    )


def run(folder, initial, protocol_path, output):
    import torch

    output.mkdir(parents=True, exist_ok=False)
    heads = output / "heads"
    heads.mkdir()
    protocol = json.loads(protocol_path.read_text())
    started = time.monotonic()
    report = {
        "status": "RUNNING",
        "scope": "KNOWN_DEVELOPMENT_VARIANCE_NECESSITY_ONLY",
        "new_forward_attempts": 0,
        "new_forward_completions": 0,
        "cache_hits": 0,
        "complete_first_actions": 0,
        "parameter_updates": 0,
        "records": 0,
        "complete": 0,
        "errors": 0,
    }
    stream = (output / "rows.jsonl").open("x", buffering=1)
    events = (output / "events.jsonl").open("x", buffering=1)

    def event(kind, **fields):
        events.write(json.dumps({"event": kind, "utc_seconds": time.time(), **fields}) + "\n")

    def budget():
        left = 1200 - (time.monotonic() - started)
        if left <= 0:
            raise ResourceRefusal("20min whole-capture cap")
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
            raise ValueError("initial original-head inventory mismatch")
        inventory = json.loads((initial / "manifest.json").read_text())
        for name, entry in inventory.items():
            if sha(initial / name) != entry["sha256"]:
                raise ValueError(f"initial immutable packet mismatch: {name}")
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
                "initial_packet_manifest_sha256": sha(initial / "manifest.json"),
                "initial_producer": json.loads((initial / "provenance.json").read_text())[
                    "producer_commit"
                ],
                "source_sha256": protocol["source_sha256"],
                "model_revision": MODEL_REVISION,
                "labels_read_by_capture": False,
            },
        )
        torch.set_num_threads(4)
        torch.manual_seed(52050)
        torch.cuda.manual_seed_all(52050)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        prompts = json.loads((initial / "prompt-ids.json").read_text())
        inputs = json.loads((HERE / "consumer-inputs-v4.json").read_text())["questions"]
        with bounded(budget()):
            language = NumericJSON(emissions(folder), 151645, 151643)
            plan = FloatPlan(language)
            if int(np.sum(plan.effects >= 0)) * 32 > 2000000:
                raise ResourceRefusal("symbolic arc cap")
        spec = importlib.util.spec_from_file_location(
            "a52_two_stage_pinned", folder / "modeling_qwen3.py"
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
        model_bytes = torch.cuda.memory_allocated()
        torch.cuda.reset_peak_memory_stats()

        def next_head(case, canvas, warmup=False):
            active = tuple(i for i, v in enumerate(canvas) if v == 151669)
            identity = {
                "prompt": prompts[case],
                "canvas": canvas,
                "revision": MODEL_REVISION,
                "config": "BF16-SDPA-no-cache-temperature1",
                "active": active,
            }
            key = hashlib.sha256(
                json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            name = "warmup" if warmup else key
            path = heads / f"{name}.npz"
            if path.exists():
                report["cache_hits"] += 1
                bits = np.load(path)["logits_bf16"]
                return active, bits, key, True
            if report["new_forward_attempts"] >= 641:
                raise ResourceRefusal("641 new-forward cap")
            write_json(heads / f"{name}.json", identity)
            report["new_forward_attempts"] += 1
            event("forward_attempt", key=name, ordinal=report["new_forward_attempts"])
            ids = torch.tensor([prompts[case] + list(canvas)], device="cuda")
            indices = torch.tensor([len(prompts[case]) + i for i in active], device="cuda")
            with torch.no_grad(), bounded(budget()):
                logits = model(
                    ids,
                    attention_mask=torch.ones_like(ids),
                    use_cache=False,
                    logits_to_keep=indices,
                ).logits
                torch.cuda.synchronize()
            report["new_forward_completions"] += 1
            event("forward_complete", key=name)
            if logits.dtype != torch.bfloat16:
                np.savez_compressed(path, unexpected_logits=logits.detach().cpu().numpy())
                raise AssertionError("original BF16 head contract")
            bits = logits[0].view(torch.uint16).cpu().numpy()
            np.savez_compressed(path, logits_bf16=bits, active=np.asarray(active))
            if bits.shape != (len(active), 151936):
                raise AssertionError("indexed original-V head shape")
            return active, bits, key, False

        next_head(0, (151669,) * 32, warmup=True)
        for case, item in enumerate(inputs):
            initial_bits = np.load(initial / f"head-{case:02d}.npz")["logits_bf16"]
            weights = bf16_probabilities(initial_bits)
            with bounded(budget()):
                planner = CompactPlanner(plan, weights)
            for phase, count in (("pilot", 16), ("eval", 64)):
                for draw in range(count):
                    row = {
                        "case": case,
                        "input_id": item["id"],
                        "phase": phase,
                        "draw": draw,
                        "joint_seed": seed_for(case, phase, draw, "joint"),
                        "continuation_seed": seed_for(case, phase, draw, "tail"),
                    }
                    try:
                        with bounded(budget()):
                            rng = np.random.default_rng(row["joint_seed"])
                            word = plan.sample(weights, rng)
                            anchor = int(rng.integers(32))
                            bits = rng.random(32) < planner.gates[np.arange(32), word]
                            bits[anchor] = True
                            action = tuple((i, v) for i, v in enumerate(word) if bits[i])
                            canvas = tuple(dict(action).get(i, 151669) for i in range(32))
                            row.update(
                                {
                                    "initial_word": word,
                                    "anchor": anchor,
                                    "action": action,
                                    "canvas": canvas,
                                }
                            )
                            json_text(language, word)
                            collapsed = planner.statistics(action)
                            expected = plan.action_statistics(weights, action)
                            checks = compare(collapsed, expected)
                            if checks["log_probability"] > 1e-7:
                                raise AssertionError("compact observed-log tolerance")
                            scores = {
                                **planner.cheap_scores(word, anchor, action),
                                "known_anchor": planner.known_anchor(collapsed, anchor, action),
                                "collapsed": collapsed,
                            }
                            row["scores"] = {name: score_vector(s) for name, s in scores.items()}
                            row["score_checks"] = checks
                        if len(action) == 32:
                            final = word
                            report["complete_first_actions"] += 1
                            row["continuation_head"] = None
                        else:
                            active, headbits, key, hit = next_head(case, canvas)
                            row.update(
                                {"continuation_head": key, "head_cache_hit": hit, "active": active}
                            )
                            with bounded(budget()):
                                active_weights = bf16_probabilities(headbits)
                                conditioned = clamped_weights(canvas, active, active_weights)
                                final = plan.sample(
                                    conditioned, np.random.default_rng(row["continuation_seed"])
                                )
                                if any(final[i] != v for i, v in action):
                                    raise AssertionError(
                                        "continuation altered an original fixed ID"
                                    )
                        row.update(
                            {
                                "final_word": final,
                                "json": json_text(language, final),
                                "status": "COMPLETE",
                            }
                        )
                        report["complete"] += 1
                    except Exception as error:
                        row.update(
                            {
                                "status": "RESOURCE_REFUSAL"
                                if isinstance(error, ResourceRefusal)
                                else "ERROR",
                                "exception": repr(error),
                            }
                        )
                        report["errors"] += 1
                    report["records"] += 1
                    stream.write(json.dumps(serial(row), allow_nan=False) + "\n")
                    report["sampler_peak_gpu_allocated_bytes"] = (
                        torch.cuda.max_memory_allocated() - model_bytes
                    )
                    if report["sampler_peak_gpu_allocated_bytes"] > 2 * 1024**3:
                        raise ResourceRefusal("2GiB GPU sampler-workspace cap")
                    if "conditioned" in locals():
                        del conditioned, active_weights, headbits
                write_json(output / "progress.json", report)
                print(json.dumps({"case": case, "phase": phase, **report}), flush=True)
        report["status"] = (
            "CAPTURE_COMPLETE"
            if report["records"] == 640 and report["errors"] == 0
            else "CAPTURE_NEGATIVE"
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
