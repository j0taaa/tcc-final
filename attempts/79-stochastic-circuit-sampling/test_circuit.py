"""Independent finite correctness oracles; these are not accuracy benchmarks."""

from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import unittest
from fractions import Fraction as F
from math import prod
from pathlib import Path
from random import Random
from unittest.mock import patch

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

spec = importlib.util.spec_from_file_location("a79_circuit", Path(__file__).with_name("circuit.py"))
c = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = c
spec.loader.exec_module(c)


def fixture(source, emissions, rows, weights=None, canvas=None):
    canvas = (None,) * len(rows) if canvas is None else canvas
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
        CompositionalByteLevelAdapter(emissions),
        EOSPolicy(EOSMode.ABSENT),
    )
    weights = weights or tuple(
        (F(1),) if p is not None else tuple(F(1, 8) for _ in r)
        for p, r in zip(canvas, support.rows, strict=True)
    )
    data = ProbabilityInput(state, weights)
    return data, c.build(compile_cfg_sampler(source, state))


def binary():
    b = _SourceGrammarBuilder(("S",), start="S")
    b.rule("S", b"0", "S")
    b.rule("S", b"1", "S")
    b.rule("S")
    return b.build()


def dyck():
    b = _SourceGrammarBuilder(("S", "N"), start="S")
    b.rule("S", "N", "S")
    b.rule("S")
    b.rule("N", b"(", "S", b")")
    b.rule("N", b"[", "S", b"]")
    return b.build()


def recognizes_dyck(word):
    stack = []
    for byte in word:
        if byte in b"([":
            stack.append(byte)
        elif byte in b")]" and stack and stack.pop() == {41: 40, 93: 91}[byte]:
            continue
        else:
            return False
    return not stack


def original_masses(data, recognizes):
    result = {}
    for ids in itertools.product(*data.state.support.rows):
        if recognizes(data.state.tokenizer_adapter.detokenize_bytes(ids)):
            mass = prod(
                data.probabilities[p][row.index(t)]
                for p, (row, t) in enumerate(zip(data.state.support.rows, ids, strict=True))
            )
            result[ids] = mass
    return result


def expansion(circuit, rows, values=None):
    """Expand every derivation, retaining counts and its realized error factors."""
    expanded = []
    for i, gate in enumerate(circuit.gates):
        if gate.op == "input":
            p, j = gate.choice
            law = {((p, circuit.token_rows[p][j]),): (rows[p][j], 1)}
            raw = rows[p][j]
        elif gate.op == "const":
            law, raw = {(): (F(gate.value), 1)}, F(gate.value)
        elif gate.op == "add":
            law = dict(expanded[gate.left])
            for word, (mass, count) in expanded[gate.right].items():
                old, multiplicity = law.get(word, (F(), 0))
                law[word] = old + mass, multiplicity + count
            raw = values[gate.left] + values[gate.right] if values is not None else None
        else:
            law = {}
            for a, (wa, ca) in expanded[gate.left].items():
                for b, (wb, cb) in expanded[gate.right].items():
                    assert not set(dict(a)) & set(dict(b))
                    word = tuple(sorted((*a, *b)))
                    old, multiplicity = law.get(word, (F(), 0))
                    law[word] = old + wa * wb, multiplicity + ca * cb
            raw = values[gate.left] * values[gate.right] if values is not None else None
        if values is not None:
            alpha = values[i] / raw if raw else F(1)
            law = {word: (mass * alpha, count) for word, (mass, count) in law.items()}
        expanded.append(law)
    if circuit.root is None:
        return {}
    return {tuple(t for _, t in w): mc for w, mc in expanded[circuit.root].items()}


class NeedBit(Exception):
    pass


class Bits(Random):
    def __init__(self, transcript):
        super().__init__(0)
        self.transcript = iter(transcript)

    def getrandbits(self, k):
        assert k == 1
        try:
            return next(self.transcript)
        except StopIteration:
            raise NeedBit from None


class NeedChoice(Exception):
    def __init__(self, a, b):
        self.a, self.b = a, b


class NeedInteger(Exception):
    def __init__(self, stop):
        self.stop = stop


class IntegerDraws(Random):
    def __init__(self, transcript):
        super().__init__(0)
        self.transcript = iter(transcript)

    def randrange(self, stop):
        try:
            return next(self.transcript)
        except StopIteration:
            raise NeedInteger(stop) from None


class Choices:
    """Enumerate circuit control flow; numeric Bernoulli race has separate tests."""

    def __init__(self, transcript):
        self.transcript = iter(transcript)

    def choose(self, a, b, _rng):
        if not a.mantissa or not b.mantissa:
            return int(not a.mantissa)
        try:
            return next(self.transcript)
        except StopIteration:
            raise NeedChoice(c._numeric().as_fraction(a), c._numeric().as_fraction(b)) from None


