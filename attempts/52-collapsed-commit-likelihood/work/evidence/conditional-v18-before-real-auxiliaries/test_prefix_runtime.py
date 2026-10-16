"""Changed FAKE-head trajectories and original MASK ID versus explicit status."""

import unittest

import numpy as np

from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_runtime import assemble, extent, release, terminal
from .test_prefix_anchor import make
from .two_stage import json_text


class PrefixRuntimeTests(unittest.TestCase):
    def test_adaptive_float_episodes_keep_every_original_commit(self):
        base, _ = make(4)
        plan = PrefixFloatPlan(base.language)
        root = np.asarray(base.rows, dtype=np.float64)
        feature = plan.root_feature(root)["alpha"]
        for seed in range(12):
            fixed = {}
            rng = np.random.default_rng(52083 + seed)
            for step in range(4):
                end = extent(4, fixed, plan.language.eos)
                positions = tuple(i for i in range(end) if i not in fixed)
                if step == 0:
                    probabilities = root
                else:
                    salt = sum(i + v for i, v in fixed.items())
                    probabilities = (
                        1 + (np.asarray(positions)[:, None] * 3 + np.arange(8)[None] + salt) % 7
                    ).astype(np.float64)
                    probabilities /= probabilities.sum(axis=1, keepdims=True)
                weights = assemble(probabilities, positions, fixed, end, 8)
                planner = PrefixPlanner(plan, weights, fixed, feature)
                word, anchor, action, following = release(plan, planner, rng)
                self.assertTrue(json_text(plan.language, word))
                self.assertIn((anchor, word[anchor]), action)
                self.assertTrue(all(following[i] == v for i, v in fixed.items()))
                self.assertTrue(np.isfinite(planner.statistics(action)["log_probability"]))
                fixed = following
                completed = terminal(plan.language, 4, fixed)
                if completed is not None:
                    self.assertTrue(
                        all(i < len(completed) and completed[i] == v for i, v in fixed.items())
                    )
                    break
            else:
                self.fail("finite-progress bound failed in a fake-head episode")

    def test_fixed_mask_is_an_id_and_eot_cannot_hide_an_existing_id(self):
        probabilities = np.full((2, 8), 1 / 8)
        # A fixed value equal to the model's MASK marker is not an active slot.
        # The numeric grammar may later reject it, but assembly cannot erase it.
        rows = assemble(probabilities, (1, 2), {0: 7}, 3, 8)
        self.assertEqual(rows[0, 7], 1)
        self.assertEqual(np.count_nonzero(rows[0]), 1)
        with self.assertRaises(ValueError):
            assemble(np.full((3, 8), 1 / 8), (0, 1, 2), {0: 7}, 3, 8)
        with self.assertRaises(ValueError):
            extent(4, {1: 5, 3: 0}, 5)


if __name__ == "__main__":
    unittest.main()
