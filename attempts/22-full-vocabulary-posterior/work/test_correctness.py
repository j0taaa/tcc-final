"""Full original-token enumeration and exact actual-sampler law, no NN required."""

import itertools
import json
import random
import unittest
from fractions import Fraction
from math import prod

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .forest import Prepared
from .lexer import lexical_grammar
from .posterior import Posterior, Weights
from .table import LexerTable


def accepted(adapter, word):
    try:
        json.loads(
            adapter.detokenize_bytes(word).decode(),
            parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
        )
        return True
    except (ValueError, UnicodeDecodeError):
        return False


def enumerate_expected(table, canvas, weights):
    rows = [range(table.adapter.vocabulary_size) if t is None else (t,) for t in canvas]
    masses = {
        word: prod(weights.at(p, t) for p, t in enumerate(word))
        for word in itertools.product(*rows)
        if accepted(table.adapter, word)
    }
    total = sum(masses.values())
    marginal = tuple(
        {fixed: total}
        if fixed is not None
        else tuple(
            sum(w for word, w in masses.items() if word[p] == t)
            for t in range(table.adapter.vocabulary_size)
        )
        for p, fixed in enumerate(canvas)
    )
    return masses, total, marginal


class NeedDraw(Exception):
    def __init__(self, total):
        self.total = total


class Replay:
    def __init__(self, prefix):
        self.prefix, self.index = prefix, 0

    def randrange(self, total):
        if self.index == len(self.prefix):
            raise NeedDraw(total)
        value = self.prefix[self.index]
        self.index += 1
        if not 0 <= value < total:
            raise AssertionError("invalid exact draw")
        return value


def sampler_law(posterior):
    pending = [((), Fraction(1))]
    outcomes = {}
    visits = 0
    while pending:
        prefix, prob = pending.pop()
        visits += 1
        if visits > 100000:
            raise AssertionError("sampler law enumeration exceeded limit")
        try:
            word = posterior.sample(Replay(prefix))
        except NeedDraw as draw:
            pending.extend(((*prefix, u), prob / draw.total) for u in range(draw.total))
        else:
            outcomes[word] = outcomes.get(word, Fraction()) + prob
    return outcomes


class FullVocabularyCorrectness(unittest.TestCase):
    def test_original_masses_and_marginals_in_all_representations(self):
        emissions = (
            b'"',
            b"a",
            b"b",
            b"0",
            b" ",
            b"[",
            b"]",
            b'"a"',
            b"\\",
            None,
            b"\xc3",
            b"\xa1",
        )
        table = LexerTable(CompositionalByteLevelAdapter(emissions))
        rng = random.Random(2026100925)
        for case in range(36):
            canvas = [None] * 3
            if case % 3 == 0:
                canvas[0] = 0
            elif case % 3 == 1:
                canvas[1] = 3
            raw = [[rng.randint(0, 5) for _ in emissions] for _ in canvas]
            for row in raw:
                row[0] += 1
            weights = Weights(raw, canvas, len(emissions))
            _, total, marginal = enumerate_expected(table, canvas, weights)
            for kind in ("raw", "global", "position", "local"):
                prepared = Prepared(table, canvas, lexical_grammar(), kind)
                result = Posterior(prepared, weights)
                self.assertEqual(result.total, total, (case, kind))
                self.assertEqual(result.mass, Fraction(total, prod(weights.denominators)))
                if total:
                    self.assertEqual(result.marginals(), (marginal, total), (case, kind))
                    for seed in range(4):
                        sample = result.sample(random.Random(seed))
                        self.assertTrue(accepted(table.adapter, sample))
                        self.assertTrue(
                            all(t is None or t == sample[p] for p, t in enumerate(canvas))
                        )
                else:
                    with self.assertRaisesRegex(ValueError, "zero_valid_mass"):
                        result.sample(random.Random(0))

    def test_exact_actual_sampler_law_with_aliases_and_overlaps(self):
        table = LexerTable(CompositionalByteLevelAdapter((b'"', b"a", b"a", b"b", b"0", b" ")))
        for canvas, raw in [
            ((0, None, 0), [[1] * 6, [0, 2, 1, 3, 0, 0], [1] * 6]),
            ((None, 4, None), [[1, 0, 0, 0, 0, 1], [1] * 6, [1, 0, 0, 0, 0, 1]]),
        ]:
            weights = Weights(raw, canvas, 6)
            expected, total, _ = enumerate_expected(table, canvas, weights)
            law = {word: Fraction(w, total) for word, w in expected.items() if w}
            for kind in ("raw", "global", "position", "local"):
                posterior = Posterior(Prepared(table, canvas, lexical_grammar(), kind), weights)
                self.assertEqual(sampler_law(posterior), law)

    def test_full_vocabulary_reuse_after_weights_clamps_and_remasking(self):
        table = LexerTable(
            CompositionalByteLevelAdapter((b'"', b"a", b"b", b"0", b" ", b"\xc3", b"\xa1"))
        )
        frames = ((0, None, None, 0), (0, 1, None, 0), (0, None, 6, 0), (0, None, None, 0))
        for kind in ("raw", "global", "position", "local"):
            prepared = Prepared(table, frames[0], lexical_grammar(), kind)
            for step, canvas in enumerate(frames):
                probabilities = [[1 + ((t + step) % 3) for t in range(7)] for _ in canvas]
                weights = Weights(probabilities, canvas, 7)
                _, total, marginals = enumerate_expected(table, canvas, weights)
                posterior = Posterior(prepared, weights)
                self.assertEqual(posterior.total, total)
                if total:
                    self.assertEqual(posterior.marginals(), (marginals, total))
                    sample = posterior.sample(random.Random(step))
                    self.assertTrue(accepted(table.adapter, sample))
                    self.assertTrue(all(t is None or sample[p] == t for p, t in enumerate(canvas)))
            with self.assertRaisesRegex(ValueError, "initial fixed"):
                Posterior(prepared, Weights([[1] * 7] * 4, (None,) * 4, 7))

    def test_dyadic_normalization_and_scope(self):
        weights = Weights([[0.1, 0.2, 0.7]], (None,), 3)
        self.assertEqual(sum(weights.rows[0]), weights.denominators[0])
        self.assertEqual(
            Fraction(weights.rows[0][0], weights.denominators[0]),
            Fraction(0.1) / (Fraction(0.1) + Fraction(0.2) + Fraction(0.7)),
        )
        with self.assertRaisesRegex(ValueError, "zero model row"):
            Weights([[0, 0]], (None,), 2)


if __name__ == "__main__":
    unittest.main()
