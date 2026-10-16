"""SYNTHETIC full-V score support only; no pretrained/old-head data."""

import argparse
import json
import random
import resource
from pathlib import Path

import numpy as np

from .actor_coordinates import state_features
from .length_readout import NumericSuffix
from .llada_tokenizer_v10 import EOS, VOCABULARY, emissions, verify_files
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .query_support import support


def run(model_dir, output):
    output.mkdir(parents=True, exist_ok=False)
    before_py, before_np = random.getstate(), np.random.get_state()
    verify_files(model_dir)
    table = emissions(model_dir)
    plan = PrefixFloatPlan(NumericSuffix(table, EOS, EOS))
    one = table.index(b"1")
    results = []
    for n, fixed in ((64, {}), (13, {12: EOS})):
        weights = np.full((n, VOCABULARY), 1 / VOCABULARY)
        for i, v in fixed.items():
            weights[i] = 0
            weights[i, v] = 1
        planner = PrefixPlanner(plan, weights, fixed, 0.0)
        value = support(planner, ((0, one),), state_features(weights, fixed, EOS))
        if fixed:
            assert [r["length"] for r in value["lengths"]] == [13]
        results.append({"SYNTHETIC_extent": n, "fixed": fixed, "readout": value})
    after = np.random.get_state()
    unchanged = before_py == random.getstate() and all(
        np.array_equal(a, b) for a, b in zip(before_np, after, strict=True)
    )
    assert unchanged
    report = {
        "status": "PASS",
        "SYNTHETIC_states": 2,
        "pretrained_heads": 0,
        "old_real_head_queries": 0,
        "new_model_forwards": 0,
        "new_auxiliary_words": 0,
        "CUDA_used": False,
        "global_Python_NumPy_RNG_unchanged": unchanged,
        "classes": len(plan.members),
        "peak_CPU_process_RSS_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "results": results,
    }
    assert report["peak_CPU_process_RSS_bytes"] <= 2 * 1024**3
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    run(a.model_dir, a.output)
