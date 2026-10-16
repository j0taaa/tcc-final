"""Full-V complete-API correctness before any first90 timings; synthetic weights."""

import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import torch

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .development import API, validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    n = 50258
    ids = tuple(t for t in range(n) if t not in (0, 1, 50256))
    classes = ((0,), (1,), ids, (50256,))
    layers = ((((0, (0, 1)),),), (((0, (3,)),),))
    canvas = (None, 50256)
    emissions = [None] * n
    emissions[0] = b"0"
    emissions[1] = b"[]"
    adapter = CompositionalByteLevelAdapter(tuple(emissions))
    protocol = json.loads(Path(__file__).with_name("development-protocol-v9.json").read_text())
    count = 0
    for first in (0.55, 0.2):
        rows = np.zeros((2, n), dtype=np.float64)
        rows[0, 0] = first
        rows[0, 1] = 0.4
        rows[0, 50256] = 1 - first - 0.4
        rows[1, 50256] = 1
        mass = F(first) + F(0.4)
        weights = torch.from_numpy(rows).cuda()
        for method in ("ticket_scalar", "interval_exact"):
            api = API(method, classes, layers, (True,), canvas, 51, protocol)
            for _ in range(2):
                result = api.query(weights)
                validate(result, canvas, rows, adapter, mass)
                count += 1
    result = dict(
        status="PASS",
        complete_api_checks=count,
        full_original_vocabulary=n,
        new_model_forwards=0,
        speed_claim=False,
        goal_met=False,
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*development.py")
        },
    )
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
