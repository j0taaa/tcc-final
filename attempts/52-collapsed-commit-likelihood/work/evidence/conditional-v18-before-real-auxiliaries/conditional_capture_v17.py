"""CPU-only OLD70-state conditional AUXILIARY functionality, not new heads."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import resource
import subprocess
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np

from .actor_coordinates import actor_vector, state_features
from .conditional_floating import ConditionalFloatSampler
from .consumer_resource import HERE, ResourceRefusal, bounded, serial, sha, write_json
from .llada_capture_v10 import padded_score
from .llada_suffix_v10 import NumericSuffixJSON, full_text
from .llada_tokenizer_v10 import EOS, VOCABULARY, emissions, verify_files
from .numeric_verifier_v17 import independent_answer_equal
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_runtime import assemble
from .two_stage import answer_equal, bf16_probabilities


def tokenizer_from(folder):
    from tokenizers import Tokenizer

    return Tokenizer.from_file(str(folder / "tokenizer.json"))


def seed_for(case, replica, step, method):
    return int.from_bytes(
        hashlib.sha256(f"52170:{case}:{replica}:{step}:{method}".encode()).digest()[:8], "little"
    )


def execute_batch(
    row,
    transition,
    method,
    sampler,
    planner,
    grammar,
    tokenizer,
    fixed,
    action,
    features,
    labels,
    raw,
    emit,
    budget,
):
    seed = seed_for(row["case"], row["replica"], transition["step"], method)
    common = {
        "case": row["case"],
        "replica": row["replica"],
        "step": transition["step"],
        "head": transition["head"],
        "method": method,
        "seed": seed,
    }
    try:
        with bounded(budget()):
            draws = sampler.sample(4, random.Random(seed), method == "prefix_stratified")
        raw.write(json.dumps(serial({**common, "raw_word_anchor_batch": draws})) + "\n")
    except Exception as error:
        raw.write(
            json.dumps(
                serial(
                    {
                        **common,
                        "exception": repr(error),
                        "partial_trace": getattr(sampler, "partial_trace", None),
                    }
                )
            )
            + "\n"
        )
        for j in range(4):
            emit(
                {
                    **common,
                    "auxiliary_index": j,
                    "status": "RESOURCE_REFUSAL" if isinstance(error, ResourceRefusal) else "ERROR",
                    "exception": repr(error),
                }
            )
        return
    for j, (word, anchor) in enumerate(draws):
        record = {**common, "auxiliary_index": j, "word": word, "anchor": anchor}
        try:
            with bounded(budget()):
                text = full_text(grammar, word)
                decoded = tokenizer.decode(
                    [12657, 31113, 2275, *word[:-1]], skip_special_tokens=False
                )
                if text != decoded:
                    raise AssertionError("independent official original-ID tokenizer differs")
                if any(i >= len(word) or word[i] != v for i, v in (*fixed.items(), *action)):
                    raise AssertionError(
                        "conditional word changed/truncated an observed original ID"
                    )
                gold = labels[row["case"]]["answer"]
                semantic = answer_equal(text, gold)
                if independent_answer_equal(text, gold) != semantic:
                    raise AssertionError("independent unrestricted numeric verifier differs")
                decimal_ok, decimal_exception = True, None
                try:
                    parsed = json.loads(text, parse_int=Decimal, parse_float=Decimal)
                    if (parsed["answer"] == Decimal(gold)) != semantic:
                        raise AssertionError("secondary Decimal verifier differs")
                except (InvalidOperation, OverflowError, ValueError) as error:
                    decimal_ok, decimal_exception = False, repr(error)
                scores = {
                    "collapsed": sampler.statistics,
                    **planner.controls(word, anchor, action, sampler.statistics),
                }
                if not all(np.isfinite(v).all() for s in scores.values() for v in s.values()):
                    raise AssertionError("nonfinite conditional policy score")
                record.update(
                    {
                        "status": "PASS",
                        "json": text,
                        "semantic_correct_proposal": semantic,
                        "secondary_Decimal_representable": decimal_ok,
                        "secondary_Decimal_exception": decimal_exception,
                        "scores": {name: serial(padded_score(s)) for name, s in scores.items()},
                        "actor_scores": {
                            name: serial(actor_vector(s, features)) for name, s in scores.items()
                        },
                    }
                )
                if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > 2 * 1024**3:
                    raise ResourceRefusal("2GiB entire CPU process peak RSS")
        except Exception as error:
            record.update(
                {
                    "status": "RESOURCE_REFUSAL" if isinstance(error, ResourceRefusal) else "ERROR",
                    "exception": repr(error),
                }
            )
        emit(record)


def run(folder, capture, analysis, protocol_path, output):
    output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads(protocol_path.read_text())
    started = time.monotonic()
    records, preparations = [], []
    report = {
        "status": "RUNNING",
        "new_model_forwards": 0,
        "new_decoder_trajectories": 0,
        "updates": 0,
        "scope": "KNOWN_OLD_HEAD_CONDITIONAL_AUXILIARY_FUNCTIONALITY_ONLY",
        "execution_device": "cpu",
        "CUDA_used": False,
        "labels_previously_known": True,
    }
    global_python, global_numpy = random.getstate(), np.random.get_state()
    rows = [json.loads(x) for x in (capture / "rows.jsonl").read_text().splitlines()]
    inputs = [(r, t) for r in rows for t in r["transitions"]]
    stream = (output / "records.jsonl").open("x", buffering=1)
    raw = (output / "raw-batches.jsonl").open("x", buffering=1)

    def identity(row, transition, method, index):
        return {
            "case": row["case"],
            "replica": row["replica"],
            "step": transition["step"],
            "head": transition["head"],
            "method": method,
            "auxiliary_index": index,
        }

    def emit(record):
        records.append(record)
        stream.write(json.dumps(serial(record), allow_nan=False) + "\n")

    def budget():
        left = 1200 - (time.monotonic() - started)
        if left <= 0:
            raise ResourceRefusal("1200s complete functionality cap")
        return min(60, left)

    try:
        runtime = {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "tokenizers": importlib.metadata.version("tokenizers"),
        }
        if runtime != protocol["runtime"]:
            raise ValueError("runtime changed from frozen protocol")
        if any(
            os.environ.get(k) != "4"
            for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        ):
            raise ValueError("four-thread environment must be set before NumPy import")
        for name, expected in protocol["source_sha256"].items():
            if sha(HERE / name) != expected:
                raise ValueError(f"source changed: {name}")
        pins = {
            "rows": capture / "rows.jsonl",
            "manifest": capture / "manifest.json",
            "labels": analysis / "known-labels-provenance.json",
        }
        if any(sha(p) != protocol["input_sha256"][k] for k, p in pins.items()):
            raise ValueError("original input changed")
        if len(inputs) != 70 or len(rows) != 16:
            raise ValueError("ALL70 original states/16 decoder trajectories required")
        verify_files(folder)
        labels = json.loads(pins["labels"].read_text())["labels"]
        manifest = json.loads(pins["manifest"].read_text())
        write_json(output / "protocol.json", protocol)
        write_json(
            output / "provenance.json",
            {
                "producer_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "runtime": runtime,
                "source_sha256": protocol["source_sha256"],
                "thread_environment": {
                    k: os.environ[k]
                    for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
                },
            },
        )
        with bounded(budget()):
            tokenizer = tokenizer_from(folder)
            grammar = NumericSuffixJSON(emissions(folder), EOS, EOS)
            plan = PrefixFloatPlan(grammar)
        report["setup_diagnostic_seconds"] = time.monotonic() - started
        for ordinal, (row, transition) in enumerate(inputs):
            prep = {"ordinal": ordinal, **identity(row, transition, "preparation", -1)}
            try:
                with bounded(budget()):
                    filename = f"heads/{transition['head']}.npz"
                    if sha(capture / filename) != manifest[filename]["sha256"]:
                        raise ValueError("original BF16 logits changed")
                    with np.load(capture / filename) as packet:
                        probabilities = bf16_probabilities(packet["logits_bf16"])
                        if packet["positions"].tolist() != transition["queried_positions"]:
                            raise ValueError("original active positions changed")
                    fixed = dict(transition["fixed_before"])
                    action = tuple(map(tuple, transition["action"]))
                    weights = assemble(
                        probabilities,
                        transition["queried_positions"],
                        fixed,
                        transition["prefix_extent"],
                        VOCABULARY,
                    )
                    planner = PrefixPlanner(plan, weights, fixed, row["root_feature"])
                    sampler = ConditionalFloatSampler(planner, action)
                    error = abs(
                        sampler.statistics["log_probability"] - transition["log_probability"]
                    )
                    if error > 1e-7:
                        raise AssertionError(
                            "conditional sampler changed original action likelihood"
                        )
                    features = state_features(weights, fixed, EOS)
                    prep.update(
                        {
                            "status": "READY",
                            "action_log_probability_error": error,
                            "log_query_mass": sampler.log_query_mass,
                        }
                    )
            except Exception as error:
                prep.update(
                    {
                        "status": "RESOURCE_REFUSAL"
                        if isinstance(error, ResourceRefusal)
                        else "ERROR",
                        "exception": repr(error),
                    }
                )
                for method in ("iid", "prefix_stratified"):
                    for j in range(4):
                        emit(
                            {
                                **identity(row, transition, method, j),
                                "status": "NOT_RUN",
                                "reason": prep["exception"],
                            }
                        )
                preparations.append(prep)
                continue
            # Methods and full batch records are implemented below.
            for method in ("iid", "prefix_stratified"):
                execute_batch(
                    row,
                    transition,
                    method,
                    sampler,
                    planner,
                    grammar,
                    tokenizer,
                    fixed,
                    action,
                    features,
                    labels,
                    raw,
                    emit,
                    budget,
                )
            prep.update(
                {
                    "integer_CDF_cache_payload_bytes": sampler.cache_payload_bytes(),
                    "token_CDFs": len(sampler.token_cache),
                    "class_CDFs": len(sampler.class_cache),
                    "peak_CPU_process_RSS_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    * 1024,
                }
            )
            categories = (
                *sampler.class_cache.values(),
                *sampler.token_cache.values(),
                sampler.anchor,
            )
            prep.update(
                {
                    "max_categorical_ticket_bits": max(c.total.bit_length() for c in categories),
                    "positive_original_ID_CDF_entries": sum(
                        len(c.ids) for c in sampler.token_cache.values()
                    ),
                }
            )
            preparations.append(prep)
            if prep["peak_CPU_process_RSS_bytes"] > 2 * 1024**3:
                raise ResourceRefusal("2GiB entire CPU process RSS")
            print(
                json.dumps({"state": ordinal, "records": len(records), "status": prep["status"]}),
                flush=True,
            )
    except Exception as error:
        report["global_exception"] = repr(error)
    finally:
        seen = {
            (r["case"], r["replica"], r["step"], r["method"], r["auxiliary_index"]) for r in records
        }
        for row, transition in inputs:
            for method in ("iid", "prefix_stratified"):
                for j in range(4):
                    key = row["case"], row["replica"], transition["step"], method, j
                    if key not in seen:
                        emit(
                            {
                                **identity(row, transition, method, j),
                                "status": "NOT_RUN",
                                "reason": report.get("global_exception", "global resource stop"),
                            }
                        )
        stream.close()
        raw.close()
        current_numpy = np.random.get_state()
        unchanged = (
            random.getstate() == global_python
            and current_numpy[0] == global_numpy[0]
            and np.array_equal(current_numpy[1], global_numpy[1])
            and current_numpy[2:] == global_numpy[2:]
        )
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        report.update(
            {
                "declared_auxiliary_slots": 560,
                "auxiliary_records": len(records),
                "status_counts": {
                    s: sum(r["status"] == s for r in records)
                    for s in ("PASS", "ERROR", "RESOURCE_REFUSAL", "NOT_RUN")
                },
                "new_completed_auxiliary_words": sum("word" in r for r in records),
                "global_Python_NumPy_RNG_unchanged": unchanged,
                "peak_CPU_process_RSS_bytes": peak,
                "diagnostic_seconds": time.monotonic() - started,
            }
        )
        report["status"] = (
            "PASS"
            if len(records) == 560
            and all(r["status"] == "PASS" for r in records)
            and unchanged
            and peak <= 2 * 1024**3
            else "FUNCTIONALITY_NOT_CONFIRMED"
        )
        write_json(output / "preparations.json", preparations)
        batches = [
            json.loads(line) for line in (output / "raw-batches.jsonl").read_text().splitlines()
        ]
        report["auxiliary_word_attempts"] = 4 * len(batches)
        report["raw_completed_auxiliary_words"] = sum(
            len(b.get("raw_word_anchor_batch", ())) for b in batches
        )
        report["secondary_Decimal_unrepresentable_words"] = sum(
            r.get("secondary_Decimal_representable") is False for r in records
        )
        write_json(output / "summary.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("model-dir", "capture", "analysis", "protocol", "output"):
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    run(a.model_dir, a.capture, a.analysis, a.protocol, a.output)
