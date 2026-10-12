"""Small independent correctness regressions for the A49 integer reference."""

import importlib
import itertools
import unittest
from fractions import Fraction as F
from math import prod

core = importlib.import_module("attempts.49-rational-grammar-drift.work.optimal_planar_fast")
product = importlib.import_module("attempts.49-rational-grammar-drift.work.product")


class IntegerTvTests(unittest.TestCase):
    def test_signed_core_at_all_piecewise_linear_breakpoints(self):
        rows = [(i, (i * i) % 17 - 8) for i in range(-25, 26)]
        reduced = core.compress(rows, 1)
        self.assertLessEqual(len(reduced), 64)
        for w in [(1, 0), (0, 1), *((-b, a) for a, b in rows + reduced)]:
            exact = sum(abs(a * w[0] + b * w[1]) for a, b in rows)
            actual = sum(abs(a * w[0] + b * w[1]) for a, b in reduced)
            self.assertLessEqual(actual, exact)
            self.assertGreaterEqual(16 * actual, 15 * exact)

    def test_original_choice_product_against_enumeration(self):
        p = [[F(3, 8), F(1, 4), F(3, 8)]] * 5
        q = [[F(1, 2), F(3, 10), F(1, 5)]] * 5
        truth = (
            sum(
                abs(
                    prod(p[i][v] for i, v in enumerate(word))
                    - prod(q[i][v] for i, v in enumerate(word))
                )
                for word in itertools.product(range(3), repeat=5)
            )
            / 2
        )
        result = product.certificate(p, q, F(1, 10))
        self.assertLessEqual(result["lower"], truth)
        self.assertGreaterEqual(result["upper"], truth)
        self.assertLessEqual(result["upper"], F(11, 10) * result["lower"])

    def test_tiny_exact_input_extreme_precision_and_zero_mass(self):
        p, q = [[F(1, 3), F(2, 3)]], [[F(1, 4), F(3, 4)]]
        result = product.certificate(p, q, F(1, 1 << 1024))
        self.assertEqual(result["lower"], F(1, 12))
        self.assertEqual(product.certificate([], [], F(1, 10))["lower"], F())
        self.assertEqual(
            product.certificate([[F()]], [[F(1)]])["status"],
            "ZERO_VALID_MASS_UNDEFINED_TV",
        )
        with self.assertRaises(ValueError):
            product.certificate([[0.5]], [[F(1)]])
