"""Synthetic original-V prefix/partial-canvas GPU check; no model loaded."""

import argparse
import json
from pathlib import Path

import numpy as np

from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_torch import PrefixTorch
from .preflight_floating import compare
from .stopping import StoppedNumericJSON
from .tokenizer_audit import emissions
from .two_stage import json_text


def run(folder, output):
    import torch

    output.mkdir(parents=True, exist_ok=False)
    plan = PrefixFloatPlan(StoppedNumericJSON(emissions(folder), 151645, 151643))
    ids = np.arange(151936)
    base = (
        (ids % 17 + 1)[None] * (np.arange(32) % 7 + 1)[:, None] + ((ids // 17) % 5)[None] + 1
    ).astype(np.float64)
    base /= base.sum(axis=1, keepdims=True)
    feature = plan.root_feature(base)
    rng = np.random.default_rng(52082)
    original = plan.sample_prefix(base, rng)
    settings = [
        (32, {}),
        (len(original), {0: original[0], len(original) - 1: original[-1]}),
        (32, {len(original) - 2: original[-2]}),
    ]
    backend = PrefixTorch(plan)
    torch.cuda.synchronize()
    baseline = torch.cuda.memory_allocated()
    torch.cuda.reset_peak_memory_stats()
    rows = []
    with (output / "rows.jsonl").open("x", buffering=1) as stream:
        for case, (length, fixed) in enumerate(settings):
            row = {"case": case, "length": length, "fixed": fixed, "constructed_action_check": True}
            try:
                weights = base[:length].copy()
                for i, v in fixed.items():
                    weights[i] = 0
                    weights[i, v] = 1
                planner = PrefixPlanner(plan, weights, fixed, feature["alpha"])
                word = plan.sample_prefix(weights, rng, minimum=max(fixed, default=-1))
                row["word"] = word
                row["json"] = json_text(plan.language, word)
                eligible = [i for i in range(len(word)) if i not in fixed]
                anchor = int(rng.choice(eligible))
                action = tuple(
                    (i, word[i]) for i in eligible if i == anchor or (case == 2 and i % 2 == 0)
                )
                row["action"] = action
                expected = planner.statistics(action)
                actual = backend.statistics(
                    torch.as_tensor(weights, device="cuda"), fixed, feature["alpha"], action
                )
                row.update({"status": "PASS", "errors": compare(actual, expected)})
            except Exception as error:
                row.update({"status": "ERROR", "exception": repr(error)})
                stream.write(json.dumps(row) + "\n")
                raise
            stream.write(json.dumps(row) + "\n")
            rows.append(row)
    peak = torch.cuda.max_memory_allocated() - baseline
    report = {
        "status": "PASS" if peak <= 2 * 1024**3 else "RESOURCE_REFUSAL",
        "records": len(rows),
        "original_ids": 151936,
        "root_positions": 32,
        "classes": plan.class_count,
        "max_gpu_workspace_bytes": peak,
        "new_model_forwards": 0,
        "competitive_timing": False,
        "maximum_absolute_error": {k: max(r["errors"][k] for r in rows) for k in rows[0]["errors"]},
        "root_feature": feature,
    }
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "root_feature"}))
    if report["status"] != "PASS":
        raise ValueError("full-V prefix workspace cap")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.tokenizer_dir, args.output)
