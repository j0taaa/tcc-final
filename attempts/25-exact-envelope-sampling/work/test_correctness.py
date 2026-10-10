"""Independent tiny original-ID oracles and the sampler's actual random law."""

import itertools
import json
import unittest
from fractions import Fraction
from math import prod
from unittest.mock import patch

from mwpc_exact.cfg_posterior import CompilationLimit
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

from .adaptive import prepare_certified
from .cars import Cars
from .envelope import prepare_envelope
from .posterior import Weights
from .table import LexerTable


def oracle(table, weights):
    valid = {}
    domains = [
        (fixed,)
        if fixed is not None
        else tuple(t for t in range(weights.vocabulary_size) if weights.at(p, t))
        for p, fixed in enumerate(weights.canvas)
    ]
    for tokens in itertools.product(*domains):
        try:
            json.loads(
                table.adapter.detokenize_bytes(tokens).decode("utf8"),
                parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
            )
        except (ValueError, UnicodeDecodeError):
            continue
        valid[tokens] = prod(weights.at(p, t) for p, t in enumerate(tokens))
    return valid


def actual_law(action):
    class Draw(Exception):
        pass

    class Replay:
        def __init__(self, prefix):
            self.prefix, self.index = prefix, 0

        def randrange(self, stop):
            if self.index == len(self.prefix):
                raise Draw(stop)
            result = self.prefix[self.index]
            self.index += 1
            if not 0 <= result < stop:
                raise AssertionError("random replay range changed")
            return result

    pending, law, refused = [((), Fraction(1))], {}, Fraction()
    while pending:
        prefix, mass = pending.pop()
        try:
            word = action(Replay(prefix))
        except Draw as draw:
            stop = draw.args[0]
            if stop > 100:
                raise AssertionError(
                    "fixture no longer permits exhaustive random decisions"
                ) from draw
            pending.extend(((*prefix, x), mass / stop) for x in range(stop))
        except CompilationLimit:
            refused += mass
        else:
            law[word] = law.get(word, Fraction()) + mass
    if sum(law.values(), refused) != 1:
        raise AssertionError("actual random law lost mass")
    return law, refused


