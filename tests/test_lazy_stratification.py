"""A30 independent exact-RNG oracles, never a favorable performance corpus."""

import importlib
import itertools
import unittest
from collections import defaultdict
from fractions import Fraction as F
from random import Random

ledger = importlib.import_module("attempts.30-lazy-native-stratification.work.ledger")


class NeedDraw(Exception):
    def __init__(self, stop):
        self.stop = stop


class Replay:
    def __init__(self, tickets):
        self.tickets = iter(tickets)

    def randrange(self, stop):
        if stop == 1:
            return 0
        try:
            value = next(self.tickets)
        except StopIteration:
            raise NeedDraw(stop) from None
        if not 0 <= value < stop:
            raise AssertionError("oracle transcript out of range")
        return value


def exact_law(run):
    pending, law = [((), F(1))], defaultdict(F)
    while pending:
        draws, probability = pending.pop()
        try:
            result = run(Replay(draws))
        except NeedDraw as need:
            pending.extend(((*draws, r), probability / need.stop) for r in range(need.stop))
        else:
            law[result] += probability
    if sum(law.values()) != 1:
        raise AssertionError("oracle lost probability")
    return dict(law)


def assert_every_event(test, law, individual):
    support = tuple(individual)
    m = len(next(iter(law)))
    for label in range(m):
        for value, p in individual.items():
            test.assertEqual(sum(q for ys, q in law.items() if ys[label] == value), p)
    for bits in itertools.product((0, 1), repeat=len(support)):
        good = {x for x, bit in zip(support, bits, strict=True) if bit}
        p = sum(individual[x] for x in good)
        actual = sum(q for ys, q in law.items() if any(y in good for y in ys))
        test.assertGreaterEqual(actual, 1 - (1 - p) ** m)


class LazyStratificationTests(unittest.TestCase):
    def test_all_small_partial_label_sets_events_and_scores(self):
        for size in range(1, 4):
            for total in range(1, 5):
                individual = {i: F(1, total) for i in range(total)}
                for m in range(1, size + 1):
                    for labels in itertools.combinations(range(size), m):

                        def run(rng, labels=labels, size=size, total=total):
                            book = ledger.HistoryLedger(size, rng)
                            return tuple(book.draw((), i, total) for i in labels)

                        law = exact_law(run)
                        assert_every_event(self, law, individual)
                        for score in itertools.product((-1, 0, 2), repeat=total):
                            mean = sum(individual[x] * score[x] for x in individual)
                            var = sum(individual[x] * (score[x] - mean) ** 2 for x in individual)
                            batch_var = sum(
                                p * (sum(score[x] for x in ys) / F(m) - mean) ** 2
                                for ys, p in law.items()
                            )
                            self.assertLessEqual(batch_var, var / m)

    def test_async_changed_kernels_and_all_terminal_verifiers(self):
        # Two different descendant maps, additional independent auxiliary bit,
        # and histories that may have the same last canvas but never rejoin.
        for kernel0, kernel1 in itertools.product(((0, 1), (0, 0), (1, 0)), repeat=2):
            children = (kernel0, kernel1)

            def run(rng, order, children=children):
                book = ledger.HistoryLedger(3, rng)
                histories = [()] * 3
                for label, step in order:
                    h = histories[label]
                    self.assertEqual(len(h), step)
                    ticket = book.draw(h, label, 2)
                    if not h:
                        action = ticket
                    else:
                        action = children[h[0]][ticket] ^ rng.randrange(2)
                    histories[label] = (*h, action)
                return tuple(histories)

            serial = [(i, t) for i in range(3) for t in range(2)]
            interleaved = [(i, t) for t in range(2) for i in reversed(range(3))]
            law = exact_law(lambda rng, run=run, serial=serial: run(rng, serial))
            self.assertEqual(
                law,
                exact_law(lambda rng, run=run, interleaved=interleaved: run(rng, interleaved)),
            )
            individual = {(a, b): F(1, 4) for a, b in itertools.product((0, 1), repeat=2)}
            assert_every_event(self, law, individual)

    def test_full_history_keys_idempotence_and_rejections(self):
        book = ledger.HistoryLedger(4, Random(42))
        h0, h1 = ((0,), (2,)), ((1,), (2,))
        first = book.draw(h0, 0, 13)
        before = book.rng.getstate()
        self.assertEqual(book.draw(h0, 0, 13), first)
        self.assertEqual(book.rng.getstate(), before)
        book.draw(h1, 0, 13)
        self.assertEqual(len(book.tables), 2)
        before = book.rng.getstate()
        for label, total in ((0, 14), (-1, 13), (4, 13), (True, 13), (0, 0), (0, 1.0)):
            with self.assertRaises(ValueError):
                book.draw(h0, label, total)
        self.assertEqual(book.rng.getstate(), before)
        for size in (0, -1, True, 1.0):
            with self.assertRaises(ValueError):
                ledger.HistoryLedger(size, Random(0))

    def test_cpu_cuda_uniform_transform_independent_ieee_rounding(self):
        tickets = {0, 1, 2, 2**53 - 2, 2**53 - 1}
        for power in range(1, 54):
            tickets.update(z for z in range(2**power - 3, 2**power + 4) if 0 <= z < 2**53)
        for z in tickets:
            # Fraction->float is a separate correctly-rounded implementation;
            # checks half-ULP ties and the original CUDA upper-bound reversal.
            expected = float(F(2 * z + 1, 2**54))
            expected = 0.0 if expected == 1.0 else expected
            self.assertEqual(ledger.cuda_double(z).hex(), expected.hex())
            self.assertEqual(ledger.cpu_double(z).hex(), float(F(z, 2**53)).hex())
        self.assertEqual(ledger.cuda_double(2**53 - 1), 0.0)
        self.assertNotEqual(ledger.cuda_double(0), ledger.cpu_double(0))
        self.assertEqual(ledger.cuda_double(2**52), ledger.cuda_double(2**52 - 1) + 2**-54)
        for z in (-1, 2**53, True, F(1), 1.0):
            with self.assertRaises(ValueError):
                ledger.cuda_double(z)

    def test_multicoordinate_shortcut_has_parity_counterexample(self):
        # Independent stratification permutations in each dimension STILL fail:
        # the second candidate is the bitwise complement of the first.
        law = exact_law(
            lambda rng: (
                (a := rng.randrange(2)) ^ (b := rng.randrange(2)),
                (1 - a) ^ (1 - b),
            )
        )
        self.assertEqual(sum(p for ys, p in law.items() if 0 in ys), F(1, 2))
        self.assertLess(F(1, 2), 1 - (1 - F(1, 2)) ** 2)


if __name__ == "__main__":
    unittest.main()
