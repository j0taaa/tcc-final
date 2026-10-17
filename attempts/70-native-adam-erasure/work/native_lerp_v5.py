"""One prescribed native-expression correctness audit, not an optimizer or benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import traceback
from fractions import Fraction
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def power(exponent):
    return Fraction(2**exponent) if exponent >= 0 else Fraction(1, 2 ** (-exponent))


def value(bits):
    sign = -1 if bits >> 31 else 1
    exponent, mantissa = (bits >> 23) & 255, bits & 0x7FFFFF
    if exponent == 255:
        raise ValueError("Nonfinite bit pattern outside audit")
    return sign * (
        Fraction(mantissa) * power(-149)
        if exponent == 0
        else Fraction(0x800000 + mantissa) * power(exponent - 150)
    )


def nearest_even(numerator, denominator):
    quotient, remainder = divmod(numerator, denominator)
    if 2 * remainder > denominator or (2 * remainder == denominator and quotient & 1):
        quotient += 1
    return quotient


def bits(number):
    """Independent exact Fraction-to-binary32 RNE, including gradual subnormals."""
    number = Fraction(number)
    if not number:
        return 0
    sign = 0x80000000 if number < 0 else 0
    number = abs(number)
    exponent = number.numerator.bit_length() - number.denominator.bit_length()
    if number < power(exponent):
        exponent -= 1
    if exponent < -126:
        scaled = number / power(-149)
        rounded = nearest_even(scaled.numerator, scaled.denominator)
        return sign | rounded
    scaled = number / power(exponent - 23)
    rounded = nearest_even(scaled.numerator, scaled.denominator)
    if rounded == 1 << 24:
        rounded >>= 1
        exponent += 1
    if exponent > 127:
        raise ValueError("Overflow outside audit")
    return sign | ((exponent + 127) << 23) | (rounded - (1 << 23))


def rounded(number):
    return value(bits(number))


C = value(0x3DCCCCCD)


def scalar(moment, gradient):
    return bits(moment + rounded(C * rounded(gradient - moment)))


def fused(moment, gradient):
    return bits(moment + C * rounded(gradient - moment))


def box(lower, upper, gradient):
    dlo, dhi = rounded(gradient - upper), rounded(gradient - lower)
    corners = [
        bits(lower + rounded(C * dlo)),
        bits(upper + rounded(C * dhi)),
        bits(lower + C * dlo),
        bits(upper + C * dhi),
    ]
    lo, hi = min(corners, key=value), max(corners, key=value)
    admitted = lo == hi and value(lo) != 0
    return {"corners": corners, "lower_bits": lo, "upper_bits": hi, "admitted_nonzero": admitted}


def save(path, result):
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


def audit(output):
    producer = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    source_hashes = {}
    for path in (
        Path(__file__).resolve(),
        WORK / "native-contract-v5.md",
        WORK / "primary-source-manifest-v5.json",
    ):
        relative = str(path.relative_to(ROOT))
        committed = subprocess.check_output(["git", "show", producer + ":" + relative], cwd=ROOT)
        if committed != path.read_bytes():
            raise AssertionError("Source not frozen: " + relative)
        source_hashes[relative] = hashlib.sha256(committed).hexdigest()
    manifest = {
        "producer_commit": producer,
        "sources": source_hashes,
        "python": sys.version,
        "platform": platform.platform(),
        "scope": "Native lerp primitive; no neural/model/optimizer/benchmark",
    }
    save(output / "manifest.json", manifest)
    import torch

    if (
        torch.__version__ != "2.8.0+cpu"
        or torch.version.git_version != "a1cb3cc05d46d198467bebbb6e8fba50a325d4e7"
    ):
        raise AssertionError("Unfrozen Torch runtime")
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.set_flush_denormal(False)
    manifest.update(
        torch=torch.__version__,
        torch_git=torch.version.git_version,
        cpu_capability=torch.backends.cpu.get_cpu_capability(),
        torch_config=torch.__config__.show(),
    )
    save(output / "manifest.json", manifest)
    triple = [0x32C00000, 0x33000000, 0x33000001]
    expected = [0x3DCCCCD0, 0x3DCCCCD1, 0x3DCCCCD0]
    for point, wanted in zip(triple, expected, strict=True):
        if (
            scalar(value(point), Fraction(1)) != wanted
            or fused(value(point), Fraction(1)) != wanted
        ):
            raise AssertionError("Written adverse rational triple is incorrect")
    adverse = box(value(triple[0]), value(triple[-1]), Fraction(1))
    if adverse["admitted_nonzero"]:
        raise AssertionError("Sound box incorrectly admits adverse triple")
    calls = 0
    coordinate_checks = 0

    def kernel(case, points, gradient, threads, admitted_box=None):
        nonlocal calls, coordinate_checks
        signed_bits = [x if x < 0x80000000 else x - 0x100000000 for x in points]
        tensor = torch.tensor(signed_bits, dtype=torch.int32).view(torch.float32)
        end = torch.full(tensor.shape, float(gradient), dtype=torch.float32)
        calls += 1
        tensor.lerp_(end, 1 - 0.9)
        observed = [int(x) & 0xFFFFFFFF for x in tensor.view(torch.int32).tolist()]
        scalar_expected = [scalar(value(x), gradient) for x in points]
        fused_expected = [fused(value(x), gradient) for x in points]
        matches = all(
            x in (a, b) for x, a, b in zip(observed, scalar_expected, fused_expected, strict=True)
        )
        if admitted_box is not None:
            matches &= admitted_box["admitted_nonzero"] and all(
                x == admitted_box["lower_bits"] for x in observed
            )
        row = {
            "case": case,
            "threads": threads,
            "shape": len(points),
            "old_m_bits": points,
            "gradient": str(gradient),
            "native_bits": observed,
            "fraction_scalar_bits": scalar_expected,
            "fraction_fused_bits": fused_expected,
            "box": admitted_box,
            "status": "PASS" if matches else "FAIL",
        }
        with (output / "records.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        coordinate_checks += len(points)
        save(
            output / "calls.json",
            {"primitive_lerp_calls": calls, "coordinate_checks": coordinate_checks},
        )
        if not matches:
            raise AssertionError("Native source-form/box mismatch: " + case)

    tiny_boxes = []
    for exponent in (-40, -80):
        bound = power(exponent)
        for lower, upper in ((-bound, Fraction(0)), (Fraction(0), bound), (-bound, bound)):
            for gradient in (Fraction(1), Fraction(-1), power(-10), -power(-10)):
                admission = box(lower, upper, gradient)
                if not admission["admitted_nonzero"]:
                    raise AssertionError("Predeclared tiny box refuses")
                points = [bits(lower), bits((lower + upper) / 2), bits(upper)]
                tiny_boxes.append((points, gradient, admission))
    for threads in (1, 8):
        torch.set_num_threads(threads)
        for shape in (1, 2, 15, 16, 17, 31, 32, 33, 64, 65):
            for shift in range(3):
                points = [triple[(i + shift) % 3] for i in range(shape)]
                kernel(f"adverse/{shape}/{shift}", points, Fraction(1), threads)
        for index, (points, gradient, admission) in enumerate(tiny_boxes):
            kernel("tiny/" + str(index), points, gradient, threads, admission)
    if calls != 108 or coordinate_checks != 1800 or len(tiny_boxes) != 24:
        raise AssertionError("Prescribed grid/count changed")
    summary = {
        "status": "PASS",
        "primitive_lerp_calls": calls,
        "coordinate_checks": coordinate_checks,
        "tiny_boxes_admitted": len(tiny_boxes),
        "adverse_triple": {"points": triple, "values_both_forms": expected, "sound_box": adverse},
        "neural_forwards": 0,
        "backwards": 0,
        "optimizer_steps": 0,
        "claim": (
            "Finite native-expression/rational audit; no every-kernel proof, "
            "zero-anchored counterexample, practical gain or sufficient priority"
        ),
    }
    save(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        audit(args.output)
    except BaseException as error:
        save(
            args.output / "error.json",
            {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            },
        )
        raise


if __name__ == "__main__":
    main()
