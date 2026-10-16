"""Independent byte regex/Decimal, rational joint law and CPU autodiff."""

import itertools
import json
import re
import unittest
from decimal import Decimal
from fractions import Fraction as F

import numpy as np

from .llada_suffix_v10 import NumericSuffixJSON
from .numeric_json import STATE_COUNT, TAIL
from .numeric_proxy import IntegerProxy
from .prefix_anchor import PrefixAnchor
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .proposal_control import ProposalControl
from .proxy_floating import ProxyPlanner, accepting_support


def independent(digits, body):
    expression = (
        rb"[ \t\r\n]*" + digits.encode() + rb"(?:\.0+)?(?:[eE][+-]?0+)?[ \t\r\n]*}[ \t\r\n]*"
    )
    return re.fullmatch(expression, body) is not None


class NumericProxyTests(unittest.TestCase):
    def test_byte_language_subset_regex_decimal_aliases_and_rejected_spellings(self):
        count = 0
        for digits in ("1", "270", "123456789012"):
            proxy = IntegerProxy((b"", b"", b"<EOT>", b"<MASK>"), 2, 2, digits)
            for lead, fraction, exponent, ws, trail in itertools.product(
                ("", " ", "\t\r\n"),
                ("", ".0", ".000", ".1", "."),
                ("", "e0", "E+00", "e-0", "e1", "e", "E+"),
                ("", "\t"),
                ("", "\n"),
            ):
                body = (lead + digits + fraction + exponent + ws + "}" + trail).encode()
                actual = 0
                for b in body:
                    actual = proxy.byte_step(actual, b) if actual >= 0 else -1
                self.assertEqual(actual == 20, independent(digits, body))
                # One original token may emit the whole string.
                g = IntegerProxy((body, b"", b"", b"<EOT>"), 3, 3, digits)
                broad = NumericSuffixJSON(g.emissions, 3, 3)
                self.assertEqual(g.accepts((0, 1, 2, 3)), actual == 20)
                if actual == 20:
                    self.assertTrue(broad.accepts((0, 1, 2, 3)))
                    value = json.loads(
                        '{"answer":' + body.decode(), parse_int=Decimal, parse_float=Decimal
                    )
                    self.assertEqual(value["answer"], Decimal(digits))
                count += 1
            for malformed in ("", "0", "01", "-1", "1.0", "1e0", "1" * 13):
                with self.assertRaises(ValueError):
                    IntegerProxy(proxy.emissions, 2, 2, malformed)
        # A semantically correct spelling outside the regular subset stays excluded.
        body = b"27e1}"
        g = IntegerProxy((body, b"<EOT>"), 1, 1, "270")
        self.assertFalse(g.accepts((0, 1)))
        self.assertTrue(NumericSuffixJSON(g.emissions, 1, 1).accepts((0, 1)))
        self.assertEqual(json.loads('{"answer":27e1}', parse_float=Decimal)["answer"], 270)
        print(json.dumps({"independent_proxy_byte_cases": count}))

    def test_rational_projection_and_cpu_floating_with_fixed_eos_and_zero_support(self):
        emissions = (b"1}", b"1.0}", b"1e0}", b"2}", b" ", b"", b"", b"<EOT>")
        broad = NumericSuffixJSON(emissions, 7, 7)
        narrow = IntegerProxy(emissions, 7, 7, "1")
        queries = zeros = 0
        for n, fixed in ((2, {}), (3, {}), (3, {0: 3}), (3, {2: 7})):
            raw = [[F(1 + (i + v) % 5) for v in range(8)] for i in range(n)]
            rows = tuple(tuple(x / sum(row, F()) for x in row) for row in raw)
            gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in rows)
            base = PrefixAnchor(broad, rows, gates, (F(1),) * n, fixed)
            reference = ProposalControl(base, narrow)
            floats = np.asarray(rows, dtype=float)
            for i, v in fixed.items():
                floats[i] = 0
                floats[i, v] = 1
            planner = PrefixPlanner(PrefixFloatPlan(broad), floats, fixed, 0.0)
            control = ProxyPlanner(planner, PrefixFloatPlan(narrow))
            # Exhaustive independent original-ID action enumeration.
            active = [i for i in range(n) if i not in fixed]
            for size in range(1, len(active) + 1):
                for positions in itertools.combinations(active, size):
                    for tokens in itertools.product(range(8), repeat=size):
                        action = tuple(zip(positions, tokens, strict=True))
                        probability = base.action_statistics(action)[0]
                        if not probability:
                            continue
                        z, vector = reference(action)
                        actual = control.statistics(action)
                        gates_ref = np.asarray(vector[: n * 8], dtype=float).reshape(n, 8)
                        beta = float(np.sum(gates_ref * np.log(np.asarray(rows, dtype=float))))
                        np.testing.assert_allclose(
                            actual["posterior"], float(z), atol=1e-12, rtol=1e-12
                        )
                        np.testing.assert_allclose(
                            actual["correction"]["alpha"], gates_ref.sum(1), atol=1e-12
                        )
                        np.testing.assert_allclose(actual["correction"]["beta"], beta, atol=1e-12)
                        np.testing.assert_allclose(
                            actual["correction"]["anchor"],
                            np.asarray(vector[n * 8 :], dtype=float),
                            atol=1e-12,
                        )
                        zeros += int(not z)
                        queries += 1
        self.assertGreater(zeros, 0)
        print(json.dumps({"proxy_rational_float_queries": queries, "structural_zeros": zeros}))

    def test_boolean_support_rejects_nonfinite_and_distinguishes_tiny_positive(self):
        a = np.zeros((2, STATE_COUNT, STATE_COUNT))
        a[0, 0, 20] = 1e-300
        a[1, 20, TAIL] = 1e-300
        self.assertTrue(accepting_support(a))
        self.assertEqual(a[0, 0, 20] * a[1, 20, TAIL], 0)
        a[1, 20, TAIL] = 0
        self.assertFalse(accepting_support(a))
        a[0, 0, 20] = np.nan
        with self.assertRaises(ValueError):
            accepting_support(a)


if __name__ == "__main__":
    unittest.main()
