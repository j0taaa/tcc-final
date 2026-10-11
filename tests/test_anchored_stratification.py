"""Independent enumeration of conditional tickets, not performance evidence."""

import importlib
import itertools
import unittest
from collections import defaultdict
from fractions import Fraction

a = importlib.import_module("attempts.31-sufficient-state-coupling.work.anchored_ledger")
ledger = importlib.import_module("attempts.31-sufficient-state-coupling.work.ledger")


class NeedDraw(Exception):
    def __init__(self, stop):
        self.stop = stop


class Replay:
    def __init__(self, draws):
        self.draws = iter(draws)

    def randrange(self, stop):
        if stop == 1:
            return 0
        try:
            return next(self.draws)
        except StopIteration as exc:
            raise NeedDraw(stop) from exc


def enumerate_law(operation):
    out = defaultdict(Fraction)

    def visit(draws, mass):
        try:
            result = operation(Replay(draws))
        except NeedDraw as ask:
            for value in range(ask.stop):
                visit((*draws, value), mass / ask.stop)
        else:
            out[result] += mass

    visit((), Fraction(1))
    return dict(out)


class AnchoredTests(unittest.TestCase):
    def test_all_small_joint_laws_and_orders(self):
        for size in range(1, 4):
            for total in range(1, 5):
                for order in itertools.permutations(range(size)):

                    def ordinary(rng, size=size, total=total, order=order):
                        book = ledger.HistoryLedger(size, rng)
                        values = [None] * size
                        for label in order:
                            values[label] = book.draw("node", label, total)
                        return tuple(values)

                    def anchored(rng, size=size, total=total, order=order):
                        book = a.AnchoredLedger(size, rng)
                        values = [None] * size
                        values[order[0]] = rng.randrange(total)
                        book.anchor("node", order[0], total, values[order[0]])
                        for label in order[1:]:
                            values[label] = book.draw("node", label, total)
                        return tuple(values)

                    self.assertEqual(enumerate_law(anchored), enumerate_law(ordinary))

    def test_refusals_idempotence_and_freshness(self):
        import random

        book = a.AnchoredLedger(2, random.Random(1))
        for total, label, ticket in ((0, 0, 0), (2, 2, 0), (2, 0, 2), (2, 0, -1)):
            with self.assertRaises(ValueError):
                book.anchor("node", label, total, ticket)
            self.assertFalse(book.tables)
        book.anchor("node", 1, 3, 2)
        self.assertEqual(book.draw("node", 1, 3), 2)
        with self.assertRaises(ValueError):
            book.anchor("node", 0, 3, 1)
        with self.assertRaises(ValueError):
            book.draw("node", 0, 4)

    def test_observed_cpu_cuda_posterior_from_independent_rounding(self):
        total = 2**53
        boundaries = (
            tuple(range(6))
            + tuple(total // 2 + d for d in range(-4, 6))
            + tuple(total - d for d in range(1, 8))
        )
        for ticket in boundaries:
            for profile in ("cpu", "cuda"):
                exact = Fraction(ticket, total) + (
                    Fraction(1, 2 * total) if profile == "cuda" else 0
                )
                observed = float(exact)
                if profile == "cuda" and observed == 1:
                    observed = 0.0
                expected = tuple(
                    j
                    for j in range(max(0, ticket - 2), min(total, ticket + 3))
                    if (
                        0.0
                        if profile == "cuda"
                        and float(Fraction(j, total) + Fraction(1, 2 * total)) == 1
                        else float(
                            Fraction(j, total)
                            + (Fraction(1, 2 * total) if profile == "cuda" else 0)
                        )
                    )
                    == observed
                )
                actual = enumerate_law(
                    lambda rng, observed=observed, profile=profile: a.observed_ticket(
                        observed, profile, rng
                    )
                )
                self.assertEqual(actual, {j: Fraction(1, len(expected)) for j in expected})
        for value, profile in (
            (1.0, "cpu"),
            (-0.1, "cuda"),
            (float("nan"), "cpu"),
            (0.1, "cuda"),
            (0.5, "x"),
        ):
            with self.assertRaises(ValueError):
                a.observed_ticket(value, profile, Replay(()))


if __name__ == "__main__":
    unittest.main()
