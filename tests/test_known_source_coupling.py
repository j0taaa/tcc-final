"""Exhaustive finite sources/proof obligations, not favourable neural benchmarks."""

import importlib
import itertools
import math
import unittest
from collections import Counter
from fractions import Fraction as F

kernel = importlib.import_module("attempts.39-known-source-coupling.work.kernel")
source = importlib.import_module("attempts.39-known-source-coupling.work.source")


def falling(n, k):
    return math.prod(n - i for i in range(k))


def partitions(n):
    def extend(prefix):
        if len(prefix) == n:
            yield tuple(prefix)
        else:
            for label in range(max(prefix) + 2):
                yield from extend([*prefix, label])

    yield from extend([0])


def law(keys, budgeted=False):
    n = len(keys)
    joint, work, weighted = Counter(), 0, 0
    coins = tuple(itertools.product(range(2), range(6))) if budgeted else ((0, u) for u in range(6))
    coins = tuple(coins)
    denominator = falling(n, 4) * len(coins)
    for tape in itertools.permutations(range(n), 4):
        for outer, inner in coins:
            original = [{"source": s, "key": keys[s]} for s in tape]
            iterator, used = iter(original), []
            random = iter((outer, inner) if budgeted else (inner,))

            def draw(iterator=iterator, used=used):
                item = next(iterator)
                used.append(item)
                return item

            sampler = kernel.pair_mean_three if budgeted else kernel.pair
            x, y, queries = sampler(draw, lambda item: item["key"], lambda k, r=random: next(r) % k)
            assert x is original[0] and y is not x and y in used[1:]
            assert queries == len(used)
            joint[x["source"], y["source"]] += 1
            work += queries
            weighted += sum(1 if item["source"] == n - 1 else 10 for item in used)
    return (
        {pair: F(c, denominator) for pair, c in joint.items()},
        F(work, denominator),
        F(weighted, denominator),
    )


