"""Small exact A80 source oracles; no scientific timings or production campaign."""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import sys
import unittest
from collections import defaultdict
from dataclasses import replace
from fractions import Fraction as F
from math import prod
from pathlib import Path
from random import Random
from unittest.mock import patch

from mwpc_exact.cfg_posterior import CfgSampler, CompilationLimit
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.recognizer import recognizes_cnf

spec = importlib.util.spec_from_file_location("a80_cases", Path(__file__).with_name("cases.py"))
assert spec is not None and spec.loader is not None
c = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = c
spec.loader.exec_module(c)


def recursive_reference(family, data):
    """Recursive byte recognizers, independent of the sampler and its validators."""

    def expression(i):
        if i == len(data):
            raise ValueError
        if data[i] == ord("a"):
            return i + 1
        if data[i] == ord("!"):
            return expression(i + 1)
        if data[i] == ord("&"):
            return expression(expression(i + 1))
        raise ValueError

    def sequence(i):
        while i < len(data) and data[i] in b"([":
            close = ord(")") if data[i] == ord("(") else ord("]")
            i = sequence(i + 1)
            if i == len(data) or data[i] != close:
                raise ValueError
            i += 1
        return i

    try:
        return (sequence(0) if family == "dyck" else expression(0)) == len(data)
    except ValueError:
        return False


def cartesian_oracle(prepared, recognizes):
    """Enumerate original IDs only in tiny fixtures, never in source preparation."""
    state = prepared.private.plan.state
    lookups = tuple(
        dict(zip(row, weights, strict=True))
        for row, weights in zip(state.support.rows, prepared.private.weights, strict=True)
    )
    result = {}
    for word in itertools.product(*state.support.rows):
        data = state.tokenizer_adapter.detokenize_bytes(word)
        if recognizes(data):
            result[word] = prod(row[t] for row, t in zip(lookups, word, strict=True))
    return result


class NeedDraw(Exception):
    def __init__(self, stop):
        self.stop = stop


class TranscriptRandom(Random):
    def __init__(self, transcript):
        super().__init__(0)
        self.transcript = iter(transcript)

    def randrange(self, stop):
        if stop == 1:
            return 0
        try:
            result = next(self.transcript)
        except StopIteration:
            raise NeedDraw(stop) from None
        if not 0 <= result < stop:
            raise AssertionError("invalid test transcript")
        return result


def exact_rng_law(draw):
    """Exhaust all integer RNG outcomes for small-weight source fixtures."""
    pending = [((), F(1))]
    law = defaultdict(F)
    visited = 0
    while pending:
        transcript, mass = pending.pop()
        visited += 1
        if visited > 50_000:
            raise AssertionError("fixture RNG transcript expansion is too large")
        try:
            outcome = draw(TranscriptRandom(transcript))
        except NeedDraw as exc:
            if exc.stop > 100:
                raise AssertionError("not a small-weight correctness fixture") from exc
            pending.extend(((*transcript, j), mass / exc.stop) for j in range(exc.stop))
        else:
            law[outcome] += mass
    return dict(law)


