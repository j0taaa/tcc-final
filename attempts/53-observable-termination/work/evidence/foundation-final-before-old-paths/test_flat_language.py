"""Independent finite-language and stopping-law oracles; no neural data."""

import itertools
import json
import random
import unittest
from fractions import Fraction

from .flat_language import EMPTY, MANY, analyze, classify, concat, join


def all_sets(words):
    return [set(c) for n in range(len(words) + 1) for c in itertools.combinations(words, n)]


class FlatLanguageTests(unittest.TestCase):
    def test_finite_language_quotient_and_cancellation(self):
        sets = all_sets((b"", b"a", b"b", b"aa", b"ab"))
        for a, b in itertools.product(sets, repeat=2):
            self.assertEqual(classify(a | b), join(classify(a), classify(b)))
            self.assertEqual(
                classify({x + y for x in a for y in b}), concat(classify(a), classify(b))
            )
        # Prefix lengths make per-class lexicographic min/max substitution unsafe.
        self.assertLess(b"az", b"z")
        self.assertEqual(concat(classify((b"", b"a")), b"z"), MANY)
        self.assertIs(concat(MANY, EMPTY), EMPTY)

    def test_all_paths_random_dags_aliases_and_epsilon(self):
        rng = random.Random(53001)
        for n in range(2, 10):
            for _ in range(40):
                edges = [[] for _ in range(n)]
                for i in range(n):
                    for j in range(i + 1, n):
                        if rng.randrange(3) == 0:
                            edges[i].append((rng.choice((b"", b"0", b"1", b"}", b"01")), j))
                terminals = {n - 1}

                def enumerate_at(i, terminals=terminals, edges=edges):
                    words = {b""} if i in terminals else set()
                    for s, j in edges[i]:
                        words.update(s + t for t in enumerate_at(j))
                    return words

                values = analyze(edges, terminals)
                for i in range(n):
                    self.assertEqual(values[i], classify(enumerate_at(i)))
        with self.assertRaises(ValueError):
            analyze([[(b"a", 0)]], {0})

    def test_original_ids_first_eos_clamps_and_whitespace(self):
        emissions = (b"0", b"1", b"}", b" ", b"", b"", b"EOS")
        eos = 6

        # Toy suffix grammar: ONE digit, }, whitespace; whitespace also before digit/}.
        def step(s, v):
            if v in (3, 4, 5):
                return s
            if s == 0 and v in (0, 1):
                return 1
            if s == 1 and v == 2:
                return 2
            return -1

        cases = 0
        for width in (3, 4, 5):
            for fixed in (
                {},
                {0: 1},
                {1: 1},
                {2: 2},
                {width - 1: eos},
                {0: 1, width - 1: eos},
                {0: 4, 1: 1, 2: 2},
            ):
                n = 3 * (width + 1) + 1
                terminal = n - 1
                edges = [[] for _ in range(n)]
                for i in range(width):
                    for s in range(3):
                        for v in (fixed[i],) if i in fixed else range(7):
                            if v == eos:
                                if s == 2 and i >= max(fixed, default=-1):
                                    edges[3 * i + s].append((b"", terminal))
                            else:
                                t = step(s, v)
                                if t >= 0:
                                    label = emissions[v].replace(b" ", b"")
                                    edges[3 * i + s].append((label, 3 * (i + 1) + t))
                expected, originals = set(), 0
                for length in range(1, width + 1):
                    for prefix in itertools.product(range(6), repeat=length - 1):
                        w = (*prefix, eos)
                        if any(i >= length or w[i] != v for i, v in fixed.items()):
                            continue
                        text = b'{"answer":' + b"".join(emissions[v] for v in prefix)
                        try:
                            parsed = json.loads(text)
                        except ValueError:
                            continue
                        if set(parsed) != {"answer"} or parsed["answer"] not in (0, 1):
                            continue
                        # Independent byte check rejects multi-digit numbers.
                        number = text.split(b":", 1)[1].split(b"}", 1)[0].strip()
                        if number not in (b"0", b"1"):
                            continue
                        expected.add(b"".join(emissions[v] for v in prefix).replace(b" ", b""))
                        originals += 1
                self.assertEqual(analyze(edges, {terminal})[0], classify(expected))
                if len(expected) == 1:
                    self.assertGreater(originals, 0)
                cases += 1
        self.assertEqual(cases, 21)
        self.assertEqual(classify((b"1}", b"1.0}")), MANY)  # conservative for numeric semantics
        self.assertNotEqual(json.loads('{"s":"a b"}'), json.loads('{"s":"ab"}'))
        self.assertEqual(b'{"s":"a b"}'.replace(b" ", b""), b'{"s":"ab"}')

    def test_terminal_coupling_all_binary_leaf_labels(self):
        def evaluate(labels, stop):
            if len(labels) == 1 or (stop and len(set(labels)) == 1):
                return {labels[0]: Fraction(1)}, Fraction(0)
            midpoint = len(labels) // 2
            first, cost_a = evaluate(labels[:midpoint], stop)
            second, cost_b = evaluate(labels[midpoint:], stop)
            law = {v: (first.get(v, 0) + second.get(v, 0)) / 2 for v in (0, 1)}
            return {v: p for v, p in law.items() if p}, 1 + (cost_a + cost_b) / 2

        strict = 0
        for labels in itertools.product((0, 1), repeat=8):
            original, cost = evaluate(labels, False)
            optimized, reduced = evaluate(labels, True)
            self.assertEqual(original, optimized)
            self.assertLessEqual(reduced, cost)
            strict += reduced < cost
        self.assertGreater(strict, 0)
