"""All original families, every norm breakpoint, original-ID forest answers."""

import argparse
import importlib
import json
import traceback
from fractions import Fraction as F
from pathlib import Path
from random import Random

base = "attempts.49-rational-grammar-drift.work."
old = importlib.import_module(base + "verify_planar")
compiled = importlib.import_module(base + "verify_forest")
engine = importlib.import_module(base + "optimal_planar")


def verify(rows, grid):
    result = engine.compress(rows, grid)
    directions = {(1, 0), (0, 1), *((-b, a) for a, b in [*rows, *result] if a or b)}
    factor = 16 * grid * grid
    for w in directions:
        before, after = old.norm(rows, w), old.norm(result, w)
        assert after <= before, (grid, w, "upper", before, after)
        assert factor * after >= (factor - 1) * before, (grid, w, "lower", before, after)
    assert len(result) <= 64 * grid
    assert all(isinstance(x, int) for row in result for x in row)
    return dict(input_rows=len(rows), output_rows=len(result), queries=len(directions), grid=grid)


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    count = queries = shortened = forests = certified = zero = 0
    try:
        with (output / "rows.jsonl").open("w") as stream:
            for name, rows in old.cases():
                for grid in [1, 2, 4, 8]:
                    report = verify(rows, grid)
                    count += 1
                    queries += report["queries"]
                    shortened += report["output_rows"] < report["input_rows"]
                    stream.write(json.dumps(dict(kind="geometry", case=name, **report)) + "\n")
            rng = Random(202610120492)
            for name, kind, emissions, rows in compiled.fixtures():
                source = (
                    compiled.dyck_source() if kind == "dyck" else compiled.json_source_grammar()
                )
                for mode in ["equal", "tiny-scale", "zero", "near-equal", "different"]:
                    first, second = compiled.make_inputs(source, emissions, rows, mode, rng)
                    plan = compiled.compile_cfg_sampler(source, first.state)
                    truth = compiled.expected(first, second, emissions, kind)
                    for epsilon in [F(1), F(1, 2), F(1, 10)]:
                        for version, compressor in [("v2", None), ("v3", engine)]:
                            report = compiled.certificate(
                                plan, first, second, epsilon, compressor=compressor
                            )
                            if truth is None:
                                assert report["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                                zero += 1
                            else:
                                assert (
                                    report["lower"]
                                    <= truth
                                    <= report["upper"]
                                    <= (1 + epsilon) * report["lower"]
                                )
                                certified += 1
                            forests += 1
                            stream.write(
                                json.dumps(
                                    dict(
                                        kind="forest",
                                        version=version,
                                        case=name,
                                        mode=mode,
                                        epsilon=str(epsilon),
                                        expected=str(truth),
                                        **report,
                                    ),
                                    default=str,
                                )
                                + "\n"
                            )
        summary = dict(
            status="CORRECTNESS_ONLY",
            geometry_cases=count,
            exact_norm_queries=queries,
            shortened_cases=shortened,
            forest_cases=forests,
            certified=certified,
            zero_mass=zero,
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
