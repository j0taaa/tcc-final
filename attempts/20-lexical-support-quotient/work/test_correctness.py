"""Independent product recognition, original-ID oracle, all-state congruence."""

import itertools
import json
import random
import unittest
from dataclasses import replace

from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

from .lexer import OUT, STATES, Partition, finish, lexical_grammar, scan
from .lexical_selectors import ClassEngine, LexRoot, compile_lexical
from .monotone import Monotone


def valid(adapter, word):
    try:
        json.loads(
            adapter.detokenize_bytes(word).decode(),
            parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
        )
        return True
    except (ValueError, UnicodeDecodeError):
        return False


def state_for(emissions, rows, canvas=None):
    canvas = (None,) * len(rows) if canvas is None else tuple(canvas)
    adapter = CompositionalByteLevelAdapter(tuple(emissions))
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=len(emissions)),
        explicit_support=dict(enumerate(rows)),
    )
    return SelectionInput(
        lexical_grammar(), canvas, (), support, adapter, EOSPolicy(EOSMode.ABSENT)
    )


def oracle(words, canvas, proposals, threshold, cap):
    words = [w for w in words if all(t is None or w[p] == t for p, t in enumerate(canvas))]
    if not words:
        return None
    accepted = []
    for p, t, confidence in proposals:
        trial = [w for w in words if w[p] == t]
        if trial:
            words = trial
            accepted.append((p, t, confidence))
    updates = [(p, t) for p, t, c in accepted if c >= threshold][:cap]
    if updates:
        return tuple(updates)
    if accepted:
        return ((accepted[0][0], accepted[0][1]),)
    p = canvas.index(None)
    return ((p, min(w[p] for w in words)),)


def audit(include_sat=False):
    rng = random.Random(2026100923)
    texts = [
        b'["hello",0]',
        b'{"a":[true,null]}',
        b'"\\uD800"',
        b'"\xe2\x82\xac"',
        b"1.2e-3",
        b'"a\\"b"',
        b"0",
        b"[{},[]]",
        b'"\xf0\x90\x80\x80"',
    ]
    noise = [
        b'"',
        b"0",
        b"1",
        b"2",
        b"00",
        b"hi",
        b"zz",
        b"\\",
        b" ",
        b",",
        b"null",
        b"true",
        b"\x80",
        b"\xed\xa0",
        b"\x01",
        b"\xe2",
        b"\x82",
        b"\xac",
        b"\\u",
        b"ff",
        b"n",
    ]
    trajectories = transitions = 0
    for iteration in range(72):
        text = texts[iteration % len(texts)]
        cuts = [0, *sorted(rng.sample(range(1, len(text)), min(3, len(text) - 1))), len(text)]
        pieces = [text[a:b] for a, b in itertools.pairwise(cuts)]
        emissions = [*pieces, *noise, *pieces]
        rows = [
            tuple(
                sorted({p, len(emissions) - len(pieces) + p, *rng.sample(range(len(emissions)), 2)})
            )
            for p in range(len(pieces))
        ]
        state = state_for(emissions, rows)
        adapter = state.tokenizer_adapter
        words = [w for w in itertools.product(*rows) if valid(adapter, w)]
        # Original text is present, but only for exhaustive correctness oracle;
        # never used to construct model experimental supports.
        assert words
        for kind in ("monotone", "root", "speculative", *(("sat",) if include_sat else ())):
            rows = list(state.support.rows)
            words = [w for w in itertools.product(*rows) if valid(adapter, w)]
            engine = ClassEngine(state, state.grammar, kind)
            if kind == "monotone":
                control = Monotone(compile_lexical(state, state.grammar))
            else:
                control = LexRoot(state, grammar=state.grammar)
            canvas = list(state.canvas)
            step = 0
            while None in canvas:
                current = replace(
                    state,
                    canvas=tuple(canvas),
                    support=replace(
                        state.support,
                        canvas=tuple(canvas),
                        rows=tuple(
                            (t,) if t is not None else row
                            for t, row in zip(canvas, rows, strict=True)
                        ),
                    ),
                )
                assert engine.update_original_domains(current)
                # Add previously unavailable aliases (same signature) while
                # leaving genuinely new classes to force explicit rejection.
                if step:
                    altered = []
                    for p, row in enumerate(current.support.rows):
                        equivalents = (
                            [
                                t
                                for t in range(len(emissions))
                                if any(
                                    engine.partition.classify(t) == engine.partition.classify(u)
                                    for u in row
                                )
                            ]
                            if canvas[p] is None
                            else []
                        )
                        altered.append(tuple(sorted(set(row).union(equivalents))))
                    expanded = replace(
                        current, support=replace(current.support, rows=tuple(altered))
                    )
                    assert engine.update_original_domains(expanded)
                    rows = list(altered)
                    words = [w for w in itertools.product(*rows) if valid(adapter, w)]
                    control = (
                        Monotone(compile_lexical(expanded, state.grammar))
                        if kind == "monotone"
                        else LexRoot(expanded, grammar=state.grammar)
                    )
                proposals = sorted(
                    [
                        (p, rng.choice(rows[p]), rng.choice([0.0, 0.5, 0.8, 0.95]))
                        for p, t in enumerate(canvas)
                        if t is None
                    ],
                    key=lambda x: (-x[2], x[0], x[1]),
                )
                expected = oracle(words, canvas, proposals, 0.8, 2)
                got = engine.transition(proposals, threshold=0.8, cap=2)
                assert got == expected, (iteration, kind, expected, got)
                observed = control.transition(proposals, threshold=0.8, cap=2)
                assert observed == expected, (
                    iteration,
                    kind,
                    step,
                    proposals,
                    expected,
                    observed,
                    canvas,
                )
                for p, t in got:
                    canvas[p] = t
                transitions += 1
                step += 1
            assert valid(adapter, canvas)
            engine.close()
            trajectories += 1
    return dict(
        trajectories=trajectories,
        transitions=transitions,
        seed=2026100923,
        oracle="strict decoded UTF8 Python JSON, enumerate original token products",
        timings="not performance evidence",
    )


