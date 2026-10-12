"""Independent segment projections, complete norm breakpoints and ID forests."""

import argparse
import json
import random
import traceback
from fractions import Fraction as F
from pathlib import Path

from . import optimal_planar_fast as fast
from . import verify_forest as words
from . import verify_planar as old
from .forest import certificate


def distance(point, a, b):
    e = b[0] - a[0], b[1] - a[1]
    delta = point[0] - a[0], point[1] - a[1]
    fraction = min(
        F(1), max(F(), F(sum(x * y for x, y in zip(e, delta, strict=True)), sum(x * x for x in e)))
    )
    return sum((F(point[i]) - a[i] - fraction * e[i]) ** 2 for i in [0, 1])


def verify(rows, grid):
    result = fast.compress(rows, grid)
    directions = {(1, 0), (0, 1), *((-b, a) for a, b in [*rows, *result] if a or b)}
    factor = 16 * grid * grid
    for w in directions:
        before, after = old.norm(rows, w), old.norm(result, w)
        assert after <= before and factor * after >= (factor - 1) * before
    assert len(result) <= 64 * grid and all(isinstance(x, int) for a in result for x in a)
    rows = [tuple(a) for a in rows if tuple(a) != (0, 0)]
    queries = 0
    if rows and any(fast.det(rows[0], a) for a in rows):
        _, mapped, volume = fast.geometry(rows)
        for side in range(4):
            polygon = [fast.rotate((grid * x, grid * y), side) for x, y in mapped]
            chain = fast.right_chain(polygon)
            for j in range(-4 * grid, 4 * grid):
                point = [
                    (4 * grid * volume, j * volume),
                    (j * volume, 4 * grid * volume),
                    (-4 * grid * volume, j * volume),
                    (j * volume, -4 * grid * volume),
                ][side]
                point = fast.rotate(point, side)
                a, b = fast.nearest_edge(polygon, chain, point)
                expected = min(
                    distance(point, v, polygon[(i + 1) % len(polygon)])
                    for i, v in enumerate(polygon)
                )
                assert distance(point, polygon[a], polygon[b]) == expected
                queries += 1
    return dict(
        input_rows=len(rows),
        output_rows=len(result),
        norm_queries=len(directions),
        exhaustive_projection_queries=queries,
        grid=grid,
    )


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    total = norms = projections = forests = 0
    try:
        with (output / "rows.jsonl").open("w") as stream:
            for name, rows in old.cases():
                for grid in [1, 2, 4]:
                    report = verify(rows, grid)
                    total += 1
                    norms += report["norm_queries"]
                    projections += report["exhaustive_projection_queries"]
                    stream.write(json.dumps(dict(kind="geometry", case=name, **report)) + "\n")
            rng = random.Random(202610120492)
            for name, kind, emissions, rows in words.fixtures():
                source = words.dyck_source() if kind == "dyck" else words.json_source_grammar()
                for mode in ["equal", "tiny-scale", "zero", "near-equal", "different"]:
                    first, second = words.make_inputs(source, emissions, rows, mode, rng)
                    plan = words.compile_cfg_sampler(source, first.state)
                    expected = words.expected(first, second, emissions, kind)
                    for epsilon in [F(1), F(1, 2), F(1, 10)]:
                        report = certificate(plan, first, second, epsilon, compressor=fast)
                        if expected is None:
                            assert report["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                        else:
                            assert (
                                report["lower"]
                                <= expected
                                <= report["upper"]
                                <= (1 + epsilon) * report["lower"]
                            )
                        forests += 1
                        stream.write(
                            json.dumps(
                                dict(
                                    kind="forest",
                                    case=name,
                                    mode=mode,
                                    epsilon=str(epsilon),
                                    expected=str(expected),
                                    **report,
                                ),
                                default=str,
                            )
                            + "\n"
                        )
        summary = dict(
            status="CORRECTNESS_ONLY",
            geometry_cases=total,
            exact_norm_queries=norms,
            independent_exhaustive_projection_queries=projections,
            original_id_forest_cases=forests,
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
