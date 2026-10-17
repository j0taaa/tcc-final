"""Independent finite kernel/absorbing-trace and rendering risk oracles."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from fractions import Fraction as F
from itertools import product
from math import comb
from pathlib import Path

from reference import rounded_simplex, terminal_mean

KERNELS = {
    "A": [
        (F(1, 4), (F(1, 10), F(1, 5))),
        (F(1, 4), (F(1, 5), F(2, 5))),
        (F(1, 4), (F(4, 5), F(1, 5))),
        (F(1, 4), None),
    ],
    "B": [
        (F(1, 3), (F(0), F(0))),
        (F(1, 6), (F(1), F(0))),
        (F(1, 6), (F(0), F(1))),
        (F(1, 3), None),
    ],
}


def semantic(raw: tuple) -> tuple:
    if sum(raw) == 0:
        return tuple(F(1, len(raw)) for _ in raw)
    return tuple(F(v, sum(raw)) for v in raw)


def squared(point: tuple) -> F:
    return sum((v * v for v in point), F(0))


def stats(kernel: list) -> tuple[F, tuple, F]:
    alpha = sum((p for p, raw in kernel if raw is not None), F(0))
    mu = tuple(
        sum((p * semantic(raw)[j] / alpha for p, raw in kernel if raw is not None), F(0))
        for j in range(2)
    )
    variance = sum(
        (p * squared(semantic(raw)) / alpha for p, raw in kernel if raw is not None), F(0)
    ) - squared(mu)
    return alpha, mu, variance


def tapes(kernel: list, budget: int):
    for choices in product(kernel, repeat=budget):
        probability = F(1)
        for p, _ in choices:
            probability *= p
        yield probability, tuple(raw for _, raw in choices)


def call_reference(first: tuple, auxiliary: tuple) -> tuple:
    calls = []
    iterator = iter(auxiliary)
    copy = tuple(first)

    def draw():
        calls.append(1)
        return next(iterator)

    point, accepted = terminal_mean(first, draw, len(auxiliary))
    assert len(calls) == len(auxiliary) and first == copy
    assert accepted == sum(raw is not None for raw in auxiliary)
    if not accepted:
        assert point == semantic(first)
    return point, accepted


def kernel_oracle() -> dict:
    leaves = helper_calls = 0
    cases = []
    for name, kernel in KERNELS.items():
        alpha, mu, variance = stats(kernel)
        for budget in (0, 1, 3):
            mean, second, mass = [F(0), F(0)], F(0), F(0)
            counts: Counter = Counter()
            for p0, first in kernel:
                if first is None:
                    continue
                for probability, auxiliary in tapes(kernel, budget):
                    weight = p0 * probability / alpha
                    point, accepted = call_reference(first, auxiliary)
                    mass += weight
                    for j in range(2):
                        mean[j] += weight * point[j]
                    second += weight * squared(point)
                    counts[accepted] += weight
                    leaves += 1
                    helper_calls += budget
            ratio = sum(
                (
                    F(comb(budget, m), m + 1) * alpha**m * (1 - alpha) ** (budget - m)
                    for m in range(budget + 1)
                ),
                F(0),
            )
            closed = (1 - (1 - alpha) ** (budget + 1)) / ((budget + 1) * alpha)
            assert ratio == closed and mass == 1 and tuple(mean) == mu
            assert second == squared(mu) + variance * ratio
            for m in range(budget + 1):
                assert counts[m] == comb(budget, m) * alpha**m * (1 - alpha) ** (budget - m)
            cases.append(
                {
                    "kernel": name,
                    "helpers": budget,
                    "alpha": str(alpha),
                    "mean": list(map(str, mu)),
                    "variance": str(variance),
                    "remaining_variance_factor": str(ratio),
                }
            )
    guards = [
        lambda: terminal_mean([], lambda: None, 0),
        lambda: terminal_mean([-1, 2], lambda: None, 0),
        lambda: terminal_mean([1, 0], lambda: None, -1),
        lambda: terminal_mean([1, 0], lambda: [1], 1),
    ]
    for guard in guards:
        try:
            guard()
        except ValueError:
            continue
        raise AssertionError("Invalid proof-reference input was accepted")
    return {
        "status": "PASS",
        "exact_leaves": leaves,
        "reference_helper_calls": helper_calls,
        "invalid_inputs_rejected": len(guards),
        "cases": cases,
    }


def absorbing_oracle() -> dict:
    original = []
    # No reference code constructs the original chain or its occupation weights.
    for pa, a in KERNELS["A"]:
        if a is not None:
            original.append((pa, (a,), "A", a, 1))
        else:
            for pb, b in KERNELS["B"]:
                original.append((pa * pb, (None, b), "B", b, 2))
    assert len(original) == 7 and sum(p for p, *_ in original) == 1
    results = []
    total_leaves = 0
    for budget in (0, 1, 3):
        traces: Counter = Counter()
        steps: Counter = Counter()
        before = [F(0), F(0)]
        after = [F(0), F(0)]
        second_before = second_after = failure = helpers = F(0)
        for mass, trace, state, first, calls in original:
            if first is None:
                failure += mass
                traces[trace] += mass
                steps[calls] += mass
                continue
            for j in range(2):
                before[j] += mass * semantic(first)[j]
            second_before += mass * squared(semantic(first))
            for p, auxiliary in tapes(KERNELS[state], budget):
                point, _ = call_reference(first, auxiliary)
                weight = mass * p
                traces[trace] += weight
                steps[calls] += weight
                helpers += weight * budget
                for j in range(2):
                    after[j] += weight * point[j]
                second_after += weight * squared(point)
                total_leaves += 1
        expected = Counter({trace: mass for mass, trace, *_ in original})
        assert traces == expected and steps == {1: F(3, 4), 2: F(1, 4)}
        assert failure == F(1, 12) and helpers == F(11, 12) * budget and before == after
        gain = F(0)
        for state, occupation in (("A", F(1)), ("B", F(1, 4))):
            alpha, _, variance = stats(KERNELS[state])
            remaining = (1 - (1 - alpha) ** (budget + 1)) / ((budget + 1) * alpha)
            gain += occupation * alpha * variance * (1 - remaining)
        assert second_before - second_after == gain >= 0
        if budget:
            assert gain > 0
        results.append(
            {
                "helpers": budget,
                "whole_trace_squared_risk_gain_any_gold": str(gain),
                "expected_additional_helpers": str(helpers),
                "failure_mass": str(failure),
                "native_model_step_law": {str(k): str(v) for k, v in steps.items()},
            }
        )
    return {
        "status": "PASS",
        "original_absorbing_paths": 7,
        "exact_retained_output_leaves": total_leaves,
        "cases": results,
    }


def rendering_oracle() -> dict:
    points = [
        (F(1),),
        (F(0), F(1)),
        (F(1, 3), F(2, 3)),
        (F(22, 45), F(23, 45)),
        (F(1, 2), F(1, 2)),
        (F(1, 7), F(2, 7), F(4, 7)),
        (F(1, 3),) * 3,
        (F(1, 2), F(1, 2), F(0)),
    ]
    checks = 0
    for point in points:
        k = len(point)
        golds = [(F(1, k),) * k] + [tuple(F(int(j == i)) for j in range(k)) for i in range(k)]
        for digits in (0, 2, 8):
            result = rounded_simplex(point, digits)
            q = 10**digits
            assert sum(result) == 1 and min(result) >= 0
            assert all(abs(a - b) < F(1, q) for a, b in zip(result, point, strict=True))
            for gold in golds:
                old = tuple(a - g for a, g in zip(point, gold, strict=True))
                new = tuple(a - g for a, g in zip(result, gold, strict=True))
                assert abs(squared(old) - squared(new)) <= F(2 * k, q)
                assert abs(sum(map(abs, old)) - sum(map(abs, new))) / 2 <= F(k, 2 * q)
                checks += 1
    raw = [(F(2, 5), F(3, 5)), (F(1, 100), F(1, 100))]
    baseline_risk = (
        sum(
            (
                squared(tuple(v - g for v, g in zip(semantic(r), (F(1), F(0)), strict=True)))
                for r in raw
            ),
            F(0),
        )
        / 2
    )
    shortcut = semantic(tuple(sum(r[j] for r in raw) for j in range(2)))
    shortcut_risk = squared((shortcut[0] - 1, shortcut[1]))
    correct = tuple(sum(semantic(r)[j] for r in raw) / 2 for j in range(2))
    assert baseline_risk == F(61, 100) and shortcut == (F(41, 102), F(61, 102))
    assert shortcut_risk > baseline_risk and correct == (F(9, 20), F(11, 20))
    return {
        "status": "PASS",
        "finite_rendering_risk_checks": checks,
        "wrong_normalization_counterexample": {
            "native_risk": str(baseline_risk),
            "shortcut_risk": str(shortcut_risk),
            "correct_mean": list(map(str, correct)),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "status": "PASS",
        "scope": "Three exact proof oracles, no native/model execution",
        "kernels": kernel_oracle(),
        "absorbing_trace": absorbing_oracle(),
        "rendering": rendering_oracle(),
        "new_neural_forwards": 0,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
