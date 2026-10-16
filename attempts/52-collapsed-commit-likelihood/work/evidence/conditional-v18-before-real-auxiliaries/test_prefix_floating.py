"""Finite floating adapter/root calibration against exact rational prefix laws."""

import unittest
from fractions import Fraction as F
from itertools import pairwise

import numpy as np

from .prefix_anchor import PrefixAnchor
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .preflight_floating import compare
from .test_numeric_json import independent_accepts
from .test_prefix_anchor import joint_law, make, prefixes


def cases():
    items = []
    for n, fixed, scale in (
        (2, {}, F(1, 10)),
        (3, {}, F(1)),
        (4, {3: 5}, F(10)),
        (3, {0: 0}, F(1, 10)),
        (4, {}, F(1, 10)),
    ):
        base, _ = make(n, fixed)
        gates = tuple(tuple(c * scale / (c * scale + F(1, 100)) for c in row) for row in base.rows)
        reference = PrefixAnchor(base.language, base.rows, gates, (F(1),) * n, fixed)
        law = joint_law(prefixes(base.language, n, fixed), base.rows, gates, (F(1),) * n, fixed)
        actions = sorted({b for _, _, b in law})
        weights = np.asarray(base.rows, dtype=np.float64)
        for i, v in fixed.items():
            weights[i] = 0
            weights[i, v] = 1
        plan = PrefixFloatPlan(base.language)
        feature = float(np.log(float(scale)))
        for index in np.linspace(0, len(actions) - 1, min(8, len(actions)), dtype=int):
            action = actions[index]
            p, _, hh, rr = reference.action_statistics(action)
            expected = {
                "log_probability": float(np.log(float(p))),
                "alpha": np.asarray([float(sum(row, F())) for row in hh]),
                "beta": sum(
                    float(hh[i][v]) * np.log(float(base.rows[i][v]))
                    for i in range(n)
                    for v in range(8)
                    if i not in fixed
                ),
                "anchor": np.asarray(rr, dtype=np.float64),
            }
            items.append((plan, weights, fixed, feature, action, expected))
    return items


class PrefixFloatingTests(unittest.TestCase):
    def test_partial_controls_against_rational_conditional_scores(self):
        base, _ = make(3)
        scale = F(1, 10)
        gates = tuple(tuple(c * scale / (c * scale + F(1, 100)) for c in row) for row in base.rows)
        reference = PrefixAnchor(base.language, base.rows, gates, (F(1),) * 3)
        law = joint_law(prefixes(base.language, 3, {}), base.rows, gates, (F(1),) * 3, {})
        planner = PrefixPlanner(
            PrefixFloatPlan(base.language),
            np.asarray(base.rows, dtype=np.float64),
            {},
            float(np.log(float(scale))),
        )

        def project(score):
            _, hh, rr = score
            return {
                "alpha": np.asarray([float(sum(row, F())) for row in hh]),
                "beta": sum(
                    float(hh[i][v]) * np.log(float(base.rows[i][v]))
                    for i in range(3)
                    for v in range(8)
                ),
                "anchor": np.asarray(rr, dtype=np.float64),
            }

        for w, a, b in list(law)[::7]:
            p, *collapsed = reference.action_statistics(b)
            del p
            expected = {
                "full_triple": project(reference.full_score(w, a, b)),
                "anchor_integrated": project(reference.cheap_anchor_score(w, b)),
                "class_integrated": project(reference.class_score(w, b)),
            }
            expected["length_integrated"] = {
                **expected["anchor_integrated"],
                "anchor": project(collapsed)["anchor"],
            }
            expected["combined_partial"] = {
                **expected["class_integrated"],
                "anchor": project(collapsed)["anchor"],
            }
            group = [(ww, aa, pp) for (ww, aa, bb), pp in law.items() if aa == a and bb == b]
            total = sum((pp for _, _, pp in group), F())
            known = {
                k: sum(
                    float(pp / total) * project(reference.full_score(ww, aa, b))[k]
                    for ww, aa, pp in group
                )
                for k in ("alpha", "beta", "anchor")
            }
            expected["known_anchor"] = known
            actual = planner.controls(w, a, b)
            for name, wanted in expected.items():
                for key in ("alpha", "beta", "anchor"):
                    np.testing.assert_allclose(
                        actual[name][key], wanted[key], atol=1e-10, rtol=1e-7
                    )

    def test_compact_original_scores_variable_occupancy_and_prefix_sampler(self):
        rng = np.random.default_rng(52081)
        for plan, weights, fixed, feature, action, expected in cases():
            planner = PrefixPlanner(plan, weights, fixed, feature)
            compare(planner.statistics(action), expected)
            word = plan.sample_prefix(weights, rng, minimum=max(fixed, default=-1))
            self.assertTrue(independent_accepts(plan.language, word))
            self.assertTrue(all(i < len(word) and word[i] == v for i, v in fixed.items()))
            reference = plan.infer(weights, minimum=max(fixed, default=-1))
            self.assertAlmostEqual(reference["stops"].sum(), 1)
            self.assertTrue((reference["classes"].sum(axis=1) <= 1 + 1e-12).all())

    def test_root_feature_expected_release_against_full_rational_law(self):
        for n in (2, 3, 4):
            base, _ = make(n)
            plan = PrefixFloatPlan(base.language)
            weights = np.asarray(base.rows, dtype=np.float64)
            result = plan.root_feature(weights)
            scale = F(float(np.exp(result["alpha"])))
            gates = tuple(
                tuple(c * scale / (c * scale + F(1, 100)) for c in row) for row in base.rows
            )
            law = joint_law(prefixes(base.language, n, {}), base.rows, gates, (F(1),) * n, {})
            exact = sum((p * len(b) for (_, _, b), p in law.items()), F())
            self.assertAlmostEqual(float(exact), result["target"], places=10)
            self.assertAlmostEqual(float(exact), result["expected"], places=10)
            ordered = sorted(result["trials"], key=lambda r: r["alpha"])
            self.assertTrue(
                all(a["expected"] <= b["expected"] + 1e-12 for a, b in pairwise(ordered))
            )


if __name__ == "__main__":
    unittest.main()
