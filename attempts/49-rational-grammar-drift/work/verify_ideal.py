"""Original-word oracle for ideal Hellinger/chi bounds and exact overlap rounding."""

import argparse
import itertools
import json
import random
import subprocess
from fractions import Fraction as F
from math import isqrt, prod
from pathlib import Path

from . import verify_forest as words
from .ideal_controls import controls as ideal_bounds
from .mass_aware_controls import controls as mass_controls
from .public_audit import integers
from .sampler_overlap import controls as overlap_controls


def sqrt_upper(value):
    scaled = value * (1 << 2048)
    root = isqrt(scaled.numerator // scaled.denominator)
    return F(root + (F(root * root) < scaled), 1 << 1024)


def exact_overlap(plan, first, second):
    p, q = integers(first), integers(second)
    a, b, agreement = ([0] * len(plan.terms) for _ in range(3))
    for node in plan.order:
        alternatives = plan.terms[node]
        left = [plan.term_mass(t, p, a) for t in alternatives]
        right = [plan.term_mass(t, q, b) for t in alternatives]
        a[node], b[node] = sum(left), sum(right)
        if a[node] and b[node]:
            agreement[node] = sum(
                (
                    min(F(x, a[node]), F(y, b[node])) * prod(agreement[c] for c in t.children)
                    for t, x, y in zip(alternatives, left, right, strict=True)
                ),
                F(),
            )
    return 1 - agreement[plan.root]


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    rng = random.Random(202610120492)
    rows_out = []
    for name, kind, emissions, rows in words.fixtures():
        source = words.dyck_source() if kind == "dyck" else words.json_source_grammar()
        for mode in ["equal", "tiny-scale", "zero", "near-equal", "different"]:
            first, second = words.make_inputs(source, emissions, rows, mode, rng)
            plan = words.compile_cfg_sampler(source, first.state)
            valid = [
                path
                for path in itertools.product(
                    *[range(len(row)) for row in first.state.support.rows]
                )
                if words.recognizes(
                    b"".join(emissions[first.state.support.rows[i][j]] for i, j in enumerate(path)),
                    kind,
                )
            ]
            raw_p = [prod(first.probabilities[i][j] for i, j in enumerate(path)) for path in valid]
            raw_q = [prod(second.probabilities[i][j] for i, j in enumerate(path)) for path in valid]
            for epsilon in [F(1), F(1, 2), F(1, 10)]:
                if not sum(raw_p) or not sum(raw_q):
                    rows_out.append(
                        dict(
                            case=name, mode=mode, epsilon=str(epsilon), status="UNDEFINED_ZERO_MASS"
                        )
                    )
                    continue
                p, q = [[v / sum(row) for v in row] for row in [raw_p, raw_q]]
                mass = mass_controls(plan, first, second)
                overlap = overlap_controls(plan, first, second)
                base = dict(
                    hellinger_upper=mass["conditional_bounds"]["hellinger"],
                    range_upper=mass["conditional_bounds"]["range"],
                    sqrt_fraction_bits=64,
                    mass_aware=mass,
                    sampler_overlap=overlap,
                )
                report = ideal_bounds(base, len(first.state.canvas), len(plan.terms))
                individual = report["individual_lower_bounds"]
                affinity_upper = min(
                    F(1), sum((sqrt_upper(x * y) for x, y in zip(p, q, strict=True)), F())
                )
                assert individual["original_hellinger"] ** 2 <= 1 - affinity_upper**2
                assert individual["common_hellinger"] ** 2 <= 1 - affinity_upper**2
                for label, left, right in [("common_chi_QP", p, q), ("common_chi_PQ", q, p)]:
                    ideal_squared = (
                        sum((y * y / x for x, y in zip(left, right, strict=True)), F()) - 1
                    ) / 4
                    assert individual[label] ** 2 <= ideal_squared
                ratios = [y / x for x, y in zip(p, q, strict=True)]
                lo, hi = min(ratios), max(ratios)
                expected_range = F() if lo == hi else (1 - lo) * (hi - 1) / (hi - lo)
                assert individual["original_range"] == individual["common_range"] == expected_range
                exact = exact_overlap(plan, first, second)
                assert individual["sampler_overlap"] <= exact <= overlap["upper"]
                rows_out.append(
                    dict(
                        case=name,
                        mode=mode,
                        epsilon=str(epsilon),
                        status="PASS",
                        ideal_overlap=str(exact),
                        **report,
                    )
                )
    summary = dict(
        status="CORRECTNESS_ONLY",
        producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        cases=len(rows_out),
        counts={
            s: sum(r["status"] == s for r in rows_out)
            for s in sorted({r["status"] for r in rows_out})
        },
        new_forwards=0,
    )
    (output / "rows.jsonl").write_text("".join(json.dumps(r, default=str) + "\n" for r in rows_out))
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
