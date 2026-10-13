"""Independent exact enumeration, then the pre-existing original-word oracle."""

import argparse
import importlib
import itertools
import json
import random
import subprocess
import traceback
from fractions import Fraction as F
from pathlib import Path

BASE = "attempts.49-rational-grammar-drift.work."
norm = importlib.import_module(BASE + "implicit_product_v30").product_norm
oracle = importlib.import_module(BASE + "verify_forest")


def direct(a, b, w):
    return sum(abs(w[0] * x * u + w[1] * y * v) for x, y in a for u, v in b)


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    checks = forests = zeros = 0
    try:
        atoms = tuple(itertools.product(range(-1, 2), repeat=2))
        lists = [tuple()]
        for size in [1, 2]:
            lists.extend(itertools.product(atoms, repeat=size))
        for a, b, w in itertools.product(lists, lists, atoms):
            assert norm(a, b, w) == direct(a, b, w), (a, b, w)
            checks += 1
        rng = random.Random(20261013030)
        for size in [3, 8, 33, 128]:
            for bits in [4, 64, 256, 4096]:
                a = [
                    tuple(rng.getrandbits(bits) * rng.choice([-1, 0, 1]) for _ in range(2))
                    for _ in range(size)
                ]
                b = [
                    tuple(rng.getrandbits(bits) * rng.choice([-1, 0, 1]) for _ in range(2))
                    for _ in range(size)
                ]
                for w in [(0, 0), (1, -1), (-1, 1), (1 << bits, -((1 << bits) - 1))]:
                    assert norm(a, b, w) == direct(a, b, w), (size, bits, w)
                    checks += 1
        engines = [
            importlib.import_module(BASE + name)
            for name in [
                "adaptive_angular",
                "calibrated_endpoint",
                "hybrid_endpoint",
                "ordered_planar",
            ]
        ]
        with (output / "forest.jsonl").open("w") as stream:
            for name, kind, emissions, rows in oracle.fixtures():
                source = oracle.dyck_source() if kind == "dyck" else oracle.json_source_grammar()
                for mode in ["equal", "tiny-scale", "zero", "near-equal", "different"]:
                    first, second = oracle.make_inputs(source, emissions, rows, mode, rng)
                    plan = oracle.compile_cfg_sampler(source, first.state)
                    truth = oracle.expected(first, second, emissions, kind)
                    for epsilon, engine in itertools.product([F(1), F(1, 2), F(1, 10)], engines):
                        options = dict(
                            epsilon=epsilon,
                            compressor=engine,
                            exact_passthrough=True,
                            known_root_query=True,
                        )
                        old = oracle.certificate(plan, first, second, **options)
                        new = oracle.certificate(
                            plan, first, second, implicit_root_query=True, **options
                        )
                        assert new == old, (name, mode, epsilon, engine.__name__, old, new)
                        if truth is None:
                            assert new["status"] == "ZERO_VALID_MASS_UNDEFINED_TV"
                            zeros += 1
                        else:
                            assert (
                                new["lower"]
                                <= truth
                                <= new["upper"]
                                <= (1 + epsilon) * new["lower"]
                            )
                        forests += 1
                        stream.write(
                            json.dumps(
                                dict(
                                    case=name,
                                    mode=mode,
                                    epsilon=str(epsilon),
                                    engine=engine.__name__,
                                    truth=str(truth),
                                    **new,
                                ),
                                default=str,
                            )
                            + "\n"
                        )
        summary = dict(
            status="CORRECTNESS_ONLY",
            exact_signed_queries=checks,
            original_word_checks=forests,
            undefined_zero_mass=zeros,
            producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
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
