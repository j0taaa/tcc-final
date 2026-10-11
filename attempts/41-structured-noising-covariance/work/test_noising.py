"""Independent finite matrix/cost obligations; constructed cases are NOT benchmarks."""

import itertools
import unittest
from collections import Counter
from fractions import Fraction as Q
from math import prod

from .kernel import pair
from .noising import evaluate_pair


def partitions(n, prefix=()):
    if len(prefix) == n:
        yield prefix
    else:
        for label in range(max(prefix, default=-1) + 2):
            yield from partitions(n, (*prefix, label))


def covariance(joint, values):
    m, d = len(values), len(values[0])
    mean = [sum(Q(v[i]) for v in values) / m for i in range(d)]
    return [
        [
            sum(p * values[a][i] * values[b][j] for (a, b), p in joint.items()) - mean[i] * mean[j]
            for j in range(d)
        ]
        for i in range(d)
    ]


def determinant(a):
    if len(a) == 1:
        return a[0][0]
    return sum(
        (-1) ** j * a[0][j] * determinant([r[:j] + r[j + 1 :] for r in a[1:]])
        for j in range(len(a))
    )


class NoisingTests(unittest.TestCase):
    def test_full_matrix_law_and_covariance_order(self):
        checked = 0
        for m in (4, 5):
            denominator = prod(range(m - 3, m + 1))
            values = [(i % 2, i - m // 2, i * i % 3) for i in range(m)]
            for keys in partitions(m):
                counts = Counter()
                for tape in itertools.permutations(range(m), 4):
                    for ticket in range(6):
                        items, coins = iter(tape), []

                        def choose(n, ticket=ticket, coins=coins):
                            coins.append(n)
                            return ticket % n

                        x, y, calls = pair(
                            lambda items=items: next(items), keys.__getitem__, choose
                        )
                        self.assertLessEqual(len(coins), 1)
                        self.assertIn(calls, (3, 4))
                        counts[x, y] += 1
                joint = {k: Q(c, 6 * denominator) for k, c in counts.items()}
                self.assertEqual(sum(joint.values()), 1)
                for s in range(m):
                    self.assertEqual(sum(p for (a, _), p in joint.items() if a == s), Q(1, m))
                    self.assertEqual(sum(p for (_, b), p in joint.items() if b == s), Q(1, m))
                actual = covariance(joint, values)
                class_counts = Counter(keys)
                means = [Q(sum(v[i] for v in values), m) for i in range(3)]
                groups = [
                    [v for s, v in enumerate(values) if keys[s] == label] for label in class_counts
                ]
                sizes = [len(v) for v in groups]
                offsets = [
                    [sum(Q(v[i]) for v in group) / len(group) - means[i] for i in range(3)]
                    for group in groups
                ]
                h = [
                    sum(n * n * g[i] for n, g in zip(sizes, offsets, strict=True)) for i in range(3)
                ]
                s2 = sum(n * n for n in sizes)
                for i in range(3):
                    for j in range(3):
                        predicted = (
                            -(m * m - s2)
                            * sum(n * n * g[i] * g[j] for n, g in zip(sizes, offsets, strict=True))
                            - h[i] * h[j]
                            + (4 * m - 6)
                            * sum(n * g[i] * g[j] for n, g in zip(sizes, offsets, strict=True))
                        ) / denominator
                        for n, group in zip(sizes, groups, strict=True):
                            if n < 2:
                                continue
                            mu_i, mu_j = (
                                sum(Q(v[i]) for v in group) / n,
                                sum(Q(v[j]) for v in group) / n,
                            )
                            sigma = sum((v[i] - mu_i) * (v[j] - mu_j) for v in group) / n
                            diagonal = Q(n * (n - 1) * (n - 2) * (2 * m - n - 3), denominator)
                            predicted -= diagonal * sigma / (n - 1)
                        self.assertEqual(actual[i][j], predicted)
                        self.assertEqual(actual[i][j], actual[j][i])
                # All principal minors: independent exact PSD check of -C.
                for k in (1, 2, 3):
                    for indices in itertools.combinations(range(3), k):
                        minor = [[-actual[i][j] for j in indices] for i in indices]
                        self.assertGreaterEqual(determinant(minor), 0)
                checked += 1
        self.assertEqual(checked, 67)

    def test_mirror_counterexample_and_stronger_analytic_control(self):
        g = [(0,), (1,), (1,), (0,)]  # Gradient divided by sigmoid(theta).
        iid = {(a, b): Q(1, 16) for a, b in itertools.product(range(4), repeat=2)}
        mirror = {(s, s ^ 3): Q(1, 4) for s in range(4)}
        analytic = {(s, s ^ 1): Q(1, 4) for s in range(4)}
        derangement = {(a, b): Q(1, 12) for a, b in itertools.permutations(range(4), 2)}
        single_var = Q(1, 4)
        expected = {"iid": Q(1, 8), "mirror": Q(1, 4), "analytic": Q(0), "derange": Q(1, 12)}
        for name, law in (
            ("iid", iid),
            ("mirror", mirror),
            ("analytic", analytic),
            ("derange", derangement),
        ):
            variance = (single_var + covariance(law, g)[0][0]) / 2
            self.assertEqual(variance, expected[name])
        # Analytic control is cheaper than C4 here: no empirical victory credit.

    def test_only_retained_states_call_expensive_evaluator(self):
        for seed in range(20):
            import random

            rng, cheap, expensive = random.Random(seed), [], []

            def prepare(s, cheap=cheap):
                cheap.append(s)
                return s

            def evaluate(s, expensive=expensive):
                expensive.append(s)
                return s * s

            _, _, calls = evaluate_pair(16, prepare, lambda s: s % 3, rng.randrange, evaluate)
            self.assertEqual(len(expensive), 2)
            self.assertEqual(len(cheap), calls)
            self.assertEqual(len(set(cheap)), calls)
            self.assertEqual(expensive[0], cheap[0])
            self.assertNotEqual(expensive[0], expensive[1])


if __name__ == "__main__":
    unittest.main()
