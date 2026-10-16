"""Independent exact count-ceiling and preconversion guard checks (opt-in CUDA)."""

import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import torch
import triton as tr
import triton.language as tl

from .gpu_tickets import _counts


@tr.jit
def _check(numerators, denominators, cdf, totals, bad, B: tl.constexpr):
    row, lane = tl.program_id(0), tl.arange(0, B)
    n, d = tl.load(numerators + row * B + lane), tl.load(denominators + row * B + lane)
    prefixes, total, invalid = _counts(n, d, tl.full((B,), True, tl.int1))
    tl.store(cdf + row * B + lane, prefixes)
    tl.store(totals + row, total)
    tl.store(bad + row, invalid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(51)
    numerators = []
    denominators = []
    expected = []
    for _ in range(128):
        v = rng.random(8)
        v /= v.sum()
        numerators.append(v)
        denominators.append(np.ones(8))
        expected.append(False)
    for k in (0, 1, 2, 127, (1 << 24) - 1, (1 << 40) - 1):
        value = k / (1 << 40)
        numerators.append(
            [value, np.nextafter(value, 0), np.nextafter(value, np.inf), 0, 0, 0, 0, 0]
        )
        denominators.append(np.full(8, 8.0))
        expected.append(False)
    special = [
        (0.0, 0.0, False),
        (1.0, 0.0, True),
        (np.finfo(float).max, np.finfo(float).tiny, True),
        (-1.0, 1.0, True),
        (0.0, -1.0, True),
        (0.0, np.inf, True),
        (1.0, np.nan, True),
        (np.nextafter(0.0, 1.0), 1.0, False),
    ]
    for n, d, bad in special:
        numerators.append([n] + [0] * 7)
        denominators.append([d] + [1] * 7)
        expected.append(bad)
    nums, dens = np.array(numerators, dtype=np.float64), np.array(denominators, dtype=np.float64)
    a, b = torch.from_numpy(nums).cuda(), torch.from_numpy(dens).cuda()
    cdf = torch.empty(nums.shape, dtype=torch.long, device="cuda")
    totals = torch.empty(len(nums), dtype=torch.long, device="cuda")
    flags = torch.empty(len(nums), dtype=torch.bool, device="cuda")
    _check[(len(nums),)](a, b, cdf, totals, flags, 8)
    found, total, invalid = cdf.cpu().tolist(), totals.cpu().tolist(), flags.cpu().tolist()
    checked = 0
    for i, wanted in enumerate(expected):
        if invalid[i] != wanted:
            raise AssertionError(f"wrong count guard row{i}: {invalid[i]} versus{wanted}")
        if total[i] != found[i][-1]:
            raise AssertionError("integer prefix total changed")
        if wanted:
            continue
        for j in range(8):
            count = found[i][j] - (found[i][j - 1] if j else 0)
            ratio = F(float(nums[i, j])) / F(float(dens[i, j])) if dens[i, j] else F()
            if count < 1 or count < (1 << 40) * ratio:
                raise AssertionError("executed count underestimates exact dyadic ratio")
            checked += 1
    result = dict(
        status="PASS",
        categorical_rows=len(nums),
        upward_count_checks=checked,
        guard_refusals=sum(expected),
        new_model_forwards=0,
        speed_claim=False,
        goal_met=False,
        torch=torch.__version__,
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), Path(__file__).with_name("gpu_tickets.py"))
        },
    )
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
