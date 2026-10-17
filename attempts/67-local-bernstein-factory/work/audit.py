"""Independent power-basis/elevation checks of the frozen coefficient candidate."""

import hashlib
import json
import subprocess
import sys
from fractions import Fraction as F
from math import comb, isqrt
from pathlib import Path

from coefficients import Coefficients, degree_check, stencil

HERE = Path(__file__).resolve().parent


def positive(x):
    return max(F(), x)


def fixtures():
    def spline(x):
        return F(1, 4) + x / 8 + positive(x - F(1, 2)) ** 3 / 4

    return [
        ("constant", lambda x: F(1, 2), lambda x: F(), F(), F(), 2, 0),
        ("affine", lambda x: F(1, 4) + x / 2, lambda x: F(), F(), F(), 4, 1),
        ("quadratic", lambda x: F(1, 4) + x**2 / 4, lambda x: F(1, 2), F(1, 2), F(), 4, 2),
        ("cubic", lambda x: F(1, 4) + x**3 / 4, lambda x: 3 * x / 2, F(3, 2), F(3, 2), 4, 3),
        ("spline", spline, lambda x: 3 * positive(x - F(1, 2)) / 2, F(3, 4), F(3, 2), 32, 3),
        (
            "reflected_spline",
            lambda x: spline(1 - x),
            lambda x: 3 * positive(F(1, 2) - x) / 2,
            F(3, 4),
            F(3, 2),
            32,
            3,
        ),
    ]


def to_power(row):
    n = len(row) - 1
    return tuple(
        sum((row[i] * comb(n, i) * comb(n - i, j - i) * (-1) ** (j - i) for i in range(j + 1)), F())
        for j in range(n + 1)
    )


def power_to_bernstein(power, n, k):
    return sum((v * F(comb(k, j), comb(n, j)) for j, v in enumerate(power[: k + 1])), F())


def evaluate(row, p):
    n = len(row) - 1
    return sum((v * comb(n, k) * p**k * (1 - p) ** (n - k) for k, v in enumerate(row)), F())


def counted(function):
    calls = []

    def run(x):
        calls.append(x)
        return function(x)

    return run, calls


