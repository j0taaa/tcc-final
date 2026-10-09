"""Small exhaustive JSON oracle, independent of forest recognition/selection."""

import itertools
import json
import random
import unittest

from grammar_selectors import CachedPrefix, Recompute, witness
from monotone import Monotone
from relevant_forest import relevant_forest

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind


def setup(emissions, rows):
    source = json_source_grammar()
    canvas = (None,) * len(rows)
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
    valid = []
    for path in itertools.product(*rows):
        try:
            json.loads(b"".join(emissions[t] for t in path))
            valid.append(path)
        except (ValueError, UnicodeDecodeError):
            pass
    return compile_cfg_sampler(source, state), valid


def oracle(valid, canvas, proposals, threshold, cap):
    domain = [y for y in valid if all(t is None or t == y[p] for p, t in enumerate(canvas))]
    accepted = []
    for p, token, confidence in proposals:
        compatible = [y for y in domain if y[p] == token]
        if compatible:
            accepted.append((p, token, confidence))
            domain = compatible
    updates = {}
    for p, token, confidence in accepted:
        if confidence >= threshold and canvas[p] is None and len(updates) < cap:
            updates.setdefault(p, token)
    if not updates:
        free = [(p, t) for p, t, _ in accepted if canvas[p] is None]
        if free:
            updates = dict(free[:1])
        else:
            p = canvas.index(None)
            # No accepted proposal: domain is unchanged by the scan.
            updates[p] = min(y[p] for y in domain)
    return tuple(updates.items())


class Correctness(unittest.TestCase):
    def test_independent_json_trajectories(self):
        fixtures = [
            ((b"[", b"0", b"1", b",", b"]", b"0"), ((0,), (1, 2, 5), (3,), (1, 2, 5), (4,))),
            (
                (b"[", b'{"a":', b"0", b"1", b",", b"]", b"}", b" ", b'{"b":'),
                ((0, 1), (0, 2, 8), (2, 3, 4, 5, 6), (2, 3, 5, 6, 7), (5, 6, 7)),
            ),
            (
                (b"[", b"[]", b"]", b"0", b"00", b"0]", b" "),
                ((0, 1), (0, 1, 2, 3, 4), (1, 2, 3, 5, 6)),
            ),
        ]
        rng = random.Random(2026100918)
        for emissions, rows in fixtures:
            plan, valid = setup(emissions, rows)
            self.assertTrue(valid)
            trimmed = relevant_forest(plan)
            self.assertEqual(relevant_forest(trimmed), trimmed)
            self.assertLessEqual(trimmed.alternatives, plan.alternatives)
            for trial in range(50):
                engines = [
                    engine(p)
                    for p in (plan, trimmed)
                    for engine in (
                        Monotone,
                        Recompute,
                        lambda p: Recompute(p, lex=True),
                        CachedPrefix,
                    )
                ]
                canvas = [None] * len(rows)
                while None in canvas:
                    proposals = [
                        (p, rng.choice(row), rng.choice((0.1, 0.8, 0.9)))
                        for p, row in enumerate(rows)
                        if canvas[p] is None
                    ]
                    if trial % 5 == 0:
                        proposals += proposals[:2]  # IDs/order multiplicity survives.
                    if trial % 7 == 0:
                        proposals = []  # canonical no-proposal fallback.
                    proposals.sort(key=lambda p: (-p[2], p[0], p[1]))
                    threshold, cap = rng.choice((0.0, 0.8, 1.0)), rng.randrange(1, 4)
                    expected = oracle(valid, canvas, proposals, threshold, cap)
                    for engine in engines:
                        self.assertEqual(
                            engine.transition(proposals, threshold=threshold, cap=cap), expected
                        )
                    for p, token in expected:
                        canvas[p] = token
                    domain = [
                        y
                        for y in valid
                        if all(t is None or t == y[p] for p, t in enumerate(canvas))
                    ]
                    for p, row in enumerate(rows):
                        for token in row:
                            self.assertEqual(
                                engines[0].feasible(p, token), any(y[p] == token for y in domain)
                            )
                    self.assertLessEqual(engines[0].deactivated, plan.alternatives)
                    self.assertLessEqual(engines[0].flow_removed, plan.alternatives)
                self.assertIn(tuple(canvas), valid)

    def test_large_integer_priorities(self):
        plan, valid = setup((b"[", b"0", b"1", b"]"), ((0,), (1, 2), (3,)))
        proposals = [(1, 2, 0.9)] + [(1, 1, 0.8)] * 256
        path = witness(plan, [None] * 3, proposals)
        self.assertEqual(path[1], 2)
        self.assertIn(path, valid)

    def test_reject_unfix_and_bad_order(self):
        plan, _ = setup((b"[", b"0", b"1", b"]"), ((0,), (1, 2), (3,)))
        engine = Monotone(plan)
        engine.commit(1, 1)
        with self.assertRaises(ValueError):
            engine.commit(1, 2)
        with self.assertRaises(ValueError):
            engine.transition([(0, 0, 0.2), (2, 3, 0.9)])


if __name__ == "__main__":
    unittest.main()
