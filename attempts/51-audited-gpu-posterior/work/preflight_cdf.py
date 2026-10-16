"""Independent exact inverse-CDF/law oracle for executed GPU interval decisions."""

import argparse
import hashlib
import json
import subprocess
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import torch

from .gpu_cdf import decide
from .gpu_primitives import directed_cast


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(51)
    cases = [[0.0, 1.0], [0.1, 0.2, 0.7], [0.5, 0.5], [1.0], [1e-38, 1.0], [0.0, 0.0, 1.0]]
    cases.extend(rng.random(n).tolist() for n in (3, 7, 16, 33, 257, 1025))
    checked = certified = ambiguous = laws = 0
    records = []
    for case, weights in enumerate(cases):
        original = torch.tensor(weights, dtype=torch.float64, device="cuda")
        lo, hi = directed_cast(original)
        truth, total = list(map(F, weights)), sum(map(F, weights), F())
        cdf, acc = [F()], F()
        for weight in truth:
            acc += weight / total
            cdf.append(acc)
        for bits in (2, 4, 8, 32):
            raw = list(range(1 << bits)) if bits < 32 else rng.integers(0, 1 << bits, 128).tolist()
            answers = (
                decide(lo, hi, torch.tensor(raw, dtype=torch.int64, device="cuda"), bits)
                .cpu()
                .tolist()
            )
            law = [F()] * len(weights)
            for r, answer in zip(raw, answers, strict=True):
                u0, u1 = F(r, 1 << bits), F(r + 1, 1 << bits)
                if answer >= 0:
                    if not cdf[answer] <= u0 <= u1 <= cdf[answer + 1]:
                        raise AssertionError(
                            "executed certificate chose a wrong inverse-CDF interval"
                        )
                    certified += 1
                else:
                    ambiguous += 1
                for j in range(len(weights)):
                    if answer >= 0:
                        law[j] += F(int(j == answer), 1 << bits)
                    else:
                        # Exact fallback conditioned on the SAME uniform prefix.
                        law[j] += max(F(), min(u1, cdf[j + 1]) - max(u0, cdf[j]))
                checked += 1
            if bits < 32:
                if law != [w / total for w in truth]:
                    raise AssertionError("retained-uniform fallback changed the complete law")
                laws += 1
            records.append(
                dict(
                    case=case, bits=bits, prefixes=len(raw), certified=sum(a >= 0 for a in answers)
                )
            )
    if not certified or not ambiguous:
        raise AssertionError("must exercise both proved and ambiguous decisions")
    result = dict(
        status="PASS",
        exact_prefix_checks=checked,
        certified=certified,
        ambiguous=ambiguous,
        full_category_laws=laws,
        new_model_forwards=0,
        speed_claim=False,
        goal_met=False,
        torch=torch.__version__,
        gpu=torch.cuda.get_device_name(),
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*cdf.py")
        },
        records=records,
    )
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}))


if __name__ == "__main__":
    main()
