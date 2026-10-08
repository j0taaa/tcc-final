"""Full decision-tree laws, not favorable frequencies or performance cases."""

import itertools
import json
import unittest
from collections import defaultdict
from dataclasses import replace
from fractions import Fraction as F
from functools import cache
from math import prod
from pathlib import Path
from random import Random
from unittest.mock import patch

from scripts.exact_commit.adaptive_semantics import AdaptiveSemanticSampler, compile_semantic_core
from scripts.exact_commit.semantic_json import boolean_rule_grammar, evaluate_semantics
from test_cfg_posterior import inputs
from test_semantic_json import enumeration, execute

from mwpc_exact.cfg_posterior import CompilationLimit, _categorical, compile_cfg_sampler


class AdaptiveSemanticTests(unittest.TestCase):
    def test_archived_adaptive_and_core_recomputation(self):
        from scripts.exact_commit.audit_adaptive_semantics import load, replay

        archive = (
            Path(__file__).resolve().parents[1] / "docs/artifacts/raw/m36_adaptive_semantics_v1"
        )
        config, preparation, rows = replay(archive)
        self.assertEqual(len(rows), preparation["targets"] * len(config["seeds"]))
        _, data, capture = load(config)
        plan = compile_cfg_sampler(boolean_rule_grammar(capture["fields"]), data.state)
        # Fixed selection rule: first positive and first zero target, first seed.
        chosen = (
            next(r for r in rows if F(*r["mass"]) > 0),
            next(r for r in rows if F(*r["mass"]) == 0),
        )
        for row in chosen:
            labels = tuple(bool(row["target"] & (1 << i)) for i in range(len(capture["records"])))
            core = compile_semantic_core(plan, data, capture["records"], labels)
            self.assertTrue(core.verify())
            self.assertEqual(core.active, tuple(row["core"]["active"]))
            posterior = core.evaluate(data)
            self.assertEqual(posterior.valid_mass, F(*row["mass"]))
            adaptive = AdaptiveSemanticSampler(plan, data, capture["records"], labels)
            for name, draw in (("adaptive", adaptive.sample), ("certified_core", posterior.sample)):
                rng = Random(row["metadata"]["seed"])
                if posterior.valid_mass:
                    current = [
                        list(draw(rng)) for _ in range(config["samples_per_positive_target"])
                    ]
                    self.assertEqual(current, row["methods"][name]["samples"])
                else:
                    with self.assertRaisesRegex(ValueError, "ZERO_MASS_ON_SUPPORT"):
                        draw(rng)

    def test_structural_core_reweighting_and_reuse_boundaries(self):
        source = boolean_rule_grammar(("a", "b"))
        pieces = (b'{"var":"a"}', b'{"var":"b"}')
        original = inputs(source, pieces, ((0, 1),))
        data = replace(original, probabilities=((F(1), F()),))
        plan = compile_cfg_sampler(source, data.state)
        records = ({"a": True, "b": False},)
        core = compile_semantic_core(plan, data, records, (True,))
        self.assertTrue(core.verify())
        # A certificate based on the original probabilities would unsoundly
        # ignore the zero-weight invalid token and fail after this reweighting.
        self.assertEqual(core.active, (0,))
        for probabilities in ((F(), F(1)), (F(1, 4), F(3, 4)), (F(1), F())):
            candidate = replace(data, probabilities=(probabilities,))
            posterior = core.evaluate(candidate)
            self.assertEqual(posterior.valid_mass, probabilities[0])
            if posterior.valid_mass:
                self.assertEqual(posterior.sample(Random(20261007)), (0,))
            else:
                with self.assertRaisesRegex(ValueError, "ZERO_MASS_ON_SUPPORT"):
                    posterior.sample(Random(20261007))
        # The plan is broader than the certified state: validate both bounds.
        narrow = inputs(source, pieces, ((0,),))
        empty = compile_semantic_core(plan, narrow, records, (True,))
        self.assertEqual(empty.active, ())
        self.assertTrue(empty.verify())
        self.assertEqual(empty.evaluate(narrow).valid_mass, 1)
        with self.assertRaisesRegex(ValueError, "certified support"):
            empty.evaluate(original)
        fixed = inputs(source, pieces, ((0,),), canvas=(0,))
        fixed_core = compile_semantic_core(plan, fixed, records, (True,))
        with self.assertRaisesRegex(ValueError, "fixed slot"):
            fixed_core.evaluate(narrow)
        with self.assertRaises(CompilationLimit):
            compile_semantic_core(plan, data, records, (True,), max_active=0)

    def test_core_all_targets_and_independent_implications(self):
        source = boolean_rule_grammar(("a", "b"))
        pieces = (
            b'{"var":"a"}',
            b'{"var":"b"}',
            b'{"!":[{"var":"a"}]}',
            b'{"!":[{"var":"b"}]}',
            b'{"var":"a"}',
        )
        data = inputs(source, pieces, (tuple(range(5)),))
        plan = compile_cfg_sampler(source, data.state)
        records = tuple(
            dict(zip(("a", "b"), bits, strict=True))
            for bits in itertools.product((False, True), repeat=2)
        )
        oracle = enumeration(data, records)
        for target in range(16):
            labels = tuple(bool(target & (1 << i)) for i in range(4))
            core = compile_semantic_core(plan, data, records, labels)
            self.assertTrue(core.verify())
            # Check every original token path, not just samples or chosen rows.
            active_valid = {
                path
                for profile, paths in oracle.items()
                for path in paths
                if all(bool(profile & (1 << i)) == labels[i] for i in core.active)
            }
            self.assertEqual(active_valid, set(oracle[target]))
            self.assertLessEqual(len(core.active), len(records))
            for seed in (20261007, 20261008):
                weights = [Random(seed + i).randrange(5) for i in range(5)]
                denominator = sum(weights) or 1
                candidate = replace(
                    data, probabilities=(tuple(F(w, denominator) for w in weights),)
                )
                expected = enumeration(candidate, records)
                posterior = core.evaluate(candidate)
                self.assertEqual(posterior.valid_mass, sum(expected[target].values(), F()))
                if posterior.valid_mass:
                    self.assertIn(posterior.sample(Random(seed)), expected[target])

        # Distinct records, multiple correct programs, unchanged generic grammar:
        # a monotone filter is fixed on the cube by two boundary requirements.
        fields = tuple("abcdef")
        source = boolean_rule_grammar(fields)
        pieces = (
            b'{"and":[',
            b'{"or":[',
            *(f'{{"var":"{f}"}}'.encode() for f in fields),
            b",",
            b"]}",
        )
        data = inputs(source, pieces, ((0, 1), tuple(range(2, 8)), (8,), tuple(range(2, 8)), (9,)))
        plan = compile_cfg_sampler(source, data.state)
        records = tuple(
            dict(zip(fields, bits, strict=True))
            for bits in itertools.product((False, True), repeat=len(fields))
        )
        labels = tuple(r["a"] for r in records)
        core = compile_semantic_core(plan, data, records, labels, initial_active=(31, 32))
        self.assertEqual(core.active, (31, 32))
        self.assertTrue(core.verify())
        with self.assertRaisesRegex(ValueError, "twelve|12"):
            evaluate_semantics(plan, data, records)
        oracle = enumeration(data, records)
        expected = {
            p
            for profile, paths in oracle.items()
            for p in paths
            if all(bool(profile & (1 << i)) == labels[i] for i in range(len(records)))
        }
        self.assertEqual(len(expected), 2)
        self.assertEqual(core.evaluate(data).valid_mass, F(1, 36))
        for seed in range(20):
            self.assertIn(core.evaluate(data).sample(Random(seed)), expected)

    def test_prefix_control_complete_weighted_law(self):
        from scripts.exact_commit.audit_adaptive_semantics import PrefixControl

        paths = (((0, 0), 1, 0), ((0, 1), 2, 1), ((1, 0), 1, 1), ((1, 1), 0, 0))

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

        pending, law = [((), F(1))], defaultdict(F)
        while pending:
            draws, probability = pending.pop()
            session = PrefixControl(paths, 1)
            try:
                path = session.sample(Decisions(draws))
            except NeedDraw as need:
                total = need.args[0]
                pending.extend(((*draws, i), probability / total) for i in range(total))
            else:
                law[path] += probability
                self.assertLessEqual(session.rejections, 1)
        self.assertEqual(dict(law), {(0, 1): F(2, 3), (1, 0): F(1, 3)})

    def test_prefix_batch_expected_rejections(self):
        from scripts.exact_commit.audit_adaptive_semantics import PrefixControl

        class NeedCategory(Exception):
            pass

        for row_weights, count in (
            (((1, 1),), 3),
            (((1, 1),) * 2, 3),
            (((1, 1),) * 3, 1),
            (((1, 1),) * 3, 3),
            (((2, 1), (1, 3)), 3),
            (((2, 1), (1, 3), (2, 5)), 1),
        ):
            n = len(row_weights)
            paths = tuple(
                (
                    path,
                    prod(row[b] for row, b in zip(row_weights, path, strict=True)),
                    sum(path) % 2,
                )
                for path in itertools.product((0, 1), repeat=n)
            )
            groups = 1 << (n - 1)
            pending, expectation, total_probability = [((), F(1))], F(), F()
            while pending:
                decisions, probability = pending.pop()
                cursor = iter(decisions)

                def category(weights, _rng):
                    try:
                        index = next(cursor)
                    except StopIteration:
                        raise NeedCategory(weights) from None
                    self.assertGreater(weights[index], 0)
                    return index

                control = PrefixControl(paths, 1)
                with patch("scripts.exact_commit.audit_adaptive_semantics._categorical", category):
                    try:
                        for _ in range(count):
                            path = control.sample(Random(20261008))
                            self.assertEqual(sum(path) % 2, 1)
                    except NeedCategory as need:
                        weights = need.args[0]
                        pending.extend(
                            ((*decisions, i), probability * F(weight, sum(weights)))
                            for i, weight in enumerate(weights)
                            if weight
                        )
                    else:
                        total_probability += probability
                        expectation += probability * control.rejections

            # Independent finite Markov recursion over visited pair groups,
            # using the independently listed valid/invalid original weights.
            group_weights = []
            for prefix in itertools.product((0, 1), repeat=n - 1):
                group_weights.append(
                    tuple(
                        next(
                            w for p, w, profile in paths if p[:-1] == prefix and profile == desired
                        )
                        for desired in (1, 0)
                    )
                )

            @cache
            def expected(remaining, visited):
                if remaining == 0 or visited == (1 << groups) - 1:
                    return F()
                denominator = sum(
                    v + (0 if visited & (1 << i) else b) for i, (v, b) in enumerate(group_weights)
                )
                result = F()
                for i, (valid, invalid) in enumerate(group_weights):
                    new = visited | (1 << i)
                    result += F(valid, denominator) * expected(remaining - 1, new)
                    if new != visited:
                        result += F(invalid, denominator) * (1 + expected(remaining, new))
                return result

            self.assertEqual(total_probability, 1)
            self.assertEqual(expectation, expected(count, 0))
            alpha = F(min(row_weights[-1]), sum(row_weights[-1]))
            total_valid = sum(v for v, _ in group_weights)
            lower = alpha * sum(1 - (1 - F(v, total_valid)) ** count for v, _ in group_weights)
            self.assertGreaterEqual(expectation, lower)
            if n == 3 and count == 3 and all(row == (1, 1) for row in row_weights):
                self.assertGreater(lower, 1)  # Already exceeds refinement's total budget.
            # A worst-case branch has positive probability: every still-uncut
            # invalid path followed by a valid path, even with the perfect oracle.
            bad = [p for p, _, profile in paths if profile == 0]
            good = next(p for p, _, profile in paths if profile == 1)
            forced = iter((*[bit for p in bad for bit in p], *good))

            def force(weights, _rng):
                i = next(forced)
                self.assertGreater(weights[i], 0)
                return i

            control = PrefixControl(paths, 1)
            with patch("scripts.exact_commit.audit_adaptive_semantics._categorical", force):
                self.assertEqual(control.sample(Random(20261008)), good)
            self.assertEqual(control.rejections, groups)

    def test_nonprefix_refinement_family(self):
        # Mathematical diagnostic, not a speed benchmark. All bit assignments
        # become valid JsonLogic programs; ! toggles and !! preserves a Boolean.
        source = boolean_rule_grammar(("a",), identity_operator=True)
        pieces = (b'{"!":[', b'{"!!":[', b'{"var":"a"}', b"]}")
        for n in range(1, 6):
            data = inputs(
                source,
                pieces,
                ((0, 1),) * n + ((2,),) + ((3,),) * n,
                canvas=(None,) * n + (2,) + (3,) * n,
            )
            plan = compile_cfg_sampler(source, data.state)
            records = ({"a": True},)
            expected = enumeration(data, records)
            posterior = evaluate_semantics(plan, data, records, identity_operator=True)
            self.assertEqual(posterior.profile_masses, (F(1, 2), F(1, 2)))
            for target in (False, True):
                session = AdaptiveSemanticSampler(
                    plan, data, records, (target,), identity_operator=True
                )
                rng = Random(20261007 + n)
                for _ in range(40):
                    path = session.sample(rng)
                    self.assertIn(path, expected[int(target)])
                    self.assertEqual(path[n:], (2,) + (3,) * n)
                self.assertLessEqual(session.rejections, 1)
                self.assertLessEqual(session.draws, 41)
            # No proper prefix of the n choices proves failure; every prefix
            # has a completing valid choice. Excluding all failures needs
            # 2**(n-1) disjoint complete-choice prefixes, for either target.
            for target, paths in expected.items():
                invalid = set(expected[1 - target])
                self.assertEqual(len(invalid), 2 ** (n - 1))
                for path in invalid:
                    for length in range(n):
                        self.assertTrue(any(p[:length] == path[:length] for p in paths))

    def test_complete_two_sample_law_and_all_targets(self):
        source = boolean_rule_grammar(("a", "b"))
        pieces = (
            b'{"var":"a"}',
            b'{"var":"b"}',
            b'{"!":[{"var":"a"}]}',
            b'{"!":[{"var":"b"}]}',
            b'{"var":"a"}',
            b"invalid",
        )
        data = inputs(source, pieces, (tuple(range(len(pieces))),))
        plan = compile_cfg_sampler(source, data.state)
        records = ({"a": True, "b": False}, {"a": False, "b": True})
        oracle = enumeration(data, records)

        class NeedDraw(Exception):
            pass

        class Decisions(Random):
            def __init__(self, draws):
                self._draws = iter(draws)

            def category(self, weights):
                try:
                    value = next(self._draws)
                except StopIteration:
                    raise NeedDraw(weights) from None
                assert weights[value] > 0
                return value

        verified = set()

        def compressed_category(weights, rng):
            # Consolidate equal outcomes of integer draws, without assuming
            # the helper is correct: first exhaust its actual integer mapping.
            if weights not in verified:

                class IntegerDraw(Random):
                    def __init__(self, value):
                        self.value = value

                    def randrange(self, total):
                        assert 0 <= self.value < total
                        return self.value

                counts = [0] * len(weights)
                for value in range(sum(weights)):
                    counts[_categorical(weights, IntegerDraw(value))] += 1
                self.assertEqual(tuple(counts), weights)
                verified.add(weights)
            return rng.category(weights)

        for target in range(4):
            labels = tuple(bool(target & (1 << i)) for i in range(2))
            pending, law, zero_probability = [((), F(1))], defaultdict(F), F()
            while pending:
                draws, probability = pending.pop()
                session = AdaptiveSemanticSampler(plan, data, records, labels)
                rng = Decisions(draws)
                try:
                    with (
                        patch("mwpc_exact.cfg_posterior._categorical", compressed_category),
                        patch(
                            "scripts.exact_commit.semantic_json._categorical", compressed_category
                        ),
                    ):
                        pair = session.sample(rng), session.sample(rng)
                except NeedDraw as need:
                    weights = need.args[0]
                    pending.extend(
                        ((*draws, i), probability * weight / sum(weights))
                        for i, weight in enumerate(weights)
                        if weight
                    )
                    continue
                except ValueError as error:
                    self.assertIn("ZERO_MASS_ON_SUPPORT", str(error))
                    zero_probability += probability
                else:
                    law[pair] += probability
                self.assertLessEqual(session.rejections, len(records))
                self.assertEqual(session.rejections, len(session.active))
                self.assertEqual(len(set(session.active)), len(session.active))
                self.assertLessEqual(session.draws, session.rejections + 2)
            mass = sum(oracle[target].values(), F())
            if not mass:
                self.assertEqual(zero_probability, 1)
                self.assertEqual(dict(law), {})
            else:
                expected = {
                    pair: a * b / mass**2
                    for pair, (a, b) in (
                        (p, (oracle[target][p[0]], oracle[target][p[1]]))
                        for p in itertools.product(oracle[target], repeat=2)
                    )
                }
                self.assertEqual(zero_probability, 0)
                self.assertEqual(dict(law), expected)

    def test_checker_scope_refusal_and_snapshot(self):
        source = boolean_rule_grammar(("a", "b"))
        data = inputs(source, (b'{"var":"a"}', b'{"var":"b"}'), ((0, 1),))
        plan = compile_cfg_sampler(source, data.state)
        records = [{"a": True, "b": False}, {"a": False, "b": True}] * 7
        labels = [True, False] * 7
        session = AdaptiveSemanticSampler(plan, data, records, labels)
        records[0]["a"] = False  # Caller mutations cannot change the specification.
        for _ in range(30):
            path = session.sample(Random(20261007 + _))
            self.assertEqual(path, (0,))
            self.assertEqual(
                execute(
                    json.loads(data.state.tokenizer_adapter.detokenize_bytes(path)),
                    {"a": True, "b": False},
                ),
                True,
            )
        self.assertLessEqual(session.rejections, 14)
        self.assertEqual(session.proposal_mass, F(1, 2))
        for options in ({"max_active": 0}, {"max_profile_entries": 0}, {"max_work": 1_000}):
            # Contradiction forces a rejection for every first draw, not a chosen seed.
            try:
                failed = AdaptiveSemanticSampler(
                    plan, data, ({"a": True, "b": True},), (False,), **options
                )
            except CompilationLimit:
                continue  # Grammar admission can exhaust the shared preparation budget.
            with self.assertRaises(CompilationLimit):
                failed.sample(Random(20261007))
            draws = failed.draws
            with self.assertRaises(CompilationLimit):
                failed.sample(Random(20261008))
            self.assertEqual(failed.draws, draws)
        for records, labels in (
            ([], []),
            ([{"a": 1, "b": False}], [True]),
            ([{"a": True, "b": False}], [1]),
        ):
            with self.assertRaises(ValueError):
                AdaptiveSemanticSampler(plan, data, records, labels)


if __name__ == "__main__":
    unittest.main()
