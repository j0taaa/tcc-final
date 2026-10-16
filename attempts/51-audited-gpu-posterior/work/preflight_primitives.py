"""Exact Fraction checks of executed directed GPU primitives; not a speed test."""

import argparse
import hashlib
import json
import math
import subprocess
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import torch
import triton

from .gpu_primitives import directed_binary, directed_cast, multiply_high


def check_bracket(lower, exact, upper):
    if math.isnan(lower) or math.isnan(upper):
        raise AssertionError("NaN returned for finite nonnegative test operands")
    if math.isinf(lower) or F(lower) > exact or (math.isfinite(upper) and F(upper) < exact):
        raise AssertionError(f"invalid enclosure: {lower} <= {exact} <= {upper}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(2026101651)
    torch.set_flush_denormal(False)
    checks, infinite_uppers, subnormal_results = 0, 0, 0
    records = []
    for dtype in (np.float32, np.float64):
        integer = np.uint32 if dtype == np.float32 else np.uint64
        mask = (1 << (31 if dtype == np.float32 else 63)) - 1
        raw = rng.integers(0, mask, 2048, dtype=integer)
        values = raw.view(dtype)
        values = values[np.isfinite(values)]
        special = np.array(
            [
                0,
                np.nextafter(dtype(0), dtype(1)),
                np.finfo(dtype).tiny,
                np.nextafter(dtype(1), dtype(0)),
                1,
                np.nextafter(dtype(1), dtype(2)),
                np.finfo(dtype).max,
            ],
            dtype=dtype,
        )
        a = np.concatenate([np.repeat(special, len(special)), values])
        b = np.concatenate([np.tile(special, len(special)), np.roll(values, 1)])
        for op in ("add", "mul", "div"):
            valid = b != 0 if op == "div" else np.ones(len(b), dtype=bool)
            x, y = a[valid], b[valid]
            lower, upper = directed_binary(
                torch.from_numpy(x).cuda(), torch.from_numpy(y).cuda(), op
            )
            lower, upper = lower.cpu().numpy(), upper.cpu().numpy()
            for xv, yv, lo, hi in zip(x, y, lower, upper, strict=True):
                xf, yf = F(float(xv)), F(float(yv))
                exact = xf + yf if op == "add" else xf * yf if op == "mul" else xf / yf
                check_bracket(float(lo), exact, float(hi))
                checks += 1
                infinite_uppers += int(math.isinf(float(hi)))
                subnormal_results += int(0 < float(hi) < np.finfo(dtype).tiny)
            records.append(dict(dtype=str(dtype), op=op, checks=len(x)))
        if dtype == np.float64:
            lower, upper = directed_cast(torch.from_numpy(a).cuda())
            for xv, lo, hi in zip(a, lower.cpu().tolist(), upper.cpu().tolist(), strict=True):
                check_bracket(lo, F(float(xv)), hi)
                checks += 1
                infinite_uppers += int(math.isinf(hi))
                subnormal_results += int(0 < hi < np.finfo(np.float32).tiny)
            records.append(dict(dtype="binary64_to_binary32", checks=len(a)))
    x = rng.integers(0, np.iinfo(np.uint64).max, 4096, dtype=np.uint64)
    y = rng.integers(1, 1 << 41, len(x), dtype=np.uint64)
    x[:4] = [0, 1, (1 << 64) - 1, 1 << 63]
    y[:4] = [1, (1 << 41), (1 << 41) - 1, (1 << 41)]
    observed = multiply_high(torch.from_numpy(x).cuda(), torch.from_numpy(y).cuda()).cpu().tolist()
    for a, b, got in zip(x.tolist(), y.tolist(), observed, strict=True):
        if got != a * b >> 64:
            raise AssertionError("executed high64 differs from exact integer product")
        checks += 1
    if not subnormal_results or not infinite_uppers:
        raise AssertionError("extreme value coverage was not exercised")
    torch.cuda.synchronize()
    result = dict(
        status="PASS",
        scope="primitive enclosures/finite ticket arithmetic only, no timing",
        total_exact_checks=checks,
        multiply_high_checks=len(x),
        infinite_uppers=infinite_uppers,
        positive_subnormal_upper_results=subnormal_results,
        operations=records,
        torch=torch.__version__,
        triton=triton.__version__,
        cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(),
        new_model_forwards=0,
        goal_met=False,
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*primitives.py")
        },
    )
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
