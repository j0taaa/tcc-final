"""Opt-in independent mass audit of BOTH exact GPU reductions; no timings."""

import argparse
import hashlib
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path
from random import Random

import numpy as np
import torch

from .block_stats import Partition, numpy_stats
from .gpu_stats import DevicePartition, torch_stats, triton_stats


def original_check(matrix, partition, stats):
    checks = 0
    for values, totals, low in zip(matrix, stats.totals, stats.minimum_exponents, strict=True):
        unit = Fraction(2) ** (low - 1074)
        for block, total in zip(partition.blocks, totals, strict=True):
            if total * unit != sum((Fraction(float(values[t])) for t in block), Fraction()):
                raise AssertionError("exact original block mass changed")
            checks += 1
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = dict(
        producer_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        torch=torch.__version__,
        device=torch.cuda.get_device_name(0),
        seed=2026101129,
        scope="Correctness, not timing or novelty",
        rows=[],
        complete=False,
    )
    with args.output.open("x") as log:
        rng = Random(result["seed"])
        try:
            for v in (1, 7, 513, 1025, 5000):
                matrix = np.array(
                    [
                        [
                            math.ldexp(float(rng.randrange(1, 1 << 52)), rng.randrange(-1074, 960))
                            for _ in range(v)
                        ]
                        for _ in range(3)
                    ],
                    dtype=np.float64,
                )
                if v > 1:
                    matrix[0, 0], matrix[1, 0], matrix[2, 0] = 0.0, -0.0, np.nextafter(0.0, 1.0)
                    matrix[0, 1], matrix[1, 1] = np.nextafter(0.0, 1.0), np.finfo(np.float64).max
                q = torch.tensor(matrix, dtype=torch.float64, device="cuda")
                for size in (1, 127, 512, 1024):
                    p = Partition([i % 5 for i in range(v)], 5, size)
                    mapping = DevicePartition(p, "cuda:0")
                    reference = numpy_stats(matrix, p)
                    for method in (triton_stats, torch_stats):
                        stats = method(q, mapping)
                        if (
                            stats.minimum_exponents != reference.minimum_exponents
                            or stats.totals != reference.totals
                        ):
                            raise AssertionError(f"{method.__name__}: differs from vector control")
                        checks = original_check(matrix, p, stats)
                        result["rows"].append(
                            dict(
                                v=v,
                                block_size=size,
                                method=method.__name__,
                                exact_checks=checks,
                                status="complete",
                            )
                        )
            for bad in (float("nan"), float("inf"), -float("inf"), -1.0, -np.nextafter(0.0, 1.0)):
                q = torch.tensor([[1.0, bad]], dtype=torch.float64, device="cuda")
                mapping = DevicePartition(Partition([0, 1], 2), "cuda:0")
                for method in (triton_stats, torch_stats):
                    try:
                        method(q, mapping)
                    except ValueError:
                        result["rows"].append(
                            dict(method=method.__name__, status="invalid_refused", input=repr(bad))
                        )
                    else:
                        raise AssertionError("invalid weight was not refused")
            q = torch.zeros((1, 2), dtype=torch.float64, device="cuda")
            for method in (triton_stats, torch_stats):
                try:
                    method(q, mapping)
                except ValueError as e:
                    if str(e) != "zero original row":
                        raise
                    result["rows"].append(dict(method=method.__name__, status="zero_refused"))
                else:
                    raise AssertionError("zero original row was not refused")
            result["complete"] = True
        except Exception as e:
            result["failure"] = dict(type=type(e).__name__, message=str(e))
            raise
        finally:
            json.dump(result, log, indent=2)
            log.write("\n")
    print(
        json.dumps(
            dict(
                complete=result["complete"],
                rows=len(result["rows"]),
                checks=sum(r.get("exact_checks", 0) for r in result["rows"]),
            )
        )
    )


if __name__ == "__main__":
    main()
