"""Independent terminated-word/conditional-mass and finite-ticket laws."""

import itertools
import json
import unittest
from collections import defaultdict
from fractions import Fraction as F
from random import Random

import numpy as np

from ..certificate import CounterTable, conditional_error
from ..consumer_v2.block_stats import Partition
from ..consumer_v2.query import BoundaryWeights, ConfidenceCursor, FullSparseOutside, sample
from ..consumer_v2.test_query import Branch, Tickets
from .mosaic_control import accepts
from .termination import posterior, surrogate_table, terminated_graph

LIMITS = dict(timeout_seconds=5, max_cells=10000, max_edges=10000, max_terms=10000)


def fixture(words, rows, canvas, eot, pad):
    table = surrogate_table(words, eot, pad)
    partition = Partition(tuple(table.class_of), len(table.classes), 3)
    head = np.asarray([rows[p] for p, t in enumerate(canvas) if t is None], dtype=np.float64)
    weights = BoundaryWeights(table, head, canvas, partition)
    return table, weights


def enumerate_terminated(words, weights, eot, pad, depth=None):
    """Original bytes -> strict UTF8/Python JSON, independent of all graph code."""
    law = {}
    domains = [(t,) if t is not None else range(len(words)) for t in weights.canvas]
    for word in itertools.product(*domains):
        if eot not in word:
            continue
        k = word.index(eot)
        if any(t != pad for t in word[k + 1 :]):
            continue
        if any(t in (eot, pad) or words[t] is None for t in word[:k]):
            continue
        try:
            text = b"".join(words[t] for t in word[:k]).decode("utf8")
            json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeDecodeError):
            continue
        height, peak, quoted, escaped = 0, 0, False, False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                height += 1
                peak = max(peak, height)
            elif char in "]}":
                height -= 1
        if depth is not None and peak > depth:
            continue
        value = F(1)
        for p, t in enumerate(word):
            value *= F(weights.at(p, t), weights.denominators[p])
        if value:
            law[word] = value
    return law


def examples():
    return [
        ([b"0", b"0", b"[]", b"[[]]", None, None, b" "], (None,) * 3, 4, 5),
        ([b"[", b"]", b"0", b"[]", None, b" "], (0, None, None, None), 4, 4),
        ([b'"', b"\xc3", b"\xa9", b"a", None, None], (0, None, None, None, None), 4, 5),
        ([b"1", b"e", b"0", b" ", None, None], (None, None, None, 4), 4, 5),
    ]


class TerminationTests(unittest.TestCase):
    def test_original_language_true_mass_confidences_and_closed_tail(self):
        for case, (words, canvas, eot, pad) in enumerate(examples()):
            rows = [
                [1 + (p + 2 * t + case) % 3 for t in range(len(words))] for p in range(len(canvas))
            ]
            table, weights = fixture(words, rows, canvas, eot, pad)
            full = enumerate_terminated(words, weights, eot, pad)
            full_mass = sum(full.values(), F())
            self.assertTrue(full)
            for depth in (0, 1, 2, None):
                graph = terminated_graph(table, canvas, depth, eot, pad, **LIMITS)
                post = posterior(graph, table, weights, **LIMITS)
                expected = enumerate_terminated(words, weights, eot, pad, depth)
                mass = sum(expected.values(), F())
                self.assertEqual(post.mass, mass)
                domains = [(t,) if t is not None else range(len(words)) for t in canvas]
                for word in itertools.product(*domains):
                    self.assertEqual(accepts(graph, word), word in expected, (case, depth, word))
                if depth is not None:
                    upper, _ = CounterTable(table).tail(weights, depth, sums=weights.sums)
                    self.assertGreaterEqual(upper, full_mass - mass)
                    if mass:
                        self.assertGreaterEqual(
                            conditional_error(mass, upper), 1 - mass / full_mass
                        )
                if not mass:
                    continue
                numerators, total = post.marginals()
                sparse = FullSparseOutside(post)
                for p in range(len(canvas)):
                    cursor = ConfidenceCursor(post)
                    for t in range(len(words)):
                        target = sum((v for w, v in expected.items() if w[p] == t), F()) / mass
                        num = (
                            numerators[p].get(t, 0)
                            if isinstance(numerators[p], dict)
                            else numerators[p][t]
                        )
                        self.assertEqual(F(num, total), target)
                        self.assertEqual(F(sparse.at(p, t), total), target)
                        self.assertEqual(F(cursor.at(p, t), total), target)
                for seed in range(8):
                    weights.consumed = False
                    self.assertIn(sample(post, weights, Random(seed)), expected)

    def test_variable_boundary_entire_original_word_sampling_law(self):
        words, canvas = [b"0", b" ", None, None], (None,) * 3
        table, weights = fixture(words, [[1, 1, 1, 1]] * 3, canvas, 2, 3)
        graph = terminated_graph(table, canvas, 0, 2, 3, **LIMITS)
        post = posterior(graph, table, weights, **LIMITS)
        expected = enumerate_terminated(words, weights, 2, 3, 0)
        mass = sum(expected.values(), F())
        self.assertGreater(len(expected), 1)
        observed, pending = defaultdict(F), [((), F(1))]
        while pending:
            tickets, probability = pending.pop()
            weights.consumed = False
            try:
                word = sample(post, weights, Tickets(tickets))
            except Branch as branch:
                self.assertLessEqual(branch.size, 16)
                pending.extend(
                    ((*tickets, i), probability / branch.size) for i in range(branch.size)
                )
            else:
                observed[word] += probability
        self.assertEqual(dict(observed), {w: v / mass for w, v in expected.items()})

    def test_reweighting_preserves_canvas_and_fixed_eot_alias(self):
        words, canvas = [b"0", b"0", b" ", None, None], (None, None, None)
        rows = [[1, 2, 1, 2, 1]] * 3
        table, original = fixture(words, rows, canvas, 3, 4)
        graph = terminated_graph(table, canvas, 0, 3, 4, **LIMITS)
        _, fixed = fixture(words, rows, (1, None, 3), 3, 4)
        post = posterior(graph, table, fixed, **LIMITS)
        truth = enumerate_terminated(words, fixed, 3, 4)
        self.assertEqual(post.mass, sum(truth.values(), F()))
        for seed in range(10):
            fixed.consumed = False
            word = sample(post, fixed, Random(seed))
            self.assertEqual((word[0], word[2]), (1, 3))
        fixed_graph = terminated_graph(table, fixed.canvas, 0, 3, 4, **LIMITS)
        with self.assertRaisesRegex(ValueError, "initial fixed"):
            posterior(fixed_graph, table, original, **LIMITS)
