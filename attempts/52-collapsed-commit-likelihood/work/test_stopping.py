"""Complete rational original-word laws; independent parser and length TV."""

import itertools
import random
import unittest
from collections import defaultdict
from fractions import Fraction as F
from math import prod

import numpy as np

from .floating import FloatPlan
from .numeric_json import NumericJSON
from .stopping import StoppedNumericJSON, first_eot_logs, length_statistics
from .test_numeric_json import independent_accepts


class StoppingTests(unittest.TestCase):
    def test_original_word_prefix_law_tv_dominance_and_fixed_ids(self):
        emissions = (
            b'{"answer":0}',
            b'{"answer":1',
            b"}",
            b" ",
            b"",
            b"",
            b"<EOT>",
            b"<PAD>",
            b"<MASK>",
            b"\xff",
        )
        stopped = StoppedNumericJSON(emissions, 6, 7)
        padded = NumericJSON(emissions, 6, 7)
        rng = random.Random(52060)
        for n in (2, 3, 4):
            for fixture in range(2):
                raw = [[F(rng.randrange(1, 8)) for _ in emissions] for _ in range(n)]
                if fixture and n == 4:
                    raw[0] = [F(v == 0) for v in range(len(emissions))]
                    raw[1] = [F(v == 6) for v in range(len(emissions))]
                    raw[3] = [F(v == 8) for v in range(len(emissions))]
                rows = tuple(tuple(v / sum(row) for v in row) for row in raw)
                full_stop, full_pad = defaultdict(F), defaultdict(F)
                for word in itertools.product(range(len(emissions)), repeat=n):
                    expected = 6 in word and independent_accepts(padded, word[: word.index(6) + 1])
                    self.assertEqual(stopped.accepts(word), expected)
                    probability = prod(rows[i][v] for i, v in enumerate(word))
                    if expected:
                        prefix = word[: word.index(6) + 1]
                        full_stop[prefix] += probability
                        if padded.accepts(word):
                            full_pad[prefix] += probability
                z = sum(full_stop.values(), F())
                zp = sum(full_pad.values(), F())
                plan = FloatPlan(stopped)
                weights = np.asarray(rows, dtype=np.float64)
                logs = first_eot_logs(plan, weights)
                actual = length_statistics(logs, weights[:, 7])
                self.assertAlmostEqual(np.exp(actual["log_z_stop"]), float(z), places=13)
                self.assertAlmostEqual(
                    np.exp(plan.forwards(plan.matrices(weights)[0])[0]), float(z), places=13
                )
                stop_lengths = [
                    sum((p for w, p in full_stop.items() if len(w) == i), F()) / z
                    for i in range(1, n + 1)
                ]
                np.testing.assert_allclose(
                    actual["stop_lengths"], np.asarray(stop_lengths, dtype=np.float64), atol=1e-13
                )
                for w, p in full_stop.items():
                    self.assertEqual(p, prod(rows[i][v] for i, v in enumerate(w)))
                if zp:
                    tv = (
                        sum(
                            (abs(p / z - full_pad.get(w, F()) / zp) for w, p in full_stop.items()),
                            F(),
                        )
                        / 2
                    )
                    self.assertAlmostEqual(actual["tv"], float(tv), places=13)
                    pad_lengths = [
                        sum((p for w, p in full_pad.items() if len(w) == i), F()) / zp
                        for i in range(1, n + 1)
                    ]
                    self.assertEqual(
                        tv,
                        sum(
                            (abs(a - b) for a, b in zip(stop_lengths, pad_lengths, strict=True)),
                            F(),
                        )
                        / 2,
                    )
                    for k in range(n):
                        self.assertGreaterEqual(
                            sum(pad_lengths[k:], F()), sum(stop_lengths[k:], F())
                        )
                else:
                    self.assertEqual(actual["pad_target_status"], "ZERO_MASS")
                    self.assertIsNone(actual["tv"])

    def test_arbitrarily_large_bias_and_mask_is_legal_only_after_stop(self):
        language = StoppedNumericJSON(
            (b'{"answer":0}', b'{"answer":1', b"}", b"<EOT>", b"<PAD>", b"<MASK>"), 3, 4
        )
        delta = F(1, 2**20)
        epsilon = delta**2
        rows = (
            (1 - delta, delta, F(), F(), F(), F()),
            (F(), F(), 1 / (2 - epsilon), (1 - epsilon) / (2 - epsilon), F(), F()),
            (F(), F(), F(), 1 - epsilon, epsilon, F()),
        )
        plan = FloatPlan(language)
        weights = np.asarray(rows, dtype=np.float64)
        actual = length_statistics(first_eot_logs(plan, weights), weights[:, 4])
        self.assertAlmostEqual(actual["stop_lengths"][1], float(1 - delta), places=13)
        self.assertAlmostEqual(
            actual["pad_lengths"][1],
            float((1 - delta) * epsilon / ((1 - delta) * epsilon + delta)),
            places=13,
        )
        self.assertGreater(actual["tv"], 0.99999)
        self.assertTrue(language.accepts((0, 3, 5)))
        self.assertFalse(language.accepts((5, 0, 3)))


if __name__ == "__main__":
    unittest.main()
