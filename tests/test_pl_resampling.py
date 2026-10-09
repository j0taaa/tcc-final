"""Focused exact oracles for the independently preserved PL research attempt."""

import importlib.util
import itertools
import math
import sys
import unittest
from fractions import Fraction as Q
from pathlib import Path

WORK = Path(__file__).resolve().parents[1] / "attempts/17-pl-latent-resampling/work"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, WORK / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reference = load("resampling", "resampling.py")
audit = load("pl_resampling_audit", "audit.py")
stationary = load("pl_stationary_control", "stationary_control.py")


class PlLatentOracleTests(unittest.TestCase):
    def test_product_proposal_separation_normalizer(self):
        # Independently integrate the proof family, including nonidentical
        # product proposals. This checks finite algebra, not asymptotic novelty.
        for m in range(1, 4):
            plan, data = audit.fixture(2 * m)
            q = tuple((Q(1, 10), Q(9, 10)) if len(row) == 2 else row for row in data.probabilities)
            data = audit.ProbabilityInput(data.state, q)
            order = tuple(i for i, t in enumerate(data.state.canvas) if t is None)[:m]
            p = reference.Problem(plan, q, q, order, dict.fromkeys(order, 4))
            paths = {
                y: w
                for y, w in audit.enumerated_paths(data).items()
                if all(y[i] == 4 for i in order)
            }
            target = {
                y: w * audit.direct_pl(y, order, p.free, q, p.indices) for y, w in paths.items()
            }
            target_mass = sum(target.values(), Q())
            binomial_mass = Q(9, 10) ** m * sum(
                (
                    math.comb(m, z)
                    * Q(1, 10) ** (m - z)
                    * Q(9, 10) ** z
                    * p.f(Q(m, 10) + Q(4 * z, 5))
                    for z in range(m + 1)
                ),
                Q(),
            )
            self.assertEqual(target_mass, binomial_mass)
            # Bound the secant's exponential through its exact m-th root.
            ratio, lower, upper = p.f(p.L) / p.f(p.H), Q(1), Q(9)
            for _ in range(80):
                middle = (lower + upper) / 2
                if middle**m <= ratio:
                    lower = middle
                else:
                    upper = middle
            optimum_lower = Q(9, 10) ** m * p.f(p.H) * (Q(9, 10) + lower / 10) ** m
            single = reference.SingleTilt(p)
            self.assertGreaterEqual(single.rejection_normalizer, optimum_lower)
            for probabilities in itertools.product((Q(1, 4), Q(1, 2), Q(3, 4)), repeat=m):
                normalizer = max(
                    w
                    / math.prod(
                        r if y[i] == 4 else 1 - r
                        for i, r in zip(p.hidden, probabilities, strict=True)
                    )
                    for y, w in target.items()
                )
                self.assertGreaterEqual(normalizer, optimum_lower)

    def test_conditional_sampler_laws_and_token_aliases(self):
        for dyadic, tight, coefficients in (
            (False, False, False),
            (True, False, False),
            (True, True, False),
            (True, True, True),
        ):
            report = audit.correctness(
                max_n=2,
                dyadic_unaries=dyadic,
                tight_bounds=tight,
                single_tilt=tight,
                dyadic_coefficients=coefficients,
            )
            self.assertGreater(report["events"], 20)
            self.assertEqual(report["exact_mismatches"], 0)

    def test_independent_gradient_and_two_replica_covariance(self):
        for power in (1, 2):
            for weighted in (False, True):
                for constrained in (False, True):
                    result = audit.gradient_case(3, weighted, power, 2, constrained)
                    self.assertGreaterEqual(Q(result["latent_fraction"]), 0)

    def test_stationary_metropolis_and_integrated_coin(self):
        plan, data = audit.fixture(3, True)
        paths = audit.enumerated_paths(data)
        p = reference.Problem(plan, data.probabilities, data.probabilities, (1,), {1: 4})
        weights = {
            y: w * audit.direct_pl(y, p.order, p.free, p.rates, p.indices)
            for y, w in paths.items()
            if y[1] == 4
        }
        z = sum(weights.values(), Q())
        target = {y: w / z for y, w in weights.items()}
        for constructor in (reference.BaseRejection, reference.SingleTilt):
            sampler = constructor(p)
            proposal = audit.forest_law(sampler.base)
            transition = stationary.audit_transition(sampler, target, proposal)
            # Every scalar statistic in the finite-state basis is covered.
            scores = {y: tuple(Q(y == v) for v in target) for y in target}
            pairs, integrated = [], []
            for x in target:
                for y in target:
                    pairs.append(
                        (
                            target[x] * transition[x][y],
                            tuple((a + b) / 2 for a, b in zip(scores[x], scores[y], strict=True)),
                        )
                    )
                    a = min(Q(1), sampler.acceptance(y) / sampler.acceptance(x))
                    integrated.append(
                        (
                            target[x] * proposal[y],
                            stationary.conditional_average(scores[x], scores[y], a),
                        )
                    )
            mean, original = audit.moments([(target[y], scores[y]) for y in target], len(target))
            pair_mean, pair_cov = audit.moments(pairs, len(target))
            rb_mean, rb_cov = audit.moments(integrated, len(target))
            self.assertEqual(mean, pair_mean)
            self.assertEqual(mean, rb_mean)
            # Test PSD ordering by all integer directions in {-1,0,1}^d;
            # general PSD guarantee is a written covariance identity.
            for direction in itertools.product((-1, 0, 1), repeat=len(target)):

                def quadratic(matrix, direction=direction):
                    return sum(
                        direction[i] * matrix[i][j] * direction[j]
                        for i in range(len(target))
                        for j in range(len(target))
                    )

                self.assertLessEqual(quadratic(rb_cov), quadratic(pair_cov))
                self.assertLessEqual(quadratic(pair_cov), quadratic(original))

    def test_invalid_and_impossible_evidence_is_not_sampled(self):
        plan, data = audit.fixture(2, values=(b"0", b"oops"))
        rates = data.probabilities
        with self.assertRaises(ValueError):
            reference.TangentMixture(
                reference.Problem(plan, data.probabilities, rates, (1,), {1: 4})
            )
        with self.assertRaises(ValueError):
            reference.Problem(plan, data.probabilities, rates, (1, 1), {1: 3})
        bad = tuple(tuple(Q() for _ in row) for row in rates)
        with self.assertRaises(ValueError):
            reference.Problem(plan, data.probabilities, bad, (1,), {1: 3})
        negative = tuple(tuple(-q for q in row) for row in rates)
        with self.assertRaises(ValueError):
            reference.Problem(plan, data.probabilities, negative, (1,), {1: 3})

    def test_fixed_slots_and_certified_extreme_exponential(self):
        plan, data = audit.fixture(2, fixed={1: 3})
        p = reference.Problem(plan, data.probabilities, data.probabilities, (), {})
        audit.check_problem(p, audit.enumerated_paths(data))
        tiny = Q(1, 2**300)
        self.assertEqual(reference.negative_exp_upper(Q(2**300), tiny), tiny)
        lower, upper = reference.exp_bounds(Q(1), tiny)
        self.assertLessEqual(upper - lower, tiny)
        self.assertGreater(lower, Q(27, 10))
        self.assertLess(upper, Q(28, 10))
        tolerance = Q(17, 13000)
        for x in (Q(1, 7), Q(12, 7), Q(11)):
            u = reference.dyadic_negative_exp_upper(x, tolerance)
            lo, hi = reference.exp_bounds(x, tolerance / 8)
            self.assertGreaterEqual(u, 1 / lo)
            self.assertLessEqual(u - 1 / hi, tolerance)
            self.assertEqual(u.denominator & (u.denominator - 1), 0)


if __name__ == "__main__":
    unittest.main()
