"""Pinned OLD-head length/anchor support readouts; no new neural call or draw."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import resource
import signal
import subprocess
import time
from collections import Counter
from pathlib import Path

import numpy as np

from .actor_coordinates import actor_vector, state_features
from .length_readout import NumericSuffix
from .llada_tokenizer_v10 import EOS, VOCABULARY, emissions, verify_files
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .query_support import support

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probabilities(bits):
    logits = (np.asarray(bits, dtype=np.uint32) << 16).view(np.float32).astype(np.float64)
    if logits.ndim != 2 or not np.isfinite(logits).all():
        raise ValueError("invalid original BF16 head")
    values = np.exp(logits - logits.max(axis=1, keepdims=True))
    values /= values.sum(axis=1, keepdims=True)
    if not (values > 0).all():
        raise ValueError("original head probability underflow")
    return values


def run(model_dir, capture, features_path, auxiliary, protocol_path, output):
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "RUNNING",
        "new_model_forwards": 0,
        "new_auxiliary_words": 0,
        "new_decoder_paths": 0,
        "updates": 0,
        "CUDA_used": False,
        "scope": "OLD-known70-state numerical ideal-kernel readouts, NOT exact native coupling",
    }
    records = []
    inputs = []
    started = time.monotonic()
    py_state, np_state = random.getstate(), np.random.get_state()
    stream = (output / "records.jsonl").open("x", buffering=1)

    def emit(value):
        records.append(value)
        stream.write(json.dumps(value) + "\n")

    def timed_out(signum, frame):
        raise TimeoutError("operation/whole CPU readout cap")

    signal.signal(signal.SIGALRM, timed_out)
    try:
        protocol = json.loads(protocol_path.read_text())
        runtime = {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "tokenizers": importlib.metadata.version("tokenizers"),
        }
        assert runtime == protocol["runtime"]
        assert all(
            os.environ.get(k) == "4"
            for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        )
        assert all(sha(HERE / n) == h for n, h in protocol["source_sha256"].items())
        paths = {
            "rows": capture / "rows.jsonl",
            "manifest": capture / "manifest.json",
            "features": features_path,
            "auxiliary": auxiliary / "records.jsonl",
            "auxiliary_summary": auxiliary / "summary.json",
        }
        assert all(sha(p) == protocol["input_sha256"][k] for k, p in paths.items())
        rows = [json.loads(s) for s in paths["rows"].read_text().splitlines()]
        inputs = [(row, t) for row in rows for t in row["transitions"]]
        features = [json.loads(s) for s in features_path.read_text().splitlines()]
        manifest = json.loads(paths["manifest"].read_text())
        assert len(rows) == 16 and len(inputs) == len(features) == 70
        (output / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
        (output / "provenance.json").write_text(
            json.dumps(
                {
                    "producer_commit": subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], text=True
                    ).strip(),
                    "runtime": runtime,
                },
                indent=2,
            )
            + "\n"
        )
        signal.setitimer(signal.ITIMER_REAL, 60)
        verify_files(model_dir)
        plan = PrefixFloatPlan(NumericSuffix(emissions(model_dir), EOS, EOS))
        signal.setitimer(signal.ITIMER_REAL, 0)
        for ordinal, (row, t) in enumerate(inputs):
            record = {
                "ordinal": ordinal,
                "case": row["case"],
                "replica": row["replica"],
                "step": t["step"],
                "head": t["head"],
                "remaining_requests_after_action": len(row["transitions"]) - t["step"] - 1,
            }
            try:
                left = 600 - (time.monotonic() - started)
                if left <= 0:
                    raise TimeoutError("600s whole screen cap")
                signal.setitimer(signal.ITIMER_REAL, min(60, left))
                old = features[ordinal]
                assert all(old[k] == record[k] for k in ("case", "replica", "step", "head"))
                path = capture / "heads" / (t["head"] + ".npz")
                assert sha(path) == manifest["heads/" + t["head"] + ".npz"]["sha256"]
                with np.load(path) as saved:
                    p = probabilities(saved["logits_bf16"])
                    positions = saved["positions"].tolist()
                fixed = dict(t["fixed_before"])
                n = t["prefix_extent"]
                assert positions == [i for i in range(n) if i not in fixed] and p.shape == (
                    len(positions),
                    VOCABULARY,
                )
                weights = np.zeros((n, VOCABULARY))
                for i, v in fixed.items():
                    weights[i, v] = 1
                for local, i in enumerate(positions):
                    weights[i] = p[local]
                f = state_features(weights, fixed, EOS)
                assert all(
                    np.max(np.abs(np.asarray(f[k]) - np.asarray(old["features"][k]))) < 1e-12
                    for k in f
                )
                planner = PrefixPlanner(plan, weights, fixed, row["root_feature"])
                action = tuple(map(tuple, t["action"]))
                value = support(planner, action, f)
                reference = actor_vector(t["scores"]["collapsed"], f)
                error = float(np.max(np.abs(np.asarray(value["collapsed_actor"]) - reference)))
                assert (
                    error <= 1e-7
                    and abs(value["action_log_probability"] - t["log_probability"]) <= 1e-7
                )
                record.update({"status": "PASS", "readout": value, "old_actor_error": error})
                if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > 2 * 1024**3:
                    raise MemoryError("2GiB whole process RSS")
            except Exception as error:
                record.update(
                    {
                        "status": "RESOURCE_REFUSAL"
                        if isinstance(error, (MemoryError, TimeoutError))
                        else "ERROR",
                        "exception": repr(error),
                    }
                )
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            emit(record)
    except Exception as error:
        report["global_exception"] = repr(error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        for ordinal, (row, t) in enumerate(inputs[len(records) :], start=len(records)):
            emit(
                {
                    "ordinal": ordinal,
                    "case": row["case"],
                    "replica": row["replica"],
                    "step": t["step"],
                    "head": t["head"],
                    "status": "NOT_RUN",
                }
            )
        stream.close()
        after = np.random.get_state()
        unchanged = py_state == random.getstate() and all(
            np.array_equal(a, b) for a, b in zip(np_state, after, strict=True)
        )
        counts = dict(Counter(r["status"] for r in records))
        report.update(
            {
                "status": "PASS"
                if len(records) == 70
                and counts == {"PASS": 70}
                and unchanged
                and "global_exception" not in report
                else "INCOMPLETE_OR_REFUSED",
                "status_counts": counts,
                "records": len(records),
                "global_Python_NumPy_RNG_unchanged": unchanged,
                "peak_CPU_process_RSS_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                * 1024,
                "diagnostic_seconds": time.monotonic() - started,
            }
        )
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("model-dir", "capture", "features", "auxiliary", "protocol", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.model_dir, a.capture, a.features, a.auxiliary, a.protocol, a.output)
