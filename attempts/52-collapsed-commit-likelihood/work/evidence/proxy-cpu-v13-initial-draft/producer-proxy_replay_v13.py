"""V13 CPU-only ALL70 OLD-transition correctness; no model/sampling/CUDA."""

import argparse
import importlib.metadata
import json
import re
import resource
import subprocess
import time
from decimal import Decimal
from pathlib import Path

import numpy as np

from .consumer_resource import HERE, ResourceRefusal, bounded, serial, sha, write_json
from .llada_capture_v10 import padded_score
from .llada_suffix_v10 import NumericSuffixJSON, full_text
from .llada_tokenizer_v10 import EOS, VOCABULARY, emissions, verify_files
from .numeric_proxy import IntegerProxy
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_runtime import assemble
from .prefix_torch import PrefixTorch
from .preflight_floating import compare
from .preflight_proxy_v12 import differences
from .proxy_floating import ProxyPlanner
from .proxy_torch import torch_control
from .two_stage import bf16_probabilities


def run(folder, capture, analysis, protocol_path, output):
    import torch

    output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads(protocol_path.read_text())
    started = time.monotonic()
    records = []
    report = {
        "status": "RUNNING",
        "new_model_forwards": 0,
        "updates": 0,
        "new_samples": 0,
        "labels_previously_known": True,
    }
    inputs = [
        (r, t)
        for r in [json.loads(x) for x in (capture / "rows.jsonl").read_text().splitlines()]
        for t in r["transitions"]
    ]

    def budget():
        left = 1200 - (time.monotonic() - started)
        if left <= 0:
            raise ResourceRefusal("1200s whole replay cap")
        return min(60, left)

    try:
        torch.set_num_threads(4)
        runtime = {name: importlib.metadata.version(name) for name in ("torch", "numpy")}
        if runtime != protocol["runtime"]:
            raise ValueError("runtime differs from frozen protocol")
        for name, expected in protocol["source_sha256"].items():
            if sha(HERE / name) != expected:
                raise ValueError(f"source changed: {name}")
        for key, path in (
            ("capture_manifest", capture / "manifest.json"),
            ("rows", capture / "rows.jsonl"),
            ("labels", analysis / "known-labels-provenance.json"),
        ):
            if sha(path) != protocol["input_sha256"][key]:
                raise ValueError(f"input changed: {key}")
        verify_files(folder)
        write_json(output / "protocol.json", protocol)
        write_json(
            output / "provenance.json",
            {
                "producer_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "runtime": runtime,
                "source_sha256": protocol["source_sha256"],
            },
        )
        manifest = json.loads((capture / "manifest.json").read_text())
        labels = json.loads((analysis / "known-labels-provenance.json").read_text())["labels"]
        with bounded(budget()):
            original = emissions(folder)
            broad = NumericSuffixJSON(original, EOS, EOS)
            plan = PrefixFloatPlan(broad)
            narrow = {
                d: PrefixFloatPlan(IntegerProxy(original, EOS, EOS, d))
                for d in sorted({item["answer"] for item in labels})
            }
            backend = PrefixTorch(plan, device="cpu")
            proxies = {d: PrefixTorch(p, device="cpu") for d, p in narrow.items()}
        report["setup_diagnostic_seconds"] = time.monotonic() - started
        report["proxy_classes"] = {d: p.class_count for d, p in narrow.items()}
        with (output / "records.jsonl").open("x", buffering=1) as stream:
            for row, transition in inputs:
                record = {
                    "case": row["case"],
                    "replica": row["replica"],
                    "step": transition["step"],
                    "head": transition["head"],
                }
                tick = time.monotonic()
                try:
                                with bounded(budget()):
                        name = f"heads/{transition['head']}.npz"
                        if sha(capture / name) != manifest[name]["sha256"]:
                            raise ValueError("original BF16 head changed")
                        with np.load(capture / name) as packet:
                            probabilities = bf16_probabilities(packet["logits_bf16"])
                            if packet["positions"].tolist() != transition["queried_positions"]:
                                raise ValueError("recorded queried positions differ")
                        fixed = dict(transition["fixed_before"])
                        action = tuple(map(tuple, transition["action"]))
                        n = transition["prefix_extent"]
                        weights = assemble(
                            probabilities, transition["queried_positions"], fixed, n, VOCABULARY
                        )
                        feature = row["root_feature"]
                        planner = PrefixPlanner(plan, weights, fixed, feature)
                        base = planner.statistics(action)
                        base_error = compare(
                            {"log_probability": base["log_probability"], **padded_score(base)},
                            {
                                "log_probability": transition["log_probability"],
                                **transition["scores"]["collapsed"],
                            },
                        )
                        if max(base_error.values()) > 1e-7:
                            raise AssertionError("old base score changed")
                        digits = labels[row["case"]]["answer"]
                        control = ProxyPlanner(planner, narrow[digits])
                        expected = control.statistics(action, base)
                        device_weights = torch.as_tensor(weights, device="cpu")
                        actual_base = backend.statistics(device_weights, fixed, feature, action)
                        logbase = backend.partition(device_weights, max(fixed, default=-1))
                        actual = torch_control(
                            proxies[digits],
                            device_weights,
                            fixed,
                            feature,
                            action,
                            logbase,
                            actual_base,
                        )
                        errors = differences(actual, expected)
                        word = tuple(transition["proposal_prefix"])
                        text = full_text(broad, word)
                        body = b"".join(original[v] for v in word[:-1])
                        pattern = (
                            rb"[ \t\r\n]*"
                            + digits.encode()
                            + rb"(?:\.0+)?(?:[eE][+-]?0+)?[ \t\r\n]*}[ \t\r\n]*"
                        )
                        proxy_match = re.fullmatch(pattern, body) is not None
                        if narrow[digits].language.accepts(word) != proxy_match:
                            raise AssertionError("independent proxy regex differs")
                        semantic = json.loads(text, parse_int=Decimal, parse_float=Decimal)[
                            "answer"
                        ] == Decimal(digits)
                        if proxy_match and (not semantic or expected["status"] != "POSITIVE"):
                            raise AssertionError("sampled proxy word lost positive original mass")
                        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
                        payload = peak
                        if payload > 2 * 1024**3:
                            raise ResourceRefusal("2GiB CPU process peak RSS")
                        record.update(
                            {
                                "status": "PASS",
                                "base_score": serial(base),
                                "target_digits": digits,
                                "proxy": serial(expected),
                                "independent_errors": errors,
                                "original_base_errors": base_error,
                                "proposal_proxy_match": proxy_match,
                                "proposal_semantic_correct": semantic,
                                "semantic_correct_proxy_missed": semantic and not proxy_match,
                                "tracked_sampler_payload_bytes": payload,
                                "peak_process_rss_bytes": peak,
                            }
                        )
                        del device_weights, logbase
                            except ResourceRefusal as error:
                    record.update({"status": "RESOURCE_REFUSAL", "exception": repr(error)})
                except Exception as error:
                    record.update({"status": "ERROR", "exception": repr(error)})
                record["diagnostic_seconds"] = time.monotonic() - tick
                records.append(record)
                stream.write(json.dumps(serial(record), allow_nan=False) + "\n")
                print(
                    json.dumps({k: record[k] for k in ("case", "replica", "step", "status")}),
                    flush=True,
                )
    except Exception as error:
        report["setup_exception"] = repr(error)
    finally:
        if len(records) < len(inputs):
            with (output / "records.jsonl").open("a", buffering=1) as stream:
                for row, transition in inputs[len(records) :]:
                    record = {
                        "case": row["case"],
                        "replica": row["replica"],
                        "step": transition["step"],
                        "head": transition["head"],
                        "status": "NOT_RUN",
                        "reason": report.get("setup_exception"),
                    }
                    records.append(record)
                    stream.write(json.dumps(record) + "\n")
        report.update({"execution_device": "cpu", "gpu_used": False,
                       "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024})
        report.update(
            {
                "records": len(records),
                "declared_transitions": len(inputs),
                "status_counts": {
                    s: sum(r["status"] == s for r in records)
                    for s in ("PASS", "ERROR", "RESOURCE_REFUSAL", "NOT_RUN")
                },
                "diagnostic_seconds": time.monotonic() - started,
            }
        )
        report["status"] = (
            "PASS"
            if (
                len(records) == len(inputs) == 70
                and all(r["status"] == "PASS" for r in records)
                and report["peak_process_rss_bytes"] <= 2 * 1024**3
            )
            else "FUNCTIONALITY_NOT_CONFIRMED"
        )
        write_json(output / "summary.json", report)
        write_json(
            output / "manifest.json",
            {
                p.relative_to(output).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size}
                for p in sorted(output.rglob("*"))
                if p.is_file() and p.name != "manifest.json"
            },
        )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    for argument in ("model-dir", "capture", "analysis", "protocol", "output"):
        ap.add_argument("--" + argument, type=Path, required=True)
    args = ap.parse_args()
    run(args.model_dir, args.capture, args.analysis, args.protocol, args.output)
