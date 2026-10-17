"""Independent finite rational audits; constructed cases are not benchmarks."""

import unittest
from fractions import Fraction as F
from itertools import product

from .reference import (
    Format,
    Refusal,
    add,
    certified_choice,
    convert,
    enclosure,
    multiply,
    power2,
    scale,
)


class StaticRoundingTests(unittest.TestCase):
    def test_exact_rounding_against_brute_representable_numbers(self):
        fmt = Format(3, -3, 3)
        numbers = sorted(
            {F(0)}
            | {F(k, 4) * power2(e) for e in range(-3, 4) for k in range(4, 8)}
            | {F(k, 32) for k in range(1, 4)}
        )
        checked = 0
        for value in (F(k, 128) for k in range(1793)):
            closest = min(abs(value - candidate) for candidate in numbers)
            candidates = [candidate for candidate in numbers if abs(value - candidate) == closest]
            result = fmt.round(value)
            self.assertIn(result, candidates)
            if len(candidates) == 2:
                quantum = candidates[1] - candidates[0]
                self.assertEqual((result / quantum).denominator, 1)
                self.assertEqual(int(result / quantum) % 2, 0)
            checked += 1
        print("independent representable-grid roundings:", checked)

    def test_positive_circuits_true_scaled_values_and_outward_materialization(self):
        fmt = Format(6, -30, 30)
        inputs = (F(0), F(1, 64), F(17, 64), F(65, 256), F(273, 256), F(19, 8))
        checked = 0
        for values in product(inputs, repeat=3):
            a, b, c = (convert(x, fmt) for x in values)
            nodes = (a, b, c, add(a, b, fmt), multiply(a, b, fmt))
            nodes += (multiply(add(a, b, fmt), add(b, c, fmt), fmt),)
            nodes += (scale(nodes[-1], F(3, 2), fmt),)
            for node in nodes:
                for materialize in (False, True):
                    lower, upper = enclosure(node, fmt, materialize)
                    self.assertLessEqual(lower, node.exact)
                    self.assertLessEqual(node.exact, upper)
                    checked += 1
        print("positive-circuit enclosure checks:", checked)

    def test_refuse_underflow_subnormal_and_overflow_without_pruning(self):
        fmt = Format(4, -4, 4)
        for value in (F(1, 1024), F(1, 128), F(1024)):
            with self.assertRaises(Refusal):
                convert(value, fmt)
        normal = convert(F(1, 16), fmt)
        with self.assertRaises(Refusal):
            multiply(normal, normal, fmt)
        with self.assertRaises(ValueError):
            scale(normal, 0, fmt)
        zero = multiply(convert(0, fmt), normal, fmt)
        self.assertEqual(zero.exact, 0)
        self.assertEqual(enclosure(zero, fmt), (0, 0))
        # A wrong DAG-height budget loses duplicated input errors on products.
        fmt = Format(4, -30, 30)
        node = convert(F(273, 256), fmt)
        for _ in range(5):
            node = multiply(node, node, fmt)
        self.assertEqual(node.budget, 63)
        self.assertGreater(node.rounded, (1 + fmt.epsilon) ** 6 * node.exact)
        lower, upper = enclosure(node, fmt)
        self.assertLessEqual(lower, node.exact)
        self.assertLessEqual(node.exact, upper)
        print("wrong-height-budget counterexample:", str(node.rounded / node.exact))

    def test_certified_choices_and_same_prefix_exact_refinement(self):
        fmt = Format(12, -30, 30)
        values = (F(17, 64), F(65, 256), F(273, 256))
        nodes = [multiply(convert(x, fmt), convert(x, fmt), fmt) for x in values]
        weights = [enclosure(node, fmt, True) for node in nodes]
        exact = [node.exact for node in nodes]
        cdf = [F(0)]
        for mass in exact:
            cdf.append(cdf[-1] + mass / sum(exact))
        certified = ambiguous = 0
        for prefix in range(1024):
            lower, upper = F(prefix, 1024), F(prefix + 1, 1024)
            choice = certified_choice(weights, lower, upper)
            midpoint = (lower + upper) / 2
            reference = next(i for i in range(len(exact)) if cdf[i] <= midpoint < cdf[i + 1])
            if choice is None:
                # Fallback retains this cell and every earlier revealed bit.
                self.assertGreaterEqual(midpoint, lower)
                self.assertLess(midpoint, upper)
                self.assertTrue(cdf[reference] <= midpoint < cdf[reference + 1])
                ambiguous += 1
            else:
                self.assertEqual(choice, reference)
                self.assertLessEqual(cdf[choice], lower)
                self.assertLessEqual(upper, cdf[choice + 1])
                certified += 1
        self.assertGreater(certified, 0)
        self.assertGreater(ambiguous, 0)
        print("uniform-prefix consistency:", certified, "certified,", ambiguous, "refinements")
