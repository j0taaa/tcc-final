"""Finite formula checks of a written storage theorem; no timing benchmark."""

import argparse
import json
import subprocess
import traceback
from fractions import Fraction as F
from math import lcm
from pathlib import Path

from . import angular_streamed, calibrated_endpoint


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    (output / "metadata.json").write_text(
        json.dumps(
            dict(
                producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                scope="Formula/correctness checks only; exact scalar TV is preferable at one position",
            ),
            indent=2,
        )
        + "\n"
    )
    checks = 0
    try:
        with (output / "rows.jsonl").open("w") as stream:
            for m in [64, 256, 1024, 4096, 16384]:
                values = list(range(-m // 2, m // 2 + 1))
                p = [F(1, m + 1) for j in values]
                q = [F(m + j, m * (m + 1)) for j in values]
                a, b = lcm(*(x.denominator for x in p)), lcm(*(x.denominator for x in q))
                assert sum(p) == sum(q) == 1 and (a, b) == (m + 1, m * (m + 1))
                rows = [(int(x * a), int(y * b)) for x, y in zip(p, q, strict=True)]
                assert rows == [(1, m + j) for j in values]
                s = m * (m + 2) // 4
                truth = sum(abs(x - y) for x, y in zip(p, q, strict=True)) / 2
                assert truth == F(s, 2 * m * (m + 1))
                keys = [(m * (m + 1) * j) // (s - j) for j in range(-m // 8, m // 8 + 1)]
                assert len(set(keys)) == m // 4 + 1
                epsilon = F(20, m - 20)
                counts = {}
                for engine in [angular_streamed, calibrated_endpoint]:
                    grid = engine.grid_for(epsilon, 1)
                    core = engine.compress(rows, grid)
                    lower = F(sum(abs(b * x - a * y) for x, y in core), 2 * a * b)
                    assert lower <= truth <= (1 + epsilon) * lower
                    if engine is angular_streamed:
                        assert grid == m and len(core) >= m // 4 + 1
                    else:
                        assert len(core) <= 64 * grid
                    counts[engine.__name__] = dict(
                        grid=grid,
                        rows=len(core),
                        lower=str(lower),
                        upper=str(min(F(1), (1 + epsilon) * lower)),
                    )
                stream.write(
                    json.dumps(
                        dict(
                            M=m,
                            epsilon=str(epsilon),
                            exact_scalar_tv=str(truth),
                            guaranteed_angular_rows=m // 4 + 1,
                            cores=counts,
                        )
                    )
                    + "\n"
                )
                checks += 1
        summary = dict(
            status="FORMULA_CORRECTNESS_ONLY",
            positive_families=checks,
            new_forwards=0,
            performance_measurements=0,
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
