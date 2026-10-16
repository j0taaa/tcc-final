"""Original-word exhaustive max-ratio and accepted-law audit, independent of the bound."""

import unittest
from fractions import Fraction as F
from random import Random

from .telescoping import construct, sample
from .test_reference import fixture


class TelescopingTests(unittest.TestCase):
    def test_full_original_json_laws_and_tighter_max_product(self):
        cases = [
            ([b"0", b"0", b"[]", b"[[]]", None, None, b" "], (None,) * 3, 4, 5),
            ([b"[", b"]", b"0", b"[]", None, b" "], (0, None, None, None), 4, 4),
            ([b'"', b"\xc3", b"\xa9", b"a", None, None], (0, None, None, None, None), 4, 5),
            ([b"1", b"e", b"0", b" ", None, None], (None, None, None, 4), 4, 5),
        ]
        for words, canvas, eot, pad in cases:
            for salt in (1, 2, 3):
                ref, law = fixture(words, canvas, eot, pad, salt=salt)
                for grid in (16, 64, 1024):
                    value = construct(ref.layers, ref.rows, grid=grid, bits=24)
                    q = value["proposal"]
                    envelope = value["envelope"]
                    ratios = [law[w] / q.trace(w)[1] for w in law]
                    self.assertLessEqual(max(ratios), envelope)
                    self.assertEqual(max(ratios), q.envelope)
                    accepted = {w: q.trace(w)[1] * law[w] / (envelope * q.trace(w)[1]) for w in law}
                    rate = sum(accepted.values(), F())
                    self.assertEqual(rate, ref.mass / envelope)
                    self.assertLessEqual(rate, 1)
                    for w in law:
                        self.assertEqual(accepted[w] / rate, law[w] / ref.mass)
                    for seed in range(8):
                        draw = sample(value, Random(seed), 32)
                        if draw["status"] == "COMPLETE":
                            self.assertGreater(law[draw["word"]], 0)
                    self.assertEqual(sample(value, Random(1), 0)["status"], "FAIL")

    def test_arbitrary_potential_and_bad_budget_are_not_silent_pruning(self):
        ref, law = fixture([b"0", b"0", None, None], (None, None), 2, 3, salt=1)
        value = construct(ref.layers, ref.rows)
        h = value["potentials"]
        # Arbitrary larger root remains correct; local factors account for it.
        changed = ((h[0][0] * 11,), *h[1:])
        alternate = construct(ref.layers, ref.rows, potentials=changed)
        for w, weight in law.items():
            self.assertLessEqual(weight / alternate["proposal"].trace(w)[1], alternate["envelope"])
        bad = ((h[0][0] / 1000000,), *h[1:])
        with self.assertRaisesRegex(ValueError, "budget cap"):
            construct(ref.layers, ref.rows, potentials=bad)
        with self.assertRaisesRegex(ValueError, "positive potentials"):
            construct(ref.layers, ref.rows, potentials=((F(0),), *h[1:]))


if __name__ == "__main__":
    unittest.main()
