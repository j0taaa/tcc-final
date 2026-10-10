"""Tiny independent original-ID enumeration; correctness, never speed evidence."""

import itertools
import json
import random
import re
import unittest
from fractions import Fraction
from math import prod

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .certificate import CounterTable, conditional_error
from .posterior import Weights
from .stack_control import StackPosterior, StackPrepared
from .table import LexerTable


def json_depth(value):
    if isinstance(value, dict):
        return 1 + max(map(json_depth, value.values()), default=0)
    if isinstance(value, list):
        return 1 + max(map(json_depth, value), default=0)
    return 0


def independent_scan(data):
    """Regex maximal JSON primitives + standard-library string decoder.

    Does not use project lexer, grouping, normalizer, or stack. Complete lexical
    sequences can be syntactically invalid: this oracle intentionally ignores
    delimiter types, keys, commas, and value sequencing for the counter bound.
    """
    text = data.decode("utf8")
    decoder = json.JSONDecoder()
    height = peak = position = 0
    number = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
    while position < len(text):
        char = text[position]
        if char in " \t\r\n:,":
            position += 1
        elif char in "{}[]":
            height += 1 if char in "[{" else -1
            if height < 0:
                return None
            peak = max(peak, height)
            position += 1
        elif char == '"':
            value, end = decoder.raw_decode(text, position)
            if not isinstance(value, str):
                raise AssertionError("string oracle decoded nonstring")
            position = end
        elif next((w for w in ("true", "false", "null") if text.startswith(w, position)), None):
            word = next(w for w in ("true", "false", "null") if text.startswith(w, position))
            position += len(word)
        else:
            match = number.match(text, position)
            if match is None:
                return None
            position = match.end()
            if position < len(text) and text[position] in ".eE0123456789":
                return None
    return height, peak


def enumerate_events(table, weights, depth):
    accepted, total, upper = {}, 0, 0
    numerators = [
        dict() if t is not None else [0] * weights.vocabulary_size for t in weights.canvas
    ]
    domains = [(t,) if t is not None else range(weights.vocabulary_size) for t in weights.canvas]
    for tokens in itertools.product(*domains):
        mass = prod(weights.at(p, t) for p, t in enumerate(tokens))
        if not mass or any(table.adapter.emissions[t] is None for t in tokens):
            continue
        data = b"".join(table.adapter.emissions[t] for t in tokens)
        try:
            relaxed = independent_scan(data)
        except (ValueError, UnicodeDecodeError):
            relaxed = None
        if relaxed is not None and relaxed[0] == 0 and relaxed[1] > depth:
            upper += mass
        try:
            value = json.loads(data.decode("utf8"), parse_constant=lambda _: None)
        except (ValueError, UnicodeDecodeError):
            continue
        if json_depth(value) > depth:
            continue
        accepted[tokens] = mass
        total += mass
        for p, t in enumerate(tokens):
            if isinstance(numerators[p], dict):
                numerators[p][t] = numerators[p].get(t, 0) + mass
            else:
                numerators[p][t] += mass
    return accepted, total, tuple(tuple(r) if isinstance(r, list) else r for r in numerators), upper


def prepare(table, canvas, depth):
    return StackPrepared(
        table,
        canvas,
        max_depth=depth,
        max_edges=100000,
        max_cells=100000,
        max_terms=100000,
        timeout_seconds=20,
    )


