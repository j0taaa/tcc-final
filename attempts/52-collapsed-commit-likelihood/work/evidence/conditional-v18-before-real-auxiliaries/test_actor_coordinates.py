"""Independent full-joint directional derivatives and paired/RLOO laws."""

import itertools
import json
import unittest
from collections import defaultdict
from fractions import Fraction as F

import numpy as np

from .actor_coordinates import actor_vector, paired_trace, state_features
from .prefix_anchor import PrefixAnchor
from .test_prefix_anchor import Dual, joint_law, language, make, prefixes


class ActorCoordinateTests(unittest.TestCase):
    def test_nine_coordinate_chain_against_independent_joint_duals(self):
        count = 0
        for n, fixed in ((2, {}), (3, {2: 5})):
            original, _ = make(n, fixed)
            rows = original.rows
            gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in rows)
            u = (F(1),) * n
            base = PrefixAnchor(language(), rows, gates, u, fixed)
            weights = np.asarray(rows, dtype=float)
            for i, v in fixed.items():
                weights[i] = 0
                weights[i, v] = 1
            features = state_features(weights, fixed, 5)
            x, h = tuple(map(F, features["x"])), tuple(map(F, features["h"]))
            m, e = F(features["m"]), F(features["e"])
            logs = tuple(tuple(F(np.log(float(c))) for c in row) for row in rows)
            for coordinate in range(9):
                aa = tuple(
                    (F(1), x[i], h[i], m, e, F(), F(), F(), F())[coordinate] for i in range(n)
                )
                rr = tuple(
                    (F(), F(), F(), F(), F(), x[i], h[i], m * x[i], F())[coordinate]
                    for i in range(n)
                )
                dg = tuple(
                    tuple(
                        Dual(g, g * (1 - g) * (aa[i] + F(coordinate == 8) * logs[i][v]))
                        for v, g in enumerate(row)
                    )
                    for i, row in enumerate(gates)
                )
                du = tuple(Dual(v, v * rr[i]) for i, v in enumerate(u))
                law = joint_law(prefixes(language(), n, fixed), rows, dg, du, fixed)
                grouped = defaultdict(lambda: Dual(F()))
                for (_, _, action), probability in law.items():
                    grouped[action] += probability
                for action, probability in grouped.items():
                    _, _, g, r = base.action_statistics(action)
                    score = {
                        "alpha": np.asarray([float(sum(row, F())) for row in g]),
                        "anchor": np.asarray(r, dtype=float),
                        "beta": float(
                            sum((g[i][v] * logs[i][v] for i in range(n) for v in range(8)), F())
                        ),
                    }
                    value = actor_vector(score, features)[coordinate]
                    self.assertAlmostEqual(
                        value, float(probability.derivative / probability.value), places=12
                    )
                    count += 1
        print(json.dumps({"actor_original_joint_direction_checks": count, "coordinates": 9}))

    def test_paired_trace_law_and_RLOO_dependence_counterexample(self):
        probabilities = (F(1, 3), F(1, 3), F(1, 3))
        scores = (F(-1), F(), F(1))
        rewards = (F(), F(1), F(1))
        gradients = tuple(r * s for r, s in zip(rewards, scores, strict=True))
        mean = sum((p * g for p, g in zip(probabilities, gradients, strict=True)), F())
        variance = sum(
            (p * (g - mean) ** 2 for p, g in zip(probabilities, gradients, strict=True)), F()
        )
        pair_mean, rloo, wrong = F(), [], F()
        for i, j in itertools.product(range(3), repeat=2):
            p = probabilities[i] * probabilities[j]
            a = np.zeros(9)
            a[0] = float(gradients[i])
            b = np.zeros(9)
            b[0] = float(gradients[j])
            pair_mean += p * F(paired_trace(a, b)["total"])
            first, second = (
                (rewards[i] - rewards[j]) * scores[i],
                (rewards[j] - rewards[i]) * scores[j],
            )
            rloo.append((p, (first + second) / 2))
            wrong += p * (first - second) ** 2 / 2
        self.assertEqual(pair_mean, variance)
        rmean = sum((p * g for p, g in rloo), F())
        rvar = sum((p * (g - rmean) ** 2 for p, g in rloo), F())
        self.assertEqual(rmean, mean)
        self.assertNotEqual(wrong, rvar)
        print(
            json.dumps({"true_RLOO_group_variance": str(rvar), "invalid_iid_shortcut": str(wrong)})
        )

    def test_explicit_original_extent_and_padding_refusals(self):
        features = state_features(np.full((2, 8), 1 / 8), {}, 5)
        s = {"alpha": [1.0, 0.0, 0.0], "anchor": [0.0, 0.0, 0.0], "beta": 0.0}
        self.assertEqual(actor_vector(s, features).shape, (9,))
        s["alpha"][-1] = 1.0
        with self.assertRaisesRegex(ValueError, "padding"):
            actor_vector(s, features)
        with self.assertRaisesRegex(ValueError, "nine-coordinate"):
            paired_trace(np.zeros(8), np.zeros(9))


if __name__ == "__main__":
    unittest.main()
