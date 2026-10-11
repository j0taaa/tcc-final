"""A28: independent original-event and all-ticket laws, not a timing benchmark."""

import importlib
import itertools
import json
import unittest
from collections import defaultdict
from fractions import Fraction
from math import prod
from random import Random

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

PREFIX = "attempts.28-streamed-grammar-head.work."
summary = importlib.import_module(PREFIX + "summary")
table_module = importlib.import_module(PREFIX + "frozen.table")
stack_module = importlib.import_module(PREFIX + "frozen.stack_control")


def valid(emissions, word):
    if any(emissions[t] is None for t in word):
        return False
    try:
        json.loads(b"".join(emissions[t] for t in word).decode("utf8"))
        return True
    except (ValueError, UnicodeDecodeError):
        return False


def prepare(emissions, canvas):
    table = table_module.LexerTable(CompositionalByteLevelAdapter(emissions))
    plan = stack_module.StackPrepared(
        table,
        canvas,
        timeout_seconds=10,
        max_cells=100000,
        max_edges=100000,
        max_terms=1000000,
    )
    return table, plan


class NeedTicket(Exception):
    def __init__(self, total):
        self.total = total


class ReplayRng:
    def __init__(self, tickets):
        self.tickets, self.offset = tickets, 0

    def randrange(self, total):
        if self.offset == len(self.tickets):
            raise NeedTicket(total)
        ticket = self.tickets[self.offset]
        self.offset += 1
        if not 0 <= ticket < total:
            raise AssertionError("replayed ticket changed range")
        return ticket


def exact_sampler_law(operation):
    pending, law, visited = [((), Fraction(1))], defaultdict(Fraction), 0
    while pending:
        tickets, probability = pending.pop()
        visited += 1
        if visited > 200000:
            raise AssertionError("tiny all-ticket oracle exceeded its declared size")
        try:
            result = operation(ReplayRng(tickets))
        except NeedTicket as need:
            pending.extend(((*tickets, r), probability / need.total) for r in range(need.total))
        else:
            law[result] += probability
    return dict(law)