class LexicalCorrectness(unittest.TestCase):
    def test_independent_original_token_trajectories(self):
        self.assertEqual(audit()["trajectories"], 216)

    def test_scanner_against_independent_mutated_json(self):
        rng = random.Random(2026100924)
        samples = [
            b'{"a":[1,-1.2e+4,true,false,null,"xx"]}',
            b'"\\uD800"',
            '"á😀"'.encode(),
            b"[0,12,1.0,0e0]",
            b"{}",
        ]
        lexemes = (b"{", b"}", b"[", b"]", b":", b",", b'"x"', b"0", b"true", b"false", b"null")
        for _ in range(3000):
            word = rng.choice(samples)
            p = rng.randrange(len(word))
            mutated = word[:p] + bytes([rng.randrange(256)]) + word[p + 1 :]
            actual = scan(mutated)
            predicted = False
            if actual is not None and finish(actual[0]) is not None:
                reduced = b" ".join(lexemes[t] for t in (*actual[1], *finish(actual[0])))
                predicted = valid(CompositionalByteLevelAdapter((reduced or b" ",)), (0,))
            expected = valid(CompositionalByteLevelAdapter((mutated,)), (0,))
            self.assertEqual(predicted, expected, mutated)

    def test_state_signatures_and_dangerous_boundaries(self):
        words = (
            b"hi",
            b"zz",
            b'"',
            b"\\",
            b"1",
            b"0",
            b"e",
            b"\x82",
            b"\xe2",
            b"\\u",
            b"ff",
            b"\xed\xa0\x80",
        )
        partition = Partition(CompositionalByteLevelAdapter(words))
        classes = [partition.classify(t) for t in range(len(words))]
        self.assertEqual(classes[0], classes[1])
        self.assertNotEqual(classes[4], classes[5])
        for a, b in itertools.product(range(len(words)), repeat=2):
            if classes[a] == classes[b]:
                for q in STATES:
                    self.assertEqual(scan(words[a], q), scan(words[b], q))
        self.assertIsNone(scan(b'"\xed\xa0\x80"', OUT))
        self.assertIsNone(finish(scan(b'"\\u0', OUT)[0]))
        # An original-ID minimum can belong to the highest numbered class.
        state = state_for((b'"', b"hi", b"zz"), ((0,), (1, 2), (0,)), (0, None, 0))
        engine = ClassEngine(state, state.grammar, "monotone")
        self.assertEqual(engine.transition([], threshold=0.8, cap=1), ((1, 1),))


if __name__ == "__main__":
    unittest.main()
