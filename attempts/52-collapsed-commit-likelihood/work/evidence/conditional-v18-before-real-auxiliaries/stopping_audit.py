"""Frozen OLD-head stopping contract diagnostic. No samples, labels or forwards."""

import argparse
import importlib.metadata
import json
import resource
import subprocess
import time
from pathlib import Path

import numpy as np

from .consumer_resource import HERE, ResourceRefusal, bounded, serial, sha, write_json
from .floating import FloatPlan
from .numeric_json import NumericJSON
from .stopping import StoppedNumericJSON, first_eot_logs, length_statistics
from .tokenizer_audit import emissions
from .two_stage import bf16_probabilities


def finite_json(value):
    if isinstance(value, dict):
        return {k: finite_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [finite_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return finite_json(value.tolist())
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    return serial(value)


def run(folder, initial, protocol_path, output):
    output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads(protocol_path.read_text())
    started = time.monotonic()
    report = {
        "status": "RUNNING",
        "scope": "KNOWN_OLD_HEAD_STOPPING_DIAGNOSTIC_ONLY",
        "new_model_forwards": 0,
        "new_samples": 0,
        "labels_read": False,
        "updates": 0,
        "records": [],
    }
    stream = (output / "rows.jsonl").open("x", buffering=1)
    try:
        for name, expected in protocol["source_sha256"].items():
            if sha(HERE / name) != expected:
                raise ValueError(f"frozen source mismatch: {name}")
        if sha(initial / "manifest.json") != protocol["initial_manifest_sha256"]:
            raise ValueError("initial packet inventory mismatch")
        inventory = json.loads((initial / "manifest.json").read_text())
        for name, entry in inventory.items():
            if sha(initial / name) != entry["sha256"]:
                raise ValueError(f"old packet mismatch: {name}")
        if importlib.metadata.version("numpy") != protocol["runtime"]["numpy"]:
            raise ValueError("frozen NumPy runtime mismatch")
        write_json(output / "protocol.json", protocol)
        write_json(
            output / "provenance.json",
            {
                "producer_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "old_head_producer": json.loads((initial / "provenance.json").read_text())[
                    "producer_commit"
                ],
                "numpy": importlib.metadata.version("numpy"),
                "source_sha256": protocol["source_sha256"],
            },
        )
        with bounded(60):
            table = emissions(folder)
            stopped = FloatPlan(StoppedNumericJSON(table, 151645, 151643))
            padded = FloatPlan(NumericJSON(table, 151645, 151643))
        for plan in (stopped, padded):
            if int(np.sum(plan.effects >= 0)) * 32 > 2000000:
                raise ResourceRefusal("symbolic arc cap")
        np.savez_compressed(
            output / "class-effects.npz",
            stopped_effects=stopped.effects,
            stopped_mapping=stopped.mapping,
            padded_effects=padded.effects,
            padded_mapping=padded.mapping,
        )
        old_rows = [json.loads(s) for s in (initial / "rows.jsonl").read_text().splitlines()]
        for case in range(8):
            row = {"case": case, "input_id": old_rows[case]["input_id"]}
            try:
                if time.monotonic() - started >= 1200:
                    raise ResourceRefusal("20min audit cap")
                with bounded(60):
                    weights = bf16_probabilities(
                        np.load(initial / f"head-{case:02d}.npz")["logits_bf16"]
                    )
                    logs = first_eot_logs(stopped, weights)
                    result = length_statistics(logs, weights[:, 151643])
                    direct_stop = stopped.forwards(stopped.matrices(weights)[0])[0]
                    direct_pad = padded.forwards(padded.matrices(weights)[0])[0]
                    checks = {
                        "absorbing_stop_log_error": abs(direct_stop - result["log_z_stop"]),
                        "original_pad_log_error": abs(direct_pad - result["log_z_pad"]),
                        "archived_pad_log_error": abs(
                            direct_pad - old_rows[case]["log_grammar_mass"]
                        ),
                    }
                    if any(v > 1e-7 for v in checks.values()):
                        raise AssertionError("independent partition tolerance")
                    if (result["pad_survival"] < result["stop_survival"] - 1e-10).any():
                        raise AssertionError("stochastic length order check")
                    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > 2 * 1024**3:
                        raise ResourceRefusal("2GiB process cap (no model loaded)")
                    row.update(
                        {
                            "status": "COMPLETE",
                            "first_eot_log_masses": logs,
                            "statistics": result,
                            "checks": checks,
                            "diagnostic_interest": bool(
                                result["tv"] >= 0.2 and result["mean_length_gap"] >= 4
                            ),
                        }
                    )
            except Exception as error:
                row.update(
                    {
                        "status": "RESOURCE_REFUSAL"
                        if isinstance(error, ResourceRefusal)
                        else "ERROR",
                        "exception": repr(error),
                    }
                )
            stream.write(json.dumps(finite_json(row), allow_nan=False) + "\n")
            report["records"].append(finite_json(row))
        count = sum(r.get("diagnostic_interest", False) for r in report["records"])
        complete = sum(r["status"] == "COMPLETE" for r in report["records"])
        report.update(
            {
                "status": "DIAGNOSTIC_INTEREST"
                if complete == 8 and count >= 6
                else "DIAGNOSTIC_NOT_LARGE",
                "complete_cases": complete,
                "interest_cases": count,
                "class_counts": {"stopped": stopped.class_count, "padded": padded.class_count},
            }
        )
    except Exception as error:
        report.update(
            {
                "status": "RESOURCE_REFUSAL" if isinstance(error, ResourceRefusal) else "ERROR",
                "exception": repr(error),
            }
        )
        raise
    finally:
        report["diagnostic_seconds"] = time.monotonic() - started
        report["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        write_json(output / "summary.json", finite_json(report))
        stream.close()
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer-dir", type=Path, required=True)
    ap.add_argument("--initial-packet", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.tokenizer_dir, args.initial_packet, args.protocol, args.output)
