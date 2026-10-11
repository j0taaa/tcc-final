"""A27: independent tiny JSON oracles, not performance-selected instances."""

import importlib
import itertools
import json
import unittest
from fractions import Fraction
from math import prod
from random import Random

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

closure = importlib.import_module("attempts.27-finite-closure-certificates.work.finite_closure")
frozen = "attempts.27-finite-closure-certificates.work.frozen."
Weights = importlib.import_module(frozen + "posterior").Weights
LexerTable = importlib.import_module(frozen + "table").LexerTable
stack = importlib.import_module(frozen + "stack_control")


def prepare(emissions, rows, canvas, depth):
    table = LexerTable(CompositionalByteLevelAdapter(emissions))
    weights = Weights(rows, canvas, len(emissions))
    plan = stack.StackPrepared(
        table,
        canvas,
        max_depth=depth,
        track_overflow=True,
        max_cells=100000,
        max_edges=100000,
        max_terms=1000000,
        timeout_seconds=20,
    )
    return weights, plan, closure.FiniteClosure(plan, weights)


def json_depth(value):
    if isinstance(value, dict):
        return 1 + max(map(json_depth, value.values()), default=0)
    if isinstance(value, list):
        return 1 + max(map(json_depth, value), default=0)
    return 0


def exact_masses(emissions, weights, depth):
    """Enumerate original events; standard-library parser, no project lexer."""
    full = shallow = 0
    domains = [(fixed,) if fixed is not None else range(len(emissions)) for fixed in weights.canvas]
    for word in itertools.product(*domains):
        mass = prod(weights.at(p, t) for p, t in enumerate(word))
        if not mass or any(emissions[t] is None for t in word):
            continue
        try:
            value = json.loads(b"".join(emissions[t] for t in word).decode("utf8"))
        except (ValueError, UnicodeDecodeError):
            continue
        full += mass
        shallow += mass * (json_depth(value) <= depth)
    denominator = prod(weights.denominators)
    return Fraction(full, denominator), Fraction(shallow, denominator)


class FiniteClosureTests(unittest.TestCase):
    def test_all_original_events_have_sound_limits(self):
        emissions = (
            b"[",
            b"]",
            b"{",
            b"}",
            b",",
            b":",
            b"0",
            b'"x"',
            b"[[]]",
            b"[]",
            b" ",
            None,
            b"[]",
        )
        rng = Random(2026101127)
        for canvas in ((None,) * 3, (0, None, 1), (None,), ()):
            rows = [[rng.randint(0, 5) for _ in emissions] for _ in canvas]
            for depth in range(4):
                weights, plan, bounds = prepare(emissions, rows, canvas, depth)
                full, shallow = exact_masses(emissions, weights, depth)
                self.assertEqual(stack.StackPosterior(plan, weights).mass, shallow)
                residue = {m: bounds.residue(m)[0] for m in (1, 2, 3, 4, 6, 8)}
                for upper in (*residue.values(), bounds.potential((0, 1, 2, 4))[0]):
                    self.assertLessEqual(full - shallow, upper, (canvas, depth))
                    self.assertLessEqual(upper, 1)
                    if shallow:
                        self.assertLessEqual((full - shallow) / full, upper / (shallow + upper))
                self.assertLessEqual(residue[6], min(residue[2], residue[3]))
                self.assertLessEqual(residue[8], residue[4])
                self.assertLessEqual(residue[4], residue[2])

    def test_exact_residue_mass_and_potential_with_invalid_prefix(self):
        emissions = (b"[[", b"[[,]]", b"[]", b"]]", b" ")
        s, t, r = Fraction(1, 4), Fraction(1, 4), Fraction(1, 8)
        rows = [[float(s), float(t), float(1 - s - t), 0, 0], [0, 0, 0, float(r), float(1 - r)]]
        weights, _, bounds = prepare(emissions, rows, (None, None), 1)
        self.assertEqual(bounds.residue(1)[0], s)
        self.assertEqual(bounds.residue(2)[0], s)
        for m in (3, 4, 8):
            self.assertEqual(bounds.residue(m)[0], s * r)
        for k in (0, 1, 2, 4):
            self.assertEqual(bounds.potential((k,))[0], s * (r + (1 - r) / 2 ** (2 * k)))
        full, shallow = exact_masses(emissions, weights, 1)
        self.assertEqual(full - shallow, s * r)

    def test_peak_inside_token_and_partial_strings_are_not_raw_brackets(self):
        emissions = (b"[[]]", b"[[]]", b'"[[', b']]"', b" ", None)
        rows = [[1, 2, 3, 0, 4, 0], [0, 0, 0, 2, 3, 0]]
        for canvas in ((None, None), (0, 4)):
            weights, plan, bounds = prepare(emissions, rows, canvas, 1)
            full, shallow = exact_masses(emissions, weights, 1)
            self.assertEqual(stack.StackPosterior(plan, weights).mass, shallow)
            # First overflow ends at height zero: never drop it based on h<=d.
            self.assertTrue(any(height == 0 for _, _, height in bounds.frontier))
            for m in (1, 2, 3, 4):
                self.assertEqual(bounds.residue(m)[0], full - shallow)
            self.assertEqual(bounds.potential((0, 1, 2))[0], full - shallow)

    def test_resource_and_input_boundaries(self):
        weights, plan, bounds = prepare((b"[]",), [[1]], (None,), 0)
        for bad in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                bounds.residue(bad)
        for bad in ((), (1.5,), (-1,), (True,)):
            with self.assertRaises(ValueError):
                bounds.potential(bad)
        with self.assertRaises(CompilationLimit):
            closure.FiniteClosure(plan, weights, timeout_seconds=0)
