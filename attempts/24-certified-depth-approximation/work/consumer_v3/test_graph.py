"""Small offline language oracles; native Torch tests remain opt-in."""

import itertools
import unittest

from ..consumer_v2.test_query import enumerate_words, fixture
from ..stack_control import StackPrepared
from .mosaic_control import accepts, sparse_graph


class GraphLanguageTests(unittest.TestCase):
    def test_full_descriptor_merge_keeps_aliases_and_internal_depth_peaks(self):
        words = [b"0", b"0", b"[]", b"[[]]", b" ", b"["]
        rows = [[1, 2, 3, 1, 2, 1]] * 3
        table, weights, _ = fixture(words, rows)
        for depth in (0, 1, 2, None):
            prepared = StackPrepared(
                table,
                weights.canvas,
                max_depth=depth,
                timeout_seconds=5,
                max_cells=10000,
                max_edges=10000,
                max_terms=10000,
            )
            graph = sparse_graph(prepared)
            expected = enumerate_words(table, weights, depth)
            for word in itertools.product(range(len(words)), repeat=3):
                self.assertEqual(accepts(graph, word), word in expected, (depth, word))
            self.assertTrue(accepts(graph, (0, 4, 4)))
            self.assertTrue(accepts(graph, (1, 4, 4)))

    def test_split_unicode_and_fixed_original_alias(self):
        words = [b'"', b"\xc3", b"\xa9", b"a", b"a", b'\\"']
        canvas = (0, None, None, 0)
        table, weights, _ = fixture(words, [[1, 1, 1, 1, 2, 1]] * 2, canvas)
        prepared = StackPrepared(
            table,
            canvas,
            max_depth=0,
            timeout_seconds=5,
            max_cells=10000,
            max_edges=10000,
            max_terms=10000,
        )
        graph = sparse_graph(prepared)
        expected = enumerate_words(table, weights, 0)
        for a, b in itertools.product(range(len(words)), repeat=2):
            word = (0, a, b, 0)
            self.assertEqual(accepts(graph, word), word in expected, word)
        self.assertTrue(accepts(graph, (0, 1, 2, 0)))
        self.assertFalse(accepts(graph, (0, 2, 1, 0)))
