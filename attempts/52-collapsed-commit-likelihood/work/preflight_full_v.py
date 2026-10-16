"""Synthetic full-V consumer check. No pretrained model is loaded or evaluated."""

import argparse
import json
from pathlib import Path

import numpy as np

from .floating import FloatPlan, TorchPlan
from .numeric_json import NumericJSON
from .preflight_floating import compare
from .test_numeric_json import independent_accepts
from .tokenizer_audit import emissions


def run(folder, output):
    import torch

    output.mkdir(parents=True, exist_ok=False)
    language = NumericJSON(emissions(folder), 151645, 151643)
    plan = FloatPlan(language)
    ids = np.arange(151936)
    positions = np.arange(32)[:, None]
    weights = ((ids % 17 + 1)[None] * (positions % 7 + 1) + ((ids // 17) % 5)[None] + 1).astype(
        np.float64
    )
    weights /= weights.sum(axis=1, keepdims=True)
    rng = np.random.default_rng(520402)
    torch.cuda.reset_peak_memory_stats()
    baseline = torch.cuda.memory_allocated()
    backend = TorchPlan(plan)
    device_weights = torch.as_tensor(weights, device="cuda")
    rows = []
    with (output / "rows.jsonl").open("x") as stream:
        for case in range(3):
            word = plan.sample(weights, rng)
            anchor = int(rng.integers(32))
            action = tuple(
                (i, v)
                for i, v in enumerate(word)
                if i == anchor or case == 2 or (case == 1 and i % 3 == 0)
            )
            row = {"case": case, "word": word, "action": action, "constructed_action_check": True}
            try:
                if not language.accepts(word) or not independent_accepts(language, word):
                    raise AssertionError("whole-V original word failed independent JSON parser")
                expected = plan.action_statistics(weights, action)
                actual = backend.action_statistics(device_weights, action)
                row.update({"errors": compare(actual, expected), "status": "PASS"})
            except Exception as error:
                row.update({"status": "ERROR", "exception": repr(error)})
                stream.write(json.dumps(row) + "\n")
                stream.flush()
                raise
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            rows.append(row)
    peak = torch.cuda.max_memory_allocated() - baseline
    report = {
        "status": "PASS" if peak <= 2 * 1024**3 else "RESOURCE_REFUSAL",
        "records": len(rows),
        "original_ids": 151936,
        "positions": 32,
        "classes": plan.class_count,
        "max_workspace_allocated_bytes": peak,
        "max_error": {k: max(r["errors"][k] for r in rows) for k in rows[0]["errors"]},
        "pretrained_model_forwards": 0,
        "competitive_timing": False,
        "native_rng_exactness_claimed": False,
    }
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    if peak > 2 * 1024**3:
        raise ValueError("whole-V sampler workspace exceeds the frozen2GiB cap")
    print(json.dumps(report))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.tokenizer_dir, args.output)
