"""Independent executable semantics for the A34 application, not quality data."""

import importlib
import unittest
from fractions import Fraction

task = importlib.import_module("attempts.34-oracle-diversity-frontier.work.arithmetic_task_v6")
checkpoint = importlib.import_module(
    "attempts.34-oracle-diversity-frontier.work.number_checkpoint_v8"
).number_checkpoint


class ArithmeticJsonTests(unittest.TestCase):
    def test_only_newly_accepted_original_ids_define_number_event(self):
        emissions = {7: "9", 8: "2,3", 9: "\uff18", 10: "1", 11: "alias 2"}
        previous = [7, 7, 99, 99, 99, 99, 99]
        current = [7, 7, 10, 8, 9, 11, 99]
        found = checkpoint(
            previous, current, emissions.__getitem__, start=3, mask_id=99, special_ids=(10,)
        )
        self.assertEqual(found, dict(position=3, token_id=8, emission="2,3", digit=2))
        self.assertIsNone(
            checkpoint(current, current, emissions.__getitem__, start=0, mask_id=99, special_ids=())
        )
        alias = checkpoint([99], [11], emissions.__getitem__, start=0, mask_id=99, special_ids=())
        self.assertEqual(alias["token_id"], 11)
        self.assertIsNone(
            checkpoint([99], [9], emissions.__getitem__, start=0, mask_id=99, special_ids=())
        )
        with self.assertRaises(ValueError):
            checkpoint([], [8], emissions.__getitem__, start=0, mask_id=99, special_ids=())

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
