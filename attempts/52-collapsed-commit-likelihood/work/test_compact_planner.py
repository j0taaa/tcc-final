"""Independent rational means for compact and cheap reverse score controls."""

import itertools
import unittest
from collections import defaultdict
from fractions import Fraction as F

import numpy as np

from .anchor import AnchorPolicy
from .compact_planner import CompactPlanner, score_vector
from .floating import FloatPlan
from .numeric_json import NumericJSON
from .preflight_floating import cases, compare
from .test_anchor import full_law
from .test_numeric_json import independent_accepts


class CompactPlannerTests(unittest.TestCase):
    def test_compact_original_id_scores_against_fraction(self):
        for plan, weights, _, action, expected in cases():
            compact = CompactPlanner(plan, weights)
            compare(compact.statistics(action), expected)

    def test_reverse_and_known_anchor_against_complete_independent_law(self):
        language = NumericJSON(
            (b'{"answer":', b"0", b"1}", b'{"answer":0}', b" ", b"", b"<EOT>", b"<PAD>"), 6, 7
        )
        n, size = 3, len(language.emissions)
        raw = tuple(tuple(1 + (i + v) % 7 for v in range(size)) for i in range(n))
        rows = tuple(tuple(F(w, sum(row)) for w in row) for row in raw)
        gates = tuple(tuple(w / (w + F(1, 100)) for w in row) for row in rows)
        anchors = (F(1, n),) * n
        policy = AnchorPolicy(
            language.small_reference_graph(n), rows, gates, anchors, tuple(range(n))
        )
        words = [
            w for w in itertools.product(range(size), repeat=n) if independent_accepts(language, w)
        ]
        law = full_law(words, rows, gates, anchors, tuple(range(n)))
        compact = CompactPlanner(FloatPlan(language), np.asarray(rows, dtype=np.float64))

        def project(word, anchor, action):
            _, hh, rr = policy.full_score(word, anchor, action)
            return score_vector(
                {
                    "alpha": np.asarray([float(sum(row, F())) for row in hh]),
                    "beta": sum(
                        float(hh[i][v]) * np.log(float(rows[i][v]))
                        for i in range(n)
                        for v in range(size)
                    ),
                    "anchor": np.asarray(rr, dtype=np.float64),
                }
            )

        reverse_groups, known_groups = defaultdict(list), defaultdict(list)
        for (w, anchor, action), p in law.items():
            reverse_groups[w, action].append((anchor, p))
            known_groups[anchor, action].append((w, p))
        for (w, action), entries in reverse_groups.items():
            mass = sum((p for _, p in entries), F())
            expected = sum(float(p / mass) * project(w, a, action) for a, p in entries)
            actual = compact.cheap_scores(w, entries[0][0], action)
            np.testing.assert_allclose(
                score_vector(actual["full_triple"]), project(w, entries[0][0], action), atol=1e-12
            )
            np.testing.assert_allclose(
                score_vector(actual["anchor_integrated"]), expected, atol=1e-12
            )
        for (a, action), entries in known_groups.items():
            mass = sum((p for _, p in entries), F())
            expected = sum(float(p / mass) * project(w, a, action) for w, p in entries)
            actual = compact.known_anchor(compact.statistics(action), a, action)
            np.testing.assert_allclose(score_vector(actual), expected, atol=1e-12)


if __name__ == "__main__":
    unittest.main()
