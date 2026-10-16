"""Independent json parser over ALL small original-ID completions."""

import itertools
import json
import unittest

from .flat_language import EMPTY, classify
from .terminal_compiler import NumericSuffix, TerminalCompiler, project


class TerminalCompilerTests(unittest.TestCase):
    def test_all_small_original_completions_and_independent_graph(self):
        emissions = (b"0", b"1", b"}", b" ", b"", b"", b"1.0", b"EOS")
        language = NumericSuffix(emissions, 7, 7)
        checks = 0
        for erase in (False, True):
            compiler = TerminalCompiler(language, erase)
            for width in (2, 3, 4):
                for fixed in (
                    {},
                    {0: 1},
                    {1: 1},
                    {1: 2},
                    {width - 1: 7},
                    {0: 4},
                    {0: 1, width - 1: 7},
                ):
                    words = []
                    for length in range(1, width + 1):
                        for prefix in itertools.product(range(7), repeat=length - 1):
                            w = (*prefix, 7)
                            if any(i >= length or w[i] != v for i, v in fixed.items()):
                                continue
                            raw = b"".join(emissions[v] for v in prefix)
                            try:
                                parsed = json.loads(b'{"answer":' + raw)
                            except ValueError:
                                continue
                            if set(parsed) != {"answer"} or not isinstance(
                                parsed["answer"], (int, float)
                            ):
                                continue
                            words.append(project(raw, erase))
                            self.assertEqual(compiler.witness_projection(w), project(raw, erase))
                    expected = classify(words)
                    self.assertEqual(compiler.classify(width, fixed), expected)
                    self.assertEqual(compiler.generic_graph_control(width, fixed), expected)
                    checks += 1
        self.assertEqual(checks, 42)

    def test_eos_cannot_truncate_fixed_ids_and_empty_is_not_certificate(self):
        c = TerminalCompiler(NumericSuffix((b"1}", b"", b"EOS"), 2, 2), True)
        self.assertIs(c.classify(1, {}), EMPTY)
        with self.assertRaises(ValueError):
            c.classify(4, {1: 2, 3: 0})
        with self.assertRaises(ValueError):
            c.classify(3, {3: 0})
        self.assertEqual(c.classify(4, {0: 0}), b"1}")
