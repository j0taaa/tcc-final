"""Independent Fraction reference for once-reduced original-weight acceptance."""

import unittest
from fractions import Fraction as F
from math import prod

from .scalar_acceptance import acceptance


class ScalarAcceptanceTests(unittest.TestCase):
    def test_exact_extremes_and_actual_preimages_match_naive_fraction(self):
        packets = (
            ((3, 0, 1), (3, 1, 3), (1 << 40, 0, 1 << 40)),
            ((7, 1, 2), (13, 5, 9), (1024, 1023, 1024)),
        )
        rows = ((0.1, 1.0, 0.7), (float.fromhex("0x1p-1074"), 1e-300, 0.125), (1.0,) * 69)
        h = 1 << 64
        for packet in packets:
            q = prod(
                (F(-(-h * end // a) + (-h * start // a), h) for a, start, end in packet), start=F(1)
            )
            for weights in rows:
                w = prod(map(F, weights), start=F(1))
                envelope = w / q * F(17, 10)
                self.assertEqual(acceptance(weights, packet, envelope), F(10, 17))
                self.assertEqual(acceptance(weights, packet, w / q), 1)
                with self.assertRaisesRegex(RuntimeError, "never clamp"):
                    acceptance(weights, packet, w / q / 2)

    def test_zero_invalid_terminal_and_malformed_packet_are_distinct(self):
        self.assertEqual(acceptance((0.0,), ((3, 0, 1),), F(1)), 0)
        self.assertEqual(acceptance((1.0,), ((3, 0, 1),), F(1), valid=False), 0)
        for packet in (((0, 0, 0),), ((3, 2, 2),), ((3, 2, 4),), (((1 << 41) + 1, 0, 1),)):
            with self.assertRaisesRegex(ValueError, "packet"):
                acceptance((0.1,), packet, F(1000))
        with self.assertRaisesRegex(ValueError, "negative"):
            acceptance((-1.0,), ((1, 0, 1),), F(1000))


if __name__ == "__main__":
    unittest.main()
