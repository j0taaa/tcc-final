"""Independent JSON parser oracle for the common lexical task boundary."""

import importlib
import itertools
import json
import re
import unittest

m = importlib.import_module("attempts.31-sufficient-state-coupling.work.schema_task")
o = importlib.import_module("attempts.31-sufficient-state-coupling.work.official_checker")


class ExternalJsonTaskTests(unittest.TestCase):
    def test_lexical_strings_against_json_parser(self):
        alphabet = ("a", " ", "\\", '"', "\n", "/", "`")
        words = [
            '"' + "".join(x) + '"' for n in range(4) for x in itertools.product(alphabet, repeat=n)
        ]
        words += [
            '"\\u0040"',
            '"\\u004X"',
            '"\\u0000"',
            '"\\u00e9"',
            '"\\t"',
            '"\\b"',
            '"\\f"',
            '"\\r"',
            '"\\x"',
        ]
        for text in words:
            try:
                json.loads(text)
                expected = True
            except ValueError:
                expected = False
            self.assertEqual(bool(re.fullmatch(m.JSON_STRING, text)), expected, text)

    def test_consumed_json_rejects_duplicates_and_nonfinite_values(self):
        for text in ('{"x":1,"x":2}', '{"a":{"x":1,"x":2}}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError):
                o.strict_json(text)
        self.assertEqual(o.strict_json('{"x":"a b", "y":[1,true]}'), {"x": "a b", "y": [1, True]})


if __name__ == "__main__":
    unittest.main()
