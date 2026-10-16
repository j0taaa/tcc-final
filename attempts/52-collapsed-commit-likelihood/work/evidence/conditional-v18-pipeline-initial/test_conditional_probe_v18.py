"""Independent finite probability laws, negative estimates and semantic tails."""

import itertools
import json
import unittest
from decimal import Decimal
from fractions import Fraction as F

import numpy as np

from .conditional_probe_v18 import certified_fixed_answer, paired_conditional_trace, select_family
from .llada_suffix_v10 import PREFIX, NumericSuffixJSON
from .prefix_anchor import PrefixAnchor
from .test_conditional_prefix import scalar_score
from .test_prefix_anchor import joint_law


class ConditionalProbeV18Tests(unittest.TestCase):
    def test_frozen_selection_never_credits_zero_or_negative_controls(self):
        entry = {
            "estimate": 0.8,
            "query_types": ["base"],
            "draw_count": 1,
            "method": "candidate",
            "baseline": "zero",
            "coefficients": [0, 0, 0],
        }
        control = {**entry, "method": "control", "estimate": 1.0}
        self.assertEqual(
            select_family([entry], [control])["status"], "ZERO_OVERHEAD_NECESSITY_PASS"
        )
        self.assertEqual(
            select_family([{**entry, "estimate": 0.81}], [control])["status"], "NECESSITY_NEGATIVE"
        )
        for value in (0.0, -1.0, float("nan")):
            self.assertEqual(
                select_family([entry], [{**control, "estimate": value}])["status"],
                "INCONCLUSIVE_NONPOSITIVE_CONTROL",
            )
        self.assertEqual(
            select_family([{**entry, "estimate": 0}], [control])["status"],
            "INCONCLUSIVE_NONPOSITIVE_CANDIDATES",
        )

    def test_zeroing_certified_tail_has_exactly_zero_statewise_mean(self):
        grammar = NumericSuffixJSON((b"1}", b"2}", b" ", b"", b"1", b"0}", b"}", b"<EOT>"), 7, 7)
        fixed = {0: 0}
        rows = tuple(tuple(F(v + 1, 36) for v in range(8)) for _ in range(3))
        gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in rows)
        policy = PrefixAnchor(grammar, rows, gates, (F(1),) * 3, fixed)
        words = [(0, 7), (0, 2, 7), (0, 3, 7)]
        law = joint_law(words, rows, gates, (F(1),) * 3, fixed)
        self.assertTrue(certified_fixed_answer(grammar, fixed)[0])
        self.assertEqual(sum(law.values(), F()), 1)
        full = sum(
            (p * scalar_score(policy.full_score(w, a, b)) for (w, a, b), p in law.items()), F()
        )
        cheap = sum(
            (p * scalar_score(policy.cheap_anchor_score(w, b)) for (w, _, b), p in law.items()), F()
        )
        self.assertEqual((full, cheap), (F(), F()))

    def test_cross_half_and_stratified_batch_expectations_by_complete_enumeration(self):
        # Path0 Bernoulli(1/4); path1 Bernoulli(1/2). Two iid replicas each.
        # Two independent STRATIFIED M2 batch means, with path1 deterministic1/2.
        total = dict.fromkeys(
            (
                "mean_gap_cross_estimate",
                "mean_gap_u_estimate",
                "hidden_iid1",
                "hidden_stratified_batch",
                "iid1",
                "iid_batch",
                "stratified_batch",
            ),
            F(),
        )
        count = 0
        for bits in itertools.product((0, 1), repeat=6):
            probability = F(1)
            for bit in bits[:2]:
                probability *= F(1, 4) if bit else F(3, 4)
            probability *= F(1, 2) ** 4
            a, b, x, y = [np.zeros((2, 9)) for _ in range(4)]
            a[:, 0], b[:, 0] = bits[:2], bits[2:4]
            x[:, 0], y[:, 0] = [v / 2 for v in bits[4:]], 0.5
            result = paired_conditional_trace(a, b, x, y, 2)["total"]
            for key in total:
                total[key] += probability * F(result[key])
            count += 1
        self.assertEqual(total["mean_gap_cross_estimate"], F(1, 32))
        self.assertEqual(total["mean_gap_u_estimate"], F(1, 32))
        self.assertEqual(total["hidden_iid1"], F(7, 32))
        self.assertEqual(total["hidden_stratified_batch"], F(1, 32))
        self.assertEqual(total["iid1"], F(1, 4))
        self.assertEqual(total["iid_batch"], F(9, 64))
        self.assertEqual(total["stratified_batch"], F(1, 16))
        print(
            json.dumps(
                {
                    "independent_cross_half_joint_cases": count,
                    "true_expected_paired_iid1": str(total["iid1"]),
                }
            )
        )

    def test_negative_cross_estimates_are_not_clipped(self):
        a, b, x, y = [np.zeros((2, 9)) for _ in range(4)]
        a[:, 0] = [1, -1]
        value = paired_conditional_trace(a, b, x, y)["total"]
        self.assertEqual(value["mean_gap_cross_estimate"], -0.5)
        self.assertEqual(value["stratified_batch"], -0.5)
        with self.assertRaises(ValueError):
            paired_conditional_trace(np.zeros((3, 9)), np.zeros((3, 9)), x, y)

    def test_all_pair_primary_keeps_negative_gap_but_nonnegative_iid_total(self):
        a, b = np.zeros((4, 9)), np.zeros((4, 9))
        a[:, 0], b[:, 0] = [1, 1, -1, -1], [-1, -1, 1, 1]
        result = paired_conditional_trace(a, b, np.zeros((2, 9)), np.zeros((2, 9)))["total"]
        self.assertEqual(result["mean_gap_cross_estimate"], -2.0)
        self.assertAlmostEqual(result["mean_gap_u_estimate"], -1 / 3)
        self.assertGreaterEqual(result["iid1"], 0)
        self.assertLess(result["cross_half_iid1"], 0)
        self.assertLess(result["stratified_batch"], 0)

    def test_pre_state_certificate_against_ALL_small_grammar_completions(self):
        emissions = (b"1}", b"2}", b" ", b"", b"1", b"0}", b"}", b"<EOT>")
        grammar = NumericSuffixJSON(emissions, 7, 7)
        checked = 0
        for fixed in ({0: 0}, {0: 1, 2: 7}, {0: 3, 1: 0}, {0: 4}, {1: 0, 2: 7}, {}):
            certificate, text = certified_fixed_answer(grammar, fixed)
            values = set()
            for size in range(1, 4):
                for body in itertools.product(range(7), repeat=size - 1):
                    word = (*body, 7)
                    if any(
                        i >= len(word) or word[i] != v for i, v in fixed.items()
                    ) or not grammar.accepts(word):
                        continue
                    full = (PREFIX + b"".join(emissions[v] for v in word[:-1])).decode()
                    values.add(json.loads(full, parse_int=Decimal, parse_float=Decimal)["answer"])
                    checked += 1
            self.assertTrue(values)
            if certificate:
                self.assertEqual(len(values), 1)
                self.assertEqual(
                    values, {json.loads(text, parse_int=Decimal, parse_float=Decimal)["answer"]}
                )
        self.assertFalse(certified_fixed_answer(grammar, {0: 4})[0])
        self.assertFalse(certified_fixed_answer(grammar, {1: 0, 2: 7})[0])
        print(json.dumps({"independent_semantic_tail_completions": checked}))


if __name__ == "__main__":
    unittest.main()
