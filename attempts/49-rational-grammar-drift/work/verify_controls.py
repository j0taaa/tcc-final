"""Same prospective independent norm/ID/product families for all V12 controls."""

import argparse
import json
import random
import subprocess
import traceback
from fractions import Fraction as F
from pathlib import Path

from . import angular_control, angular_streamed, calibrated_endpoint, hybrid_endpoint
from . import verify_forest as words
from .forest import certificate
from .product import certificate as product_certificate
from .verify_planar import cases, norm
from .verify_product import cases as products, expected as product_truth

ENGINES = [angular_control, calibrated_endpoint, hybrid_endpoint]


def run(output, streamed=False):
    engines = [angular_streamed, calibrated_endpoint, hybrid_endpoint] if streamed else ENGINES
    output.mkdir(parents=True, exist_ok=False)
    (output / "metadata.json").write_text(
        json.dumps(
            dict(producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
        )
        + "\n"
    )
    geometry = queries = forests = products_checked = zeros = 0
    try:
        with (output / "rows.jsonl").open("w") as stream:
            for name, rows in cases():
                for engine in engines:
                    for grid in (
                        [21, 40, 80] if engine in [angular_control, angular_streamed] else [1, 2, 4]
                    ):
                        result = engine.compress(rows, grid)
                        factor = (
                            grid
                            if engine in [angular_control, angular_streamed]
                            else 16 * grid * grid
                        )
                        loss = 20 if engine in [angular_control, angular_streamed] else 1
                        directions = {
                            (1, 0),
                            (0, 1),
                            *((-b, a) for a, b in [*rows, *result] if a or b),
                        }
                        for w in directions:
                            before, after = norm(rows, w), norm(result, w)
                            assert after <= before and factor * after >= (factor - loss) * before
                        bound = (
                            8 * grid + 4
                            if engine in [angular_control, angular_streamed]
                            else 64 * grid
                        )
                        assert len(result) <= bound
                        queries += len(directions)
                        geometry += 1
                        stream.write(
                            json.dumps(
                                dict(
                                    kind="geometry",
                                    engine=engine.__name__,
                                    case=name,
                                    grid=grid,
                                    input_rows=len(rows),
                                    output_rows=len(result),
                                )
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
                    for engine in engines:
                        for epsilon in [F(1), F(1, 2), F(1, 10)]:
                            result = certificate(plan, first, second, epsilon, compressor=engine)
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
                                        engine=engine.__name__,
                                        epsilon=str(epsilon),
                                        expected=str(truth),
                                        **result,
                                    ),
                                    default=str,
                                )
                                + "\n"
                            )
            for name, p, q in products():
                truth = product_truth(p, q)
                for engine in engines:
                    for epsilon in [F(1), F(1, 2), F(1, 10)]:
                        result = product_certificate(p, q, epsilon, compressor=engine)
                        if truth is None:
                            assert result["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                            zeros += 1
                        else:
                            assert isinstance(truth, F)
                            assert (
                                result["lower"]
                                <= truth
                                <= result["upper"]
                                <= (1 + epsilon) * result["lower"]
                            )
                        products_checked += 1
                        stream.write(
                            json.dumps(
                                dict(
                                    kind="product",
                                    case=name,
                                    engine=engine.__name__,
                                    epsilon=str(epsilon),
                                    expected=str(truth),
                                    **result,
                                ),
                                default=str,
                            )
                            + "\n"
                        )
        streamed_products = 0
        if streamed:
            rng = random.Random(2026101204913)
            for _ in range(100):
                left = [(rng.randrange(-10, 11), rng.randrange(-10, 11)) for _ in range(7)]
                right = [(rng.randrange(-10, 11), rng.randrange(-10, 11)) for _ in range(9)]
                rows = [(a * x, b * y) for a, b in left for x, y in right]
                for grid in [21, 40, 80]:
                    result = angular_streamed.compress_product(left, right, grid)
                    assert result == angular_streamed.compress(rows, grid)
                    for w in {(1, 0), (0, 1), *((-b, a) for a, b in [*rows, *result] if a or b)}:
                        before, after = norm(rows, w), norm(result, w)
                        assert after <= before and grid * after >= (grid - 20) * before
                    streamed_products += 1
        summary = dict(
            status="CORRECTNESS_ONLY",
            geometry_cases=geometry,
            exact_norm_queries=queries,
            original_id_forest_cases=forests,
            product_cases=products_checked,
            zero_mass_refusals=zeros,
            streamed_cartesian_checks=streamed_products,
        )
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    except Exception:
        (output / "failure.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--streamed", action="store_true")
    args = parser.parse_args()
    run(args.output, args.streamed)
