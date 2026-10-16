"""Independent JSON/parser and rational original-ID suffix/alias score oracles."""

import itertools
import json
import unittest
from collections import defaultdict
from fractions import Fraction as F
from math import prod

import numpy as np

from .llada_suffix_v10 import NumericSuffixJSON, full_text, parsed_text, terminal_prefix
from .prefix_floating import PrefixFloatPlan, PrefixPlanner
from .prefix_runtime import assemble, extent
from .test_prefix_anchor import joint_law


def language():
    return NumericSuffixJSON(
        (b"0}", b"1}", b"-2.0e3}", b"0", b"1", b"}", b" ", b"", b"", b"<EOS>", b"[MASK]"),
        9,
        9,
    )


def independently_valid(grammar, word):
    if not word or word[-1] != grammar.eos or grammar.eos in word[:-1]:
        return False
    try:
        text = b'{"answer":' + b"".join(grammar.emissions[v] for v in word[:-1])
        value = json.loads(text, parse_int=F, parse_float=F)
    except (ValueError, UnicodeDecodeError):
        return False
    return isinstance(value, dict) and set(value) == {"answer"} and type(value["answer"]) is F


def words(grammar, n, fixed):
    body_ids = [v for v in range(len(grammar.emissions)) if v != grammar.eos]
    for length in range(1, n + 1):
        for body in itertools.product(body_ids, repeat=length - 1):
            word = (*body, grammar.eos)
            if any(i >= length or word[i] != v for i, v in fixed.items()):
                continue
            if independently_valid(grammar, word):
                yield word


def cases():
    grammar, rng = language(), np.random.default_rng(52100)
    plan = PrefixFloatPlan(grammar)
    result = []
    for n, fixed in ((2, {}), (3, {}), (4, {0: 0}), (4, {3: 9}), (5, {2: 8})):
        raw = rng.integers(1, 12, size=(n, len(grammar.emissions)))
        rows = tuple(tuple(F(int(v), int(row.sum())) for v in row) for row in raw)
        gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in rows)
        valid = tuple(words(grammar, n, fixed))
        direct = joint_law(valid, rows, gates, (F(1),) * n, fixed)
        groups = defaultdict(list)
        for (w, anchor, action), p in direct.items():
            groups[action].append((w, anchor, p))
        active = [i for i in range(n) if i not in fixed]
        weights = assemble(np.asarray(rows, dtype=float)[active], active, fixed, n, len(rows[0]))
        planner = PrefixPlanner(plan, weights, fixed, 0)
        actions = sorted(groups, key=lambda a: (len(a), a))
        chosen = sorted({0, len(actions) // 3, len(actions) // 2, len(actions) - 1})
        for index in chosen:
            action = actions[index]
            entries = groups[action]
            mass = sum((p for _, _, p in entries), F())
            alpha = [F()] * n
            beta = 0.0
            anchor_score = [F()] * n
            for w, anchor, p in entries:
                eligible = [i for i in range(len(w)) if i not in fixed]
                for i in eligible:
                    h = (F(i in dict(action)) - gates[i][w[i]]) * (i != anchor)
                    alpha[i] += p / mass * h
                    beta += float(p / mass * h) * np.log(float(rows[i][w[i]]))
                    anchor_score[i] += p / mass * (F(i == anchor) - F(1, len(eligible)))
            expected = {
                "log_probability": np.log(float(mass)),
                "alpha": np.asarray(alpha, dtype=float),
                "beta": beta,
                "anchor": np.asarray(anchor_score, dtype=float),
            }
            result.append((plan, planner, fixed, action, expected))
    return result


class LLaDASuffixTests(unittest.TestCase):
    def test_entire_small_suffix_language_and_eos_pad_alias(self):
        grammar, checked = language(), 0
        for length in range(1, 5):
            for body in itertools.product(range(len(grammar.emissions)), repeat=length - 1):
                word = (*body, grammar.eos)
                if grammar.eos in body:
                    with self.assertRaises(ValueError):
                        full_text(grammar, word)
                    continue
                self.assertEqual(grammar.accepts(word), independently_valid(grammar, word))
                if grammar.accepts(word):
                    parsed_text(full_text(grammar, word))
                checked += 1
        print(json.dumps({"original_suffix_words": checked, "eos_pad_same_original_id": True}))

    def test_bruteforce_mass_occupancy_and_all_scores(self):
        queries = cases()
        for plan, planner, fixed, action, expected in queries:
            actual = planner.statistics(action)
            for name in expected:
                np.testing.assert_allclose(actual[name], expected[name], atol=1e-10, rtol=1e-9)
            valid = tuple(words(plan.language, planner.n, fixed))
            mass = sum((prod(planner.weights[i, v] for i, v in enumerate(w)) for w in valid), 0.0)
            self.assertAlmostEqual(planner.base["logz"], np.log(mass), places=11)
            occupied = np.zeros_like(planner.base["classes"])
            stops = np.zeros(planner.n)
            for word in valid:
                p = prod(planner.weights[i, v] for i, v in enumerate(word)) / mass
                stops[len(word) - 1] += p
                for i, v in enumerate(word):
                    occupied[i, plan.mapping[v]] += p
            np.testing.assert_allclose(planner.base["classes"], occupied, atol=1e-11)
            np.testing.assert_allclose(planner.base["stops"], stops, atol=1e-11)
            rng = np.random.default_rng(52101)
            for _ in range(3):
                w = plan.sample_prefix(planner.weights, rng, max(fixed, default=-1))
                self.assertTrue(independently_valid(plan.language, w))
                self.assertTrue(all(i < len(w) and w[i] == v for i, v in fixed.items()))
        print(json.dumps({"suffix_exact_score_queries": len(queries), "new_model_forwards": 0}))

    def test_terminal_original_ids_undefined_aliases_and_invalid_shapes(self):
        grammar = language()
        self.assertEqual(full_text(grammar, (3, 5, 9)), '{"answer":0}')
        self.assertEqual(full_text(grammar, (0, 7, 8, 9)), '{"answer":0}')
        self.assertEqual(terminal_prefix(grammar, 5, {0: 0, 1: 7, 2: 8, 3: 9}), (0, 7, 8, 9))
        self.assertIsNone(terminal_prefix(grammar, 5, {0: 0, 3: 9}))
        with self.assertRaises(ValueError):
            extent(5, {1: 9, 3: 8}, 9)
        for text in (
            '{"answer":"0"}',
            '{"answer":true}',
            '{"answer":NaN}',
            '{"answer":0,"answer":1}',
        ):
            with self.assertRaises(ValueError):
                parsed_text(text)
        with self.assertRaises(ValueError):
            full_text(grammar, (9,))


if __name__ == "__main__":
    unittest.main()
