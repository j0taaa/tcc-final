"""Independent exhaustive product-law oracle, not a benchmark."""

import argparse
import itertools
import json
import random
import traceback
from fractions import Fraction as F
from math import prod
from pathlib import Path

from .product import certificate


def expected(first, second):
    norms = [prod(sum(row) for row in head) for head in [first, second]]
    if 0 in norms:
        return None
    return (
        sum(
            abs(
                prod(first[i][v] for i, v in enumerate(word)) / norms[0]
                - prod(second[i][v] for i, v in enumerate(word)) / norms[1]
            )
            for word in itertools.product(*(range(len(row)) for row in first))
        )
        / 2
    )


def cases():
    yield "empty", [], []
    binary = [[F(a, 3), F(3 - a, 3)] for a in range(4)]
    for n in [1, 2]:
        for i, rows in enumerate(itertools.product(binary, repeat=2 * n)):
            yield f"binary-{n}-{i}", list(rows[:n]), list(rows[n:])
    rng = random.Random(2026101204910)
    for n in range(1, 6):
        for index in range(20):
            p = [[rng.randrange(6) for _ in range(3)] for _ in range(n)]
            q = [[rng.randrange(6) for _ in range(3)] for _ in range(n)]
            p = [[F(x, max(1, sum(row))) for x in row] for row in p]
            q = [[F(x, max(1, sum(row))) for x in row] for row in q]
            yield f"ternary-{n}-{index}", p, q
            if index == 0:
                yield f"equal-{n}", p, p
                yield f"unequal-row-mass-{n}", [[x / 7 for x in row] for row in p], q
                big = 1 << 256
                near = [[F(1, big), F(big - 2, big), F(1, big)] for _ in range(n)]
                other = [[F(2, big), F(big - 3, big), F(1, big)] for _ in range(n)]
                yield f"near256-{n}", near, other
    yield "zero", [[F(), F()]], [[F(1), F()]]


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    checks = zeros = invalid = 0
    try:
        with (output / "rows.jsonl").open("w") as stream:
            for name, p, q in cases():
                truth = expected(p, q)
                for epsilon in [F(1), F(1, 2), F(1, 10)]:
                    result = certificate(p, q, epsilon)
                    if truth is None:
                        assert result["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                        zeros += 1
                    else:
                        assert result["lower"] <= truth <= result["upper"]
                        assert result["upper"] <= (1 + epsilon) * result["lower"]
                    stream.write(
                        json.dumps(
                            dict(case=name, epsilon=str(epsilon), expected=str(truth), **result),
                            default=str,
                        )
                        + "\n"
                    )
                    checks += 1
        for p, q, epsilon in [
            ([], [[]], F(1)),
            ([[]], [[]], F(1)),
            ([[F(1)]], [[F(1), F()]], F(1)),
            ([[F(-1)]], [[F(1)]], F(1)),
            ([[F(2)]], [[F(1)]], F(1)),
            ([[0.5]], [[F(1)]], F(1)),
            ([], [], F()),
            ([], [], F(2)),
        ]:
            try:
                certificate(p, q, epsilon)
            except ValueError:
                invalid += 1
            else:
                raise AssertionError("invalid input accepted")
        summary = dict(
            status="CORRECTNESS_ONLY",
            cases=checks,
            undefined_zero_mass=zeros,
            invalid_refusals=invalid,
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
