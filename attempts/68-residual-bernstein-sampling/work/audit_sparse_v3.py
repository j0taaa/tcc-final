"""Exact finite quartic/moment/rejection certificates and conditional laws."""

import hashlib
import json
import subprocess
import sys
from fractions import Fraction as F
from math import comb, isqrt
from pathlib import Path

from audit import fixtures, independent_center
from residual_v2 import envelope as previous_envelope
from sparse_v3 import Proposal, RejectionPlan

HERE = Path(__file__).resolve().parent


def main(destination):
    counts = dict(
        moment_proposals=0,
        factorial_moment_values=0,
        envelope_points=0,
        log_concavity_points=0,
        mode_cutoff_checks=0,
        rejection_height_points=0,
        rejection_laws=0,
        conditional_laws=0,
        term_branch_calls=0,
        residual_branch_points=0,
        zero_h_points=0,
        guards=0,
    )
    prepared = {}
    max_calls = max_ratio_queries = max_cutoff_queries = 0
    largest_attempts = (F(), None)
    input_means = []
    for m in (16, 64, 256):
        for k in range(4 * m + 1):
            p = Proposal(m, k, F(1))
            indices = tuple(range(max(0, k - 3 * m), min(m, k) + 1))
            nu = tuple(F(comb(m, i) * comb(3 * m, k - i), comb(4 * m, k)) for i in indices)
            assert sum(nu) == 1
            for j in range(5):
                assert (
                    sum((mass * i**j for i, mass in zip(indices, nu, strict=True)), F())
                    == (p.raw_moments[j])
                )
                counts["factorial_moment_values"] += 1
            weights = []
            fourth = F()
            for i, mass in zip(indices, nu, strict=True):
                z, t = F(i, m) - F(k, 4 * m), (F(i) - F(k, 4)) / isqrt(m)
                value = F(9, 20) + 21 * t * t / 20 + t**4 / 12
                assert p.point_polynomial(i) == value
                assert p.envelope(i) >= previous_envelope(m, z)
                weights.append(mass * value)
                fourth += mass * t**4
                counts["envelope_points"] += 1
            assert fourth <= 1
            assert sum(weights) == p.total
            assert p.mass <= F(191, 240 * m * isqrt(m))
            assert p.increment_weight / 2 - p.term_bound - p.mass >= F(53, 1680 * m * isqrt(m))
            assert p.term_probability + p.residual_probability + p.fair_probability == 1
            assert min(p.term_probability, p.residual_probability, p.fair_probability) >= 0
            for j in range(1, len(weights) - 1):
                assert weights[j] ** 2 > weights[j - 1] * weights[j + 1]
                counts["log_concavity_points"] += 1
            plan = RejectionPlan(p)
            max_ratio_queries = max(max_ratio_queries, plan.mode_ratio_queries)
            max_cutoff_queries = max(max_cutoff_queries, plan.cutoff_weight_queries)
            assert plan.mode_weight == max(weights)
            assert plan.mode_ratio_queries <= (m + 1).bit_length()
            assert plan.cutoff_weight_queries <= 3 + 2 * (m + 1).bit_length()
            for sign, cutoff in zip((-1, 1), plan.cutoffs, strict=True):
                assert cutoff > 0 and cutoff & (cutoff - 1) == 0
                assert p.point_weight(plan.mode + sign * cutoff) <= plan.mode_weight / 2
                if cutoff >= 2:
                    assert p.point_weight(plan.mode + sign * (cutoff // 2)) > plan.mode_weight / 2
            central_count = plan.left + plan.right - 1
            tail_mass = sum(
                (F(1, 2) / (1 - (1 - F(1, 2 * cutoff))) for cutoff in plan.cutoffs), F()
            )
            assert central_count + tail_mass == plan.relative_mass
            acceptance = F()
            for i, weight in zip(indices, weights, strict=True):
                hat = plan.relative_height(i)
                assert weight <= plan.mode_weight * hat
                proposal_p = hat / plan.relative_mass
                accept_p = weight / (plan.mode_weight * hat)
                acceptance += proposal_p * accept_p
                assert proposal_p * accept_p * plan.expected_attempts == weight / p.total
                counts["rejection_height_points"] += 1
            assert acceptance == 1 / plan.expected_attempts
            assert plan.expected_attempts <= 8
            for i in (p.left - 1, p.right + 1):
                assert plan.relative_height(i) > 0 and p.point_weight(i) == 0
            if plan.expected_attempts > largest_attempts[0]:
                largest_attempts = plan.expected_attempts, (m, k)
            counts["moment_proposals"] += 1
            counts["mode_cutoff_checks"] += 1
            counts["rejection_laws"] += 1
            if m < 256:
                prepared[m, k] = p
    for name, function, curvature, h in fixtures():
        n0 = 16
        while curvature / (8 * (n0 - 1)) + 17 * h / (15 * n0 * isqrt(n0)) > F(1, 4):
            n0 *= 4
        mean = F(n0) + 12 * h / isqrt(n0)
        input_means.append(dict(function=name, classical_mean=str(mean), sparse_mean=str(mean)))
        if not h:
            for pvalue in (F(), F(1, 8), F(1, 3), F(1, 2), F(3, 4), F(7, 8), F(1)):
                row = [independent_center(function, 16, F(i, 16)) for i in range(17)]
                assert sum(
                    (
                        a * comb(16, i) * pvalue**i * (1 - pvalue) ** (16 - i)
                        for i, a in enumerate(row)
                    ),
                    F(),
                ) == function(pvalue)
                counts["zero_h_points"] += 1
            try:
                Proposal(16, 32, h)
            except ValueError:
                counts["guards"] += 1
            else:
                raise AssertionError("Zero H not refused")
            continue
        for m in (16, 64):
            old_row = [independent_center(function, m, F(i, m)) for i in range(m + 1)]
            for k in range(4 * m + 1):
                calls = []

                def callback(x, calls=calls, function=function):
                    assert 0 <= x <= 1
                    calls.append(x)
                    return function(x)

                p = Proposal(m, k, h)
                assert not calls
                unit = prepared[m, k]
                assert p.total == unit.total and p.mass == h * unit.mass
                term_coin = p.term_coin(callback)
                assert len(calls) == 6 and 0 <= term_coin <= 1
                counts["term_branch_calls"] += 1
                max_calls = max(max_calls, len(calls))
                residual_coin = old_elevated = F()
                for i in range(p.left, p.right + 1):
                    before = len(calls)
                    coin, g = p.residual_coin(callback, i)
                    assert len(calls) - before == 6 and 0 <= coin <= 1
                    assert abs(g) <= p.envelope(i)
                    max_calls = max(max_calls, len(calls) - before)
                    probability = p.point_weight(i) / p.total
                    residual_coin += probability * coin
                    nu = F(comb(m, i) * comb(3 * m, k - i), comb(4 * m, k))
                    old_elevated += nu * old_row[i]
                    counts["residual_branch_points"] += 1
                law = (
                    p.fair_probability / 2
                    + p.term_probability * term_coin
                    + p.residual_probability * residual_coin
                )
                target = (
                    F(1, 2)
                    + (independent_center(function, 4 * m, F(k, 4 * m)) - old_elevated)
                    / p.increment_weight
                )
                assert law == target
                counts["conditional_laws"] += 1
    for m, k, h in ((4, 0, 1), (32, 0, 1), (16, -1, 1), (16, 65, 1), (16, 0, -1)):
        try:
            Proposal(m, k, h)
        except ValueError:
            counts["guards"] += 1
        else:
            raise AssertionError("Invalid input not refused")
    assert max_calls == 6
    sources = (
        "sparse_v3.py",
        "audit_sparse_v3.py",
        "sparse-proposal-theory-v3.md",
        "protocol-v3.json",
        "consumer-primary-v3.md",
        "residual.py",
        "residual_v2.py",
        "audit.py",
    )
    summary = dict(
        status="PASS",
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        counts=counts,
        maximum_callback_calls_per_enumerated_branch=max_calls,
        maximum_mode_ratio_queries=max_ratio_queries,
        maximum_cutoff_weight_queries=max_cutoff_queries,
        largest_written_rejection_mean_in_finite_cases=str(largest_attempts[0]),
        largest_rejection_state=largest_attempts[1],
        input_count_formula_comparison=input_means,
        hashes={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in sources},
        scope="Finite exact certificates and laws; no full sampler/genealogy/RNG/timing/model run.",
        limits="Bit engine, complete-cost benefit and specific novelty remain OPEN.",
    )
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=False)
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