class CaseTests(unittest.TestCase):
    def assert_source_law(self, prepared, recognizes):
        raw = cartesian_oracle(prepared, recognizes)
        self.assertTrue(raw)
        total = sum(raw.values())
        self.assertEqual(prepared.valid_count, len(raw))
        self.assertEqual(prepared.reference.total, len(raw))
        self.assertEqual(prepared.private.total, total)
        self.assertEqual(prepared.min_ratio_product, min(raw.values()))
        self.assertEqual(prepared.max_ratio_product, max(raw.values()))
        triples = prepared.enumerate_law(len(raw))
        self.assertEqual(len(triples), len(raw))
        self.assertEqual(len({word for word, _, _ in triples}), len(raw))
        law = {word: (p, mu) for word, p, mu in triples}
        self.assertEqual(law, {word: (F(w, total), F(1, len(raw))) for word, w in raw.items()})
        self.assertEqual(sum(p for _, p, _ in triples), 1)
        self.assertEqual(sum(mu for _, _, mu in triples), 1)
        for word, p, mu in triples:
            self.assertIsNone(prepared.validate(word))
            self.assertEqual(prepared.private.probability(word), p)
            self.assertEqual(prepared.reference.probability(word), mu)
            self.assertEqual(p / mu, F(raw[word] * len(raw), total))
            self.assertLessEqual((raw[word] * len(raw)).bit_length(), prepared.max_work_bits)
        self.assertEqual(prepared.exactness_scope, "exact_on_support")
        self.assertEqual(prepared.omitted_mass, 0)
        return raw

    def test_official_case_roster_and_exact_sha_tags(self):
        self.assertEqual(
            [(case.family, case.n) for case in c.cases()],
            [(family, n) for family in ("dyck", "expr") for n in (8, 16, 32)],
        )
        known = (
            ("dyck", 8, 0, 0, 597529931124),
            ("dyck", 8, 0, 4, 513180105691),
            ("expr", 32, 31, 3, 607641576468),
        )
        for family, n, pos, token, expected in known:
            self.assertEqual(c.raw_weight(family, n, pos, token), expected)
        for case in c.cases():
            for position in range(case.n):
                for token in range(5 if case.family == "dyck" else 4):
                    literal = f"A80-v1|{case.family}|{case.n}|{position}|{token}"
                    value = int(hashlib.sha256(literal.encode("ascii")).hexdigest(), 16)
                    expected = 3 * 2**37 + value % (2**38 + 1)
                    self.assertEqual(c.raw_weight(case.family, case.n, position, token), expected)
                    self.assertGreaterEqual(expected, 3 * 2**37)
                    self.assertLessEqual(expected, 5 * 2**37)

    def test_small_lengths_against_original_id_cartesian_reference(self):
        for family in ("dyck", "expr"):
            for n in (2, 4, 6) if family == "dyck" else (1, 2, 3, 4, 5, 6):
                with self.subTest(family=family, n=n):
                    prepared = c.prepare(c.Case(family, n))
                    raw = self.assert_source_law(
                        prepared, lambda data, family=family: recursive_reference(family, data)
                    )
                    for position, row in enumerate(prepared.private.plan.state.support.rows):
                        self.assertEqual(
                            prepared.private.weights[position],
                            tuple(c.raw_weight(family, n, position, token) for token in row),
                        )
                    # PRNG reproducibility and valid draws, not an empirical IID claim.
                    first, second = Random("source-test"), Random("source-test")
                    for _ in range(12):
                        for sampler in (prepared.private, prepared.reference):
                            word = sampler.draw(first)
                            self.assertEqual(word, sampler.draw(second))
                            self.assertIn(word, raw)
                            self.assertIsNone(prepared.validate(word))
                    self.assertGreaterEqual(prepared.compile_seconds, 0)
                    self.assertGreaterEqual(prepared.prepare_seconds, 0)

    def test_byte_recognizers_against_independent_boolean_cnf(self):
        for family in ("dyck", "expr"):
            source, emissions = c._source(family)
            plan = c._compile(source, emissions, (tuple(range(len(emissions))),) * 3)
            check = c._dyck_bytes if family == "dyck" else c._expr_bytes
            for n in range(5):
                alphabet = b"()[]" if family == "dyck" else b"a!&"
                for data in itertools.product(alphabet, repeat=n):
                    self.assertEqual(check(bytes(data)), recognizes_cnf(plan.state.grammar, data))

    def test_aliases_remain_distinct_and_exact_draw_laws(self):
        source, emissions = c._source("dyck")
        plan = c._compile(source, emissions, ((0, 4), (1,)))
        prepared = c._prepare(plan, ((2, 3), (2,)), c._dyck_bytes)
        self.assert_source_law(prepared, lambda data: recursive_reference("dyck", data))
        self.assertEqual(prepared.valid_count, 2)
        self.assertEqual(exact_rng_law(prepared.private.draw), {(0, 1): F(2, 5), (4, 1): F(3, 5)})
        self.assertEqual(exact_rng_law(prepared.reference.draw), {(0, 1): F(1, 2), (4, 1): F(1, 2)})
        self.assertEqual(
            plan.state.tokenizer_adapter.detokenize_bytes((0, 1)),
            plan.state.tokenizer_adapter.detokenize_bytes((4, 1)),
        )
        observed = exact_rng_law(lambda rng: next(prepared.observations(rng)))
        self.assertEqual(observed, {(8, 10): F(9, 20), (12, 10): F(11, 20)})
        for u, v in observed:
            self.assertIs(type(u), int)
            self.assertIs(type(v), int)
            self.assertGreater(v, 0)

    def test_multibyte_tokens_pins_and_zero_target_scores(self):
        source, _ = c._source("dyck")
        emissions = (b"(", b")", b"()", b"[]", b"(", None)
        plan = c._compile(source, emissions, ((4,), (1, 2, 3), (1, 2, 3)), (4, None, None))
        self.assertEqual(plan.state.support.rows[0], (4,))
        prepared = c._prepare(plan, ((9,), (0, 2, 0), (5, 1, 0)), c._dyck_bytes)
        raw = self.assert_source_law(prepared, lambda data: recursive_reference("dyck", data))
        self.assertTrue(any(weight == 0 for weight in raw.values()))
        self.assertEqual(prepared.min_ratio_product, 0)
        for word in raw:
            self.assertEqual(word[0], 4)
        self.assertEqual(exact_rng_law(prepared.private.draw), {(4, 2, 1): F(1)})
        for invalid in ((0, 2, 1), (4, 1, 1), (4, 2), (4, 2, 99), (True, 2, 1)):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    prepared.validate(invalid)
                self.assertEqual(prepared.private.probability(invalid), 0)
                self.assertEqual(prepared.reference.probability(invalid), 0)

    def test_recursive_sampler_exact_rng_laws(self):
        for family, n in (("dyck", 4), ("expr", 3)):
            with self.subTest(family=family):
                source, emissions = c._source(family)
                rows = (tuple(range(len(emissions))),) * n
                plan = c._compile(source, emissions, rows)
                weights = tuple(
                    tuple(1 + int(position == 0 and token == 0) for token in row)
                    for position, row in enumerate(rows)
                )
                check = c._dyck_bytes if family == "dyck" else c._expr_bytes
                prepared = c._prepare(plan, weights, check)
                raw = self.assert_source_law(
                    prepared, lambda data, family=family: recursive_reference(family, data)
                )
                self.assertEqual(
                    exact_rng_law(prepared.private.draw),
                    {word: F(w, sum(raw.values())) for word, w in raw.items()},
                )
                self.assertEqual(
                    exact_rng_law(prepared.reference.draw),
                    {word: F(1, len(raw)) for word in raw},
                )

    def test_utf8_bytes_aliases_and_equal_sources(self):
        b = _SourceGrammarBuilder(("S",), start="S")
        b.rule("S", "é".encode(), "S")
        b.rule("S", b"!", "S")
        b.rule("S")
        emissions = (b"\xc3\xa9", b"\xc3", b"\xa9", b"!", b"\xc3\xa9")
        plan = c._compile(b.build(), emissions, ((0, 1, 2, 3, 4),) * 2)

        def check(data):
            return recognizes_cnf(plan.state.grammar, tuple(data))

        prepared = c._prepare(plan, ((1,) * 5,) * 2, check)
        self.assert_source_law(prepared, check)
        self.assertIsNone(prepared.validate((1, 2)))
        for _word, p, mu in prepared.enumerate_law():
            self.assertEqual(p, mu)
        self.assertEqual(prepared.min_ratio_product, 1)
        self.assertEqual(prepared.max_ratio_product, 1)

    def test_zero_mass_and_resource_refusals_remain_distinct(self):
        with self.assertRaisesRegex(c.ZeroMassOnSupport, "empty_public_language"):
            c.prepare(c.Case("dyck", 1))
        source, emissions = c._source("expr")
        plan = c._compile(source, emissions, ((0, 3),))
        with self.assertRaisesRegex(c.ZeroMassOnSupport, "zero_target_mass"):
            c._prepare(plan, ((0, 0),), c._expr_bytes)
        prepared = c._prepare(plan, ((1, 1),), c._expr_bytes)
        with patch.object(c.Prepared, "_enumerate_words", side_effect=AssertionError("enumerated")):
            with self.assertRaises(c.ResourceRefusal):
                prepared.enumerate_law(1)
            with self.assertRaises(c.ResourceRefusal):
                replace(prepared, valid_count=65_537).enumerate_law(10**9)
        for cap, value in (
            ("MAX_CHART_CELLS", 0),
            ("MAX_ALTERNATIVES", 0),
            ("MAX_PREPROCESSING_WORK", 1),
        ):
            with self.subTest(cap=cap), patch.object(c, cap, value):
                with self.assertRaises(CompilationLimit):
                    c.prepare(c.Case("expr", 2))

    def test_no_outside_and_fixed_compilation_caps(self):
        with patch.object(CfgSampler, "evaluate", side_effect=AssertionError("outside")):
            with patch.object(c, "compile_cfg_sampler", wraps=c.compile_cfg_sampler) as compiler:
                c.prepare(c.Case("expr", 2))
        caps = compiler.call_args.kwargs
        self.assertEqual(caps["max_chart_cells"], 200_000)
        self.assertEqual(caps["max_alternatives"], 1_000_000)
        self.assertGreater(caps["max_preprocessing_work"], 0)
        self.assertLess(caps["max_preprocessing_work"], 5_000_000)

    def test_input_contracts(self):
        for args in (("other", 8), ("dyck", 0), ("dyck", True)):
            with self.assertRaises(ValueError):
                c.Case(*args)
        for args in (("expr", 2, -1, 0), ("dyck", 2, 0, 5), ("expr", 2, 0, True)):
            with self.assertRaises(ValueError):
                c.raw_weight(*args)
        prepared = c.prepare(c.Case("expr", 1))
        for weights in (((-1,) * 4,), ((True,) * 4,), ((1.0,) * 4,), ((1,),)):
            with self.assertRaises(ValueError):
                c._prepare(prepared.private.plan, weights, c._expr_bytes)
        with self.assertRaises(TypeError):
            prepared.private.draw(None)
        for limit in (-1, True):
            with self.assertRaises(ValueError):
                prepared.enumerate_law(limit)


if __name__ == "__main__":
    unittest.main()
