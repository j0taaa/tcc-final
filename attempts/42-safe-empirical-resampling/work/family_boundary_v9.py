"""Screen a NECESSARY family boundary; absence of obstruction is not a proof."""

import argparse
import importlib
import json
from pathlib import Path

import numpy as np

family = importlib.import_module("attempts.42-safe-empirical-resampling.work.family_probe_v8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(202610110428)
    cases, worst, obstruction = 0, (0, None, None), None
    for classes in range(2, 33):
        for concentration in (0.02, 0.1, 0.5, 1, 5, 50):
            for _ in range(100):
                p = rng.dirichlet(np.full(classes, concentration))
                p = p[p > 0]
                _, six = family.base.joints(p)
                cross = np.asarray(six) - np.outer(p, p)
                delta = family.difference(p)
                for endpoint in (0, 4 / 45):
                    value = float(np.linalg.eigvalsh(cross + (endpoint - 1 / 30) * delta)[-1])
                    cases += 1
                    if value > worst[0]:
                        worst = value, endpoint, p.tolist()
                    if value > 1e-10:
                        obstruction = dict(
                            probabilities=p.tolist(), endpoint=endpoint, eigenvalue=value
                        )
                        break
                if obstruction:
                    break
            if obstruction:
                break
        if obstruction:
            break
    out = dict(
        scope="Numerical obstruction screen only; interval remains unproved",
        seed=202610110428,
        cases=cases,
        worst_maximum_eigenvalue=worst[0],
        worst_endpoint=worst[1],
        worst_probabilities=worst[2],
        obstruction=obstruction,
    )
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print({k: out[k] for k in ("cases", "worst_maximum_eigenvalue", "obstruction")})


if __name__ == "__main__":
    main()
