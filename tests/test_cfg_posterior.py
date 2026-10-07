"""New, focused offline oracles authorized in M34; no historical suite restored."""

from __future__ import annotations

import hashlib
import itertools
import json
import unittest
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
from random import Random

from scripts.exact_commit.cfg_stack_control import compile_stack_plan

from mwpc_exact.cfg_posterior import CompilationLimit, PosteriorStatus, compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.ll1 import UnsupportedGrammar, check_ll1
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind


def dyck():
    b = _SourceGrammarBuilder(("S", "N"), start="S")
    b.rule("S", "N", "S")
    b.rule("S")
    b.rule("N", b"(", "S", b")")
    b.rule("N", b"[", "S", b"]")
    return b.build()


def valid_dyck(word):
    stack = []
    for byte in word:
        if byte in b"([":
            stack.append(byte)
        elif byte in b")]" and stack and stack.pop() == {41: 40, 93: 91}[byte]:
            continue
        else:
            return False
    return not stack


def inputs(source, emissions, rows, probabilities=None, canvas=None):
    canvas = tuple(canvas) if canvas is not None else (None,) * len(rows)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=len(emissions)),
        explicit_support=dict(enumerate(rows)),
    )
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        canvas,
        (),
        support,
        CompositionalByteLevelAdapter(tuple(emissions)),
        EOSPolicy(EOSMode.ABSENT),
    )
    probabilities = probabilities or tuple(tuple(F(1, len(r)) for _ in r) for r in support.rows)
    return ProbabilityInput(state, tuple(map(tuple, probabilities)))


def oracle(data, recognizes=valid_dyck):
    """Enumerate original tokens and recognize with a stack, never project parsing."""
    weights = [
        dict(zip(row, p, strict=True))
        for row, p in zip(data.state.support.rows, data.probabilities, strict=True)
    ]
    accepted = {}
    for path in itertools.product(*data.state.support.rows):
        emissions = [data.state.tokenizer_adapter.emissions[t] for t in path]
        if any(e is None for e in emissions) or not recognizes(b"".join(emissions)):
            continue
        weight = F(1)
        for i, token in enumerate(path):
            weight *= weights[i][token]
        accepted[path] = weight
    total = sum(accepted.values(), F())
    marginals = tuple(
        tuple(
            sum((v for p, v in accepted.items() if p[i] == t), F()) / total if total else F()
            for t in row
        )
        for i, row in enumerate(data.state.support.rows)
    )
    return total, marginals, {p: w / total for p, w in accepted.items() if w}


class NeedDraw(Exception):
    def __init__(self, stop):
        self.stop = stop


class EnumeratedRandom(Random):
    """Exhaust all integer RNG transcripts without inspecting parser/sampler branches."""

    def __init__(self, transcript):
        super().__init__(0)
        self.transcript = iter(transcript)

    def randrange(self, stop):
        if stop == 1:
            return 0
        try:
            return next(self.transcript)
        except StopIteration:
            raise NeedDraw(stop) from None


