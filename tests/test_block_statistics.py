"""Independent dyadic mass oracle; CPU-only normal CI, no timing claim."""

import importlib
import math
import unittest
from fractions import Fraction
from random import Random

import numpy as np

b = importlib.import_module("attempts.28-streamed-grammar-head.work.block_stats")


def check_original_sums(test, matrix, partition, stats):
    for row, (values, totals, low) in enumerate(
        zip(matrix, stats.totals, stats.minimum_exponents, strict=True)
    ):
        unit = Fraction(2) ** (low - 1074)
        for block, total in zip(partition.blocks, totals, strict=True):
            expected = sum((Fraction(float(values[t])) for t in block), Fraction())
            test.assertEqual(total * unit, expected, (row, block))
        test.assertEqual(sum(totals) * unit, sum(map(Fraction, map(float, values))))


class BlockStatisticsTests(unittest.TestCase):
    def test_every_block_matches_independent_fraction_and_zero_aliases(self):
        rng = Random(2026101129)
        for v in (1, 7, 513, 1025):
            matrix = np.array(
                [
                    [
                        math.ldexp(float(rng.randrange(1, 1 << 52)), rng.randrange(-1074, 960))
                        for _ in range(v)
                    ]
                    for _ in range(2)
                ],
                dtype=np.float64,
            )
            if v > 1:
                matrix[0, 0], matrix[1, 0] = 0.0, -0.0
                matrix[0, 1], matrix[1, 1] = np.nextafter(0.0, 1.0), np.finfo(np.float64).max
            for size in (1, 127, 512, 1024):
                p = b.Partition([i % 5 for i in range(v)], 5, size)
                stats = b.numpy_stats(matrix, p)
                check_original_sums(self, matrix, p, stats)
                for values, sums, low in zip(
                    matrix, stats.class_sums(), stats.minimum_exponents, strict=True
                ):
                    for cid, mass in enumerate(sums):
                        self.assertEqual(
                            mass * Fraction(2) ** (low - 1074),
                            sum(
                                (
                                    Fraction(float(x))
                                    for t, x in enumerate(values)
                                    if p.class_of[t] == cid
                                ),
                                Fraction(),
                            ),
                        )

    def test_partition_bad_numeric_rows_and_scale_are_explicit(self):
        p = b.Partition((0, 1), 2)
        for value in (float("nan"), float("inf"), -float("inf"), -1.0):
            with self.assertRaisesRegex(ValueError, "finite"):
                b.numpy_stats(np.array([[1.0, value]]), p)
        with self.assertRaisesRegex(ValueError, "zero original"):
            b.numpy_stats(np.zeros((1, 2)), p)
        for mapping, count, size in (
            ((), 1, 512),
            ((-1,), 2, 512),
            ((True,), 2, 512),
            ((0,), 0, 512),
            ((0,), 1, 1025),
        ):
            with self.assertRaises(ValueError):
                b.Partition(mapping, count, size)
        with self.assertRaisesRegex(ValueError, "scale"):
            b.integer_weight(np.nextafter(0.0, 1.0), 1)
        self.assertEqual(b.integer_weight(0.5, 1020), 1 << 53)


if __name__ == "__main__":
    unittest.main()
