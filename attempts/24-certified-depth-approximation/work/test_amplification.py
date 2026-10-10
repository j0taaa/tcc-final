"""Independent full-product enumeration checks the certified reweighting identity."""

import itertools
import json
import unittest
from fractions import Fraction
from math import prod

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .amplification import amplify
from .posterior import Weights
from .sampler import evaluate_certified
from .table import LexerTable


def full_mass(table, weights):
    result = 0
    for word in itertools.product(range(weights.vocabulary_size), repeat=len(weights.canvas)):
        if any(t is not None and t != word[p] for p, t in enumerate(weights.canvas)):
            continue
        if any(table.adapter.emissions[t] is None for t in word):
            continue
        try:
            json.loads(table.adapter.detokenize_bytes(word).decode("utf8"))
        except (ValueError, UnicodeDecodeError):
            continue
        result += prod(weights.at(p, t) for p, t in enumerate(word))
    return Fraction(result, prod(weights.denominators))


class CertifiedAmplification(unittest.TestCase):
    def test_true_complete_valid_mass_increases_and_old_product_is_unchanged(self):
        table = LexerTable(
            CompositionalByteLevelAdapter((b"[[", b"[]", b"[]", b"[[]]", b"]]", b"]}", b" ", None))
        )
        for shift in range(4):
            weights = Weights(
                [[i + 1 + shift for i in range(8)], list(range(8, 0, -1))], (None, None), 8
            )
            old_rows, old_den = tuple(weights.rows), tuple(weights.denominators)
            posterior, certificate = evaluate_certified(table, weights, "9/10", depths=(1,))
            numerators, lower = posterior.marginals()
            upper = Fraction(certificate["upper_tail"]) * prod(weights.denominators)
            self.assertEqual(upper.denominator, 1)
            mass = full_mass(table, weights)
            for factor in (2, 4, 7):
                outcome = amplify(weights, numerators, lower, upper.numerator, factor=factor)
                self.assertIsNotNone(outcome)
                new, claim = outcome
                actual = full_mass(table, new) / mass
                self.assertGreater(actual, 1)
                self.assertGreaterEqual(actual, Fraction(claim["minimum_mass_ratio"]))
                p, t = claim["position"], claim["token"]
                selected_mass = sum(
                    prod(weights.at(i, v) for i, v in enumerate(word))
                    for word in itertools.product(range(8), repeat=2)
                    if word[p] == t and self.valid(table, word)
                )
                marginal = Fraction(selected_mass, prod(weights.denominators)) / mass
                prior = Fraction(weights.at(p, t), weights.denominators[p])
                self.assertEqual(actual, (1 + (factor - 1) * marginal) / (1 + (factor - 1) * prior))
                self.assertEqual(tuple(weights.rows), old_rows)
                self.assertEqual(tuple(weights.denominators), old_den)
                self.assertTrue(all(new.at(i, v) > 0 for i in range(2) for v in range(8)))
        # Already all mass valid: no fabricated "improvement".
        weights = Weights([[1, 1]], (None,), 2)
        self.assertIsNone(amplify(weights, ((1, 1),), 2, 0))
        with self.assertRaises(ValueError):
            amplify(weights, ((2, 1),), 2, 0)

    @staticmethod
    def valid(table, word):
        if any(table.adapter.emissions[t] is None for t in word):
            return False
        try:
            json.loads(table.adapter.detokenize_bytes(word).decode("utf8"))
        except (ValueError, UnicodeDecodeError):
            return False
        return True
