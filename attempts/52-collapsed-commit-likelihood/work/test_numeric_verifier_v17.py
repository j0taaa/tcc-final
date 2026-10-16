"""Independent Decimal comparisons where representable; huge legal exponents."""

import itertools
import json
import unittest
from decimal import Decimal

from .numeric_verifier_v17 import independent_answer_equal
from .two_stage import answer_equal


class NumericVerifierV17Tests(unittest.TestCase):
    def test_moderate_spellings_against_independent_decimal(self):
        checked = 0
        for mantissa, exponent, gold in itertools.product(
            ("0", "-0", "1", "27", "270", "2700", "0.27", "2.7", "2.70", "27.0", "3.14", "-270"),
            ("", "e0", "e-0", "e+0", "e1", "e2", "e3", "e-1", "e-2", "e-3", "e+0002"),
            ("1", "60", "270"),
        ):
            text = '{"answer":' + mantissa + exponent + "}"
            expected = json.loads(text, parse_int=Decimal, parse_float=Decimal)[
                "answer"
            ] == Decimal(gold)
            self.assertEqual(independent_answer_equal(text, gold), expected)
            self.assertEqual(answer_equal(text, gold), expected)
            checked += 1
        print(json.dumps({"independent_numeric_verifier_decimal_cases": checked}))

    def test_huge_exponents_remain_legal_and_do_not_expand(self):
        for lexeme, expected in (
            ("27e+" + "9" * 5000, False),
            ("270e-" + "9" * 5000, False),
            ("270e+" + "0" * 5000, True),
            ("2.70e+" + "0" * 5000 + "2", True),
            ("0e" + "9" * 5000, False),
        ):
            text = '{"answer":' + lexeme + "}"
            self.assertEqual(independent_answer_equal(text, "270"), expected)
            self.assertEqual(answer_equal(text, "270"), expected)

    def test_invalid_object_number_type_and_label_remain_explicit(self):
        for text in (
            '{"answer":"270"}',
            '{"answer":true}',
            '{"answer":NaN}',
            '{"answer":270,"answer":270}',
            '{"answer":270,"extra":0}',
        ):
            with self.assertRaises(ValueError):
                independent_answer_equal(text, "270")
        with self.assertRaises(ValueError):
            independent_answer_equal('{"answer":0}', "0")


if __name__ == "__main__":
    unittest.main()
