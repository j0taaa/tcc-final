"""Independent original-word enumeration, including atom-zero regressions."""

import argparse
import json
import random
import subprocess
import traceback
from fractions import Fraction as F
from pathlib import Path

from mwpc_exact.mass_certificate import ProbabilityInput

from . import verify_forest as words
from .sampler_overlap import controls
from .tight_control_v28 import controls as tight_controls
from .two_sided_controls import controls as two_sided_controls


def run(output, two_sided=False, tight=False):
    output.mkdir(parents=True, exist_ok=False)
    (output / "metadata.json").write_text(
        json.dumps(
            dict(producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
        )
        + "\n"
    )
    checks = zeros = 0
    try:
        with (output / "rows.jsonl").open("w") as stream:
            rng = random.Random(202610120492)
            zero_rng = random.Random(202610120492)
            for name, kind, emissions, rows in words.fixtures():
                source = words.dyck_source() if kind == "dyck" else words.json_source_grammar()
                for mode in [
                    "equal",
                    "tiny-scale",
                    "zero",
                    "near-equal",
                    "different",
                    "one-zero",
                    "two-zero",
                ]:
                    first, second = words.make_inputs(
                        source,
                        emissions,
                        rows,
                        "different" if mode.endswith("zero") and mode != "zero" else mode,
                        zero_rng if mode in ["one-zero", "two-zero"] else rng,
                    )
                    if mode in ["one-zero", "two-zero"]:
                        second = ProbabilityInput(
                            second.state,
                            tuple(
                                tuple(F() if j == 0 else v for j, v in enumerate(row))
                                for row in second.probabilities
                            ),
                        )
                        if mode == "two-zero":
                            first = ProbabilityInput(
                                first.state,
                                tuple(
                                    tuple(F() if j == 1 else v for j, v in enumerate(row))
                                    for row in first.probabilities
                                ),
                            )
                    plan = words.compile_cfg_sampler(source, first.state)
                    truth = words.expected(first, second, emissions, kind)
                    for epsilon in [F(1), F(1, 2), F(1, 10)]:
                        result = (
                            tight_controls
                            if tight
                            else two_sided_controls
                            if two_sided
                            else controls
                        )(plan, first, second)
                        if truth is None:
                            assert result["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                            zeros += 1
                        else:
                            assert 0 <= truth <= result["upper"] <= 1
                            assert all(truth <= bound <= 1 for bound in result["bounds"].values())
                            if two_sided:
                                assert all(
                                    0 <= bound <= truth for bound in result["lower_bounds"].values()
                                )
                            if mode in ["equal", "tiny-scale"]:
                                assert result["upper"] == 0
                        stream.write(
                            json.dumps(
                                dict(
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
                        checks += 1
        summary = dict(
            status="CORRECTNESS_ONLY",
            original_id_forest_cases=checks,
            undefined_zero_mass=zeros,
            new_forwards=0,
            two_sided_controls=two_sided,
            grammar_restricted_moment_lower=tight,
        )
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    except Exception:
        (output / "failure.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--two-sided", action="store_true")
    parser.add_argument("--tight", action="store_true")
    args = parser.parse_args()
    if args.tight and not args.two_sided:
        parser.error("--tight requires --two-sided")
    run(args.output, args.two_sided, args.tight)
