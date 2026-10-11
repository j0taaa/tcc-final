"""Independent numeric JSON evaluation boundaries; no model/benchmark selection."""

import importlib
import unittest
from fractions import Fraction

task = importlib.import_module("attempts.32-native-oracle-antithetics.work.numeric_task")


class NativeNumericTaskTests(unittest.TestCase):
    def test_exact_decimal_exponent_and_unrestricted_schema(self):
        for text in ('{"answer":0.1}', ' {"answer":1e-1} ', '{"answer":0.100}'):
            parsed = task.strict_json(text)
            self.assertEqual(parsed["answer"], Fraction(1, 10))
            self.assertTrue(task.correct(parsed, "unrelated reasoning #### 0.1"))
        self.assertTrue(task.correct(task.strict_json('{"answer":1000}'), "#### 1,000"))
        self.assertTrue(task.correct(task.strict_json('{"answer":-7}'), "#### -7"))
        self.assertFalse(task.correct(task.strict_json('{"answer":0.1000001}'), "#### 0.1"))
        source = task.task("Compute an unrestricted quantity.")
        self.assertEqual(source["prefix"], '{"answer":')
        self.assertEqual(source["grammar"], task.GRAMMAR)
        self.assertIn("[0-9]*", source["lexical"]["lexNumber"])

    def test_duplicate_non_json_bool_string_and_wrong_shape(self):
        for text in ('{"answer":1,"answer":2}', '{"answer":NaN}', '{"answer":Infinity}'):
            with self.assertRaises(ValueError):
                task.strict_json(text)
        for text in ('{"answer":true}', '{"answer":"1"}', '{"answer":1,"other":0}', "[1]", "1"):
            self.assertFalse(task.correct(task.strict_json(text), "#### 1"))


if __name__ == "__main__":
    unittest.main()
