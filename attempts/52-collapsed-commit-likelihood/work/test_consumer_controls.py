"""Real-consumer score controls against independent complete rational laws."""

import itertools
import unittest
from collections import defaultdict
from fractions import Fraction as F

import numpy as np

from .anchor import AnchorPolicy
from .consumer_resource import auxiliary_statistics
from .floating import FloatPlan
from .numeric_json import NumericJSON
from .test_anchor import full_law
from .test_numeric_json import independent_accepts


class ConsumerControlTests(unittest.TestCase):
    def test_full_and_known_anchor_scores_against_complete_law(self):
        language = NumericJSON(
            (b'{"answer":', b"0", b"1}", b'{"answer":0}', b" ", b"", b"<EOT>", b"<PAD>"),
            6,
            7,
        )
        n, size = 3, len(language.emissions)
        rows = tuple(
            tuple(
                F(1 + (i + v) % 7, sum(1 + (i + j) % 7 for j in range(size))) for v in range(size)
            )
            for i in range(n)
        )
        gates = tuple(tuple(w / (w + F(1, 100)) for w in row) for row in rows)
        policy = AnchorPolicy(
            language.small_reference_graph(n), rows, gates, (F(1, n),) * n, tuple(range(n))
        )
        words = [
            w for w in itertools.product(range(size), repeat=n) if independent_accepts(language, w)
        ]
        law = full_law(words, rows, gates, (F(1, n),) * n, tuple(range(n)))
        groups = defaultdict(list)
        for (word, anchor, action), p in law.items():
            groups[anchor, action].append((word, p))
        plan = FloatPlan(language)
        weights = np.asarray(rows, dtype=np.float64)

        def project(word, anchor, action):
            _, hh, rr = policy.full_score(word, anchor, action)
            return {
                "alpha": np.asarray([float(sum(row, F())) for row in hh]),
                "beta": sum(
                    float(hh[i][v]) * np.log(float(rows[i][v]))
                    for i in range(n)
                    for v in range(size)
                ),
                "anchor": np.asarray(rr, dtype=np.float64),
            }

        for (anchor, action), group in groups.items():
            total = sum((p for _, p in group), F())
            expected = {
                name: sum(float(p / total) * project(w, anchor, action)[name] for w, p in group)
                for name in ("alpha", "beta", "anchor")
            }
            word = group[0][0]
            actual = auxiliary_statistics(plan, weights, word, anchor, action)
            for name, value in project(word, anchor, action).items():
                np.testing.assert_allclose(
                    actual["full_triple"][name], value, atol=1e-12, rtol=1e-10
                )
                np.testing.assert_allclose(
                    actual["known_anchor"][name], expected[name], atol=1e-12, rtol=1e-10
                )


if __name__ == "__main__":
    unittest.main()
