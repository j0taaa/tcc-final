"""Independent exact categorical and complete small conditional-word laws."""

import itertools
import json
import random
import unittest
from collections import defaultdict
from fractions import Fraction as F

import numpy as np

from .conditional_floating import ConditionalFloatSampler, IntegerCategorical
from .conditional_prefix import conditional_prefix_law
from .prefix_anchor import PrefixAnchor
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .test_prefix_anchor import language, make


def configuration(n, fixed):
    original, _ = make(n, fixed)
    rows = original.rows
    gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in rows)
    exact = PrefixAnchor(language(), rows, gates, (F(1),) * n, fixed)
    weights = np.asarray(rows, dtype=float)
    for i, v in fixed.items():
        weights[i] = 0
        weights[i, v] = 1
    floating = PrefixPlanner(PrefixFloatPlan(language()), weights, fixed, 0.0)
    return exact, floating


def stratum_law(categorical, count, j):
    start, result = 0, {}
    for index, mass in zip(categorical.ids, categorical.counts, strict=True):
        end = start + mass
        overlap = min(count * end, (j + 1) * categorical.total) - max(
            count * start, j * categorical.total
        )
        if overlap > 0:
            result[index] = F(overlap, categorical.total)
        start = end
    return result


def exact_tree(sampler, prefix=(), state=0, phase="class", cls=None):
    """Independent finite decision tree, including the final posterior anchor."""
    i = len(prefix)
    if phase == "anchor":
        categorical = sampler.anchor
        return categorical, {a: (prefix, a) for a in categorical.ids}
    if phase == "class":
        categorical = sampler.classes(i, state)
        return categorical, {
            c: exact_tree(sampler, prefix, state, "token", c) for c in categorical.ids
        }
    categorical = sampler.tokens(i, cls)
    following = int(sampler.plan.effects[cls, state])
    children = {}
    for index in categorical.ids:
        word = (*prefix, int(sampler.plan.members[cls][index]))
        children[index] = exact_tree(
            sampler, word, following, "anchor" if following == 21 else "class"
        )
    return categorical, children


def one_and_pair(tree):
    if not isinstance(tree[0], IntegerCategorical):
        return {tree: F(1)}, {(tree, tree): F(1)}
    categorical, children = tree
    child_laws = {i: one_and_pair(child) for i, child in children.items()}
    one, pair = defaultdict(F), defaultdict(F)
    for i, probability in categorical.probabilities().items():
        for leaf, p in child_laws[i][0].items():
            one[leaf] += probability * p
    left, right = (stratum_law(categorical, 2, j) for j in range(2))
    for i, j in itertools.product(categorical.ids, repeat=2):
        probability = (
            left.get(i, F()) * right.get(j, F()) + right.get(i, F()) * left.get(j, F())
        ) / 2
        if not probability:
            continue
        if i == j:
            for leaves, p in child_laws[i][1].items():
                pair[leaves] += probability * p
        else:
            for a, pa in child_laws[i][0].items():
                for b, pb in child_laws[j][0].items():
                    pair[a, b] += probability * pa * pb
    return dict(one), dict(pair)


