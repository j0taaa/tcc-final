"""Opt-in independent rational/NumPy/Torch CPU/CUDA prefix-score checks."""

import argparse
import json
from pathlib import Path

from .prefix_floating import PrefixPlanner
from .prefix_torch import PrefixTorch
from .preflight_floating import compare
from .test_prefix_floating import cases


def run(output):
    import torch

    output.mkdir(parents=True, exist_ok=False)
    rows = []
    with (output / "rows.jsonl").open("x", buffering=1) as stream:
        for case, (plan, weights, fixed, feature, action, expected) in enumerate(cases()):
            for device in ("numpy", "cpu", "cuda"):
                row = {
                    "case": case,
                    "device": device,
                    "fixed": fixed,
                    "feature": feature,
                    "action": action,
                }
                try:
                    if device == "numpy":
                        actual = PrefixPlanner(plan, weights, fixed, feature).statistics(action)
                    else:
                        actual = PrefixTorch(plan, device).statistics(
                            torch.as_tensor(weights, device=device), fixed, feature, action
                        )
                    row.update({"errors": compare(actual, expected), "status": "PASS"})
                except Exception as error:
                    row.update({"status": "ERROR", "exception": repr(error)})
                    stream.write(json.dumps(row) + "\n")
                    raise
                stream.write(json.dumps(row) + "\n")
                rows.append(row)
    report = {
        "status": "PASS",
        "records": len(rows),
        "new_model_forwards": 0,
        "new_samples_real_heads": 0,
        "native_rng_exactness_claimed": False,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "maximum_absolute_error": {k: max(r["errors"][k] for r in rows) for k in rows[0]["errors"]},
    }
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    run(ap.parse_args().output)
