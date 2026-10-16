"""Independent full-joint posterior, replicated moments and correlated strata."""

import itertools
import json
import unittest
from collections import defaultdict
from fractions import Fraction as F

from .conditional_prefix import conditional_prefix_law, stratified_laws
from .test_prefix_anchor import direct_score, make
from .test_proposal_control import good


def scalar_score(score):
    _, g, r = score
    return sum((sum(row, F()) for row in g), F()) + sum(
        ((i + 1) * value for i, value in enumerate(r)), F()
    )


def scalar_moments(law, values):
    mean = sum((p * values[w] for w, p in law.items()), F())
    return mean, sum((p * (values[w] - mean) ** 2 for w, p in law.items()), F())


class ConditionalPrefixTests(unittest.TestCase):
    def test_original_word_and_anchor_posterior_from_independent_joint(self):
        actions = triples = 0
        for n, fixed in ((2, {}), (3, {}), (4, {3: 5}), (3, {0: 0})):
            base, joint = make(n, fixed)
            grouped = defaultdict(lambda: defaultdict(lambda: F()))
            anchors = defaultdict(lambda: defaultdict(lambda: F()))
            for (word, a, action), p in joint.items():
                grouped[action][word] += p
                anchors[action, word][a] += p
            for action, words in grouped.items():
                total = sum(words.values(), F())
                law, rho = conditional_prefix_law(base, action)
                self.assertEqual(law, {w: p / total for w, p in words.items()})
                for word, mass in words.items():
                    actual = anchors[action, word]
                    for i in range(n):
                        self.assertEqual(actual.get(i, F()) / mass, rho[i])
                actions += 1
            triples += len(joint)
        print(
            json.dumps(
                {"conditional_original_laws": 4, "actions": actions, "joint_triples": triples}
            )
        )

    def test_full_semantic_baseline_is_kept_and_exact_projection_is_stronger(self):
        base, joint = make(3)
        grouped = defaultdict(list)
        full_mean, posterior_mean = F(), F()
        for (word, a, action), p in joint.items():
            reward = F(any(i == 0 and v == 1 for i, v in action))
            baseline = F(1, 3)
            h = (reward - baseline - F(2, 3) * good(base, word)) * scalar_score(
                direct_score(base, word, a, action, base.prior)
            )
            full_mean += p * h
            grouped[action].append((word, p))
        positive_hidden = False
        for action, entries in grouped.items():
            probability = sum((p for _, p in entries), F())
            law, _ = conditional_prefix_law(base, action)
            reward = F(any(i == 0 and v == 1 for i, v in action))
            values = {
                word: (reward - F(1, 3) - F(2, 3) * good(base, word))
                * scalar_score(base.cheap_anchor_score(word, action))
                for word in law
            }
            mean, variance = scalar_moments(law, values)
            s = scalar_score(base.action_statistics(action)[1:])
            semantic_projection = sum(
                (
                    p * F(good(base, w)) * scalar_score(base.cheap_anchor_score(w, action))
                    for w, p in law.items()
                ),
                F(),
            )
            self.assertEqual(mean, (reward - F(1, 3)) * s - F(2, 3) * semantic_projection)
            posterior_mean += probability * mean
            positive_hidden |= variance > 0
        self.assertEqual(full_mean, posterior_mean)
        self.assertTrue(positive_hidden)

    def test_replicated_variance_identity_by_complete_independent_enumeration(self):
        base, joint = make(2)
        grouped = defaultdict(lambda: F())
        for (_, _, action), p in joint.items():
            grouped[action] += p
        visible, hidden, distributions = F(), F(), {}
        overall_mean = F()
        for action, p in grouped.items():
            law, _ = conditional_prefix_law(base, action)
            reward = F(any(i == 0 and v == 1 for i, v in action))
            values = {
                w: (reward - F(good(base, w))) * scalar_score(base.cheap_anchor_score(w, action))
                for w in law
            }
            mean, variance = scalar_moments(law, values)
            overall_mean += p * mean
            hidden += p * variance
            distributions[action] = law, values, mean
        visible = sum(
            (p * (distributions[a][2] - overall_mean) ** 2 for a, p in grouped.items()), F()
        )
        for count in (1, 2, 4):
            mean, second = F(), F()
            for action, action_probability in grouped.items():
                law, values, _ = distributions[action]
                for words in itertools.product(law, repeat=count):
                    probability = action_probability
                    for w in words:
                        probability *= law[w]
                    value = sum((values[w] for w in words), F()) / count
                    mean += probability * value
                    second += probability * value**2
            self.assertEqual(mean, overall_mean)
            self.assertEqual(second - mean**2, visible + hidden / count)
        self.assertGreater(hidden, 0)
        print(
            json.dumps(
                {
                    "iid_replicas_exact_counts": [1, 2, 4],
                    "visible_variance": str(visible),
                    "hidden_variance": str(hidden),
                }
            )
        )

    def test_correlated_strata_and_exact_enumeration_controls(self):
        base, joint = make(3)
        actions = sorted({a for _, _, a in joint})
        checks = 0
        for action in actions:
            law, _ = conditional_prefix_law(base, action)
            values = {
                w: F(good(base, w)) * scalar_score(base.cheap_anchor_score(w, action)) for w in law
            }
            mean, variance = scalar_moments(law, values)
            for count in (1, 2, 4, 8):
                strata = stratified_laws(law, count)
                self.assertTrue(all(sum(row.values(), F()) == 1 for row in strata))
                reconstructed = {
                    w: sum((row.get(w, F()) for row in strata), F()) / count for w in law
                }
                self.assertEqual(reconstructed, law)
                means_and_variances = [scalar_moments(row, values) for row in strata]
                self.assertEqual(sum((m for m, _ in means_and_variances), F()) / count, mean)
                self.assertLessEqual(
                    sum((v for _, v in means_and_variances), F()) / count**2, variance / count
                )
                # Full enumeration computes mean with no auxiliary variance.
                self.assertEqual(sum((p * values[w] for w, p in law.items()), F()), mean)
                checks += 1
        with self.assertRaisesRegex(ValueError, "zero conditional"):
            conditional_prefix_law(base, ((0, 5),))
        print(
            json.dumps(
                {
                    "conditional_correlated_strata_checks": checks,
                    "exact_enumeration_control_preserved": True,
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