def main(destination):
    counts = dict(
        coefficients=0,
        derivative_bounds=0,
        common_denominators=0,
        elevations=0,
        mixture_bounds=0,
        approximation_points=0,
        guards=0,
    )
    results = []
    controls = []
    ps = [F(0), F(1, 8), F(1, 3), F(1, 2), F(3, 4), F(7, 8), F(1)]
    for name, function, derivative2, m, h, denominator, degree in fixtures():
        spec = Coefficients(function, F(1, 4), m, h)
        assert spec.initial_degree == 16
        rows = {}
        for n in (16, 64, 256):
            row = []
            for k in range(n + 1):
                args = stencil(n, k)
                assert len(set(args)) == 3 and all(0 <= x <= 1 for x in args)
                lo, hi, dd = spec.coefficient(n, k)
                assert 0 <= lo <= hi <= 1
                assert abs(dd - derivative2(F(k, n))) <= h / isqrt(n)
                counts["derivative_bounds"] += 1
                scale = 2 * denominator * n ** (degree + 2)
                assert (lo * scale).denominator == (hi * scale).denominator == 1
                counts["common_denominators"] += 1
                counts["coefficients"] += 1
                row.append((lo, hi))
                if spec.c:
                    probability, weight = spec.mixture_coefficient(n, k)
                    assert 0 <= probability <= 1 and weight > 0
                    counts["mixture_bounds"] += 1
            rows[n] = row
            delta = spec.c / (n * isqrt(n))
            for p in ps:
                low_value = evaluate([x[0] for x in row], p)
                high_value = evaluate([x[1] for x in row], p)
                assert low_value <= function(p) <= high_value
                assert high_value - low_value == 2 * delta
                if spec.c:
                    conditional_truncation = low_value / (1 - 2 * delta)
                    assert abs(conditional_truncation - function(p)) <= 2 * delta
                else:
                    assert low_value == function(p)
                counts["approximation_points"] += 1
        for old in (16, 64):
            n = 4 * old
            lower_power = to_power([x[0] for x in rows[old]])
            upper_power = to_power([x[1] for x in rows[old]])
            for k in range(n + 1):
                low_old = power_to_bernstein(lower_power, n, k)
                high_old = power_to_bernstein(upper_power, n, k)
                assert low_old == spec.elevated_lower(old, k)
                assert low_old <= rows[n][k][0] <= rows[n][k][1] <= high_old
                if spec.c:
                    prob, weight = spec.mixture_coefficient(n, k)
                    assert prob * weight == rows[n][k][0] - low_old
                counts["elevations"] += 1
            for k in (old // 4, old // 2, 3 * old // 4):
                fn, local_calls = counted(function)
                lo, hi, _ = Coefficients(fn, F(1, 4), m, h).coefficient(old, k)
                assert len(local_calls) == 3
                grid = [function(F(i, old)) for i in range(old + 1)]
                raw = grid[k]
                boolean = 2 * raw - evaluate(grid, F(k, old))
                analytic = raw - F(k, old) * (1 - F(k, old)) * derivative2(F(k, old)) / (2 * old)
                controls.append(
                    {
                        "function": name,
                        "n": old,
                        "k": k,
                        "local_center": str((lo + hi) / 2),
                        "raw": str(raw),
                        "analytic_derivative": str(analytic),
                        "boolean_sum": str(boolean),
                        "cold_local_f_calls": 3,
                        "cold_boolean_f_calls_with_grid_reuse": old + 1,
                        "analytic_f_calls": 1,
                        "analytic_derivative_calls": 1,
                        "scope": (
                            "One cold coefficient, not complete sampler/latency "
                            "or cached superiority."
                        ),
                    }
                )
        c, base = spec.c, spec.initial_degree
        delta0 = c / (base * isqrt(base))
        w0 = 1 - 2 * delta0
        w1 = 2 * delta0 * F(7, 8)
        assert w0 + w1 / (1 - F(1, 8)) == 1
        expected = w0 * base + w1 * (4 * base) / (1 - F(1, 2))
        assert expected == base + 12 * c / isqrt(base)
        if name == "spline":
            assert expected == F(91, 4)
        results.append(
            {
                "name": name,
                "n0": base,
                "c": str(c),
                "mixture_tail_at_n0": str(2 * delta0),
                "expected_input_count_of_mixture": str(expected),
                "affine_direct_factory_preferred": not bool(c),
            }
        )

    for args in ((4, 0), (8, 0), (20, 0), (16, -1), (16, 17)):
        try:
            degree_check(*args)
        except ValueError:
            counts["guards"] += 1
        else:
            raise AssertionError("Invalid degree accepted")
    for epsilon, m, h in (
        (F(), F(1), F()),
        (F(3, 4), F(1), F()),
        (F(1, 4), F(-1), F()),
        (F(1, 4), F(), F(-1)),
    ):
        try:
            Coefficients(lambda x: F(1, 2), epsilon, m, h)
        except ValueError:
            counts["guards"] += 1
        else:
            raise AssertionError("Invalid metadata accepted")
    report = {
        "status": "PASS",
        "producer_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "scope": (
            "Exact small coefficient proof obligations only. No full sampler, "
            "timing benchmark, model, dataset, gold, head/forward/update "
            "or publication priority claim."
        ),
        "source_sha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ("coefficients.py", "audit.py", "protocol-v1.json", "theory-v1.md")
        },
        "counts": counts,
        "functions": results,
        "controls": controls,
        "limits": [
            "Naive Fraction elevation is NOT the fast bit-work implementation.",
            (
                "Cold coefficient locality is scoped to specified operators; "
                "derivatives/caching/local quasi-interpolants remain controls."
            ),
            (
                "HNP already gives smooth finite-mean existence. Specific own "
                "effectiveness/priority/useful full cost remain unconfirmed."
            ),
        ],
    }
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ("controls", "source_sha256")}, indent=2
        )
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
