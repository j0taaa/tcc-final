"""Exploratory ALL16 OLD-path diagnostic, not a fresh-data variance gate."""

import argparse
import itertools
import json
import subprocess
import time
from decimal import Decimal
from pathlib import Path

import numpy as np

from .actor_coordinates import actor_vector, paired_trace, state_features
from .consumer_resource import HERE, bounded, serial, sha, write_json
from .llada_tokenizer_v10 import EOS, VOCABULARY
from .prefix_runtime import assemble
from .two_stage import bf16_probabilities

METHODS = (
    "full_triple",
    "anchor_integrated",
    "class_integrated",
    "length_integrated",
    "combined_partial",
    "known_anchor",
    "collapsed",
)
BASELINES = ("zero", "half", "proxy_state", "proxy_root")
COEFFICIENTS = tuple(itertools.product((0.0, 0.5, 1.0), repeat=3))


def estimate(path, method, baseline, coefficients):
    score = path["scores"][method]
    value = path["reward"] * score - path["baseline_scores"][method][baseline]
    return value - np.asarray(coefficients) @ path["controls"]


def run(capture, replay, analysis, protocol_path, output):
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    protocol = json.loads(protocol_path.read_text())
    summary = {
        "status": "RUNNING",
        "scope": "EXPLORATORY_KNOWN16_PATHS_ONLY",
        "new_model_forwards": 0,
        "new_samples": 0,
        "updates": 0,
        "independent_confirmation": False,
        "competitive_cost_claim": False,
    }
    processed = []
    try:
        if np.__version__ != protocol["numpy"]:
            raise ValueError("NumPy version changed")
        for name, expected in protocol["source_sha256"].items():
            if sha(HERE / name) != expected:
                raise ValueError(f"source changed: {name}")
        files = {
            "rows": capture / "rows.jsonl",
            "head_manifest": capture / "manifest.json",
            "proxy_records": replay / "records.jsonl",
            "rewards": analysis / "reward-rows.json",
        }
        if any(sha(p) != protocol["input_sha256"][k] for k, p in files.items()):
            raise ValueError("frozen original input changed")
        rows = [json.loads(x) for x in files["rows"].read_text().splitlines()]
        proxy = [json.loads(x) for x in files["proxy_records"].read_text().splitlines()]
        manifest = json.loads(files["head_manifest"].read_text())
        rewards = {
            (r["case"], r["replica"]): r["candidate_correct"]
            for r in json.loads(files["rewards"].read_text())
        }
        if (
            len(rows) != 16
            or len(proxy) != 70
            or len(rewards) != 16
            or sum(len(r["transitions"]) for r in rows) != 70
        ):
            raise ValueError("ALL16 paths/70 transitions required")
        write_json(output / "protocol.json", protocol)
        write_json(
            output / "provenance.json",
            {
                "producer_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "numpy": np.__version__,
                "scientific_scope": summary["scope"],
            },
        )
        roots, paths, ordinal = {}, [], 0
        with (output / "state-features.jsonl").open("x", buffering=1) as stream:
            for row in rows:
                path = {
                    "case": row["case"],
                    "replica": row["replica"],
                    "reward": float(rewards[row["case"], row["replica"]]),
                    "scores": {m: np.zeros(9) for m in METHODS},
                    "baseline_scores": {m: np.zeros((4, 9)) for m in METHODS},
                    "controls": np.zeros((3, 9)),
                }
                if row["status"] != "COMPLETE":
                    raise ValueError("a failed original path may not be dropped")
                for transition in row["transitions"]:
                    with bounded(min(60, max(0.001, 1200 - (time.monotonic() - started)))):
                        if time.monotonic() - started >= 1200:
                            raise ValueError("1200s diagnostic cap")
                        old = proxy[ordinal]
                        for key, source in (
                            ("case", row),
                            ("replica", row),
                            ("step", transition),
                            ("head", transition),
                        ):
                            if old[key] != source[key] or old["status"] != "PASS":
                                raise ValueError("proxy/state order differs")
                        name = f"heads/{transition['head']}.npz"
                        if sha(capture / name) != manifest[name]["sha256"]:
                            raise ValueError("original BF16 head changed")
                        with np.load(capture / name) as packet:
                            bits = packet["logits_bf16"]
                            probabilities = bf16_probabilities(bits)
                            logits = (
                                (bits.astype(np.uint32) << 16).view(np.float32).astype(np.float64)
                            )
                            reference_h = (
                                -np.log(np.exp(logits - logits.max(1, keepdims=True)).sum(1)) / 10
                            )
                        fixed = dict(transition["fixed_before"])
                        weights = assemble(
                            probabilities,
                            transition["queried_positions"],
                            fixed,
                            transition["prefix_extent"],
                            VOCABULARY,
                        )
                        features = state_features(weights, fixed, EOS)
                        error = float(
                            np.max(
                                np.abs(features["h"][transition["queried_positions"]] - reference_h)
                            )
                        )
                        if error > 1e-12:
                            raise ValueError("independent original confidence feature differs")
                        p = old["proxy"]["log_prior"]
                        prior = 0.0 if p is None else float(np.exp(p))
                        if transition["step"] == 0:
                            if row["case"] in roots and abs(roots[row["case"]] - prior) > 1e-12:
                                raise ValueError("paired root feature differs")
                            roots[row["case"]] = prior
                        baselines = np.asarray((0.0, 0.5, prior, roots[row["case"]]))
                        vectors = {
                            m: actor_vector(transition["scores"][m], features) for m in METHODS
                        }
                        controls = np.stack(
                            (
                                actor_vector(old["proxy"]["correction"], features),
                                old["proposal_semantic_correct"] * vectors["full_triple"],
                                old["proposal_semantic_correct"] * vectors["anchor_integrated"],
                            )
                        )
                        for m in METHODS:
                            path["scores"][m] += vectors[m]
                            path["baseline_scores"][m] += baselines[:, None] * vectors[m]
                        path["controls"] += controls
                        feature_record = {
                            "ordinal": ordinal,
                            "case": row["case"],
                            "replica": row["replica"],
                            "step": transition["step"],
                            "head": transition["head"],
                            "features": serial(features),
                            "baselines": serial(baselines),
                            "controls": serial(controls),
                            "independent_feature_error": error,
                        }
                        stream.write(json.dumps(feature_record, allow_nan=False) + "\n")
                        processed.append(feature_record)
                        ordinal += 1
                target = proxy[ordinal - 1]["target_digits"]
                independent_reward = json.loads(
                    row["json"], parse_int=Decimal, parse_float=Decimal
                )["answer"] == Decimal(target)
                if independent_reward != bool(path["reward"]):
                    raise ValueError("independent final reward differs")
                paths.append(path)
        write_json(output / "path-sufficient-statistics.json", serial(paths))
        indexed = {(p["case"], p["replica"]): p for p in paths}
        if set(indexed) != set(itertools.product(range(8), range(2))):
            raise ValueError("all eight original paired questions required")
        table, rloo = [], []
        for method, baseline, coefficients in itertools.product(METHODS, range(4), COEFFICIENTS):
            gradients = {
                (q, r): estimate(indexed[q, r], method, baseline, coefficients) for q, r in indexed
            }
            by_question = {q: paired_trace(gradients[q, 0], gradients[q, 1]) for q in range(8)}
            table.append(
                {
                    "method": method,
                    "baseline": BASELINES[baseline],
                    "coefficients_C_Wfull_Wanchor": coefficients,
                    "individual_gradients": [
                        {"case": q, "replica": r, "gradient": serial(g)}
                        for (q, r), g in gradients.items()
                    ],
                    "paired_single_path_trace_by_question": by_question,
                    "equal8_question_mean_trace_estimate": {
                        block: sum(d[block] for d in by_question.values()) / 64
                        for block in ("total", "gate", "anchor", "confidence")
                    },
                }
            )
        for method, coefficients in itertools.product(METHODS, COEFFICIENTS):
            groups = []
            for q in range(8):
                p, z = indexed[q, 0], indexed[q, 1]
                gradient = (
                    (p["reward"] - z["reward"]) * (p["scores"][method] - z["scores"][method])
                    - np.asarray(coefficients) @ (p["controls"] + z["controls"])
                ) / 2
                groups.append({"case": q, "group_gradient": serial(gradient)})
            rloo.append(
                {
                    "method": method,
                    "coefficients_C_Wfull_Wanchor": coefficients,
                    "independent_groups_per_question": 1,
                    "variance": None,
                    "groups": groups,
                }
            )
        write_json(output / "ALL756-fixed-configurations.json", serial(table))
        write_json(output / "RLOO-one-group-variance-unavailable.json", serial(rloo))
        summary.update(
            {
                "status": "PASS",
                "paths": len(paths),
                "transitions": ordinal,
                "fixed_configurations": len(table),
                "RLOO_variance": None,
            }
        )
    except Exception as error:
        summary.update(
            {"status": "ERROR", "exception": repr(error), "processed_transitions": len(processed)}
        )
    summary["diagnostic_seconds"] = time.monotonic() - started
    write_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("capture", "replay", "analysis", "protocol", "output"):
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    run(a.capture, a.replay, a.analysis, a.protocol, a.output)
