"""Exact classical-reduction and query-obstruction oracles; NO model benchmark."""

import itertools
import unittest
from collections import Counter
from fractions import Fraction as Q
from math import prod

from .kernel import pair
from .label_kernel import pair_labels
from .test_noising import covariance, determinant, partitions

MATCHINGS = (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2)))


def pivotal_companion(tape, keys):
    """Original pivotal two half-inclusion updates, conditioned on the anchor."""
    scores = [sum(keys[tape[a]] == keys[tape[b]] for a, b in pairs) for pairs in MATCHINGS]
    allowed = [p for p, score in zip(MATCHINGS, scores, strict=True) if score == max(scores)]
    result = Counter()
    for pairs in allowed:
        for selected in itertools.product(*pairs):
            if 0 in selected:
                other = next(s for s in selected if s != 0)
                result[tape[other]] += Q(1, 2 * len(allowed))
    assert sum(result.values()) == 1
    return result


def rss_joint(keys):
    """Random class-order independent min/max pools, random output orientation."""
    m, sizes = len(keys), Counter(keys)
    orders = list(itertools.permutations(sizes))
    result = Counter()
    for order in orders:
        position = {c: i for i, c in enumerate(order)}
        minimum, maximum = [], []
        for c in keys:
            above = sum(n for k, n in sizes.items() if position[k] > position[c])
            below = sum(n for k, n in sizes.items() if position[k] < position[c])
            minimum.append(Q(sizes[c] + 2 * above, m * m))
            maximum.append(Q(sizes[c] + 2 * below, m * m))
        assert sum(minimum) == sum(maximum) == 1
        for a, b in itertools.product(range(m), repeat=2):
            result[a, b] += (minimum[a] * maximum[b] + maximum[a] * minimum[b]) / (2 * len(orders))
    return result


class ReductionTests(unittest.TestCase):
    def test_source_joint_pivotal_equivalence_and_separate_label_costs(self):
        checked = 0
        for m in (4, 5):
            denominator = prod(range(m - 3, m + 1))
            for keys in partitions(m):
                original, lazy, pivotal = Counter(), Counter(), Counter()
                raw_total = label_total = 0
                for tape in itertools.permutations(range(m), 4):
                    for s, weight in pivotal_companion(tape, keys).items():
                        pivotal[tape[0], s] += weight / denominator
                    for ticket in range(6):
                        x, y, _ = pair(
                            iter(tape).__next__,
                            keys.__getitem__,
                            lambda n, ticket=ticket: ticket % n,
                        )
                        original[x, y] += Q(1, 6 * denominator)
                        labels = []

                        def key(s, labels=labels, keys=keys):
                            labels.append(s)
                            return keys[s]

                        x, y, calls = pair_labels(
                            iter(tape).__next__, key, lambda n, ticket=ticket: ticket % n
                        )
                        lazy[x, y] += Q(1, 6 * denominator)
                        self.assertEqual(x, tape[0])
                        self.assertIn(len(labels), (2, 3, 4))
                        raw_total += calls
                        label_total += len(labels)
                self.assertEqual(original, pivotal)
                self.assertEqual(lazy, pivotal)
                sizes = Counter(keys).values()
                c2 = sum(Q(n * (n - 1), m * (m - 1)) for n in sizes)
                c3 = sum(Q(n * (n - 1) * (n - 2), m * (m - 1) * (m - 2)) for n in sizes)
                self.assertEqual(Q(raw_total, 6 * denominator), 4 - 2 * c2 + c3)
                self.assertEqual(Q(label_total, 6 * denominator), 4 - 4 * c2 + 2 * c3)
                checked += 1
        self.assertEqual(checked, 67)

    def test_iid_ranked_set_matrix_and_conditional_comparison(self):
        for m in (4, 5):
            values = [(s % 2, s - m // 2, s * s % 3) for s in range(m)]
            mean = [Q(sum(v[i] for v in values), m) for i in range(3)]
            for keys in partitions(m):
                rss = covariance(rss_joint(keys), values)
                c4 = Counter()
                for tape in itertools.product(range(m), repeat=4):
                    for ticket in range(6):
                        x, y, _ = pair_labels(
                            iter(tape).__next__,
                            keys.__getitem__,
                            lambda n, ticket=ticket: ticket % n,
                        )
                        c4[x, y] += Q(1, 6 * m**4)
                actual = covariance(c4, values)
                groups = [[values[s] for s in range(m) if keys[s] == c] for c in set(keys)]
                ps = [Q(len(g), m) for g in groups]
                gs = [
                    [sum(Q(v[i]) for v in g) / len(g) - mean[i] for i in range(3)] for g in groups
                ]
                s2 = sum(p * p for p in ps)
                h = [sum(p * p * g[i] for p, g in zip(ps, gs, strict=True)) for i in range(3)]
                improvement = []
                for i in range(3):
                    row = []
                    for j in range(3):
                        a = sum(p * p * g[i] * g[j] for p, g in zip(ps, gs, strict=True))
                        self.assertEqual(-rss[i][j], ((1 + s2) * a - h[i] * h[j]) / 3)
                        self.assertEqual(-actual[i][j], (1 - s2) * a + h[i] * h[j])
                        row.append(rss[i][j] - actual[i][j])
                    improvement.append(row)
                if s2 <= Q(1, 2):
                    for k in (1, 2, 3):
                        for indices in itertools.combinations(range(3), k):
                            minor = [[improvement[i][j] for j in indices] for i in indices]
                            self.assertGreaterEqual(determinant(minor), 0)

    def test_required_query_obstructions_allow_unclassified_outputs_and_clones(self):
        for observed in ((), (0,), (0, 1), (0, 1, 2)):
            completions = [
                (*observed, *remaining)
                for remaining in itertools.product(range(3), repeat=4 - len(observed))
            ]
            for anchor, companion in itertools.product(range(4), repeat=2):
                # Every possible returned pair violates some hidden size-two class.
                violates = any(
                    sum(keys[s] == c for s in (anchor, companion)) != 1
                    for keys in completions
                    for c, n in Counter(keys).items()
                    if n == 2
                )
                self.assertTrue(violates, (observed, anchor, companion))


if __name__ == "__main__":
    unittest.main()
