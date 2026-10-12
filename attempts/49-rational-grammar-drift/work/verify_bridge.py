"""Independent original-ID enumeration for JSON stack bridge and both controls."""

import argparse
import itertools
import json
import math
import random
import traceback
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.types import SupportKind

from . import optimal_planar_fast as optimal_planar
from . import verify_forest
from .forest import certificate
from .public_audit import bridge, controls, prepare, rounded, scalar


def truth(data, emissions):
    count, mass = 0, F()
    for path in itertools.product(*[range(len(row)) for row in data.state.support.rows]):
        ids = [data.state.support.rows[p][i] for p, i in enumerate(path)]
        if verify_forest.recognizes(b"".join(emissions[t] for t in ids), "json"):
            count += 1
            mass += math.prod(data.probabilities[p][i] for p, i in enumerate(path))
    return count, mass


def cases():
    rng = random.Random(202610120492)
    for name, kind, emissions, rows in verify_forest.fixtures():
        if kind != "json":
            continue
        for mode in ["equal", "tiny-scale", "zero", "near-equal", "different"]:
            first, second = verify_forest.make_inputs(
                verify_forest.json_source_grammar(), emissions, rows, mode, rng
            )
            yield name, mode, emissions, first, second
            fixed = first.state.support.rows[-1][0]
            canvas = (*first.state.canvas[:-1], fixed)
            support = build_per_position_support(
                canvas=canvas,
                policy=SupportPolicy(SupportKind.EXPLICIT, len(emissions)),
                explicit_support=dict(enumerate((*first.state.support.rows[:-1], (fixed,)))),
            )
            state = replace(first.state, canvas=canvas, support=support)
            yield (
                name,
                mode + "-fixed",
                emissions,
                ProbabilityInput(state, (*first.probabilities[:-1], (F(1),))),
                ProbabilityInput(state, (*second.probabilities[:-1], (F(1),))),
            )


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    try:
        for name, mode, emissions, first, second in cases():
            plan = bridge(prepare(first.state.tokenizer_adapter, first.state.canvas), first.state)
            count, left = truth(first, emissions)
            _, right = truth(second, emissions)
            assert scalar(plan, tuple((1,) * len(s) for s in first.state.support.rows)) == count
            assert plan.evaluate(first).valid_mass == left
            assert plan.evaluate(second).valid_mass == right
            expected = verify_forest.expected(first, second, emissions, "json")
            for epsilon in [F(1, 2), F(1, 10)]:
                report = certificate(plan, first, second, epsilon, compressor=optimal_planar)
                baseline = controls(plan, first, second)
                if expected is None:
                    assert report["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                else:
                    assert (
                        report["lower"]
                        <= expected
                        <= report["upper"]
                        <= (1 + epsilon) * report["lower"]
                    )
                    assert expected <= min(baseline["range_upper"], baseline["hellinger_upper"])
                rows.append(
                    dict(
                        case=name,
                        mode=mode,
                        epsilon=str(epsilon),
                        count=count,
                        expected=str(expected),
                        **report,
                        controls=baseline,
                    )
                )
        import numpy as np

        values = np.array([[0.0, 1.0, 1.00390625, 1.01171875, 2.0**-140]], dtype="float64")
        assert np.array_equal(
            rounded(values, "bfloat16"), np.array([[0.0, 1.0, 1.0, 1.015625, 0.0]])
        )
        (output / "rows.jsonl").write_text(
            "".join(json.dumps(row, default=str) + "\n" for row in rows)
        )
        summary = dict(
            status="CORRECTNESS_ONLY",
            cases=len(rows),
            original_id_mass_count_tv_and_controls=True,
            rounding_ties_checked=True,
        )
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    except Exception:
        (output / "partial.jsonl").write_text(
            "".join(json.dumps(row, default=str) + "\n" for row in rows)
        )
        (output / "failure.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
