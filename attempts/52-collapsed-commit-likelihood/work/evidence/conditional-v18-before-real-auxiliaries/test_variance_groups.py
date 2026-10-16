"""Exact small RLOO group law; checks within-group dependencies are retained."""

import itertools
import unittest
from fractions import Fraction as F

import numpy as np

from .two_stage_analyze import fit_baseline, group_gradients


class VarianceGroupTests(unittest.TestCase):
    def test_exact_rloo_pair_law_and_independent_scalar_fit(self):
        p = F(1, 4)
        mean = second = F()
        for bits in itertools.product((0, 1), repeat=2):
            rewards = np.asarray(bits, dtype=np.float64)
            scores = (rewards - float(p))[:, None]
            actual = float(group_gradients(rewards, scores, 0, "rloo", group_size=2)[0, 0])
            exact = F(bits[0] - bits[1]) ** 2 / 2
            self.assertEqual(actual, float(exact))
            mass = (p if bits[0] else 1 - p) * (p if bits[1] else 1 - p)
            mean += mass * exact
            second += mass * exact**2
        self.assertEqual(mean, F(3, 16))
        self.assertEqual(second - mean**2, F(15, 256))
        pilot = np.asarray([0, 0, 0, 1], dtype=np.float64)
        self.assertEqual(fit_baseline(pilot, (pilot - float(p))[:, None]), 0.75)


if __name__ == "__main__":
    unittest.main()