def reconstructed(circuit, evaluation):
    saved, law, pending = evaluation.arithmetic, {}, [((), F(1))]
    while pending:
        transcript, probability = pending.pop()
        evaluation.arithmetic = Choices(transcript)
        try:
            word = circuit.sample(evaluation, Random(991))
        except NeedChoice as choice:
            total = choice.a + choice.b
            pending.extend(
                ((*transcript, j), probability * mass / total)
                for j, mass in enumerate((choice.a, choice.b))
                if mass
            )
        else:
            law[word] = law.get(word, F()) + probability
    evaluation.arithmetic = saved
    return law


class CircuitTests(unittest.TestCase):
    def test_independent_original_id_masses_and_unique_derivations(self):
        b = _SourceGrammarBuilder(("S", "T", "A", "B"), start="S")
        b.rule("S", "T")
        b.rule("T", "A", "B")
        b.rule("A", b"a", "A")
        b.rule("A")
        b.rule("B", b"b")
        fixtures = (
            (
                *fixture(
                    dyck(),
                    (b"(", b")", b"[", b"]", b"(", b"()"),
                    ((0, 2, 4, 5), (0, 1, 4), (1, 3, 5), (1, 3, 5)),
                ),
                recognizes_dyck,
            ),
            (
                *fixture(
                    b.build(),
                    (b"a", b"a", b"aa", b"b", b"ab"),
                    ((0, 1, 2), (0,), (3, 4)),
                    canvas=(None, 0, None),
                ),
                lambda word: word.endswith(b"b") and set(word[:-1]) <= {97},
            ),
            (
                *fixture(
                    json_source_grammar(),
                    (b"[", b"0", b"1", b",", b"]", b"0"),
                    ((0,), (1, 2, 5), (3,), (1, 2, 5), (4,)),
                    canvas=(0, None, 3, None, 4),
                ),
                lambda word: isinstance(json.loads(word), list),
            ),
        )
        for data, circuit, recognizes in fixtures:
            expected = original_masses(data, recognizes)
            actual = expansion(circuit, data.probabilities)
            self.assertEqual({w: m for w, (m, _) in actual.items()}, expected)
            self.assertTrue(all(count == 1 for _, count in actual.values()))
            evaluation = circuit.evaluate(data.probabilities)
            denominator = prod(evaluation.row_scales)
            self.assertEqual(
                F(evaluation.values[circuit.root], denominator), sum(expected.values())
            )
            self.assertEqual(circuit.stats["N"], len(circuit.gates))
            self.assertGreater(circuit.stats["Sa"] + circuit.stats["Sm"], 0)
            for method in ("exact", "nearest", "sr_singleton", "sr_shared"):
                e = circuit.evaluate(data.probabilities, method, precision=5, seed=871)
                for seed in range(6):
                    self.assertIn(circuit.sample(e, Random(seed)), expected)

    def test_actual_finite_noise_executed_law_and_tv(self):
        # The second-position subtree is shared by the two first-position alternatives.
        data, circuit = fixture(
            binary(), (b"0", b"1"), ((0, 1),) * 2, ((F(9, 32), F(11, 32)), (F(5, 16), F(7, 16)))
        )
        exact = original_masses(data, lambda _word: True)
        total = sum(exact.values())
        target = {w: m / total for w, m in exact.items()}
        for method in ("sr_singleton", "sr_shared"):
            mixture, pending, cells = {}, [((), F(1))], 0
            while pending:
                bits, probability = pending.pop()
                with patch.object(c, "Random", lambda _seed, bits=bits: Bits(bits)):
                    try:
                        e = circuit.evaluate(data.probabilities, method, precision=2)
                    except NeedBit:
                        pending.extend(((*bits, bit), probability / 2) for bit in (0, 1))
                        continue
                values = tuple(c._numeric().as_fraction(v) for v in e.values)
                expanded = expansion(circuit, data.probabilities, values)
                root_mass = sum(m for m, _ in expanded.values())
                law = reconstructed(circuit, e)
                self.assertEqual(law, {w: m / root_mass for w, (m, _) in expanded.items() if m})
                for word, mass in law.items():
                    mixture[word] = mixture.get(word, F()) + probability * mass
                cells += 1
                self.assertLess(cells, 10000, "bounded finite oracle exceeded its declared size")
            u = F(1, 2)
            C = (1 + u * u / (4 * (1 + u))) ** circuit.stats["K"]
            self.assertEqual(sum(mixture.values()), 1)
            for word, mass in mixture.items():
                self.assertLessEqual(target[word] / C, mass)
                self.assertLessEqual(mass, C * target[word])
            tv = sum(abs(mixture.get(w, 0) - q) for w, q in target.items()) / 2
            self.assertLessEqual(tv, (C - 1) / (C + 1))
            self.assertGreater(cells, 1)

    def test_exact_integer_sampling_law_preserves_aliases(self):
        data, circuit = fixture(
            binary(), (b"0", b"1", b"0"), ((0, 1, 2),), ((F(1, 8), F(2, 8), F(4, 8)),)
        )
        e = circuit.evaluate(data.probabilities)
        law, pending = {}, [((), F(1))]
        while pending:
            transcript, probability = pending.pop()
            try:
                word = circuit.sample(e, IntegerDraws(transcript))
            except NeedInteger as draw:
                pending.extend(
                    ((*transcript, j), probability / draw.stop) for j in range(draw.stop)
                )
            else:
                law[word] = law.get(word, F()) + probability
        self.assertEqual(law, {(0,): F(1, 7), (1,): F(2, 7), (2,): F(4, 7)})

    def test_shared_noise_can_increase_mean_output_bias(self):
        # The third original ID is rejected; no omitted mass is renormalized away.
        data, circuit = fixture(
            binary(),
            (b"0", b"1", b"#"),
            ((0, 1, 2),),
            ((F(5, 64), F(7, 64), F(52, 64)),),
        )
        for method, expected in (("sr_singleton", F(349, 840)), ("sr_shared", F(29, 70))):
            probability_zero, pending = F(), [((), F(1))]
            while pending:
                bits, probability = pending.pop()
                with patch.object(c, "Random", lambda _seed, bits=bits: Bits(bits)):
                    try:
                        evaluation = circuit.evaluate(
                            data.probabilities, method, precision=2, measure=False
                        )
                    except NeedBit:
                        pending.extend(((*bits, bit), probability / 2) for bit in (0, 1))
                        continue
                probability_zero += probability * reconstructed(circuit, evaluation)[(0,)]
            self.assertEqual(probability_zero, expected)
        self.assertEqual(F(5, 12) - F(349, 840), F(1, 840))
        self.assertEqual(F(5, 12) - F(29, 70), F(1, 420))

    def test_zero_mass_alignment_and_pins(self):
        data, circuit = fixture(binary(), (b"0", b"1"), ((0,), (0, 1)), canvas=(0, None))
        for method in ("exact", "nearest", "sr_singleton", "sr_shared"):
            with self.assertRaises(c.ZeroMass):
                circuit.evaluate(((F(1),), (F(), F())), method)
            e = circuit.evaluate(((F(1),), (F(), F(1))), method)
            self.assertEqual(circuit.sample(e, Random(871)), (0, 1))
            if e.arithmetic is not None:
                with self.assertRaises(ValueError):
                    circuit.sample(e, e.arithmetic.rng)
        with self.assertRaises(ValueError):
            circuit.evaluate(((F(1, 2),), data.probabilities[1]))
        with self.assertRaises(ValueError):
            circuit.evaluate(((F(1),), (F(1, 3), F(1, 3))))
        zero_data, zero = fixture(dyck(), (b"]",), ((0,),))
        self.assertEqual(zero.gates, ())
        with self.assertRaises(c.ZeroMass):
            zero.evaluate(zero_data.probabilities)

    def test_verifier_rejects_unsafe_groups_and_scope(self):
        G = c.Gate
        # Coexisting conversions sharing noise; different physical positions do not cure it.
        bad = (
            G("input", choice=(0, 0), group=0),
            G("input", choice=(1, 0), group=0),
            G("mul", 0, 1, group=1),
        )
        with self.assertRaises(c.CircuitRefusal):
            c.verify(bad, 2, 2)
        # Groups individually contain no ancestor pair, yet contraction has A->B->A.
        cycle = (
            G("input", choice=(0, 0), group=0),
            G("input", choice=(0, 1), group=1),
            G("add", 0, 0, group=1),
            G("add", 1, 1, group=0),
            G("add", 2, 3, group=2),
        )
        with self.assertRaises(c.CircuitRefusal):
            c.verify(cycle, 4, 1)
        for bad in (
            (
                G("input", choice=(0, 0), group=0),
                G("input", choice=(0, 1), group=1),
                G("mul", 0, 1, group=2),
            ),
            (
                G("input", choice=(0, 0), group=0),
                G("input", choice=(1, 0), group=1),
                G("add", 0, 1, group=2),
            ),
            (G("const", value=1), G("const", value=1), G("add", 0, 1, group=0)),
        ):
            with self.assertRaises(c.CircuitRefusal):
                c.verify(bad, 2, 2)
        with self.assertRaises(c.ResourceRefusal):
            c.verify((G("input", choice=(0, 0), group=0),), 0, 1, max_workspace_bytes=0)
        with self.assertRaises(c.CircuitRefusal):
            c.verify((G("input", choice=(0, 0), group=0), G("const", value=1)), 0, 1)

    def test_exact_precision_controls(self):
        self.assertEqual(c.precision_for(4096), 9)
        self.assertEqual(c.precision_for(4096, control="nearest"), 18)
        self.assertEqual(c.precision_for(4096, control="moments"), 10)
        self.assertEqual(c.precision_for(4096, control="moments_improved"), 10)
        for control in ("sr", "nearest", "moments", "moments_improved"):
            self.assertEqual(c.precision_for(0, control=control), 2)
        for args in ((-1,), (5, F()), (5, F(1))):
            with self.assertRaises(ValueError):
                c.precision_for(*args)


if __name__ == "__main__":
    unittest.main()
