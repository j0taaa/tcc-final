"""Meaningful finite arithmetic checks; no optional Torch import in CI."""

import unittest

from .preflight_floating import cases, compare


class FloatingCPUConsumerTests(unittest.TestCase):
    def test_original_id_float_scores_against_rational_law(self):
        for plan, weights, word, action, expected in cases():
            self.assertTrue(plan.language.accepts(word))
            compare(plan.action_statistics(weights, action), expected)


if __name__ == "__main__":
    unittest.main()