class ConditionalFloatingTests(unittest.TestCase):
    def test_prefix_history_pair_law_negative_covariance_for_ALL_scores(self):
        checks = 0
        for n, action in ((2, ((1, 5),)), (3, ((2, 5),)), (3, ((0, 0), (2, 5)))):
            _, planner = configuration(n, {})
            sampler = ConditionalFloatSampler(planner, action)
            one, pair = one_and_pair(exact_tree(sampler))
            self.assertEqual(sum(one.values(), F()), 1)
            self.assertEqual(sum(pair.values(), F()), 1)
            leaves = sorted(one)
            for a in leaves:
                self.assertEqual(sum((p for (x, _), p in pair.items() if x == a), F()), one[a])
                self.assertEqual(sum((p for (_, y), p in pair.items() if y == a), F()), one[a])
            # Exact Schur/LDL positivity of minus covariance: covers ANY h on leaves.
            matrix = [[one[a] * one[b] - pair.get((a, b), F()) for b in leaves] for a in leaves]
            size = len(matrix)
            for i in range(size):
                self.assertGreaterEqual(matrix[i][i], 0)
                if not matrix[i][i]:
                    self.assertTrue(all(matrix[i][j] == matrix[j][i] == 0 for j in range(i, size)))
                    continue
                for j in range(i + 1, size):
                    for k in range(i + 1, size):
                        matrix[j][k] -= matrix[j][i] * matrix[i][k] / matrix[i][i]
            checks += size
        print(
            json.dumps({"exact_prefix_pair_kernels": 3, "all_score_PSD_leaf_coordinates": checks})
        )

    def test_exact_dyadic_tickets_subnormals_and_arbitrary_group_sizes(self):
        checked = 0
        for weights in (
            (0.0, 0.25, 0.5, 0.125),
            (1.0, 2.0**-100, 0.0, 2.0**-1074),
            (1e300, 1e-300),
        ):
            categorical = IntegerCategorical(weights)
            expected = {i: F(float(w)) for i, w in enumerate(weights) if w > 0}
            total = sum(expected.values(), F())
            self.assertEqual(
                categorical.probabilities(), {i: w / total for i, w in expected.items()}
            )
            start = 0
            for index, mass in zip(categorical.ids, categorical.counts, strict=True):
                self.assertEqual(categorical.ticket(start), index)
                self.assertEqual(categorical.ticket(start + mass - 1), index)
                start += mass
            for count in (1, 2, 3, 4, 5, 7):
                strata = [stratum_law(categorical, count, j) for j in range(count)]
                self.assertTrue(all(sum(s.values(), F()) == 1 for s in strata))
                for index, p in categorical.probabilities().items():
                    self.assertEqual(sum((s.get(index, F()) for s in strata), F()) / count, p)
                checked += 1
        for weights in ((0.0, 0.0), (-1.0, 1.0), (np.nan, 1.0), (np.inf, 1.0)):
            with self.assertRaises(ValueError):
                IntegerCategorical(weights)
        print(
            json.dumps(
                {
                    "dyadic_categorical_stratum_laws": checked,
                    "smallest_positive_binary64_ID_kept": True,
                }
            )
        )

    def test_complete_numerical_word_law_versus_independent_rational_posterior(self):
        queries, maximum = 0, 0.0
        for n, fixed in ((2, {}), (3, {}), (3, {2: 5}), (3, {0: 0})):
            exact, floating = configuration(n, fixed)
            for size in range(1, len(exact.active) + 1):
                for positions in itertools.combinations(exact.active, size):
                    for tokens in itertools.product(range(8), repeat=size):
                        action = tuple(zip(positions, tokens, strict=True))
                        if not exact.action_statistics(action)[0]:
                            continue
                        reference, _ = conditional_prefix_law(exact, action)
                        sampler = ConditionalFloatSampler(floating, action)
                        law = {w: sampler.word_probability(w) for w in reference}
                        self.assertEqual(sum(law.values(), F()), 1)
                        difference = float(
                            sum((abs(p - reference[w]) for w, p in law.items()), F())
                        )
                        maximum = max(maximum, difference)
                        self.assertLessEqual(difference, 1e-12)
                        queries += 1
        print(
            json.dumps(
                {"complete_numeric_conditional_laws": queries, "maximum_L1_vs_Fraction": maximum}
            )
        )

    def test_iid_correlated_batches_original_ids_and_global_streams(self):
        exact, floating = configuration(3, {2: 5})
        original_weights = floating.weights.copy()
        sampler = ConditionalFloatSampler(floating, ((1, 3),))
        law, _ = conditional_prefix_law(exact, ((1, 3),))
        py_before, np_before = random.getstate(), np.random.get_state()
        for stratified in (False, True):
            for seed in range(12):
                draws = sampler.sample(4, random.Random(seed), stratified)
                self.assertEqual(len(draws), 4)
                for word, anchor in draws:
                    self.assertIn(word, law)
                    self.assertEqual(word[1], 3)
                    self.assertEqual(word[2], 5)
                    self.assertEqual(anchor, 1)
        self.assertEqual(random.getstate(), py_before)
        self.assertEqual(np.random.get_state()[0], np_before[0])
        np.testing.assert_array_equal(np.random.get_state()[1], np_before[1])
        np.testing.assert_array_equal(floating.weights, original_weights)
        self.assertGreater(sampler.cache_payload_bytes(), 0)


if __name__ == "__main__":
    unittest.main()
