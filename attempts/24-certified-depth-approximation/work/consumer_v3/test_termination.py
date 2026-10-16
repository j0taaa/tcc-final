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
from .prefix_cache import PrefixCache
from .ranking import ranked_commits
from .termination import CPUCache, posterior, surrogate_table, terminated_graph

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
    def test_certified_ranking_matches_full_map_or_refuses_and_keeps_sample(self):
        words, canvas = [b"0", b" ", b"[]", b"[[]]", None, None], (None,) * 3
        rows = [[5, 1, 3, 1, 1, 1], [1, 4, 2, 1, 3, 1], [1, 2, 1, 1, 5, 2]]
        table, weights = fixture(words, rows, canvas, 4, 5)
        full_law = enumerate_terminated(words, weights, 4, 5)
        total = sum(full_law.values(), F())
        seen = set()
        for depth in (0, 1, 2):
            graph = terminated_graph(table, canvas, depth, 4, 5, symbolic=True, **LIMITS)
            post = posterior(graph, table, weights, **LIMITS)
            upper, _ = CounterTable(table).tail(weights, depth, sums=weights.sums)
            for word in enumerate_terminated(words, weights, 4, 5, depth):
                for count in (1, 2, 3):
                    result = ranked_commits(post, word, upper, count)
                    exact = {
                        p: sum((v for w, v in full_law.items() if w[p] == word[p]), F()) / total
                        for p in weights.free
                    }
                    selected = tuple(sorted(sorted(exact, key=lambda p: (-exact[p], p))[:count]))
                    if result["selected"] is None:
                        seen.add("ambiguous")
                    else:
                        seen.add("certified")
                        self.assertEqual(result["selected"], selected)
                    # Exact refinement evaluates the SAME shallow original word.
                    full_graph = terminated_graph(
                        table, canvas, None, 4, 5, symbolic=True, **LIMITS
                    )
                    full_post = posterior(full_graph, table, weights, **LIMITS)
                    resolved = ranked_commits(full_post, word, 0, count)
                    self.assertEqual(resolved["selected"], selected)
        self.assertEqual(seen, {"ambiguous", "certified"})

    def test_cached_first_overflow_and_handoff_bound_true_terminated_tail(self):
        words, canvas = [b"0", b"0", b"[]", b"[[]]", b" ", None, None], (None,) * 3
        rows = [[1, 2, 1, 1, 1, 1, 1]] * 3
        table, _ = fixture(words, rows, canvas, 5, 6)
        for depth in (0, 1, 2):
            prefix = PrefixCache(table, canvas, depth, **LIMITS)
            graph = prefix.terminated_graph(5, 6)
            compiled = CPUCache(graph, table, **LIMITS)
            for current in (canvas, (1, None, None), (None, None, 5)):
                _, weights = fixture(words, rows, current, 5, 6)
                shallow = compiled.reweight(weights).mass
                full = sum(enumerate_terminated(words, weights, 5, 6).values(), F())
                frontier = prefix.frontier(weights)
                handoff, _ = frontier.handoff(CounterTable(table))
                closed, _ = CounterTable(table).tail(weights, depth, sums=weights.sums)
                self.assertGreaterEqual(frontier.mass, full - shallow)
                self.assertGreaterEqual(handoff, full - shallow)
                self.assertLessEqual(handoff, min(frontier.mass, closed))
            fixed_prefix = PrefixCache(table, (1, None, None), depth, **LIMITS)
            _, released = fixture(words, rows, canvas, 5, 6)
            with self.assertRaisesRegex(ValueError, "initial fixed"):
                fixed_prefix.frontier(released)

    def test_symbolic_cache_reweights_new_heads_and_fixed_original_aliases(self):
        words, canvas = [b"0", b"0", b"[]", b" ", None, None], (None,) * 3
        base = [[1, 2, 1, 1, 2, 1]] * 3
        table, _ = fixture(words, base, canvas, 4, 5)
        for depth in (0, 1, None):
            graph = terminated_graph(table, canvas, depth, 4, 5, symbolic=True, **LIMITS)
            cache = CPUCache(graph, table, **LIMITS)
            for rows, current in (
                (base, canvas),
                ([[3, 0, 2, 1, 1, 4], [0, 4, 2, 1, 3, 1], [1, 2, 1, 3, 2, 1]], canvas),
                ([[0, 9, 1, 2, 4, 1]] * 3, (1, None, None)),
                ([[0, 1, 3, 2, 4, 1]] * 3, (1, None, 4)),
            ):
                _, weights = fixture(words, rows, current, 4, 5)
                post = cache.reweight(weights)
                truth = enumerate_terminated(words, weights, 4, 5, depth)
                mass = sum(truth.values(), F())
                self.assertEqual(post.mass, mass)
                if not mass:
                    continue
                outside = FullSparseOutside(post)
                for p in range(len(canvas)):
                    cursor = ConfidenceCursor(post)
                    for t in range(len(words)):
                        exact = sum((v for w, v in truth.items() if w[p] == t), F()) / mass
                        self.assertEqual(F(outside.at(p, t), post.total), exact)
                        self.assertEqual(F(cursor.at(p, t), post.total), exact)
                # Both the lazy-member legacy sampler and the class/block
                # sampler must produce ORIGINAL IDs, not symbolic labels.
                for seed in range(8):
                    self.assertIn(post.sample(Random(seed)), truth)
                    weights.consumed = False
                    self.assertIn(sample(post, weights, Random(seed)), truth)
            fixed_graph = terminated_graph(
                table, (1, None, 4), depth, 4, 5, symbolic=True, **LIMITS
            )
            fixed_cache = CPUCache(fixed_graph, table, **LIMITS)
            _, original = fixture(words, base, canvas, 4, 5)
            with self.assertRaisesRegex(ValueError, "initial fixed"):
                fixed_cache.reweight(original)

    def test_symbolic_cached_entire_law_changes_with_the_head(self):
        words, canvas = [b"0", b"0", b" ", None, None], (None,) * 3
        table, _ = fixture(words, [[1] * 5] * 3, canvas, 3, 4)
        graph = terminated_graph(table, canvas, 0, 3, 4, symbolic=True, **LIMITS)
        cache = CPUCache(graph, table, **LIMITS)
        for rows in ([[1] * 5] * 3, [[3, 1, 1, 2, 1], [1, 2, 3, 1, 2], [1, 2, 1, 3, 1]]):
            _, weights = fixture(words, rows, canvas, 3, 4)
            post = cache.reweight(weights)
            expected = enumerate_terminated(words, weights, 3, 4, 0)
            mass = sum(expected.values(), F())
            observed, pending = defaultdict(F), [((), F(1))]
            while pending:
                tickets, probability = pending.pop()
                weights.consumed = False
                try:
                    word = sample(post, weights, Tickets(tickets))
                except Branch as branch:
                    self.assertLessEqual(branch.size, 64)
                    pending.extend(
                        ((*tickets, i), probability / branch.size) for i in range(branch.size)
                    )
                else:
                    observed[word] += probability
            self.assertEqual(dict(observed), {w: v / mass for w, v in expected.items()})

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
