"""Focused research oracles: execution via JSON trees, never grammar parsing."""

import itertools
import json
import unittest
from collections import defaultdict
from dataclasses import replace
from fractions import Fraction as F
from random import Random

from scripts.exact_commit.semantic_json import (
    _union_pair,
    boolean_rule_grammar,
    covering_product,
    evaluate_semantics,
)

from mwpc_exact.cfg_posterior import CompilationLimit, compile_cfg_sampler
from mwpc_exact.reference.limits import WorkBudget

from test_cfg_posterior import inputs


def execute(rule, record):
    if not isinstance(rule, dict) or len(rule) != 1:
        raise ValueError("not a Boolean rule")
    op, value = next(iter(rule.items()))
    if op == "var" and isinstance(value, str) and value in record:
        return record[value]
    if op not in ("and", "or", "!") or not isinstance(value, list):
        raise ValueError("unsupported operator")
    if len(value) != (1 if op == "!" else 2):
        raise ValueError("incorrect arity")
    values = [execute(child, record) for child in value]
    return not values[0] if op == "!" else all(values) if op == "and" else any(values)


def enumeration(data, records):
    masses = defaultdict(dict)
    for path in itertools.product(*data.state.support.rows):
        weight = F(1)
        for token, row, probabilities in zip(path, data.state.support.rows, data.probabilities):
            weight *= probabilities[row.index(token)]
        try:
            rule = json.loads(data.state.tokenizer_adapter.detokenize_bytes(path))
            profile = sum(1 << i for i, row in enumerate(records) if execute(rule, row))
        except (ValueError, TypeError, UnicodeError):
            continue
        masses[profile][path] = weight
    return masses


class SemanticJsonTests(unittest.TestCase):
    def test_covering_product_and_conditional_pair_law(self):
        rng = Random(20261007)
        for m in range(8):
            size = 1 << m
            a, b = ([rng.randrange(6) for _ in range(size)] for _ in range(2))
            expected = [0] * size
            for x, y in itertools.product(range(size), repeat=2):
                expected[x | y] += a[x] * b[y]
            self.assertEqual(covering_product(a, b, WorkBudget()), expected)

        # Enumerate integer random decisions, not empirical frequencies.
        class Draws(Random):
            def __init__(self, first, second):
                self.draws = iter((first, second))
                self.totals = []

            def randrange(self, total):
                self.totals.append(total)
                draw = next(self.draws)
                assert 0 <= draw < total
                return draw

        for a, b in (([1, 2, 1, 0], [2, 1, 1, 1]), ([0, 2, 0, 1], [0, 1, 2, 0])):
            for target in range(4):
                pairs = {
                    (x, y): a[x] * b[y]
                    for x, y in itertools.product(range(4), repeat=2)
                    if x | y == target and a[x] * b[y]
                }
                total = sum(pairs.values())
                observed = defaultdict(F)
                for first in range(total):
                    probe = Draws(first, 0)
                    _union_pair(a, b, target, probe, WorkBudget())
                    for second in range(probe.totals[1]):
                        draws = Draws(first, second)
                        pair = _union_pair(a, b, target, draws, WorkBudget())
                        observed[pair] += F(1, total * draws.totals[1])
                self.assertEqual(dict(observed), {p: F(w, total) for p, w in pairs.items()})

    def test_profiles_original_tokens_restrictions_and_zero_mass(self):
        records = (
            {"a": False, "b": False},
            {"a": True, "b": False},
            {"a": False, "b": True},
            {"a": True, "b": True},
        )
        source = boolean_rule_grammar(("b", "a"))
        emissions = (
            b'{"var":"',
            b'{"!":[{"var":"',
            b'{"and":[{"var":"',
            b'{"or":[{"var":"',
            b'a"}',
            b'b"}',
            b'a"}]}',
            b'b"}]}',
            b'a"},{"var":"b"}]}',
            b'b"},{"var":"a"}]}',
            b'a"}',
            b"a",
        )
        data = inputs(source, emissions, (tuple(range(4)), tuple(range(4, 12))))
        plan = compile_cfg_sampler(source, data.state)
        variants = [
            data,
            replace(data, probabilities=((F(1, 10),) * 4, (F(1, 20),) * 8)),
            inputs(source, emissions, ((1,), tuple(range(4, 12))), canvas=(1, None)),
            replace(data, probabilities=((F(0),) * 4, (F(1, 8),) * 8)),
        ]
        for candidate in variants:
            posterior = evaluate_semantics(plan, candidate, records)
            expected = enumeration(candidate, records)
            self.assertEqual(
                posterior.profile_masses, tuple(sum(expected[t].values(), F()) for t in range(16))
            )
            for target, mass in enumerate(posterior.profile_masses):
                if not mass:
                    with self.assertRaisesRegex(ValueError, "ZERO_MASS_ON_SUPPORT"):
                        posterior.sample(target, Random(20261007))
                    continue
                for seed in range(20):
                    self.assertIn(posterior.sample(target, Random(seed)), expected[target])
            if candidate is data:

                class NeedDraw(Exception):
                    pass

                class Decisions(Random):
                    def __init__(self, draws):
                        self.draws = iter(draws)

                    def randrange(self, total):
                        try:
                            return next(self.draws)
                        except StopIteration:
                            raise NeedDraw(total) from None

                # Exhaust the complete sampler's decision tree, including aliases.
                for target, mass in enumerate(posterior.profile_masses):
                    if not mass:
                        continue
                    pending, law = [((), F(1))], defaultdict(F)
                    while pending:
                        draws, probability = pending.pop()
                        try:
                            path = posterior.sample(target, Decisions(draws))
                        except NeedDraw as need:
                            total = need.args[0]
                            pending.extend(((*draws, i), probability / total) for i in range(total))
                        else:
                            law[path] += probability
                    self.assertEqual(dict(law), {p: w / mass for p, w in expected[target].items()})
        with self.assertRaises(CompilationLimit):
            evaluate_semantics(plan, data, records, max_profile_entries=0)
        with self.assertRaises(CompilationLimit):
            evaluate_semantics(plan, data, records, max_work=0)
        with self.assertRaises(ValueError):
            evaluate_semantics(plan, data, ({"a": 1, "b": False},))
        with self.assertRaises(ValueError):
            evaluate_semantics(plan, data, ({"a": False},))

    def test_recursive_multi_byte_token_profiles(self):
        # Actual JSON trees of different shapes; exhaustive support-product oracle.
        source = boolean_rule_grammar(("a", "b"))
        emissions = (
            b'{"and":[{"!":[{"var":"',
            b'{"or":[{"var":"',
            b"a",
            b"b",
            b'"}]},{"var":"',
            b'"},{"var":"',
            b'"}]}',
        )
        rows = ((0, 1), (2, 3), (4, 5), (2, 3), (6,))
        data = inputs(source, emissions, rows)
        records = ({"a": True, "b": False}, {"a": False, "b": True})
        plan = compile_cfg_sampler(source, data.state)
        posterior = evaluate_semantics(plan, data, records)
        expected = enumeration(data, records)
        self.assertEqual(
            posterior.profile_masses, tuple(sum(expected[t].values(), F()) for t in range(4))
        )
        for t, mass in enumerate(posterior.profile_masses):
            if mass:
                for seed in range(20):
                    self.assertIn(posterior.sample(t, Random(seed)), expected[t])


if __name__ == "__main__":
    unittest.main()
