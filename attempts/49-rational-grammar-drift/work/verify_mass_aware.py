"""Independent original-ID enumeration for strengthened scalar controls."""

import argparse
import json
import random
import subprocess
import traceback
from fractions import Fraction as F
from pathlib import Path

from . import verify_forest as words
from .mass_aware_controls import controls


def run(output):
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
            for name, kind, emissions, rows in words.fixtures():
                source = words.dyck_source() if kind == "dyck" else words.json_source_grammar()
                for mode in ["equal", "tiny-scale", "zero", "near-equal", "different"]:
                    first, second = words.make_inputs(source, emissions, rows, mode, rng)
                    plan = words.compile_cfg_sampler(source, first.state)
                    truth = words.expected(first, second, emissions, kind)
                    for epsilon in [F(1), F(1, 2), F(1, 10)]:
                        result = controls(plan, first, second)
                        if truth is None:
                            assert result["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                            zeros += 1
                        else:
                            assert result["lower"] <= truth <= result["upper"] <= 1
                            assert all(truth <= bound <= 1 for bound in result["bounds"].values())
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
