"""Focused exact oracles for the independently preserved PL research attempt."""

import importlib.util
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


class PlLatentOracleTests(unittest.TestCase):
    def test_conditional_sampler_laws_and_token_aliases(self):
        for dyadic in (False, True):
            report = audit.correctness(max_n=2, dyadic_unaries=dyadic)
            self.assertGreater(report["events"], 20)
            self.assertEqual(report["exact_mismatches"], 0)

    def test_independent_gradient_and_two_replica_covariance(self):
        for power in (1, 2):
            for weighted in (False, True):
                for constrained in (False, True):
                    result = audit.gradient_case(3, weighted, power, 2, constrained)
                    self.assertGreaterEqual(Q(result["latent_fraction"]), 0)

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
