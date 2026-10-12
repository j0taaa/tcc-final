"""Independent norm, exhaustive projection, product and original-ID oracles."""

import argparse
import json
import random
import subprocess
import traceback
from fractions import Fraction as F
from pathlib import Path

from . import optimal_planar_fast as previous
from . import ordered_planar as engine
from . import verify_forest as words
from .forest import certificate as forest_certificate
from .product import certificate
from .verify_fast import distance
from .verify_planar import cases, norm
from .verify_product import cases as products, expected


def ordered(rows):
    assert all(a == engine.canonical(a) and a != (0, 0) for a in rows)
    assert all(engine.det(a, b) > 0 for a, b in zip(rows, rows[1:]))


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    (output / "metadata.json").write_text(
        json.dumps(
            dict(
                producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                scope="Correctness only; no timing benchmark/new neural capture",
            )
        )
        + "\n"
    )
    geometry = queries = projections = product_cases = extremes = forests = images = 0
    try:
        with (output / "rows.jsonl").open("w") as stream:
            for name, rows in cases():
                for grid in [1, 2, 4]:
                    result = engine.compress(rows, grid)
                    ordered(result)
                    directions = {(1, 0), (0, 1), *((-b, a) for a, b in [*rows, *result] if a or b)}
                    for w in directions:
                        before, after = norm(rows, w), norm(result, w)
                        assert (
                            after <= before
                            and 16 * grid * grid * after >= (16 * grid * grid - 1) * before
                        )
                    queries += len(directions)
                    assert len(result) <= 64 * grid
                    source = engine.ordered(rows)
                    if len(source) >= 2:
                        polygon, mapped, volume = engine.geometry(source)
                        assert set(polygon) == set(previous.geometry(rows)[0])
                        for side in range(4):
                            turned = [engine.rotate((grid * x, grid * y), side) for x, y in mapped]
                            chain = engine.right_chain(turned)
                            for point, (a, b) in engine.sweep(turned, chain, grid, volume):
                                truth = min(
                                    distance(point, v, turned[(i + 1) % len(turned)])
                                    for i, v in enumerate(turned)
                                )
                                assert distance(point, turned[a], turned[b]) == truth
                                projections += 1
                    weights = [(0, 0), (1, 0), (0, 1), (2, 3), (4, 1), (1, 7)]
                    via_images = engine.compress_images(result, weights, grid)
                    via_explicit = engine.compress(
                        [(a * x, b * y) for a, b in weights for x, y in result], grid
                    )
                    assert via_images == via_explicit
                    ordered(via_images)
                    images += 1
                    geometry += 1
                    stream.write(
                        json.dumps(
                            dict(
                                kind="geometry",
                                case=name,
                                grid=grid,
                                input_rows=len(rows),
                                output_rows=len(result),
                            )
                        )
                        + "\n"
                    )
            for name, p, q in products():
                truth = expected(p, q)
                for epsilon in [F(1), F(1, 2), F(1, 10), F(1, 1 << 1024)]:
                    result = certificate(p, q, epsilon, compressor=engine)
                    if truth is None:
                        assert result["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                    else:
                        assert isinstance(truth, F)
                        assert (
                            result["lower"]
                            <= truth
                            <= result["upper"]
                            <= (1 + epsilon) * result["lower"]
                        )
                        if epsilon.denominator == 1 << 1024:
                            assert result["lower"] == truth
                    if epsilon.denominator == 1 << 1024:
                        extremes += 1
                    else:
                        product_cases += 1
                    stream.write(
                        json.dumps(
                            dict(
                                kind="product",
                                case=name,
                                epsilon=str(epsilon),
                                expected=str(truth),
                                **result,
                            ),
                            default=str,
                        )
                        + "\n"
                    )
            rng = random.Random(202610120492)
            for name, kind, emissions, rows in words.fixtures():
                source = words.dyck_source() if kind == "dyck" else words.json_source_grammar()
                for mode in ["equal", "tiny-scale", "zero", "near-equal", "different"]:
                    first, second = words.make_inputs(source, emissions, rows, mode, rng)
                    plan = words.compile_cfg_sampler(source, first.state)
                    truth = words.expected(first, second, emissions, kind)
                    for epsilon in [F(1), F(1, 2), F(1, 10)]:
                        result = forest_certificate(
                            plan, first, second, epsilon, compressor=engine, exact_passthrough=True
                        )
                        if truth is None:
                            assert result["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                        else:
                            assert (
                                result["lower"]
                                <= truth
                                <= result["upper"]
                                <= (1 + epsilon) * result["lower"]
                            )
                        forests += 1
                        stream.write(
                            json.dumps(
                                dict(
                                    kind="forest",
                                    case=name,
                                    mode=mode,
                                    epsilon=str(epsilon),
                                    expected=str(truth),
                                    **result,
                                ),
                                default=str,
                            )
                            + "\n"
                        )
        summary = dict(
            status="CORRECTNESS_ONLY",
            geometry_cases=geometry,
            exact_norm_queries=queries,
            independent_exhaustive_projections=projections,
            ordered_image_checks=images,
            product_cases=product_cases,
            extreme_precision_cases=extremes,
            original_id_forests=forests,
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
