"""Optional independent CPU/Torch checks before real OLD-head functionality."""

import argparse
import json
from pathlib import Path

import numpy as np

from .consumer_resource import serial, write_json
from .llada_suffix_v10 import NumericSuffixJSON
from .numeric_proxy import IntegerProxy
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_torch import PrefixTorch
from .proxy_floating import ProxyPlanner
from .proxy_torch import torch_control


def differences(actual, expected):
    if actual["status"] != expected["status"]:
        raise AssertionError("symbolic and Torch support disagree")
    pairs = [("posterior", actual["posterior"], expected["posterior"])]
    if expected["log_prior"] is not None:
        pairs.append(("log_prior", actual["log_prior"], expected["log_prior"]))
    pairs.extend(
        (k, actual["correction"][k], expected["correction"][k]) for k in expected["correction"]
    )
    result = {}
    for key, a, e in pairs:
        delta = np.abs(np.asarray(a) - np.asarray(e))
        result[key] = float(delta.max())
        relative = float((delta / np.maximum(1, np.abs(e))).max())
        if result[key] > 1e-7 or relative > 1e-7:
            raise AssertionError(f"{key} proxy tolerance: {result[key]}/{relative}")
    return result


def run(output):
    import torch

    output.mkdir(exist_ok=False, parents=True)
    torch.set_num_threads(4)
    emissions = (b"1}", b"1.0}", b"1e0}", b"2}", b" ", b"", b"", b"<EOT>")
    broad = NumericSuffixJSON(emissions, 7, 7)
    plan = PrefixFloatPlan(broad)
    records = []
    for index, (fixed, action, digits) in enumerate(
        (
            ({}, ((0, 0),), "1"),
            ({}, ((0, 3),), "1"),
            ({0: 3}, ((2, 7),), "1"),
            ({2: 7}, ((0, 1),), "1"),
            ({}, ((0, 0), (2, 7)), "1"),
            ({}, ((0, 0),), "5"),
        )
    ):
        rows = np.asarray([[1 + (i + v) % 5 for v in range(8)] for i in range(3)], dtype=float)
        rows /= rows.sum(axis=1, keepdims=True)
        for i, v in fixed.items():
            rows[i] = 0
            rows[i, v] = 1
        narrow = PrefixFloatPlan(IntegerProxy(emissions, 7, 7, digits))
        for feature in (0.0, -1.3):
            base = PrefixPlanner(plan, rows, fixed, feature)
            expected = ProxyPlanner(base, narrow).statistics(action)
            backend, proxy = PrefixTorch(plan, "cpu"), PrefixTorch(narrow, "cpu")
            weights = torch.as_tensor(rows)
            bs = backend.statistics(weights, fixed, feature, action)
            actual = torch_control(
                proxy,
                weights,
                fixed,
                feature,
                action,
                backend.partition(weights, max(fixed, default=-1)),
                bs,
            )
            records.append(
                {
                    "case": index,
                    "feature": feature,
                    "status": actual["status"],
                    "errors": differences(actual, expected),
                }
            )
    write_json(output / "records.json", serial(records))
    write_json(
        output / "summary.json",
        {
            "status": "PASS",
            "CPU_autodiff_cases": len(records),
            "new_model_forwards": 0,
            "updates": 0,
        },
    )
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    run(ap.parse_args().output)
