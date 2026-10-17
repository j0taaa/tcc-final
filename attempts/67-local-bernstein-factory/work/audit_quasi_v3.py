"""Bounded exact audit of the frozen classical-control derivation."""

import hashlib
import json
import subprocess
import sys
from fractions import Fraction as F
from math import comb, isqrt
from pathlib import Path

from audit import counted, evaluate, fixtures, power_to_bernstein, to_power
from coefficients import Coefficients, stencil
from quasi_control_v3 import QuasiControl

HERE = Path(__file__).resolve().parent
PS = (F(), F(1, 8), F(1, 3), F(1, 2), F(3, 4), F(7, 8), F(1))


def moments(weights, values, x, variance, degree):
    assert sum(weights) == 1
    assert sum((w * v for w, v in zip(weights, values, strict=True)), F()) == x
    assert sum((w * (v - x) ** 2 for w, v in zip(weights, values, strict=True)), F()) == (variance)
    for power, bound in ((1, F(1, 2 * isqrt(degree))), (3, F(1, degree * isqrt(degree)))):
        assert (
            sum((w * abs(v - x) ** power for w, v in zip(weights, values, strict=True)), F())
            <= bound
        )


def main(destination):
    counts = dict(
        coefficients=0,
        value_call_counts=0,
        derivative_bounds=0,
        common_denominators=0,
        elevations=0,
        ideal_elevation_bounds=0,
        local_elevation_bounds=0,
        mixture_bounds=0,
        approximation_points=0,
        quadratic_reproduction_points=0,
        binomial_moments=0,
        hypergeometric_moments=0,
        guards=0,
    )
    for n in (16, 64, 256):
        values = tuple(F(i, n) for i in range(n + 1))
        for p in PS:
            weights = tuple(F(comb(n, i)) * p**i * (1 - p) ** (n - i) for i in range(n + 1))
            moments(weights, values, p, p * (1 - p) / n, n)
            counts["binomial_moments"] += 1
    hg = {}
    for m in (16, 64):
        n = 4 * m
        for k in range(n + 1):
            indices = tuple(range(max(0, k - 3 * m), min(m, k) + 1))
            weights = tuple(F(comb(m, i) * comb(3 * m, k - i), comb(n, k)) for i in indices)
            values = tuple(F(i, m) for i in indices)
            x = F(k, n)
            moments(weights, values, x, 3 * x * (1 - x) / (n - 1), m)
            assert sum((w * v * (1 - v) for w, v in zip(weights, values, strict=True)), F()) == (
                4 * (m - 1) * x * (1 - x) / (n - 1)
            )
            hg[m, k] = indices, weights
            counts["hypergeometric_moments"] += 1

    results = []
    for name, fn, derivative, curvature, lipschitz, denominator, degree in fixtures():
        spec = QuasiControl(fn, F(1, 4), curvature, lipschitz)
        old_spec = Coefficients(fn, F(1, 4), curvature, lipschitz)
        base = spec.initial_degree
        assert base == old_spec.initial_degree == 16
        rows, ideals = {}, {}
        for n in (16, 64, 256):
            row, ideal = [], []
            for k in range(n + 1):
                x = F(k, n)
                wrapped, calls = counted(fn)
                lo, hi, dd = QuasiControl(wrapped, F(1, 4), curvature, lipschitz).coefficient(n, k)
                assert len(calls) == 3 and tuple(calls) == stencil(n, k)
                assert 0 <= lo <= hi <= 1
                assert hi - lo == 2 * lipschitz / (n * isqrt(n))
                assert abs(dd - derivative(x)) <= lipschitz / isqrt(n)
                scale = 2 * denominator * (n - 1) * n ** (degree + 2)
                assert (lo * scale).denominator == (hi * scale).denominator == 1
                c = fn(x) - x * (1 - x) * derivative(x) / (2 * (n - 1))
                assert abs((lo + hi) / 2 - c) <= 2 * lipschitz / (15 * n * isqrt(n))
                ideal.append(c)
                row.append((lo, hi))
                for key in (
                    "coefficients",
                    "value_call_counts",
                    "derivative_bounds",
                    "common_denominators",
                ):
                    counts[key] += 1
                if lipschitz:
                    probability, weight = spec.mixture_coefficient(n, k)
                    assert 0 <= probability <= 1 and weight > 0
                    counts["mixture_bounds"] += 1
            rows[n], ideals[n] = row, ideal
            for p in PS:
                low, high = (evaluate([r[j] for r in row], p) for j in (0, 1))
                assert low <= fn(p) <= high
                assert abs(evaluate(ideal, p) - fn(p)) <= 7 * lipschitz / (30 * n * isqrt(n))
                assert abs((low + high) / 2 - fn(p)) <= 11 * lipschitz / (30 * n * isqrt(n))
                counts["approximation_points"] += 1
                if not lipschitz:
                    assert low == high == fn(p)
                    counts["quadratic_reproduction_points"] += 1
        for m in (16, 64):
            n = 4 * m
            low_power, high_power = (to_power([r[j] for r in rows[m]]) for j in (0, 1))
            for k in range(n + 1):
                indices, weights = hg[m, k]
                low = power_to_bernstein(low_power, n, k)
                high = power_to_bernstein(high_power, n, k)
                assert low == spec.elevated_lower(m, k)
                assert low <= rows[n][k][0] <= rows[n][k][1] <= high
                analytic_old = sum(
                    (w * ideals[m][i] for i, w in zip(indices, weights, strict=True)), F()
                )
                assert abs(ideals[n][k] - analytic_old) <= 7 * lipschitz / (30 * m * isqrt(m))
                assert abs(sum(rows[n][k]) / 2 - (low + high) / 2) <= (
                    241 * lipschitz / (630 * m * isqrt(m))
                )
                for key in ("elevations", "ideal_elevation_bounds", "local_elevation_bounds"):
                    counts[key] += 1
                if lipschitz:
                    probability, weight = spec.mixture_coefficient(n, k)
                    assert probability * weight == rows[n][k][0] - low
        control_n = F(base) + 12 * lipschitz / isqrt(base)
        v1_n = F(base) + 12 * (curvature + lipschitz) / isqrt(base)
        if not lipschitz:
            try:
                spec.mixture_coefficient(16, 0)
            except ValueError:
                counts["guards"] += 1
            else:
                raise AssertionError("H=0 mixture was not refused")
        else:
            # Sum the infinite geometric count tail algebraically, not by simulation.
            delta = lipschitz / (base * isqrt(base))
            assert F(base) + 6 * lipschitz / isqrt(base) / (1 - F(1, 2)) == control_n
            assert (1 - 2 * delta) + 2 * delta * F(7, 8) / (1 - F(1, 8)) == 1
        results.append(
            dict(
                name=name,
                initial_degree=base,
                classical_written_input_mean=str(control_n),
                v1_written_input_mean=str(v1_n),
                cold_coefficient_value_calls_classical=3,
                cold_coefficient_value_calls_v1=3,
                note="Analytical costs only; direct polynomial factories remain cheaper.",
            )
        )
    for action in (
        lambda: QuasiControl(lambda x: x, F(), F(), F()),
        lambda: QuasiControl(lambda x: x, F(3, 4), F(), F()),
        lambda: QuasiControl(lambda x: x, F(1, 4), F(-1), F()),
        lambda: QuasiControl(lambda x: x, F(1, 4), F(), F(-1)),
        lambda: spec.coefficient(4, 0),
        lambda: spec.coefficient(32, 0),
        lambda: spec.coefficient(16, -1),
        lambda: spec.coefficient(16, 17),
        lambda: spec.coefficient(16, F(1, 2)),
    ):
        try:
            action()
        except ValueError:
            counts["guards"] += 1
        else:
            raise AssertionError("Invalid input not refused")
    sources = (
        "quasi_control_v3.py",
        "audit_quasi_v3.py",
        "protocol-v3.json",
        "quasi-comparison-v3.md",
        "primary-v3.md",
        "coefficients.py",
        "audit.py",
    )
    summary = dict(
        status="PASS",
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        counts=counts,
        functions=results,
        hashes={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in sources},
        scope="Finite coefficient audit; zero full samplers/p-coins/NN/forwards/timing.",
        polynomial_controls={
            "constant": "Zero p-coins with known probability 1/2.",
            "affine": "Known direct mixture, expected p-coins 1/2.",
            "quadratic": "Known direct mixture, expected p-coins (1+p)/4 <=1/2.",
            "cubic": "Known direct mixture, expected p-coins (1+p+p^2)/4 <=3/4.",
        },
        decision="No generic locality/effective finite-mean separation; no full campaign.",
    )
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=False)
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
