"""Optional CPU/CUDA suffix checks, rational and synthetic full-V; no model."""

import argparse
import json
from pathlib import Path

import numpy as np

from .llada_suffix_v10 import NumericSuffixJSON, full_text
from .llada_tokenizer_v10 import EOS, VOCABULARY, emissions
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_runtime import assemble
from .prefix_torch import PrefixTorch
from .preflight_floating import compare
from .test_llada_suffix_v10 import cases


def run(model_dir, output):
    import torch

    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(4)
    records = []
    with (output / "rational.jsonl").open("x") as stream:
        for index, (plan, planner, fixed, action, expected) in enumerate(cases()):
            for device in ("numpy", "cpu", "cuda"):
                actual = (
                    planner.statistics(action)
                    if device == "numpy"
                    else PrefixTorch(plan, device).statistics(
                        torch.as_tensor(planner.weights, device=device), fixed, 0, action
                    )
                )
                row = {"case": index, "device": device, "errors": compare(actual, expected)}
                records.append(row)
                stream.write(json.dumps(row) + "\n")
    grammar = NumericSuffixJSON(emissions(model_dir), EOS, EOS)
    plan = PrefixFloatPlan(grammar)
    ids = {b: i for i, b in enumerate(grammar.emissions) if b in (b"0", b" ", b"}")}
    if set(ids) != {b"0", b" ", b"}"}:
        raise ValueError("explicit original-ID suffix fixture tokens unavailable")
    word = [ids[b"0"], *([ids[b" "]] * 61), ids[b"}"], EOS]
    word[40] = 126349  # Officially audited empty ORIGINAL ID, not an omitted token.
    full_text(grammar, word)
    rng = np.random.default_rng(52100)
    weights = rng.uniform(0.25, 1.25, (64, VOCABULARY))
    weights /= weights.sum(axis=1, keepdims=True)
    feature = plan.root_feature(weights)
    backend = PrefixTorch(plan)
    torch.cuda.reset_peak_memory_stats()
    full_records = []
    configs = (
        ({}, {0: word[0], 62: word[62], 63: EOS}, 64),
        ({0: word[0], 40: 126349, 63: EOS}, {1: word[1], 62: word[62]}, 64),
        ({0: word[0], 3: EOS}, {1: ids[b" "], 2: ids[b"}"]}, 4),
    )
    for index, (fixed, retained, length) in enumerate(configs):
        active = tuple(i for i in range(length) if i not in fixed)
        rows = assemble(weights[list(active)], active, fixed, length, VOCABULARY)
        planner = PrefixPlanner(plan, rows, fixed, feature["alpha"])
        action = tuple(sorted(retained.items()))
        expected = planner.statistics(action)
        actual = backend.statistics(
            torch.as_tensor(rows, device="cuda"), fixed, feature["alpha"], action
        )
        full_records.append(
            {
                "case": index,
                "fixed": sorted(fixed.items()),
                "action": action,
                "errors": compare(actual, expected),
            }
        )
    peak = torch.cuda.max_memory_allocated()
    if peak > 2 * 1024**3:
        raise ValueError("synthetic sampler GPU allocation exceeds2GiB")
    report = {
        "status": "PASS",
        "rational_records": len(records),
        "full_v_records": len(full_records),
        "original_vocabulary": VOCABULARY,
        "root_positions": 64,
        "classes": plan.class_count,
        "root_feature": feature,
        "full_v_peak_gpu_allocated_bytes": peak,
        "rational_maximum_errors": {
            k: max(r["errors"][k] for r in records) for k in records[0]["errors"]
        },
        "full_v_maximum_errors": {
            k: max(r["errors"][k] for r in full_records) for k in full_records[0]["errors"]
        },
        "new_model_forwards": 0,
        "model_constructed": False,
        "competitive_timing": False,
    }
    (output / "full-v.json").write_text(json.dumps(full_records, indent=2) + "\n")
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "root_feature"}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.model_dir, args.output)
