"""Independent finite rational oracles; no performance or priority claims."""

import importlib.util
import sys
import unittest
from bisect import bisect_left
from fractions import Fraction
from functools import partial
from itertools import pairwise, product
from pathlib import Path
from random import Random
from unittest.mock import patch

_SPEC = importlib.util.spec_from_file_location(
    "a79_numeric_tests", Path(__file__).with_name("numeric.py")
)
assert _SPEC is not None and _SPEC.loader is not None
numeric = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = numeric
_SPEC.loader.exec_module(numeric)
DFloat = numeric.DFloat
BinaryArithmetic = numeric.BinaryArithmetic
LazyThreshold = numeric.LazyThreshold


class BitTape(Random):
    """Finite specified bits: exhaustion is never silently padded with zeros."""

    def __init__(self, bits):
        super().__init__(0)
        self.bits = iter(bits)
        self.calls = 0

    def getrandbits(self, k):
        if k != 1:
            raise AssertionError("numeric layer requested more than one bit")
        self.calls += 1
        try:
            return next(self.bits)
        except StopIteration as error:
            raise EOFError("finite test source exhausted") from error


def tape_at(cell, width):
    return BitTape((cell >> j) & 1 for j in reversed(range(width)))


class RationalGrid:
    """Enumerate the format outright, rather than implementing its rounder."""

    def __init__(self, p):
        self.points = {
            Fraction(m) * Fraction(2) ** e: DFloat(m, e)
            for m in range(2 ** (p - 1), 2**p)
            for e in range(-24, 18)
        }
        self.values = sorted(self.points)

    def neighbors(self, value):
        if not value:
            return Fraction(0), Fraction(0)
        index = bisect_left(self.values, value)
        if self.values[index] == value:
            return value, value
        return self.values[index - 1], self.values[index]

    def nearest(self, value):
        low, high = self.neighbors(value)
        if not value:
            return DFloat(0, 0)
        distances = (value - low, high - value)
        if distances[0] == distances[1]:
            return self.points[low] if self.points[low].mantissa % 2 == 0 else self.points[high]
        return self.points[low if distances[0] < distances[1] else high]


