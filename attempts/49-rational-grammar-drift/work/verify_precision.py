"""Extreme precision must preserve small exact events, without a huge grid."""

import argparse
import json
import traceback
from fractions import Fraction as F
from pathlib import Path

from .optimal_planar_fast import compress
from .product import certificate
from .verify_product import cases, expected


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    checks = zeros = 0
    try:
        with (output / "rows.jsonl").open("w") as stream:
            for name, p, q in cases():
                truth = expected(p, q)
                result = certificate(p, q, F(1, 1 << 1024))
                if truth is None:
                    assert result["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                    zeros += 1
                else:
                    assert isinstance(truth, F) and result["lower"] == truth
                    assert result["lower"] <= result["upper"] <= (1 + F(1, 1 << 1024)) * truth
                stream.write(
                    json.dumps(dict(case=name, expected=str(truth), **result), default=str) + "\n"
                )
                checks += 1
        signed = [(5, -2), (-7, 3), (9, 1), (-3, -8)]
        result = compress(signed, 1 << 512)
        assert result == signed
        for w in [(1, 0), (0, 1), *((-b, a) for a, b in signed)]:
            assert sum(abs(a * w[0] + b * w[1]) for a, b in result) == sum(
                abs(a * w[0] + b * w[1]) for a, b in signed
            )
        summary = dict(
            status="CORRECTNESS_ONLY",
            product_cases=checks,
            zero_mass_refusals=zeros,
            exact_signed_checks=6,
            epsilon="2^-1024",
        )
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    except Exception:
        (output / "failure.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
