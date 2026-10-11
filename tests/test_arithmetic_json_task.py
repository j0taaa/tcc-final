"""Independent executable semantics for the A34 application, not quality data."""

import importlib
import unittest
from fractions import Fraction

task = importlib.import_module("attempts.34-oracle-diversity-frontier.work.arithmetic_task_v6")


class ArithmeticJsonTests(unittest.TestCase):
    def test_exact_execution_and_untrusted_number_budgets(self):
        self.assertEqual(
            task.evaluate('{"op":"div","args":[{"op":"sub","args":[12,2]},4]}'),
            Fraction(5, 2),
        )
        self.assertEqual(task.evaluate('{"op":"add","args":[0.1,0.2]}'), Fraction(3, 10))
        self.assertEqual(task.evaluate('{"op":"mul","args":[1e-3,1e3]}'), 1)
        invalid = (
            '{"op":"add","op":"sub","args":[1,2]}',
            '{"op":"add","args":[true,2]}',
            '{"op":"add","args":[NaN,2]}',
            '{"op":"div","args":[1,0]}',
            '{"op":"add","args":[1e1000000000,0]}',
            '{"op":"mul","args":[1e-1000000000,0]}',
            '{"op":"add","args":[' + "1" * 257 + ",0]}",
            '{"op":"add","args":[1,2,3]}',
            '{"op":"add","args":[1,2],"extra":0}',
            '"add"',
        )
        for text in invalid:
            with self.subTest(text=text[:90]), self.assertRaises((ValueError, ZeroDivisionError)):
                task.evaluate(text)
        for op in ("add", "sub", "mul", "div"):
            self.assertEqual(task.root_operator(' {"op": "' + op + '"'), op)
        self.assertIsNone(task.root_operator('{"op":"mul'))


if __name__ == "__main__":
    unittest.main()