class KnownSourceCouplingTests(unittest.TestCase):
    def test_every_partition_of_four_to_six_sources_all_raw_verifiers_and_exact_law(self):
        total = 0
        for n in range(4, 7):
            denominator = falling(n, 4)
            for keys in partitions(n):
                total += 1
                counts = Counter(keys)
                joint, work, _ = law(keys)
                c2 = F(sum(falling(t, 2) for t in counts.values()), falling(n, 2))
                c3 = F(sum(falling(t, 3) for t in counts.values()), falling(n, 3))
                self.assertEqual(work, 4 - 2 * c2 + c3)
                s2 = sum(t**2 for t in counts.values())
                for x, y in itertools.product(range(n), repeat=2):
                    a, b = counts[keys[x]], counts[keys[y]]
                    if x == y:
                        expected = 0
                    elif keys[x] == keys[y]:
                        expected = F(falling(a, 3) * (2 * n - a - 3), denominator * a * (a - 1))
                    else:
                        expected = F(n**2 + n * (a + b) - a * b - s2 - 6 * n + 7, denominator)
                    self.assertEqual(joint.get((x, y), 0), expected)
                for i in range(n):
                    self.assertEqual(sum(v for (x, _), v in joint.items() if x == i), F(1, n))
                    self.assertEqual(sum(v for (_, y), v in joint.items() if y == i), F(1, n))
                for key, size in counts.items():
                    diagonal = sum(v for (x, y), v in joint.items() if keys[x] == keys[y] == key)
                    self.assertEqual(
                        F(falling(size, 2), falling(n, 2)) - diagonal,
                        F(falling(size, 2) * falling(n - size, 2), denominator),
                    )
                scores = [tuple((mask >> i) & 1 for i in range(n)) for mask in range(2**n)]
                scores.append((-3, 1, 9, -4, 2, 0)[:n])
                for f in scores:
                    mean = F(sum(f), n)
                    covariance = sum(v * f[x] * f[y] for (x, y), v in joint.items()) - mean**2
                    self.assertLessEqual(covariance, 0)
                    centered, variances = {}, {}
                    for key, size in counts.items():
                        values = [F(f[i]) for i in range(n) if keys[i] == key]
                        average = sum(values) / size
                        centered[key] = average - mean
                        variances[key] = sum((v - average) ** 2 for v in values) / size
                    a = sum(counts[k] ** 2 * g**2 for k, g in centered.items())
                    b = sum(counts[k] ** 2 * g for k, g in centered.items())
                    c = sum(counts[k] * g**2 for k, g in centered.items())
                    expected = (-(n**2 - s2) * a - b**2 + (4 * n - 6) * c) / denominator
                    expected -= sum(
                        F(falling(size, 3) * (2 * n - size - 3), denominator)
                        * variances[k]
                        / (size - 1)
                        for k, size in counts.items()
                        if size > 1
                    )
                    self.assertEqual(covariance, expected)
        self.assertEqual(total, 270)

    def test_rank_lifting_is_uniform_distinct_and_mixture_retains_source_law(self):
        for n in range(4, 7):
            seen = Counter()
            for ranks in itertools.product(*(range(n - j) for j in range(4))):
                tape = iter(ranks)
                uniform = source.Source(n, lambda index: index, lambda _, r=tape: next(r))
                result = tuple(uniform() for _ in range(4))
                self.assertEqual(len(set(result)), 4)
                seen[result] += 1
                with self.assertRaises(ValueError):
                    uniform()
            self.assertEqual(len(seen), falling(n, 4))
            self.assertEqual(set(seen.values()), {1})
        keys = (0, 0, 0, 1, 2)
        original, work, _ = law(keys)
        mixed, mean_work, _ = law(keys, budgeted=True)
        self.assertEqual(mean_work, (work + 2) / 2)
        for x, y in itertools.product(range(5), repeat=2):
            derangement = F(1, 20) if x != y else 0
            self.assertEqual(mixed.get((x, y), 0), (original.get((x, y), 0) + derangement) / 2)

    def test_source_derangement_countercontrol_and_no_iid_wald_shortcut(self):
        joint, work, weighted = law((0, 0, 0, 1))
        self.assertEqual(work, F(13, 4))
        self.assertEqual(weighted, F(103, 4))
        self.assertNotEqual(weighted, work * F(31, 4))
        joint, _, _ = law((0, 0, 1, 2))
        f = (1, 0, 1, 0)
        covariance = sum(v * f[x] * f[y] for (x, y), v in joint.items()) - F(1, 4)
        self.assertEqual(covariance, 0)
        self.assertLess(-F(1, 4) / 3, covariance)  # Strong cheap derangement wins.

    def test_all_sixty_four_source_coarsenings_coverage_and_pathwise_query_omission(self):
        laws = {keys: law(keys)[0] for keys in partitions(4)}
        pairs = 0
        for fine in tuple(laws):
            for grouping in partitions(len(set(fine))):
                pairs += 1
                coarse = tuple(grouping[k] for k in fine)
                for mask in range(2 ** len(set(coarse))):
                    f = tuple((mask >> k) & 1 for k in coarse)
                    before = sum(v * f[x] * f[y] for (x, y), v in laws[fine].items())
                    after = sum(v * f[x] * f[y] for (x, y), v in laws[coarse].items())
                    self.assertLessEqual(after, before)
                for tape, uniform in itertools.product(itertools.permutations(range(4)), range(6)):
                    used = []
                    for keys in (fine, coarse):
                        iterator = iter(tape)
                        _, _, count = kernel.pair(
                            lambda r=iterator: next(r),
                            lambda s, k=keys: k[s],
                            lambda n, u=uniform: u % n,
                        )
                        used.append(count)
                    self.assertLessEqual(used[1], used[0])
        self.assertEqual(pairs, 60)
        # Score coarsening does NOT guarantee every mean-score variance:
        # this score is constant on the merged class, yet covariance worsens.
        f = (0, 0, 1, -1)
        before = sum(v * f[x] * f[y] for (x, y), v in laws[(0, 1, 2, 3)].items())
        after = sum(v * f[x] * f[y] for (x, y), v in laws[(0, 0, 1, 2)].items())
        self.assertEqual(before, -F(1, 6))
        self.assertEqual(after, 0)

    def test_finite_grid_coefficients_are_triangular_and_cap_three_has_no_robust_gain(self):
        for n, degree in itertools.product((4, 5, 8), (3, 4)):
            nodes = sorted(
                ((a, b) for a in range(degree + 1) for b in range(degree + 1 - a)),
                key=lambda x: (sum(x), x),
            )
            for row, (a, b) in enumerate(nodes):
                counts = (a, b, n - a - b)
                total, expectation = F(0), F(0)
                for col, (r, s) in enumerate(nodes):
                    powers = (r, s, degree - r - s)
                    product = math.prod(falling(t, k) for t, k in zip(counts, powers, strict=True))
                    if col > row:
                        self.assertEqual(product, 0)
                    if col == row:
                        self.assertGreater(product, 0)
                    probability = F(
                        math.factorial(degree) * product,
                        math.prod(math.factorial(k) for k in powers) * falling(n, degree),
                    )
                    total += probability
                    expectation += probability * F(r, degree)
                self.assertEqual(total, 1)
                self.assertEqual(expectation, F(a, n))
            for size in range(n + 1):
                clipped = sum(
                    F(
                        math.comb(degree, k) * falling(size, k) * falling(n - size, degree - k),
                        falling(n, degree),
                    )
                    * max(F(0), F(2 * k, degree) - 1)
                    for k in range(degree + 1)
                )
                expected = (
                    F(falling(size, 2), falling(n, 2))
                    if degree == 3
                    else F(falling(size, 3) * (2 * n - size - 3), falling(n, 4))
                )
                self.assertEqual(clipped, expected)


if __name__ == "__main__":
    unittest.main()
