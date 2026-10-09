"""Independent JSON-product oracles for growing domains and reused reserves."""

import itertools
import json
import random
import unittest
from dataclasses import replace

from mwpc_exact.cfg_posterior import _binarize_source
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.limits import WorkBudget
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

from .adaptive_domains import union_rows
from .grammar_selectors import CachedPrefix, Recompute
from .monotone import Monotone
from .rooted_selectors import RootCountWarm, RootLex, RootPrefix, RootSpeculative, compile_rooted


def fixture():
    emissions = (b"[", b"]", b'"a"', b'"', b"0", b"null", b" ", b"00", b'"a"')
    rows = ((0, 3, 6), (0, 2, 3, 4, 5, 6, 7, 8), (1, 3, 4, 6))
    canvas = (None,) * 3
    source = json_source_grammar()
    grammar = normalize_to_cnf(_binarize_source(source, WorkBudget(max_work=1_000_000))).grammar
    state = SelectionInput(
        grammar,
        canvas,
        (),
        build_per_position_support(
            canvas=canvas,
            policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=len(emissions)),
            explicit_support=dict(enumerate(rows)),
        ),
        CompositionalByteLevelAdapter(emissions),
        EOSPolicy(EOSMode.ABSENT),
    )
    valid = []
    for word in itertools.product(*rows):
        try:
            json.loads(b"".join(emissions[t] for t in word))
            valid.append(word)
        except (ValueError, UnicodeDecodeError):
            pass
    return state, valid


def restrict(state, rows, canvas):
    return replace(
        state,
        canvas=tuple(canvas),
        support=replace(
            state.support,
            rows=tuple(rows),
            canvas=tuple(canvas),
            permitted_token_ids=tuple(sorted({t for row in rows for t in row})),
        ),
    )


def oracle(valid, rows, canvas, proposals, threshold, cap):
    domain = [
        y
        for y in valid
        if all(y[p] in r for p, r in enumerate(rows))
        and all(t is None or t == y[p] for p, t in enumerate(canvas))
    ]
    accepted = []
    for p, t, w in proposals:
        compatible = [y for y in domain if y[p] == t]
        if compatible:
            domain = compatible
            accepted.append((p, t, w))
    updates = {}
    for p, t, w in accepted:
        if w >= threshold and canvas[p] is None and len(updates) < cap:
            updates.setdefault(p, t)
    if not updates:
        free = [(p, t) for p, t, _ in accepted if canvas[p] is None]
        if free:
            updates = dict(free[:1])
        else:
            p = canvas.index(None)
            updates[p] = min(y[p] for y in domain)
    return tuple(updates.items())


def audit(reservoir=False):
    state, valid = fixture()
    rng = random.Random(2026100922)
    full_plan = compile_rooted(state, state.grammar) if reservoir else None
    for _ in range(60):
        canvas = [None] * 3
        rows = ((0,), (2,), (1,))
        cached = None
        if reservoir:
            from .reservoir_sat import ReserveSat

            cached = ReserveSat(full_plan, rows)
        try:
            while None in canvas:
                extra = {
                    p: rng.sample(list(row), rng.randrange(1, len(row) + 1))
                    for p, row in enumerate(state.support.rows)
                    if canvas[p] is None
                }
                rows = union_rows(rows, canvas, extra)
                current = restrict(state, rows, canvas)
                proposals = [
                    (p, rng.choice(row), rng.choice((0.1, 0.8, 0.9)))
                    for p, row in enumerate(rows)
                    if canvas[p] is None
                ]
                proposals.sort(key=lambda x: (-x[2], x[0], x[1]))
                threshold, cap = rng.choice((0.0, 0.8, 1.0)), rng.randrange(1, 4)
                expected = oracle(valid, rows, canvas, proposals, threshold, cap)
                engines = [
                    e(current) for e in (RootLex, RootPrefix, RootCountWarm, RootSpeculative)
                ]
                plan = compile_rooted(current, state.grammar)
                engines += [Monotone(plan), CachedPrefix(plan), Recompute(plan, lex=True)]
                if cached is not None:
                    cached.update_domains(rows)
                    engines.append(cached)
                for e in engines:
                    actual = e.transition(proposals, threshold=threshold, cap=cap)
                    if actual != expected:
                        raise AssertionError((type(e).__name__, actual, expected))
                for p, t in expected:
                    canvas[p] = t
        finally:
            if cached is not None:
                cached.close()


class GrowingCorrectness(unittest.TestCase):
    def test_union_preserves_committed_positions_and_old_choices(self):
        self.assertEqual(union_rows(((1, 2), (2, 3)), (1, None), {1: (0, 4)}), ((1,), (0, 2, 3, 4)))

    def test_independent_adaptive_trajectories(self):
        audit()


if __name__ == "__main__":
    unittest.main()
