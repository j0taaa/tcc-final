"""Fresh OLD-head auxiliaries for a development-only conditional variance probe."""

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

from .actor_coordinates import actor_vector
from .conditional_capture_v17 import tokenizer_from
from .conditional_floating import ConditionalFloatSampler
from .conditional_probe_v18 import certified_fixed_answer
from .consumer_resource import HERE, ResourceRefusal, bounded, serial, sha, write_json
from .llada_suffix_v10 import NumericSuffixJSON, full_text
from .llada_tokenizer_v10 import EOS, VOCABULARY, emissions, verify_files
from .numeric_verifier_v17 import independent_answer_equal
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_runtime import assemble
from .two_stage import answer_equal, bf16_probabilities


def seed_for(case, replica, step, method, batch):
    return int.from_bytes(
        hashlib.sha256(f"52180:{case}:{replica}:{step}:{method}:{batch}".encode()).digest()[:8],
        "little",
    )


def capture_batch(
    row,
    t,
    mode,
    batch,
    sampler,
    planner,
    grammar,
    tokenizer,
    labels,
    features,
    fixed,
    action,
    emit,
    stream,
    budget,
):
    seed = seed_for(row["case"], row["replica"], t["step"], mode, batch)
    common = {
        "case": row["case"],
        "replica": row["replica"],
        "step": t["step"],
        "head": t["head"],
        "method": mode,
        "batch": batch,
        "seed": seed,
    }
    try:
        with bounded(budget()):
            draws = sampler.sample(8, random.Random(seed), mode == "prefix_stratified")
        stream.write(json.dumps(serial({**common, "raw_word_anchor_batch": draws})) + "\n")
    except Exception as error:
        stream.write(
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
        for j in range(8):
            emit(
                {
                    **common,
                    "within_batch": j,
                    "draw_index": batch * 8 + j,
                    "status": "RESOURCE_REFUSAL" if isinstance(error, ResourceRefusal) else "ERROR",
                    "exception": repr(error),
                }
            )
        return
    for j, (word, anchor) in enumerate(draws):
        record = {
            **common,
            "within_batch": j,
            "draw_index": batch * 8 + j,
            "word": word,
            "anchor": anchor,
        }
        try:
            with bounded(budget()):
                text = full_text(grammar, word)
                if (
                    tokenizer.decode([12657, 31113, 2275, *word[:-1]], skip_special_tokens=False)
                    != text
                ):
                    raise AssertionError("independent official tokenizer differs")
                if any(i >= len(word) or word[i] != v for i, v in (*fixed.items(), *action)):
                    raise AssertionError("fixed/retained original ID changed")
                gold = labels[row["case"]]["answer"]
                semantic = answer_equal(text, gold)
                if independent_answer_equal(text, gold) != semantic:
                    raise AssertionError("independent unrestricted verifier differs")
                decimal_ok = True
                try:
                    value = json.loads(text, parse_int=Decimal, parse_float=Decimal)["answer"]
                    if (value == Decimal(gold)) != semantic:
                        raise AssertionError("Decimal differs")
                except (InvalidOperation, OverflowError, ValueError):
                    decimal_ok = False
                scores = {
                    "collapsed": sampler.statistics,
                    **planner.controls(word, anchor, action, sampler.statistics),
                }
                projected = {m: actor_vector(s, features) for m, s in scores.items()}
                if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024 > 2 * 1024**3:
                    raise ResourceRefusal("2GiB entire-process CPU RSS")
                record.update(
                    {
                        "status": "PASS",
                        "json": text,
                        "semantic_correct_proposal": semantic,
                        "secondary_Decimal_representable": decimal_ok,
                        "actor_scores": projected,
                    }
                )
        except Exception as error:
            record.update(
                {
                    "status": "RESOURCE_REFUSAL" if isinstance(error, ResourceRefusal) else "ERROR",
                    "exception": repr(error),
                }
            )
        emit(record)


def finalize(
    inputs, records, preps, emit, stream, batches, report, before_py, before_np, started, output
):
    seen = {
        (r["case"], r["replica"], r["step"], r["method"], r["batch"], r["within_batch"])
        for r in records
    }
    for row, t in inputs:
        for mode in ("iid", "prefix_stratified"):
            for batch in range(8):
                for j in range(8):
                    key = row["case"], row["replica"], t["step"], mode, batch, j
                    if key not in seen:
                        emit(
                            {
                                "case": row["case"],
                                "replica": row["replica"],
                                "step": t["step"],
                                "head": t["head"],
                                "method": mode,
                                "batch": batch,
                                "within_batch": j,
                                "draw_index": batch * 8 + j,
                                "status": "NOT_RUN",
                                "reason": report.get("global_exception", "resource stop"),
                            }
                        )
    stream.close()
    batches.close()
    after = np.random.get_state()
    unchanged = (
        random.getstate() == before_py
        and after[0] == before_np[0]
        and np.array_equal(after[1], before_np[1])
        and after[2:] == before_np[2:]
    )
    raw = [json.loads(x) for x in (output / "raw-batches.jsonl").read_text().splitlines()]
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    report.update(
        {
            "declared_auxiliary_slots": 8960,
            "records": len(records),
            "status_counts": {
                s: sum(r["status"] == s for r in records)
                for s in ("PASS", "ERROR", "RESOURCE_REFUSAL", "NOT_RUN")
            },
            "auxiliary_word_attempts": len(raw) * 8,
            "raw_completed_auxiliary_words": sum(
                len(r.get("raw_word_anchor_batch", ())) for r in raw
            ),
            "global_Python_NumPy_RNG_unchanged": unchanged,
            "peak_CPU_process_RSS_bytes": peak,
            "diagnostic_seconds": time.monotonic() - started,
        }
    )
    report["status"] = (
        "PASS"
        if len(records) == 8960
        and all(r["status"] == "PASS" for r in records)
        and unchanged
        and peak <= 2 * 1024**3
        else "PROBE_CAPTURE_INCOMPLETE"
    )
    write_json(output / "preparations.json", preps)
    write_json(output / "summary.json", report)


def run(folder, capture, analysis, protocol_path, output):
    output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads(protocol_path.read_text())
    started = time.monotonic()
    rows = [json.loads(x) for x in (capture / "rows.jsonl").read_text().splitlines()]
    inputs = [(r, t) for r in rows for t in r["transitions"]]
    records, preps = [], []
    stream = (output / "records.jsonl").open("x", buffering=1)
    batches = (output / "raw-batches.jsonl").open("x", buffering=1)
    before_py, before_np = random.getstate(), np.random.get_state()
    report = {
        "status": "RUNNING",
        "scope": "OLD16_PATH_CONDITIONAL_VARIANCE_DEVELOPMENT_ONLY",
        "new_model_forwards": 0,
        "new_decoder_trajectories": 0,
        "updates": 0,
        "execution_device": "cpu",
        "CUDA_used": False,
        "labels_previously_known": True,
    }

    def identity(row, t, mode, batch, j):
        return {
            "case": row["case"],
            "replica": row["replica"],
            "step": t["step"],
            "head": t["head"],
            "method": mode,
            "batch": batch,
            "within_batch": j,
            "draw_index": batch * 8 + j,
        }

    def emit(record):
        records.append(record)
        stream.write(json.dumps(serial(record), allow_nan=False) + "\n")

    def budget():
        left = 3600 - (time.monotonic() - started)
        if left <= 0:
            raise ResourceRefusal("3600s whole probe cap")
        return min(60, left)

    try:
        runtime = {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "tokenizers": importlib.metadata.version("tokenizers"),
        }
        if runtime != protocol["runtime"]:
            raise ValueError("runtime changed")
        if any(
            os.environ.get(k) != "4"
            for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        ):
            raise ValueError("four-thread environment required before NumPy import")
        for name, expected in protocol["source_sha256"].items():
            if sha(HERE / name) != expected:
                raise ValueError(f"source changed: {name}")
        pins = {
            "rows": capture / "rows.jsonl",
            "manifest": capture / "manifest.json",
            "labels": analysis / "known-labels-provenance.json",
            "rewards": analysis / "reward-rows.json",
            "features": Path(protocol["old_features_path"]),
        }
        if any(sha(p) != protocol["input_sha256"][key] for key, p in pins.items()):
            raise ValueError("old input changed")
        features = [json.loads(s) for s in pins["features"].read_text().splitlines()]
        if len(inputs) != 70 or len(rows) != 16 or len(features) != 70:
            raise ValueError("ALL16 old paths/70 states required")
        labels = json.loads(pins["labels"].read_text())["labels"]
        rewards = {
            (r["case"], r["replica"]): r["candidate_correct"]
            for r in json.loads(pins["rewards"].read_text())
        }
        manifest = json.loads(pins["manifest"].read_text())
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
        with bounded(budget()):
            tokenizer = tokenizer_from(folder)
            grammar = NumericSuffixJSON(emissions(folder), EOS, EOS)
            plan = PrefixFloatPlan(grammar)
        report["setup_diagnostic_seconds"] = time.monotonic() - started
        for ordinal, (row, t) in enumerate(inputs):
            prep = {"ordinal": ordinal, **identity(row, t, "preparation", -1, -1)}
            try:
                with bounded(budget()):
                    f = features[ordinal]
                    if any(
                        f[k] != source[k]
                        for k, source in (("case", row), ("replica", row), ("step", t), ("head", t))
                    ):
                        raise ValueError("old feature/state order differs")
                    name = f"heads/{t['head']}.npz"
                    if sha(capture / name) != manifest[name]["sha256"]:
                        raise ValueError("original head changed")
                    with np.load(capture / name) as packet:
                        p = bf16_probabilities(packet["logits_bf16"])
                        if packet["positions"].tolist() != t["queried_positions"]:
                            raise ValueError("original queried positions differ")
                    fixed, action = dict(t["fixed_before"]), tuple(map(tuple, t["action"]))
                    weights = assemble(
                        p, t["queried_positions"], fixed, t["prefix_extent"], VOCABULARY
                    )
                    planner = PrefixPlanner(plan, weights, fixed, row["root_feature"])
                    sampler = ConditionalFloatSampler(planner, action)
                    error = abs(sampler.statistics["log_probability"] - t["log_probability"])
                    if error > 1e-7:
                        raise AssertionError("old action likelihood changed")
                    certificate, known_text = certified_fixed_answer(grammar, fixed)
                    reward = rewards[row["case"], row["replica"]]
                    if (
                        certificate
                        and answer_equal(known_text, labels[row["case"]]["answer"]) != reward
                    ):
                        raise AssertionError(
                            "certified state reward differs from old completed path"
                        )
                    prep.update(
                        {
                            "status": "READY",
                            "tail_certificate": certificate,
                            "certified_fixed_json": known_text,
                            "old_final_reward": reward,
                            "baselines": f["baselines"],
                            "C_regular_actor": f["controls"][0],
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
                preps.append(prep)
                for mode in ("iid", "prefix_stratified"):
                    for batch in range(8):
                        for j in range(8):
                            emit(
                                {
                                    **identity(row, t, mode, batch, j),
                                    "status": "NOT_RUN",
                                    "reason": repr(error),
                                }
                            )
                continue
            for mode in ("iid", "prefix_stratified"):
                for batch in range(8):
                    capture_batch(
                        row,
                        t,
                        mode,
                        batch,
                        sampler,
                        planner,
                        grammar,
                        tokenizer,
                        labels,
                        f["features"],
                        fixed,
                        action,
                        emit,
                        batches,
                        budget,
                    )
            categories = (
                *sampler.class_cache.values(),
                *sampler.token_cache.values(),
                sampler.anchor,
            )
            peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
            prep.update(
                {
                    "integer_CDF_payload_bytes": sampler.cache_payload_bytes(),
                    "max_ticket_bits": max(c.total.bit_length() for c in categories),
                    "peak_RSS_bytes": peak,
                }
            )
            preps.append(prep)
            if peak > 2 * 1024**3:
                raise ResourceRefusal("2GiB whole-process CPU RSS")
            print(
                json.dumps({"state": ordinal, "records": len(records), "status": prep["status"]}),
                flush=True,
            )
    except Exception as error:
        report["global_exception"] = repr(error)
    finally:
        finalize(
            inputs,
            records,
            preps,
            emit,
            stream,
            batches,
            report,
            before_py,
            before_np,
            started,
            output,
        )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("model-dir", "capture", "analysis", "protocol", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.model_dir, a.capture, a.analysis, a.protocol, a.output)