class StreamedGrammarHeadTests(unittest.TestCase):
    def test_block_recovery_full_original_law_and_fixed_slots(self):
        import numpy as np

        blocks = importlib.import_module(PREFIX + "block_stats")
        sampler = importlib.import_module(PREFIX + "block_sampler")
        cases = (
            ((b"[", b"]", b"0", b"1", b"[]", b"[]", b" ", None), (None, None), [[1] * 8] * 2),
            ((b"[]", b"[]", b"0", None), (None,), [[2, 3, 4, 1]]),
            ((b"[", b"]", b"0", b"1", b"[]", b"[]", b" ", None), (0, None, 1), [[1] * 8]),
            ((b"[[]]", b"0", None), (0,), []),
        )
        for emissions, canvas, rows in cases:
            table, plan = prepare(emissions, canvas)
            free = [p for p, t in enumerate(canvas) if t is None]
            matrix = np.array(rows, dtype=np.float64).reshape((len(free), len(emissions)))
            expected = {}
            for word in itertools.product(
                *[(t,) if t is not None else range(len(emissions)) for t in canvas]
            ):
                if valid(emissions, word):
                    expected[word] = prod(int(matrix[row, word[p]]) for row, p in enumerate(free))
            total = sum(expected.values())
            expected = {word: Fraction(w, total) for word, w in expected.items() if w}
            for size in (1, 3):
                partition = blocks.Partition(table.class_of, len(table.classes), size)
                stats = (
                    blocks.numpy_stats(matrix, partition)
                    if free
                    else blocks.BlockStats(partition, (), (), 0)
                )

                def operation(rng, plan=plan, stats=stats, matrix=matrix, partition=partition):
                    posterior = sampler.BlockPosterior(
                        plan, stats, sampler.numpy_fetch(matrix, partition)
                    )
                    return posterior.sample(rng)

                self.assertEqual(exact_sampler_law(operation), expected)
                posterior = sampler.BlockPosterior(
                    plan, stats, sampler.numpy_fetch(matrix, partition)
                )
                self.assertEqual(posterior.mass, Fraction(total, prod(sum(row) for row in rows)))
                posterior.sample(Random(28))
                with self.assertRaisesRegex(ValueError, "consumed"):
                    posterior.sample(Random(29))

    def test_full_joint_sampler_law_by_all_random_decisions(self):
        emissions = (b"[", b"]", b"0", b"1", b"[]", b"[]", b" ", None)
        rows, canvas = [[1] * len(emissions)] * 2, (None, None)
        table, plan = prepare(emissions, canvas)

        def operation(rng):
            ledger = summary.ClassLedger(
                (iter(r) for r in rows), canvas, table.class_of, len(table.classes), rng
            )
            return summary.ClassPosterior(plan, ledger).sample(rng)

        expected = {
            word: prod(rows[p][t] for p, t in enumerate(word))
            for word in itertools.product(range(len(emissions)), repeat=2)
            if valid(emissions, word)
        }
        total = sum(expected.values())
        expected = {word: Fraction(w, total) for word, w in expected.items()}
        self.assertEqual(exact_sampler_law(operation), expected)

        # Nonuniform aliases and an unsupported positive-weight ID must retain
        # their separate original probabilities and the full denominator.
        emissions = (b"[]", b"[]", b"0", None)
        rows, canvas = [[2, 3, 4, 1]], (None,)
        table, plan = prepare(emissions, canvas)
        self.assertEqual(
            exact_sampler_law(operation),
            {
                (0,): Fraction(2, 9),
                (1,): Fraction(3, 9),
                (2,): Fraction(4, 9),
            },
        )

    def test_class_constancy_and_mass_with_macro_alias_fixed_and_partial_string(self):
        emissions = (b"[", b"]", b"[[]]", b"[[]]", b'"x', b'y"', b"0", b" ", None)
        for canvas in ((None,) * 3, (0, None, 1), (None, None), (2,), ()):
            table, plan = prepare(emissions, canvas)
            rows = [[(p + t) % 4 for t in range(len(emissions))] for p in range(len(canvas))]
            ledger = summary.ClassLedger(
                (iter(r) for r in rows), canvas, table.class_of, len(table.classes), Random(28)
            )
            domains = [(t,) if t is not None else range(len(emissions)) for t in canvas]
            seen, mass = {}, 0
            for word in itertools.product(*domains):
                classes = tuple(table.class_of[t] for t in word)
                accepted = valid(emissions, word)
                if classes in seen:
                    self.assertEqual(seen[classes], accepted)
                seen[classes] = accepted
                weight = prod(
                    1 if canvas[p] is not None else rows[p][t] for p, t in enumerate(word)
                )
                mass += weight * accepted
            posterior = summary.ClassPosterior(plan, ledger)
            self.assertEqual(posterior.mass, Fraction(mass, prod(ledger.denominators)))
            self.assertFalse(hasattr(ledger, "rows"))
            if mass:
                word = posterior.sample(Random(29))
                self.assertTrue(valid(emissions, word))
                self.assertTrue(all(t is None or t == word[p] for p, t in enumerate(canvas)))
                with self.assertRaisesRegex(ValueError, "consumed"):
                    summary.ClassPosterior(plan, ledger).sample(Random(30))

    def test_zero_mass_bad_stream_and_incompatible_frame_are_distinct(self):
        table, plan = prepare((b"[", b"]"), (None,))
        ledger = summary.ClassLedger(
            (iter([1, 0]),), (None,), table.class_of, len(table.classes), Random(1)
        )
        posterior = summary.ClassPosterior(plan, ledger)
        self.assertEqual(posterior.mass, 0)
        with self.assertRaisesRegex(ValueError, "zero_valid_mass"):
            posterior.sample(Random(2))
        self.assertFalse(ledger.consumed)
        for row in ([0, 0], [1, -1], [True, 1], [1], [1, 1, 1]):
            with self.assertRaises(ValueError):
                summary.ClassLedger(
                    (iter(row),), (None,), table.class_of, len(table.classes), Random(1)
                )
        fixed = summary.ClassLedger(((),), (0,), table.class_of, len(table.classes), Random(1))
        with self.assertRaisesRegex(ValueError, "frame"):
            summary.ClassPosterior(plan, fixed)


if __name__ == "__main__":
    unittest.main()
