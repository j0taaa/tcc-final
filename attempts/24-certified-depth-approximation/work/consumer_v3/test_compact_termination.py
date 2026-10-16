"""Original-word oracles for the direct, unbounded compact CFG controls."""

import unittest
from collections import defaultdict
from fractions import Fraction as F
from random import Random

from ..consumer_v2.compact import CompactOutside, sample_compact
from ..consumer_v2.compact import load as load_old
from ..consumer_v2.test_query import Branch, Tickets
from ..lexer import OUT
from .compact_termination import CompactCache, lexical_table, load
from .test_termination import LIMITS, enumerate_terminated, examples, fixture


class CompactTerminationTests(unittest.TestCase):
    def test_all_three_compact_forests_match_true_original_word_laws(self):
        old, _ = load_old()
        old_finish = old["forest"].finish
        modules, origin = load()
        self.assertEqual(old["forest"].finish, old_finish)
        self.assertEqual(old_finish(OUT), ())
        self.assertIsNone(modules["forest"].finish(OUT))
        self.assertTrue(origin["source_archive_sha256"])
        for words, canvas, eot, pad in examples():
            rows = [[1 + (p + 2 * t) % 3 for t in range(len(words))] for p in range(len(canvas))]
            table, weights = fixture(words, rows, canvas, eot, pad)
            lexical = lexical_table(table, eot, pad)
            expected = enumerate_terminated(words, weights, eot, pad)
            mass = sum(expected.values(), F())
            for method in ("exact_local", "exact_bidir_local", "exact_eps_local"):
                with self.subTest(method=method, words=words):
                    cache = CompactCache(lexical, canvas, method, modules=modules, **LIMITS)
                    post = cache.reweight(weights)
                    self.assertEqual(post.mass, mass)
                    query = CompactOutside(post)
                    for p in range(len(canvas)):
                        for t in range(len(words)):
                            target = sum((v for w, v in expected.items() if w[p] == t), F()) / mass
                            self.assertEqual(F(query.at(p, t), post.total), target)
                    for seed in range(8):
                        weights.consumed = False
                        self.assertIn(sample_compact(post, weights, Random(seed)), expected)

    def test_compact_cache_new_heads_fixed_aliases_and_full_joint_law(self):
        words, canvas = [b"0", b"0", b" ", None, None], (None,) * 3
        table, _ = fixture(words, [[1] * 5] * 3, canvas, 3, 4)
        lexical = lexical_table(table, 3, 4)
        modules, _ = load()
        for method in ("exact_local", "exact_bidir_local", "exact_eps_local"):
            cache = CompactCache(lexical, canvas, method, modules=modules, **LIMITS)
            for current, rows in (
                (canvas, [[1] * 5] * 3),
                ((1, None, None), [[1, 3, 2, 1, 2]] * 3),
                ((1, None, 3), [[1, 2, 1, 2, 3]] * 3),
            ):
                _, weights = fixture(words, rows, current, 3, 4)
                post = cache.reweight(weights)
                expected = enumerate_terminated(words, weights, 3, 4)
                mass = sum(expected.values(), F())
                self.assertEqual(post.mass, mass)
                observed, pending = defaultdict(F), [((), F(1))]
                while pending:
                    tickets, probability = pending.pop()
                    weights.consumed = False
                    try:
                        word = sample_compact(post, weights, Tickets(tickets))
                    except Branch as branch:
                        self.assertLessEqual(branch.size, 64)
                        pending.extend(
                            ((*tickets, i), probability / branch.size) for i in range(branch.size)
                        )
                    else:
                        observed[word] += probability
                self.assertEqual(dict(observed), {w: v / mass for w, v in expected.items()})
