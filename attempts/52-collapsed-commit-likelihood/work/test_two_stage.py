"""Independent clamped original-word laws and unbounded numeric verification."""

import itertools
import unittest
from fractions import Fraction as F
from math import prod

import numpy as np

from .floating import FloatPlan
from .numeric_json import NumericJSON
from .test_numeric_json import independent_accepts
from .two_stage import answer_equal, clamped_weights, json_text, number_equal


class TwoStageTests(unittest.TestCase):
    def test_numeric_lexemes_without_float_or_expansion_limits(self):
        for a, b in (
            ("-0e" + "9" * 5000, "0"),
            ("1e309", "10e308"),
            ("100.00", "1e2"),
            ("1e-999999999999999999999999999999", "10e-1000000000000000000000000000000"),
        ):
            self.assertTrue(number_equal(a, b), (a[:40], b[:40]))
            self.assertTrue(answer_equal('{"answer":' + a + "}", b))
        for a, b in (("-1", "1"), ("1e309", "1e308"), ("1e" + "9" * 5000, "1"), ("1e-9999", "0")):
            self.assertFalse(number_equal(a, b))

    def test_fixed_ids_tail_and_aliases_against_original_word_enumeration(self):
        language = NumericJSON(
            (b'{"answer":0}', b'{"answer":1}', b" ", b"", b"", b"<EOT>", b"<PAD>"), 5, 6
        )
        plan, n = FloatPlan(language), 3
        rows = np.arange(1, 22, dtype=np.float64).reshape(n, 7)
        rows /= rows.sum(axis=1, keepdims=True)
        rng = np.random.default_rng(520501)
        for canvas in ((-1, -1, -1), (0, -1, -1), (-1, 5, -1), (-1, -1, 5), (1, 5, -1)):
            active = tuple(i for i, v in enumerate(canvas) if v == -1)
            weights = clamped_weights(canvas, active, rows[list(active)], mask=-1)
            exact = tuple(tuple(F(float(w)) for w in row) for row in weights)
            mass = sum(
                (
                    prod(exact[i][v] for i, v in enumerate(w))
                    for w in itertools.product(range(7), repeat=n)
                    if independent_accepts(language, w)
                ),
                F(),
            )
            self.assertAlmostEqual(
                np.exp(plan.forwards(plan.matrices(weights)[0])[0]), float(mass), places=13
            )
            for _ in range(12):
                word = plan.sample(weights, rng)
                self.assertTrue(json_text(language, word))
                self.assertTrue(all(v == -1 or word[i] == v for i, v in enumerate(canvas)))


if __name__ == "__main__":
    unittest.main()
