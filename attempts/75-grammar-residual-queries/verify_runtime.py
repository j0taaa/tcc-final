"""Numeric/guard QA and untimed bit-size replay, preserving the original draws.

The replay adds operand-size accounting omitted by max_oracle_integer_bits.
It changes no cases, seeds, gates, sampler decisions or original result files.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import itertools
import json
import math
import sys
import tempfile
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

import oracle
import runtime


def exact_exp(q):
    if q < 0:
        low, high = exact_exp(-q)
        return 1 / high, 1 / low
    low = sum((q**j / math.factorial(j) for j in range(65)), F())
    return low, low + 3 * q**65 / math.factorial(65)


class Prefix:
    def __init__(self, value):
        self.value, self.used = value, 0

    def getrandbits(self, k):
        assert k == 1
        result = (self.value >> (255 - self.used)) & 1
        self.used += 1
        return result


def self_checks():
    for q in (F(-1), F(-1, 10), F(-1, 20), F(-1, 100), F(), F(1, 100), F(1, 20), F(1, 10), F(1)):
        actual = oracle.exp(oracle.Interval.of(q))
        low, high = exact_exp(q)
        assert actual.contains(low) and actual.contains(high)
    for a, b in itertools.product((F(-2, 3), F(-1, 100), F(), F(1, 7), F(3, 4)), repeat=2):
        x, y = oracle.Interval.of(a), oracle.Interval.of(b)
        assert (x + y).contains(a + b) and (x * y).contains(a * b)
        if b:
            assert (x / y).contains(a / b)
    for decision in ("bernoulli", "poisson"):
        try:
            if decision == "bernoulli":
                runtime.bernoulli_interval(
                    oracle.Interval(oracle.SCALE // 2 - 1, oracle.SCALE // 2 + 1), Prefix(1 << 255)
                )
            else:
                p0 = oracle.exp(oracle.Interval.of(-F(1, 50)))
                prefix = ((p0.lo + p0.hi) * (1 << 256)) // (2 * oracle.SCALE)
                runtime.poisson(F(1, 50), Prefix(prefix))
        except runtime.Inconclusive:
            pass
        else:
            raise AssertionError("expected explicit resource refusal")

    class Choices:
        def __init__(self, choices):
            self.choices = iter(choices)

        def randrange(self, a, b):
            value = next(self.choices)
            assert a <= value < b
            return value

    paths = 0
    for n in (4, 8):
        k, counts = n // 2, Counter()
        for choices in itertools.product(*(range(i, n) for i in range(k))):
            counts[runtime.subset(n, k, Choices(choices))] += 1
            paths += 1
        assert len(counts) == math.comb(n, k)
        assert set(counts.values()) == {math.factorial(k)}
    return {
        "rational_exp_points": 9,
        "interval_arithmetic_pairs": 25,
        "explicit_resource_refusal_guards": 2,
        "uniform_subset_transcripts": paths,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recorded", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checks = self_checks()
    observed = {
        "rational_component_bits": 0,
        "interval_raw_product_bits": 0,
        "rounding_calls": 0,
        "interval_multiplications": 0,
    }
    original_floor, original_ceil = oracle.floor, oracle.ceil
    original_mul = oracle.Interval.__mul__

    def observe(q):
        observed["rational_component_bits"] = max(
            observed["rational_component_bits"],
            abs(q.numerator).bit_length(),
            q.denominator.bit_length(),
        )

    def counted_floor(q):
        observe(q)
        observed["rounding_calls"] += 1
        return original_floor(q)

    def counted_ceil(q):
        observe(q)
        observed["rounding_calls"] += 1
        return original_ceil(q)

    def counted_mul(self, other):
        observed["interval_multiplications"] += 1
        if isinstance(other, oracle.Interval):
            observed["interval_raw_product_bits"] = max(
                observed["interval_raw_product_bits"],
                *(
                    abs(a * b).bit_length()
                    for a in (self.lo, self.hi)
                    for b in (other.lo, other.hi)
                ),
            )
        else:
            for a in (self.lo, self.hi):
                observe(a * F(other))
        return original_mul(self, other)

    oracle.floor, oracle.ceil = counted_floor, counted_ceil
    oracle.Interval.__mul__ = oracle.Interval.__rmul__ = counted_mul
    with tempfile.TemporaryDirectory(prefix="a75-bit-replay-") as directory:
        replay = Path(directory) / "runtime.jsonl"
        old_argv = sys.argv
        sys.argv = ["runtime.py", "--output", str(replay)]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                runtime.main()
        finally:
            sys.argv = old_argv
            oracle.floor, oracle.ceil = original_floor, original_ceil
            oracle.Interval.__mul__ = oracle.Interval.__rmul__ = original_mul
        original = [json.loads(s) for s in args.recorded.read_text().splitlines()]
        repeated = [json.loads(s) for s in replay.read_text().splitlines()]
    assert len(original) == len(repeated) == 49
    for before, after in zip(original, repeated, strict=True):
        before.pop("peak_process_RSS_KiB_cumulative", None)
        after.pop("peak_process_RSS_KiB_cumulative", None)
        assert before == after, "replay changed a draw, query, bit count or decision"
    result = {
        "status": "PASS",
        "timed": False,
        "checks": checks,
        "identical_runtime_rows": 48,
        "observed_arithmetic": observed,
        "scope": (
            "operand sizes at rational rounding and interval multiplication; "
            "not a CPU instruction count or universal bit-complexity bound"
        ),
    }
    with args.output.open("x") as output:
        json.dump(result, output, sort_keys=True, indent=2)
        output.write("\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