class DepthCertificateCorrectness(unittest.TestCase):
    def test_exhaustive_original_mass_tail_and_marginals(self):
        emissions = (b"[", b"]", b"{", b"}", b",", b":", b"0", b'"x"', b"[[]]", b" ", None)
        table = LexerTable(CompositionalByteLevelAdapter(emissions))
        counter = CounterTable(table)
        rng = random.Random(2026101024)
        for canvas in ((None,) * 3, (0, None, 1), (None,), ()):
            rows = [[rng.randint(1, 4) for _ in emissions] for _ in canvas]
            weights = Weights(rows, canvas, len(emissions))
            full = StackPosterior(prepare(table, canvas, None), weights)
            for depth in range(4):
                _, total, marginals, upper = enumerate_events(table, weights, depth)
                result = StackPosterior(prepare(table, canvas, depth), weights)
                closed, _ = counter.tail(weights, depth)
                hit, _ = counter.tail(weights, depth, mode="hit")
                suffix_hit, _ = counter.tail(weights, depth, mode="suffix_hit")
                self.assertEqual(result.total, total, (canvas, depth))
                self.assertEqual(closed, Fraction(upper, prod(weights.denominators)))
                self.assertLessEqual(full.mass - result.mass, closed)
                self.assertLessEqual(closed, hit)
                self.assertLessEqual(closed, suffix_hit)
                self.assertLessEqual(suffix_hit, hit)
                if total:
                    self.assertEqual(result.marginals(), (marginals, total))
                    actual = (full.mass - result.mass) / full.mass
                    self.assertLessEqual(actual, conditional_error(result.mass, closed))
                    for seed in range(4):
                        tokens = result.sample(random.Random(seed))
                        self.assertLessEqual(
                            json_depth(json.loads(table.adapter.detokenize_bytes(tokens))), depth
                        )

    def test_intra_token_peak_and_aliases(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[]", b"[]", b"[[]]", b'"[[]]"')))
        weights = Weights([[1, 2, 3, 4]], (None,), 4)
        result = StackPosterior(prepare(table, weights.canvas, 1), weights)
        self.assertEqual(result.mass, Fraction(7, 10))
        self.assertEqual(result.marginals(), (((1, 2, 0, 4),), 7))
        self.assertEqual(CounterTable(table).tail(weights, 1)[0], Fraction(3, 10))

    def test_exact_sampler_law_is_on_original_aliases(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[]", b"[]", b"[[]]", b"0")))
        result = StackPosterior(prepare(table, (None,), 1), Weights([[1, 2, 3, 1]], (None,), 4))

        class Draw(Exception):
            pass

        class Replay:
            def __init__(self, prefix):
                self.prefix = iter(prefix)

            def randrange(self, total):
                value = next(self.prefix, None)
                if value is None:
                    raise Draw(total)
                return value

        pending, law = [((), Fraction(1))], {}
        while pending:
            prefix, probability = pending.pop()
            try:
                tokens = result.sample(Replay(prefix))
            except Draw as draw:
                pending.extend(
                    ((*prefix, x), probability / draw.args[0]) for x in range(draw.args[0])
                )
            else:
                law[tokens] = law.get(tokens, Fraction()) + probability
        self.assertEqual(law, {(0,): Fraction(1, 4), (1,): Fraction(1, 2), (3,): Fraction(1, 4)})

    def test_rare_validity_requires_normalization(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[]", b"[[]]", b"invalid")))
        weights = Weights([[2**-40, 2**-40, 1]], (None,), 3)
        result = StackPosterior(prepare(table, weights.canvas, 1), weights)
        upper, _ = CounterTable(table).tail(weights, 1)
        self.assertLess(upper, Fraction(1, 10**10))
        self.assertEqual(conditional_error(result.mass, upper), Fraction(1, 2))

    def test_utf8_and_remasking_with_original_ids(self):
        table = LexerTable(
            CompositionalByteLevelAdapter((b'"', b"\xc3", b"\xa1", b"a", b"[", b"]"))
        )
        initial = (0, None, None, 0)
        prepared = prepare(table, initial, 0)
        for canvas in (initial, (0, 1, 2, 0), initial):
            weights = Weights([[1, 2, 3, 4, 5, 6]] * 4, canvas, 6)
            _, total, marginals, upper = enumerate_events(table, weights, 0)
            result = StackPosterior(prepared, weights)
            self.assertEqual((result.total, result.marginals()), (total, (marginals, total)))
            self.assertEqual(
                CounterTable(table).tail(weights, 0)[0], Fraction(upper, prod(weights.denominators))
            )
        with self.assertRaisesRegex(ValueError, "initial fixed"):
            StackPosterior(prepared, Weights([[1] * 6] * 4, (None,) * 4, 6))

    def test_closed_bound_strictly_strengthens_completed_token_hit(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[]", b"[[", b"0")))
        weights = Weights([[1, 1, 1]], (None,), 3)
        counter = CounterTable(table)
        self.assertEqual(counter.tail(weights, 1)[0], 0)
        self.assertEqual(counter.tail(weights, 1, mode="hit")[0], Fraction(1, 3))
        with self.assertRaisesRegex(ValueError, "zero lower"):
            conditional_error(Fraction(), Fraction())
        for bad in (-1, True, 1.5):
            with self.assertRaisesRegex(ValueError, "depth"):
                prepare(table, (None,), bad)


if __name__ == "__main__":
    unittest.main()
