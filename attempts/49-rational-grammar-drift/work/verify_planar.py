"""Independent integer norm/sign oracles. No performance or model evidence."""

import argparse
import importlib
import json
import random
import traceback
from itertools import combinations_with_replacement, product
from pathlib import Path

compress = importlib.import_module("attempts.49-rational-grammar-drift.work.planar").compress


def norm(rows, w):
    return sum(abs(a * w[0] + b * w[1]) for a, b in rows)


def verify(rows, grid):
    result = compress(rows, grid)
    directions = {(1, 0), (0, 1), *((-b, a) for a, b in [*rows, *result] if a or b)}
    # These are ALL breakpoints of both piecewise linear homogeneous norms.
    # A ratio of linear functions is monotone between successive breakpoints.
    for w in directions:
        before, after = norm(rows, w), norm(result, w)
        assert after <= before, (rows, result, grid, w, "upper", before, after)
        assert grid * after >= (grid - 8) * before, (
            rows,
            result,
            grid,
            w,
            "lower",
            before,
            after,
        )
    assert len(result) <= 2 * (grid + 1)
    assert all(isinstance(x, int) for row in result for x in row)
    return dict(input_rows=len(rows), output_rows=len(result), queries=len(directions), grid=grid)


def cases():
    rays = [(1, 0), (0, 1), (1, 1), (1, -1)]
    yield "empty", []
    yield "zero-lists", [[0, 0], [1, 1], [0, 0]]
    for size in range(1, 8):
        for indices in combinations_with_replacement(range(4), size):
            rows = [rays[i] for i in indices]
            yield "all-ray-multisets", rows
    for size in range(1, 6):
        for signs in product([-1, 1], repeat=size):
            yield "all-collinear-signs", [(3 * s, -5 * s) for s in signs]
    rng = random.Random(20261012049)
    for index in range(192):
        rows = [(rng.randrange(-100, 101), rng.randrange(-100, 101)) for _ in range(1 + index % 48)]
        yield "signed", rows
    for bits in [8, 64, 256, 1024]:
        for index in range(8):
            rows = [(j + 1, (j + 1) * (1 << bits) + rng.randrange(-9, 10)) for j in range(32)]
            yield f"near-collinear-{bits}-{index}", rows
    for shift in [0, 64, 256]:
        yield f"dense-{shift}", [(a << shift, b) for a in range(1, 13) for b in range(-6, 7)]


def verify_small_vertices():
    # Independent exhaustive signs of original rows, not the polygon algorithm.
    count = 0
    choices = [(1, 0), (0, 1), (1, 1), (1, -1), (2, 3)]
    for size in range(1, 6):
        for indices in combinations_with_replacement(range(len(choices)), size):
            rows = [choices[i] for i in indices]
            points = [
                tuple(sum(s * a[k] for s, a in zip(signs, rows, strict=True)) for k in [0, 1])
                for signs in product([-1, 1], repeat=size)
            ]
            for w in [(1, 0), (0, 1), (2, -3), (-7, 4)]:
                assert max(x * w[0] + y * w[1] for x, y in points) == norm(rows, w)
                count += 1
    return count


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    rows_path = output / "rows.jsonl"
    total = queries = shortened = 0
    try:
        with rows_path.open("w") as stream:
            for name, rows in cases():
                for grid in [8, 16, 32, 64, 128]:
                    result = verify(rows, grid)
                    total += 1
                    queries += result["queries"]
                    shortened += result["output_rows"] < result["input_rows"]
                    stream.write(json.dumps(dict(case=name, **result)) + "\n")
        vertex_queries = verify_small_vertices()
        summary = dict(
            status="CORRECTNESS_ONLY",
            cases=total,
            exact_norm_queries=queries,
            shortened_cases=shortened,
            exhaustive_sign_queries=vertex_queries,
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