class CfgPosteriorOracleTests(unittest.TestCase):
    def test_json_weighted_original_token_products(self):
        def recognizes(word):
            try:
                json.loads(word)
                return True
            except (ValueError, UnicodeError):
                return False

        source, rng = json_source_grammar(), Random(20261007)
        words = (
            b"{",
            b"}",
            b"[",
            b"]",
            b"null",
            b"0",
            b"00",
            b'"a"',
            b'"a":',
            b"true",
            b",",
            b" ",
            b"[]",
            b"{}",
            b"null",
            None,
        )
        for slots in (1, 2, 3):
            for _ in range(20):
                rows = tuple(tuple(sorted(rng.sample(range(len(words)), 4))) for _ in range(slots))
                raw = [[rng.randrange(6) for _ in row] for row in rows]
                probabilities = tuple(tuple(F(w, sum(row) + 3) for w in row) for row in raw)
                data = inputs(source, words, rows, probabilities)
                posterior = compile_cfg_sampler(source, data.state).evaluate(data)
                self.assertEqual(
                    (posterior.valid_mass, posterior.marginals), oracle(data, recognizes)[:2]
                )

    def test_independent_stack_control_against_token_products(self):
        rng = Random(20261006)
        for slots in (2, 4, 6):
            for distribution in range(3):
                rows = ((0, 1, 2, 3),) * slots
                weights = [
                    [rng.randrange(1, 8) if distribution else 1 for _ in row] for row in rows
                ]
                probabilities = tuple(tuple(F(w, sum(row)) for w in row) for row in weights)
                data = inputs(dyck(), (b"(", b")", b"[", b"]"), rows, probabilities)
                result = compile_stack_plan(data.state.tokenizer_adapter.emissions, rows).evaluate(
                    probabilities
                )
                self.assertEqual((result.valid_mass, result.marginals), oracle(data)[:2])

    def test_pinned_external_json_conformance(self):
        root = Path(__file__).parent / "data/json_suite"
        manifest = json.loads((root / "manifest.json").read_text())
        source = json_source_grammar()
        emissions = tuple(bytes([byte]) for byte in range(256))
        for case in manifest["files"]:
            with self.subTest(case=case["name"]):
                word = (root / case["name"]).read_bytes()
                self.assertEqual(hashlib.sha256(word).hexdigest(), case["sha256"])
                self.assertLessEqual(len(word), manifest["max_bytes"])
                if not word:
                    self.assertTrue(case["name"].startswith("n_"))
                    continue  # an empty document is outside the nonempty canvas API
                data = inputs(
                    source, emissions, tuple((byte,) for byte in word), canvas=tuple(word)
                )
                posterior = compile_cfg_sampler(source, data.state).evaluate(data)
                if case["name"].startswith("y_"):
                    self.assertEqual(posterior.valid_mass, 1)
                    self.assertEqual(posterior.sample(Random(0)), tuple(word))
                elif case["name"].startswith("n_"):
                    self.assertEqual(posterior.valid_mass, 0)
                # i_ deliberately has no oracle verdict; it still executes.

    def test_original_token_products_and_reweighting(self):
        source, rng = dyck(), Random(20261006)
        words = (b"(", b")", b"[", b"]", b"()", b"([])", b"[[", b"]]", b"(", b"x", None)
        # Fixed protocol: every length, deterministic seeds, zeros and omitted mass.
        for slots in range(1, 6):
            for _ in range(12):
                rows = tuple(
                    tuple(sorted(rng.sample(range(len(words)), rng.randint(1, 5))))
                    for _ in range(slots)
                )
                data = inputs(source, words, rows)
                plan = compile_cfg_sampler(source, data.state)
                for _ in range(3):
                    raw = [[rng.randrange(6) for _ in row] for row in rows]
                    probabilities = tuple(tuple(F(w, sum(row) + 1) for w in row) for row in raw)
                    changed = ProbabilityInput(data.state, probabilities)
                    expected, marginal, _ = oracle(changed)
                    actual = plan.evaluate(changed)
                    self.assertEqual(actual.valid_mass, expected)
                    self.assertEqual(actual.marginals, marginal)
                    self.assertEqual(actual.omitted_mass, changed.omitted_mass)
                    if expected:
                        for _ in range(8):
                            sample = actual.sample(rng)
                            self.assertTrue(
                                valid_dyck(data.state.tokenizer_adapter.detokenize_bytes(sample))
                            )
                            self.assertTrue(
                                all(t in row for t, row in zip(sample, rows, strict=True))
                            )
                    else:
                        self.assertEqual(actual.status, PosteriorStatus.ZERO_MASS_ON_SUPPORT)
                        with self.assertRaisesRegex(ValueError, "ZERO_MASS_ON_SUPPORT"):
                            actual.sample(rng)

    def test_exact_sampling_law_including_aliases(self):
        source = dyck()
        data = inputs(
            source,
            (b"(", b"[", b"(", b")", b"]"),
            ((0, 1, 2), (3, 4)),
            ((F(1, 2), F(1, 4), F(1, 4)), (F(1, 3), F(2, 3))),
        )
        posterior = compile_cfg_sampler(source, data.state).evaluate(data)
        pending = [((), F(1))]
        observed = {}
        while pending:
            transcript, mass = pending.pop()
            try:
                path = posterior.sample(EnumeratedRandom(transcript))
                observed[path] = observed.get(path, F()) + mass
            except NeedDraw as request:
                self.assertLessEqual(request.stop, 100)
                pending.extend(((*transcript, j), mass / request.stop) for j in range(request.stop))
        self.assertEqual(observed, oracle(data)[2])

    def test_fixed_prefix_and_missing_support(self):
        source = dyck()
        data = inputs(
            source,
            (b"[", b"[]", b"]", b"[[]]"),
            ((0,), (1, 2)),
            ((F(1),), (F(1, 4), F(1, 2))),
            canvas=(0, None),
        )
        actual = compile_cfg_sampler(source, data.state).evaluate(data)
        self.assertEqual((actual.valid_mass, actual.marginals), oracle(data)[:2])
        self.assertEqual(actual.sample(Random(0)), (0, 2))
        one_slot = inputs(source, (b"[", b"[]", b"[[]]"), ((0, 1, 2),))
        result = compile_cfg_sampler(source, one_slot.state).evaluate(one_slot)
        self.assertEqual(result.valid_mass, F(2, 3))
        self.assertEqual(result.marginals, ((F(), F(1, 2), F(1, 2)),))

    def test_reuse_after_support_restriction_and_commitment(self):
        source, rng = dyck(), Random(20261008)
        words = (b"(", b")", b"[", b"]", b"()", b"[]", b"(")
        base = inputs(source, words, (tuple(range(len(words))),) * 4)
        plan = compile_cfg_sampler(source, base.state)
        for _ in range(30):
            rows = tuple(
                tuple(rng.sample(range(len(words)), rng.randrange(1, 5))) for _ in range(4)
            )
            raw = [[rng.randrange(1, 6) for _ in row] for row in rows]
            probabilities = tuple(tuple(F(w, sum(row) + 1) for w in row) for row in raw)
            changed = inputs(source, words, rows, probabilities)
            actual = plan.evaluate(changed)
            self.assertEqual((actual.valid_mass, actual.marginals), oracle(changed)[:2])
            if not actual.valid_mass:
                continue
            witness = actual.sample(rng)
            fixed = inputs(
                source,
                words,
                ((witness[0],), *rows[1:]),
                ((F(1),), *probabilities[1:]),
                canvas=(witness[0], None, None, None),
            )
            result = plan.evaluate(fixed)
            self.assertEqual((result.valid_mass, result.marginals), oracle(fixed)[:2])
            self.assertEqual(result.sample(rng)[0], witness[0])
        committed_plan = compile_cfg_sampler(source, fixed.state)
        with self.assertRaises(ValueError):
            committed_plan.evaluate(base)  # an existing commitment cannot be undone

    def test_fail_closed_boundaries(self):
        source = dyck()
        b = _SourceGrammarBuilder(("S",), start="S")
        b.rule("S", "S", "S")
        b.rule("S", b"a")
        with self.assertRaises(UnsupportedGrammar):
            check_ll1(b.build())
        b = _SourceGrammarBuilder(("S", "A"), start="S")
        b.rule("S", "A", b"a")
        b.rule("A", b"a")
        b.rule("A")
        with self.assertRaises(UnsupportedGrammar):
            check_ll1(b.build())  # nullable FIRST/FOLLOW conflict
        data = inputs(source, (b"(", b")"), ((0, 1), (0, 1)))
        plan = compile_cfg_sampler(source, data.state)
        for kwargs in ({"max_chart_cells": 0}, {"max_alternatives": 0}, {"timeout_seconds": 0}):
            with self.assertRaises(CompilationLimit):
                compile_cfg_sampler(source, data.state, **kwargs)
        for limit in (-1, True, F(1)):
            with self.assertRaises(ValueError):
                compile_cfg_sampler(source, data.state, max_chart_cells=limit)
        for timeout in (float("nan"), float("inf"), -1, True):
            with self.assertRaises(ValueError):
                compile_cfg_sampler(source, data.state, timeout_seconds=timeout)
        with self.assertRaises(ValueError):
            compile_cfg_sampler(source, inputs(source, (b"(", b")"), ((0,), (1,))).state).evaluate(
                data
            )
        with self.assertRaises(ValueError):
            ProbabilityInput(data.state, ((F(-1), F(2)), (F(1, 2), F(1, 2))))
        with self.assertRaises(ValueError):
            compile_cfg_sampler(b.build(), data.state)
        other = _SourceGrammarBuilder(("S",), start="S")
        other.rule("S", b"a")
        with self.assertRaisesRegex(ValueError, "does not match"):
            compile_cfg_sampler(other.build(), data.state)
        support = build_per_position_support(
            canvas=(None, None),
            policy=SupportPolicy(
                kind=SupportKind.EXPLICIT, vocabulary_size=4, required_special_token_ids=(2, 3)
            ),
            explicit_support={0: (0, 1, 2, 3), 1: (0, 1, 2, 3)},
        )
        controls = SelectionInput(
            data.state.grammar,
            (None, None),
            (),
            support,
            CompositionalByteLevelAdapter((b"(", b")", None, None)),
            EOSPolicy(EOSMode.REQUIRED, (2,), 3),
        )
        with self.assertRaisesRegex(UnsupportedGrammar, "ABSENT EOS"):
            compile_cfg_sampler(source, controls)
        with self.assertRaises(ValueError):
            plan.evaluate(
                ProbabilityInput(
                    replace(
                        data.state, canvas=(None, None), grammar=normalize_to_cnf(b.build()).grammar
                    ),
                    data.probabilities,
                )
            )


if __name__ == "__main__":
    unittest.main()
