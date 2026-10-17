"""Independent exact complete conditional laws and callback-count audit."""

import hashlib
import json
import subprocess
import sys
from fractions import Fraction as F
from math import comb, isqrt
from pathlib import Path

from residual import Increment, KnownProposal

HERE = Path(__file__).resolve().parent


def fixtures():
    def positive(x):
        return max(F(), x)

    def spline(x):
        return F(1, 4) + x / 8 + positive(x - F(1, 2)) ** 3 / 4

    return (
        ("constant", lambda x: F(1, 2), F(), F()),
        ("affine", lambda x: F(1, 4) + x / 2, F(), F()),
        ("quadratic", lambda x: F(1, 4) + x**2 / 4, F(1, 2), F()),
        ("cubic", lambda x: F(1, 4) + x**3 / 4, F(3, 2), F(3, 2)),
        ("spline", spline, F(3, 4), F(3, 2)),
        ("reflected_spline", lambda x: spline(1 - x), F(3, 4), F(3, 2)),
    )


def independent_center(function, n, x):
    step = F(1, isqrt(n))
    if x > 1 - 2 * step:
        step = -step
    second = n * (function(x) - 2 * function(x + step) + function(x + 2 * step))
    return function(x) - x * (1 - x) * second / (2 * (n - 1))


def main(destination):
    counts = dict(
        conditional_laws=0,
        residual_points=0,
        envelope_mass_bounds=0,
        term_bounds=0,
        setup_call_checks=0,
        optional_call_checks=0,
        zero_h_polynomial_points=0,
        lower_bound_coefficients=0,
        guards=0,
    )
    comparisons = []
    maximum_path_calls = 0
    for name, function, curvature, h in fixtures():
        n0 = 16
        while curvature / (8 * (n0 - 1)) + 32 * h / (15 * n0 * isqrt(n0)) > F(1, 4):
            n0 *= 4
        comparisons.append(
            dict(
                function=name,
                initial_degree=n0,
                enlarged_written_input_mean=str(F(n0) + 24 * h / isqrt(n0)),
                tighter_classical_written_input_mean=str(F(n0) + 12 * h / isqrt(n0)),
                note="Analytical counts; direct known polynomial factories may be much cheaper.",
            )
        )
        if not h:
            row = tuple(independent_center(function, 16, F(i, 16)) for i in range(17))
            assert all(0 <= c <= 1 for c in row)
            for p in (F(), F(1, 8), F(1, 3), F(1, 2), F(3, 4), F(7, 8), F(1)):
                assert sum(
                    (c * comb(16, i) * p**i * (1 - p) ** (16 - i) for i, c in enumerate(row)),
                    F(),
                ) == function(p)
                counts["zero_h_polynomial_points"] += 1
            try:
                KnownProposal(16, 32, h)
            except ValueError:
                counts["guards"] += 1
            else:
                raise AssertionError("Zero H normalization not refused")
            continue
        for m in (16, 64):
            old_row = tuple(independent_center(function, m, F(i, m)) for i in range(m + 1))
            for k in range(4 * m + 1):
                calls = []

                def callback(x, calls=calls, function=function):
                    assert 0 <= x <= 1
                    calls.append(x)
                    return function(x)

                known = KnownProposal(m, k, h)
                assert not calls
                inc = Increment(callback, known)
                assert len(calls) == 6
                counts["setup_call_checks"] += 1
                assert sum(known.nu) == sum(known.proposal) == 1
                for index, probability in zip(known.indices, known.nu, strict=True):
                    assert probability == F(
                        comb(m, index) * comb(3 * m, k - index), comb(4 * m, k)
                    )
                assert 0 < known.mass <= 9 * h / (8 * m * isqrt(m))
                assert abs(inc.term) <= h / (21 * m * isqrt(m))
                assert known.mass < min(inc.offset, known.weight - inc.offset)
                assert 0 < known.branch_probability <= F(9, 14)
                assert 0 <= inc.baseline <= 1
                counts["envelope_mass_bounds"] += 1
                counts["term_bounds"] += 1
                output_probability, expected_residual, old_elevated = F(), F(), F()
                for index, nu, bound, proposal_p in zip(
                    known.indices, known.nu, known.bounds, known.proposal, strict=True
                ):
                    before = len(calls)
                    branch_p, g = inc.optional_branch(index)
                    assert len(calls) - before == 3
                    maximum_path_calls = max(maximum_path_calls, 6 + len(calls) - before)
                    assert abs(g) <= bound and 0 <= branch_p <= 1
                    output_probability += proposal_p * branch_p
                    expected_residual += nu * g
                    old_elevated += nu * old_row[index]
                    counts["residual_points"] += 1
                    counts["optional_call_checks"] += 1
                output_probability = (
                    known.branch_probability * output_probability
                    + (1 - known.branch_probability) * inc.baseline
                )
                new = independent_center(function, 4 * m, F(k, 4 * m))
                assert inc.term + expected_residual == new - old_elevated
                independent_target = F(1, 2) + (new - old_elevated) / known.weight
                assert output_probability == independent_target
                assert 0 <= output_probability <= 1
                counts["conditional_laws"] += 1
    m = 64
    for k in range(m, 3 * m + 1):
        weights = [F() for _ in range(m + 1)]
        for i in range(m + 1):
            nu = F(comb(m, i) * comb(3 * m, k - i), comb(4 * m, k))
            y = F(i, m)
            a = m * y * (1 - y) / (2 * (m - 1))
            step = isqrt(m) if i <= m - 2 * isqrt(m) else -isqrt(m)
            weights[i] += nu * (1 - a)
            weights[i + step] += nu * 2 * a
            weights[i + 2 * step] -= nu * a
        x = F(k, 4 * m)
        step_new = F(1, 2 * isqrt(m))
        if x > 1 - 2 * step_new:
            step_new = -step_new
        for t in range(isqrt(m)):
            point = F(t, m)
            nu_t = F(comb(m, t) * comb(3 * m, k - t), comb(4 * m, k))
            assert weights[t] == nu_t * (1 - m * point * (1 - point) / (2 * (m - 1))) > 0
            assert point not in (x, x + step_new, x + 2 * step_new)
            counts["lower_bound_coefficients"] += 1
    for degree, index, h in (
        (4, 0, F(1)),
        (32, 0, F(1)),
        (16, -1, F(1)),
        (16, 65, F(1)),
        (16, F(1, 2), F(1)),
        (16, 0, F(-1)),
    ):
        try:
            KnownProposal(degree, index, h)
        except ValueError:
            counts["guards"] += 1
        else:
            raise AssertionError("Invalid input not refused")
    assert maximum_path_calls == 9
    sources = ("residual.py", "audit.py", "theory-v1.md", "protocol-v1.json", "primary-v1.md")
    summary = dict(
        status="PASS",
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        counts=counts,
        maximum_function_calls_per_enumerated_path=maximum_path_calls,
        input_cost_comparisons=comparisons,
        hashes={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in sources},
        scope="Exhaustive small conditional laws, no full sampler/p-coins/NN/forwards/timing.",
        decision="Correctness only; priority, complete cost and useful own contribution stay OPEN.",
    )
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=False)
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