class ExactEnvelopeCorrectness(unittest.TestCase):
    def test_empty_shallow_query_does_not_need_tail_resources_to_refine(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[[]]",)))
        weights = Weights([[1]], (None,), 1)
        # Direct, uncertified tail-only reference still covers the valid word.
        direct = prepare_envelope(table, weights, 1)
        self.assertEqual(direct.lower, 0)
        self.assertEqual(direct.upper_tail, 1)
        from . import envelope

        with patch.object(envelope, "CounterDistribution", side_effect=MemoryError):
            sampler, certificate = prepare_certified(table, weights, depths=(1,))
        self.assertEqual(certificate["attempts"][0]["tail"], None)
        self.assertEqual(certificate["depth"], None)
        self.assertEqual(sampler.lower, 1)
        law, refused = actual_law(lambda rng: sampler.sample(rng)[0])
        self.assertEqual(law, {(0,): Fraction(1)})
        self.assertEqual(refused, 0)

    def test_adaptation_certifies_acceptance_without_excluding_deep_valid_ids(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[]", b"[]", b"[[]]", b"[[,]]")))
        weights = Weights([[1, 2, 1, 1]], (None,), 4)
        expected = oracle(table, weights)
        for tolerance in ("3/4", "1/1000"):
            sampler, certificate = prepare_certified(table, weights, tolerance, depths=(1,))
            self.assertLessEqual(sampler.delta, Fraction(tolerance))
            self.assertEqual(certificate["depth"], 1 if tolerance == "3/4" else None)
            law, refused = actual_law(lambda rng, sampler=sampler: sampler.sample(rng)[0])
            self.assertEqual(refused, 0)
            self.assertEqual(
                law, {w: Fraction(v, sum(expected.values())) for w, v in expected.items()}
            )
            self.assertIn((2,), law)

    def test_actual_accepted_law_including_aliases_deep_invalid_and_finite_refusal(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[[", b"[]", b"[[", b"]]", b"]}", b" ")))
        weights = Weights([[1, 2, 1, 0, 0, 0], [0, 0, 0, 1, 1, 2]], (None, None), 6)
        expected = oracle(table, weights)
        full = sum(expected.values())
        for method in ("handoff", "closed", "grammar_hit", "counter_only"):
            sampler = prepare_envelope(table, weights, 1, method=method)
            proposal, refused = actual_law(sampler.propose)
            self.assertEqual(refused, 0)
            for tokens, probability in proposal.items():
                original = prod(weights.at(p, t) for p, t in enumerate(tokens))
                self.assertEqual(probability, Fraction(original, sampler.total))
            self.assertTrue(set(expected) <= set(proposal))
            self.assertIn((0, 4), proposal)  # positive deep balanced, wrong delimiter type
            accepted, refused = actual_law(
                lambda rng, sampler=sampler: sampler.sample(rng, max_trials=2)[0]
            )
            self.assertEqual(refused, (1 - Fraction(full, sampler.total)) ** 2)
            self.assertEqual(
                accepted,
                {tokens: (1 - refused) * Fraction(mass, full) for tokens, mass in expected.items()},
            )
            self.assertLessEqual(refused, sampler.delta**2)

    def test_intratoken_peak_and_zero_lower_tail_survives_trimming(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[]", b"[]", b"[[]]", b"[[,]]")))
        weights = Weights([[1, 2, 1, 1]], (None,), 4)
        for method in ("handoff", "closed", "grammar_hit", "counter_only"):
            sampler = prepare_envelope(table, weights, 1, method=method)
            self.assertEqual(sampler.lower, 0 if method == "counter_only" else 3)
            law, refused = actual_law(
                lambda rng, sampler=sampler: sampler.sample(rng, max_trials=2)[0]
            )
            expected = oracle(table, weights)
            self.assertEqual(
                law,
                {
                    w: Fraction(v, sum(expected.values())) * (1 - refused)
                    for w, v in expected.items()
                },
            )
            self.assertIn((2,), law)  # rare valid depth2 is never removed
        fixed = Weights([[1] * 4, [1, 2, 1, 1]], (2, None), 4)
        # A separate fixed frame with NO shallow solution still has a positive
        # full solution (depth2 token followed by a whitespace token).
        table2 = LexerTable(CompositionalByteLevelAdapter((b"[]", b" ", b"[[]]", b"[[,]]")))
        sampler = prepare_envelope(table2, fixed, 1)
        self.assertEqual(sampler.lower, 0)
        self.assertGreater(sampler.upper_tail, 0)
        law, _ = actual_law(lambda rng: sampler.sample(rng, max_trials=2)[0])
        self.assertEqual(set(law), {(2, 1)})

    def test_original_fixed_ids_utf8_split_and_exact_full_fallback(self):
        table = LexerTable(CompositionalByteLevelAdapter((b'"', b"\xc3", b"\xa1", b"a")))
        weights = Weights([[1] * 4] * 4, (0, None, None, 0), 4)
        expected = oracle(table, weights)
        for depth in (0, None):
            sampler = prepare_envelope(table, weights, depth)
            law, refused = actual_law(
                lambda rng, sampler=sampler: sampler.sample(rng, max_trials=1)[0]
            )
            self.assertEqual(refused, 0)
            self.assertEqual(
                law, {w: Fraction(v, sum(expected.values())) for w, v in expected.items()}
            )
            self.assertIn((0, 1, 2, 0), law)

    def test_budget_and_product_identity_cannot_be_silently_changed(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[]", b"invalid")))
        weights = Weights([[1, 1]], (None,), 2)
        sampler = prepare_envelope(table, weights, 1)
        for bad in (0, -1, True, 1.2):
            with self.assertRaises(ValueError):
                sampler.sample(None, max_trials=bad)
        with self.assertRaises(ValueError):
            prepare_envelope(table, weights, -1)
        with self.assertRaises(CompilationLimit):
            prepare_envelope(table, weights, 1, timeout_seconds=0)
        # A valid deep word cannot silently be called invalid if the independent
        # stdlib recognizer lacks recursion resources. That would bias rejection.
        deep = LexerTable(CompositionalByteLevelAdapter((b"[" * 1100 + b"0" + b"]" * 1100,)))
        bounded = prepare_envelope(deep, Weights([[1]], (None,), 1), None)
        with self.assertRaises(CompilationLimit):
            bounded.sample(None)

    def test_cars_actual_adaptive_random_law_and_unchanged_valid_mass(self):
        table = LexerTable(CompositionalByteLevelAdapter((b"[", b"]", b"}", b" ", b"[")))
        weights = Weights([[1, 0, 0, 1, 1], [0, 1, 1, 1, 0]], (None, None), 5)
        expected = oracle(table, weights)
        for perfect, counter in ((False, False), (True, False), (False, True), (True, True)):
            # Mutable adaptive state must be reset for EVERY RNG transcript.
            law, refused = actual_law(
                lambda rng, perfect=perfect, counter=counter: Cars(
                    table, weights, perfect=perfect, counter=counter
                ).sample(rng, max_trials=2)[0]
            )
            self.assertEqual(
                law,
                {
                    w: (1 - refused) * Fraction(v, sum(expected.values()))
                    for w, v in expected.items()
                },
            )
            cars = Cars(table, weights, perfect=perfect, counter=counter)
            before = cars.root.total
            cars.learn((0, 2))  # invalid [}, removes ALL invalid sibling closes
            self.assertLess(cars.root.total, before)
            allowed, refusal = actual_law(cars.propose)
            self.assertEqual(refusal, 0)
            self.assertTrue(set(expected) <= set(allowed))
            for word, probability in allowed.items():
                self.assertEqual(
                    probability,
                    Fraction(prod(weights.at(p, t) for p, t in enumerate(word)), cars.root.total),
                )


if __name__ == "__main__":
    unittest.main()
