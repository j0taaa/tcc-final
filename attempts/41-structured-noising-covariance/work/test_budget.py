"""All-budget finite atom obligations and a preserved variance counterexample."""

import itertools
import unittest
from fractions import Fraction as Q
from math import comb, prod


def choose(n, k):
    return comb(n, k) if 0 <= k <= n else 0


def falling(n, k):
    return prod(range(n - k + 1, n + 1)) if 0 <= k <= n else 0


def frontier(m, t, budget):
    return sum(
        (
            Q(choose(t, r) * choose(m - t, budget - r), comb(m, budget))
            * max(Q(0), Q(2 * r, budget) - 1)
            for r in range(budget + 1)
        ),
        Q(0),
    )


def circle_joint(sizes):
    joint = [[Q(0) for _ in sizes] for _ in sizes]
    orders = list(itertools.permutations(range(len(sizes))))
    n = sum(sizes)
    for order in orders:
        tape = [i for i in order for _ in range(2 * sizes[i])]
        for q, i in enumerate(tape):
            joint[i][tape[(q + n) % (2 * n)]] += Q(1, 2 * n * len(orders))
    return joint


class BudgetTests(unittest.TestCase):
    def test_even_odd_and_catalan_finite_population_formula(self):
        checked = 0
        for m in range(4, 33):
            for t in range(m + 1):
                for r in range(1, (m - 1) // 2 + 1):
                    even = frontier(m, t, 2 * r)
                    self.assertEqual(even, frontier(m, t, 2 * r + 1))
                    if 2 * r + 2 <= m:
                        delta = Q(comb(2 * r, r), r + 1) * Q(
                            falling(t, r + 1) * falling(m - t, r + 1),
                            falling(m, 2 * r + 2),
                        )
                        self.assertEqual(even - frontier(m, t, 2 * r + 2), delta)
                    checked += 1
        self.assertEqual(checked, 5556)

    def test_balanced_atoms_do_not_imply_arbitrary_event_safety(self):
        sizes = (1, 1, 3, 3)
        joint = circle_joint(sizes)
        for i, n in enumerate(sizes):
            self.assertEqual(sum(joint[i]), Q(n, 8))
            self.assertEqual(joint[i][i], max(Q(0), Q(2 * n, 8) - 1))
        event = sum(joint[i][j] for i in (0, 1) for j in (0, 1))
        self.assertEqual(event, Q(1, 12))
        self.assertGreater(event, Q(1, 16))


if __name__ == "__main__":
    unittest.main()