class NumericTests(unittest.TestCase):
    def test_nearest_conversion_against_enumerated_format(self):
        for p in range(2, 6):
            grid = RationalGrid(p)
            arithmetic = BinaryArithmetic(p, "nearest", BitTape([]))
            for n, shift in product(range(97), range(9)):
                value = Fraction(n, 2**shift)
                self.assertEqual(arithmetic.convert(value), grid.nearest(value), (p, value))
            self.assertEqual(arithmetic.stats["random_calls"], 0)

    def test_nearest_operations_against_enumerated_format(self):
        for p in range(2, 5):
            grid = RationalGrid(p)
            arithmetic = BinaryArithmetic(p, "nearest", BitTape([]))
            operands = [DFloat(m, e) for m, e in product(range(2 ** (p - 1), 2**p), (-5, 0, 3))]
            operands.append(DFloat(0, 0))
            for left, right in product(operands, repeat=2):
                a, b = numeric.as_fraction(left), numeric.as_fraction(right)
                self.assertEqual(arithmetic.add(left, right), grid.nearest(a + b))
                self.assertEqual(arithmetic.mul(left, right), grid.nearest(a * b))

    def test_ties_carry_and_arbitrary_exponents(self):
        arithmetic = BinaryArithmetic(3, "nearest", BitTape([]))
        for value, expected in (
            (Fraction(9, 8), DFloat(4, -2)),
            (Fraction(11, 8), DFloat(6, -2)),
            (Fraction(15, 8), DFloat(4, -1)),
        ):
            self.assertEqual(arithmetic.convert(value), expected)
        gap = 2**60
        self.assertEqual(arithmetic.mul(DFloat(7, gap), DFloat(7, -gap)), DFloat(6, 3))
        self.assertEqual(arithmetic.mul(DFloat(7, gap), DFloat(7, gap)), DFloat(6, 2 * gap + 3))
        self.assertEqual(arithmetic.mul(DFloat(4, -gap), DFloat(4, -gap)), DFloat(4, -2 * gap + 2))

    def assert_stochastic_cells(self, p, exact, operation):
        grid = RationalGrid(p)
        low, high = grid.neighbors(exact)
        theta = Fraction(0) if low == high else (exact - low) / (high - low)
        denominator = theta.denominator
        self.assertEqual(denominator & (denominator - 1), 0)
        width = denominator.bit_length() - 1
        upper_count = 0
        total = Fraction(0)
        for cell in range(denominator):
            source = tape_at(cell, width)
            arithmetic = BinaryArithmetic(p, "stochastic", source)
            actual = numeric.as_fraction(operation(arithmetic))
            self.assertIn(actual, (low, high))
            self.assertEqual(actual, high if Fraction(cell, denominator) < theta else low)
            upper_count += actual == high and low != high
            total += actual
            self.assertEqual(arithmetic.stats["random_calls"], source.calls)
            self.assertLessEqual(arithmetic.stats["random_bits"], width)
        self.assertEqual(upper_count, theta.numerator)
        self.assertEqual(total / denominator, exact)

    def test_stochastic_conversion_exact_noise_cells(self):
        for p, n in product((2, 3, 4), range(1, 48)):
            value = Fraction(n, 16)
            self.assert_stochastic_cells(
                p, value, lambda arithmetic, value=value: arithmetic.convert(value)
            )

    def test_stochastic_operations_exact_noise_cells(self):
        for p in (2, 3):
            operands = [DFloat(m, e) for m, e in product(range(2 ** (p - 1), 2**p), (-2, 0, 2))]
            for left, right in product(operands, repeat=2):
                a, b = numeric.as_fraction(left), numeric.as_fraction(right)
                self.assert_stochastic_cells(
                    p, a + b, lambda ar, left=left, right=right: ar.add(left, right)
                )
                self.assert_stochastic_cells(
                    p, a * b, lambda ar, left=left, right=right: ar.mul(left, right)
                )

    def test_common_uniform_monotonicity_unbiasedness_and_ratio_bound(self):
        p, width = 3, 5
        values = [Fraction(n, 32) for n in (33, 35, 36, 37, 39)]
        noise = []
        for cell in range(2**width):
            arithmetic = BinaryArithmetic(p, "stochastic", tape_at(cell, width))
            arithmetic.start_group()
            noise.append([numeric.as_fraction(arithmetic.convert(v)) / v for v in values])
            self.assertEqual(arithmetic.stats["groups"], 1)
            self.assertEqual(arithmetic.stats["random_bits"], len(arithmetic._uniform.prefix))
            self.assertLessEqual(arithmetic.stats["random_bits"], width)
        u = Fraction(1, 2 ** (p - 1))
        c = u * u / (4 * (1 + u))
        for i in range(len(values)):
            self.assertEqual(sum(row[i] for row in noise) / len(noise), 1)
            self.assertTrue(all(a[i] >= b[i] for a, b in pairwise(noise)))
            for j in range(len(values)):
                self.assertLessEqual(sum(row[i] / row[j] for row in noise) / len(noise), 1 + c)

    def test_lazy_rational_thresholds_by_uniform_cells(self):
        width = 6
        for denominator in range(1, 19):
            for numerator in range(denominator + 1):
                probability = Fraction(numerator, denominator)
                yes = unresolved = 0
                for cell in range(2**width):
                    source = tape_at(cell, width)
                    uniform = numeric.SharedUniformPrefix(partial(source.getrandbits, 1))
                    try:
                        result = uniform.less_than(LazyThreshold(numerator, denominator))
                    except EOFError:
                        unresolved += 1
                        self.assertLess(Fraction(cell, 2**width), probability)
                        self.assertLess(probability, Fraction(cell + 1, 2**width))
                    else:
                        yes += result
                        if result:
                            self.assertLessEqual(Fraction(cell + 1, 2**width), probability)
                        else:
                            self.assertGreaterEqual(Fraction(cell, 2**width), probability)
                self.assertLessEqual(unresolved, 1)
                self.assertLessEqual(Fraction(yes, 2**width), probability)
                self.assertGreaterEqual(Fraction(yes + unresolved, 2**width), probability)

    def test_huge_gap_is_compressed_and_refusals_are_explicit(self):
        gap = 2**60
        large, tiny = DFloat(256, 0), DFloat(257, -gap)
        threshold = LazyThreshold(257, 1, gap)
        self.assertEqual(
            (threshold.numerator, threshold.denominator, threshold.shift), (257, 512, gap - 9)
        )
        nearest = BinaryArithmetic(9, "nearest", BitTape([]))
        self.assertEqual(nearest.add(large, tiny), large)
        stochastic = BinaryArithmetic(9, "stochastic", BitTape([1]))
        self.assertEqual(stochastic.add(large, tiny), large)
        self.assertEqual(stochastic.stats["random_bits"], 1)
        capped = BinaryArithmetic(9, "stochastic", BitTape([0] * 65), max_random_bits=64)
        with self.assertRaises(numeric.RNGRefusal) as caught:
            capped.add(large, tiny)
        self.assertEqual(caught.exception.reason, "bit_limit")
        self.assertEqual(capped.stats["random_calls"], 64)
        finite = BinaryArithmetic(9, "stochastic", BitTape([0] * 8))
        with self.assertRaises(numeric.RNGRefusal) as caught:
            finite.add(large, tiny)
        self.assertEqual(caught.exception.reason, "source_exhausted")
        self.assertEqual(finite.stats["random_calls"], 9)
        self.assertEqual(finite.stats["random_bits"], 8)

    def test_choose_threshold_and_analytic_race_identity(self):
        for p in range(2, 5):
            operands = [DFloat(m, e) for m, e in product(range(2 ** (p - 1), 2**p), (-3, 0, 2))]
            for left, right in product(operands, repeat=2):
                a, b = numeric.as_fraction(left), numeric.as_fraction(right)
                minimum = int(b <= a)  # ties: left is maximum in the implementation
                captured = []

                def accept_threshold(uniform, threshold, captured=captured):
                    captured.append(
                        Fraction(threshold.numerator, threshold.denominator)
                        * Fraction(2) ** -threshold.shift
                    )
                    return True

                ar = BinaryArithmetic(p, "stochastic", BitTape([]))
                with patch.object(numeric.SharedUniformPrefix, "less_than", accept_threshold):
                    self.assertEqual(ar.choose(left, right, BitTape([minimum])), minimum)
                (theta,) = captured
                self.assertEqual(theta, min(a, b) / max(a, b))
                # Sum the geometric retry law, independent of the implementation.
                failure = (1 - theta) / 2
                self.assertEqual((theta / 2) / (1 - failure), min(a, b) / (a + b))
                self.assertEqual((Fraction(1, 2)) / (1 - failure), max(a, b) / (a + b))
                self.assertEqual(ar.stats["random_bits"], 0)

    def test_choose_retries_zero_mass_and_noise_separation(self):
        ar = BinaryArithmetic(3, "stochastic", BitTape([0]))
        left, right = DFloat(4, 0), DFloat(6, 0)
        self.assertEqual(ar.choose(left, right, BitTape([0, 1, 1, 1])), 1)
        self.assertEqual(ar.stats["choose_attempts"], 2)
        self.assertEqual(ar.stats["choose_bits"], 4)
        self.assertEqual(ar.stats["random_bits"], 0)
        self.assertEqual(ar.convert(Fraction(9, 8)), DFloat(5, -2))
        self.assertEqual(ar.stats["random_bits"], 1)
        self.assertEqual(ar.choose(DFloat(0, 0), right, BitTape([])), 1)
        self.assertEqual(ar.choose(left, DFloat(0, 0), BitTape([])), 0)
        with self.assertRaisesRegex(ValueError, "zero total mass"):
            ar.choose(DFloat(0, 0), DFloat(0, 0), BitTape([]))
        huge = DFloat(4, -(2**60))
        self.assertEqual(ar.choose(huge, right, BitTape([0, 1, 1])), 1)

    def test_fresh_group_and_seeded_program_reproduction(self):
        ar = BinaryArithmetic(3, "stochastic", BitTape([0, 1]))
        ar.start_group()
        self.assertEqual(ar.convert(Fraction(9, 8)), DFloat(5, -2))
        self.assertEqual(ar.convert(Fraction(9, 8)), DFloat(5, -2))
        ar.start_group()
        self.assertEqual(ar.convert(Fraction(9, 8)), DFloat(4, -2))
        self.assertEqual(ar.stats["random_bits"], 2)
        self.assertIs(ar.stats, ar.counts)
        runs = []
        for _ in range(2):
            ar = BinaryArithmetic(4, "stochastic", Random(20261020))
            outputs = []
            for _ in range(100):
                ar.start_group()
                outputs.append(ar.convert(Fraction(33, 32)))
            runs.append((outputs, ar.stats))
        self.assertEqual(runs[0], runs[1])  # finite PRNG reproducibility, not IID evidence

    def test_input_refusals_and_canonical_zero(self):
        for args in ((0, 1), (-1, 0), (1.0, 0), (1, 0.0)):
            with self.assertRaises((TypeError, ValueError)):
                DFloat(*args)
        for p, mode in ((1, "nearest"), (3, "sr"), (True, "nearest")):
            with self.assertRaises(ValueError):
                BinaryArithmetic(p, mode, Random(0))
        ar = BinaryArithmetic(3, "stochastic", BitTape([]))
        for value in (Fraction(-1, 2), Fraction(1, 3)):
            with self.assertRaises(ValueError):
                ar.convert(value)
        with self.assertRaises(TypeError):
            ar.convert(0.5)
        with self.assertRaises(ValueError):
            ar.add(DFloat(1, 0), DFloat(4, 0))
        self.assertEqual(ar.convert(Fraction(0)), DFloat(0, 0))
        self.assertEqual(ar.mul(DFloat(0, 0), DFloat(7, 2**60)), DFloat(0, 0))
        self.assertEqual(ar.stats["random_calls"], 0)


if __name__ == "__main__":
    unittest.main()
