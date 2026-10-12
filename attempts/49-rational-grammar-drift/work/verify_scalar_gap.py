"""Finite arithmetic checks of a proof family; no performance/model benchmark."""

import argparse
import json
import subprocess
from fractions import Fraction as F
from math import comb, isqrt
from pathlib import Path

from .mass_aware_controls import sqrt_upper


def sqrt_lower(value):
    return F(isqrt(value.numerator * (1 << 128) // value.denominator), 1 << 64)


def run(output):
    rows = []
    for m in [4, 5, 6, 8, 12, 16]:
        n, a, delta = m * m, F(1, m**3), F(1, m**4)
        fair, biased = F(1, 2), F(1, 2) + delta
        # Independent exact counter exploits exchangeability; no core is used.
        truth = (
            sum(
                (
                    comb(n, k)
                    * sum(
                        abs(p * fair**n - q * biased**k * (1 - biased) ** (n - k))
                        for p, q in [(a, 2 * a), (1 - a, 1 - 2 * a)]
                    )
                    for k in range(n + 1)
                ),
                F(),
            )
            / 2
        )
        lo = (1 - 2 * a) / (1 - a) * (1 - 2 * delta) ** n
        hi = 2 * (1 + 2 * delta) ** n
        affinity = (sqrt_lower(2 * a * a) + sqrt_lower((1 - a) * (1 - 2 * a))) * (
            sqrt_lower(fair * biased) + sqrt_lower(fair * (1 - biased))
        ) ** n
        forward = (1 + a / (1 - a)) * (1 + 4 * delta * delta) ** n - 1
        reverse = (1 + a / (2 * (1 - 2 * a))) * (
            1 + delta * delta / (biased * (1 - biased))
        ) ** n - 1
        upper = dict(
            range=(1 - lo) * (hi - 1) / (hi - lo),
            overlap=1 - (1 - a) * (1 - delta) ** n,
            chi_QP=min(F(1), sqrt_upper(forward) / 2),
            chi_PQ=min(F(1), sqrt_upper(reverse) / 2),
            hellinger=sqrt_upper(1 - affinity * affinity),
        )
        assert a <= truth <= 3 * a
        assert min(upper.values()) >= F(1, 2 * m * m)
        assert all(truth <= u <= 1 for u in upper.values())
        assert min(upper.values()) / truth >= F(m, 6)
        # Exact lower bound for IDEAL Hellinger, independent of dyadic rounding.
        assert a / 9 >= F(1, 4 * m**4)
        rows.append(dict(m=m, n=n, truth=truth, upper=upper, guaranteed_ratio=F(m, 6)))
    output.mkdir(parents=True, exist_ok=False)
    (output / "rows.json").write_text(json.dumps(rows, indent=2, default=str) + "\n")
    summary = dict(
        status="CORRECTNESS_OF_PROOF_OBJECT_ONLY",
        producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        cases=len(rows),
        independent_truth="Exact O(n) binomial counter; not enumeration or a slow competitor",
        new_forwards=0,
        practical_or_publication_gate=False,
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
