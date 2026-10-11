"""Independent all-ticket laws and every verifier, not performance cases."""

import importlib
import itertools
import json
import unittest
from collections import defaultdict
from fractions import Fraction as F

coupling = importlib.import_module("attempts.29-collision-stationary-coupling.work.coupling")


class NeedTicket(Exception):
    def __init__(self, size):
        self.size = size


class Replay:
    def __init__(self, tickets):
        self.tickets = iter(tickets)

    def randrange(self, size):
        try:
            return next(self.tickets)
        except StopIteration:
            raise NeedTicket(size) from None


def enumerate_rng(run):
    pending, law = [((), F(1))], defaultdict(F)
    while pending:
        tickets, mass = pending.pop()
        try:
            value = run(Replay(tickets))
        except NeedTicket as need:
            pending.extend(((*tickets, r), mass / need.size) for r in range(need.size))
        else:
            law[value] += mass
    return dict(law)


def finite_draw(weights, rng):
    ticket = rng.randrange(sum(weights))
    for i, w in enumerate(weights):
        if ticket < w:
            return i
        ticket -= w
    raise AssertionError("invalid finite sampler ticket")


class CollisionCouplingTests(unittest.TestCase):
    def test_all_small_heterogeneous_laws_and_all_verifiers(self):
        # All integer triples of total1,2,3, including disjoint/delta laws.
        families = [w for w in itertools.product(range(4), repeat=3) if 1 <= sum(w) <= 3]
        for pw, qw in itertools.product(families, repeat=2):
            p, q = [F(w, sum(pw)) for w in pw], [F(w, sum(qw)) for w in qw]

            def run(rng, pw=pw, qw=qw):
                return coupling.coupled_pair(
                    lambda: finite_draw(pw, rng),
                    lambda: finite_draw(qw, rng),
                    lambda item: qw[item],
                    rng,
                )

            law = enumerate_rng(run)
            for x in range(3):
                self.assertEqual(sum(v for (a, _), v in law.items() if a == x), p[x])
                self.assertEqual(sum(v for (_, b), v in law.items() if b == x), q[x])
            for bits in itertools.product((0, 1), repeat=3):
                pe, qe = (
                    sum(p[i] * bits[i] for i in range(3)),
                    sum(q[i] * bits[i] for i in range(3)),
                )
                actual = sum(v for (a, b), v in law.items() if bits[a] or bits[b])
                flow = sum(
                    p[x] * p[z] * min(q[x], q[z])
                    for x in range(3)
                    for z in range(3)
                    if bits[x] and not bits[z]
                )
                self.assertEqual(actual, pe + qe - pe * qe + flow)
                common = {i for i in range(3) if p[i] and q[i]}
                self.assertEqual(
                    flow > 0, any(bits[i] for i in common) and any(not bits[i] for i in common)
                )
            for f in itertools.product((-1, 0, 2), repeat=3):
                cross = sum(v * f[a] * f[b] for (a, b), v in law.items())
                independent = sum(p[i] * f[i] for i in range(3)) * sum(
                    q[i] * f[i] for i in range(3)
                )
                energy = (
                    sum(
                        p[x] * p[z] * min(q[x], q[z]) * (f[x] - f[z]) ** 2
                        for x in range(3)
                        for z in range(3)
                    )
                    / 2
                )
                self.assertEqual(cross, independent - energy)

    def test_exact_weights_refusals_and_lazy_noncollision(self):
        def forbidden(*args):
            raise AssertionError("noncollision must not query weight, proposal or RNG")

        x, y = object(), object()
        self.assertEqual(coupling.repair_pair(x, y, forbidden, forbidden, forbidden), (x, y))
        for bad in (True, -1, 0.5, float("nan"), float("inf"), 0):
            with self.assertRaises(ValueError):
                coupling.repair_pair(0, 0, lambda: 1, lambda _, bad=bad: bad, Replay(()))
        law = enumerate_rng(
            lambda rng: coupling.repair_pair(0, 0, lambda: 1, lambda z: (F(7, 3), F(5, 9))[z], rng)
        )
        self.assertEqual(law, {(0, 0): F(16, 21), (0, 1): F(5, 21)})

    def test_naive_reroll_changes_marginal(self):
        p = (F(3, 4), F(1, 4))
        # Independent replacement of a duplicate, without MH, is not sound.
        second_zero = sum(
            p[x] * p[y] * (p[0] if x == y else int(y == 0))
            for x, y in itertools.product(range(2), repeat=2)
        )
        self.assertNotEqual(second_zero, p[0])
        self.assertEqual(second_zero, F(21, 32))

    def test_original_json_events_and_aliases(self):
        tokens = (b"[", b"0", b"1", b"0", b"]", b" ", b" ")
        rows = ((0, 1, 2, 3), (4, 1, 5, 6))
        valid = []
        for word in itertools.product(*rows):
            try:
                json.loads(b"".join(tokens[t] for t in word))
            except ValueError:
                continue
            valid.append(word)
        pw = tuple(1 for _ in valid)
        qw = tuple(2 if 3 in word else 1 for word in valid)
        weights = dict(zip(valid, qw, strict=True))

        def run(rng):
            return coupling.coupled_pair(
                lambda: valid[finite_draw(pw, rng)],
                lambda: valid[finite_draw(qw, rng)],
                weights.__getitem__,
                rng,
            )

        law = enumerate_rng(run)
        self.assertEqual(len(valid), 8)
        for i, word in enumerate(valid):
            self.assertEqual(sum(v for (a, _), v in law.items() if a == word), F(pw[i], sum(pw)))
            self.assertEqual(sum(v for (_, b), v in law.items() if b == word), F(qw[i], sum(qw)))
        # Same rendered JSONs remain distinct events in both marginals.
        self.assertNotEqual((1, 5), (3, 5))
        self.assertEqual(tokens[1], tokens[3])

    def test_different_future_policies_are_not_covered(self):
        def run(rng):
            return coupling.coupled_pair(
                lambda: finite_draw((1, 1), rng),
                lambda: finite_draw((1, 1), rng),
                lambda _: 1,
                rng,
            )

        law = enumerate_rng(run)
        # The second decoder flips its raw output in a DIFFERENT future step.
        terminal_pass = sum(v for (a, b), v in law.items() if a == 0 or 1 - b == 0)
        self.assertEqual(terminal_pass, F(5, 8))
        self.assertLess(terminal_pass, F(3, 4))


if __name__ == "__main__":
    unittest.main()
