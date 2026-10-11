"""Finite transcript identities and an independent absorbing-chain oracle."""

import importlib
import itertools
import math
import unittest
from collections import defaultdict
from fractions import Fraction as F

pair = importlib.import_module("attempts.34-oracle-diversity-frontier.work.ruin").pair


def solve(matrix, rhs):
    """Small rational Gaussian elimination, independent of the sampling code."""
    rows = [[*row, value] for row, value in zip(matrix, rhs, strict=True)]
    for col in range(len(rows)):
        pivot = next(i for i in range(col, len(rows)) if rows[i][col])
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        rows[col] = [v / scale for v in rows[col]]
        for i in range(len(rows)):
            if i != col:
                scale = rows[i][col]
                rows[i] = [a - scale * b for a, b in zip(rows[i], rows[col], strict=True)]
    return [row[-1] for row in rows]


def chain(r, p):
    """Solve absorption and cost equations on ALL live states simultaneously."""
    matrix = [[F(i == j) for j in range(1, r)] for i in range(1, r)]
    for i in range(1, r):
        if i > 1:
            matrix[i - 1][i - 2] -= 1 - p
        if i < r - 1:
            matrix[i - 1][i] -= p
    hit = solve(matrix, [F() for _ in range(r - 2)] + [p])
    cost = solve(matrix, [F(1) for _ in range(r - 1)])
    j11 = p * hit[0]
    j01 = (1 - p) * hit[-1]
    expected = 1 + p * cost[0] + (1 - p) * cost[-1]
    return j11, j01, expected


def excursion_coeff(r, h):
    # Number of positive excursions of length2h, first two steps UP,
    # avoiding the barrier r. Transfer counts do not call the sampler.
    if r <= 2:
        return 0
    counts = {2: 1}
    for _ in range(2 * h - 3):
        after = defaultdict(int)
        for state, count in counts.items():
            for target in (state - 1, state + 1):
                if 0 < target < r:
                    after[target] += count
        counts = after
    return counts.get(1, 0)


class OracleDiversityFrontierTests(unittest.TestCase):
    def test_cap_identities_for_every_small_transcript_and_every_probability(self):
        # Group by total input ones. Matching Bernstein coefficients proves
        # the marginal identity for ALL p, not only the grid below.
        for cap in range(2, 11):
            for r in range(2, 8):
                groups = defaultdict(lambda: [0, 0, 0, 0])
                for bits in itertools.product((False, True), repeat=cap):
                    first, second, used = pair(iter(bits).__next__, bool, barrier=r, max_draws=cap)
                    self.assertIs(first, bits[0])
                    self.assertLessEqual(used, cap)
                    count = groups[sum(bits)]
                    count[0] += 1
                    count[1] += second
                    count[2] += first and second
                    count[3] += used
                for ones, (total, emitted, _, _) in groups.items():
                    self.assertEqual(total, math.comb(cap, ones))
                    self.assertEqual(F(emitted, total), F(ones, cap))
                for p in (F(0), F(1, 17), F(1, 3), F(1, 2), F(16, 17), F(1)):
                    j11 = sum(c[2] * p**k * (1 - p) ** (cap - k) for k, c in groups.items())
                    expected = sum(c[3] * p**k * (1 - p) ** (cap - k) for k, c in groups.items())
                    gain = sum(
                        excursion_coeff(r, h) * (p * (1 - p)) ** h for h in range(2, cap // 2 + 1)
                    )
                    self.assertEqual(p**2 - j11, gain)
                    self.assertLessEqual(expected, r)

    def test_unbounded_law_cost_and_uniform_frontier_from_linear_equations(self):
        for r in range(2, 13):
            for p in (F(1, 101), F(1, 7), F(1, 3), F(1, 2), F(6, 7), F(100, 101)):
                j11, j01, expected = chain(r, p)
                self.assertEqual(j11 + j01, p)
                self.assertEqual(expected, r)
                predicted = (
                    F(1, 2 * r) if p == F(1, 2) else (2 * p - 1) * p**r / (p**r - (1 - p) ** r)
                )
                self.assertEqual(j11, predicted)
                eta = (p**2 - j11) / min(p**2, (1 - p) ** 2)
                self.assertGreaterEqual(eta, 1 - F(2, r))
                if p == F(1, 2):
                    self.assertEqual(eta, 1 - F(2, r))
        for b in (F(2), F(7, 3), F(3), F(17, 4), F(7)):
            m = b.numerator // b.denominator
            lam = b - m
            a, _, ca = chain(m, F(1, 2))
            z, _, cz = chain(m + 1, F(1, 2))
            self.assertEqual((1 - lam) * ca + lam * cz, b)
            eta = 1 - 4 * ((1 - lam) * a + lam * z)
            self.assertEqual(eta, 1 - 2 * ((1 - lam) / m + lam / (m + 1)))

    def test_full_payloads_aliases_failures_and_all_events(self):
        # Separate original IDs0/1 may share bytes; ID2 may denote a failure.
        probabilities = (F(1, 6), F(1, 3), F(1, 2))
        for classes in itertools.product((False, True), repeat=3):
            joint = defaultdict(F)
            for ids in itertools.product(range(3), repeat=6):
                first, second, _ = pair(
                    iter(ids).__next__, classes.__getitem__, barrier=3, max_draws=6
                )
                joint[first, second] += math.prod(probabilities[i] for i in ids)
            for i in range(3):
                self.assertEqual(sum(joint[i, j] for j in range(3)), probabilities[i])
                self.assertEqual(sum(joint[j, i] for j in range(3)), probabilities[i])
            for event in itertools.product((False, True), repeat=3):
                success = sum(
                    p for p, included in zip(probabilities, event, strict=True) if included
                )
                covered = sum(m for (i, j), m in joint.items() if event[i] or event[j])
                self.assertGreaterEqual(covered, 2 * success - success**2)

    def test_validation_before_any_draw(self):
        def forbidden():
            self.fail("invalid input consulted the oracle")

        for r, cap in ((1, 2), (True, 2), (2.0, 2), (3, 1), (3, True), (3, 2.0)):
            with self.assertRaises(ValueError):
                pair(forbidden, bool, barrier=r, max_draws=cap)


if __name__ == "__main__":
    unittest.main()
