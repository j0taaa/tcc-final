"""A31 exhaustive finite laws and energy identities, not benchmark victories."""

import importlib
import itertools
import unittest
from collections import defaultdict
from fractions import Fraction as F

batch = importlib.import_module("attempts.31-sufficient-state-coupling.work.batch")


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
            value = next(self.draws)
        except StopIteration:
            raise NeedDraw(stop) from None
        if not 0 <= value < stop:
            raise AssertionError("RNG transcript out of range")
        return value


def exact_law(run):
    pending, law = [((), F(1))], defaultdict(F)
    while pending:
        draws, p = pending.pop()
        try:
            outcome = run(Replay(draws))
        except NeedDraw as need:
            pending.extend(((*draws, r), p / need.stop) for r in range(need.stop))
        else:
            law[outcome] += p
    if sum(law.values()) != 1:
        raise AssertionError("lost probability")
    return dict(law)


def expectation(kernel, value):
    return sum(sum(value[x] for x in row) / len(row) for row in kernel.rows) / len(kernel.rows)


def continuations(kernel_for, states, horizon, score):
    result = [None] * horizon + [dict(zip(states, score, strict=True))]
    for t in reversed(range(horizon)):
        result[t] = {s: expectation(kernel_for(t, s), result[t + 1]) for s in states}
    return result


def local_energy(kernel, g, size):
    total = len(kernel.rows)
    means = [
        sum(
            sum(g[x] for x in kernel.rows[(j * total + r) // size])
            / F(len(kernel.rows[(j * total + r) // size]))
            for r in range(total)
        )
        / total
        for j in range(size)
    ]
    mean = sum(means) / size
    return sum((v - mean) ** 2 for v in means) / (size * (size - 1))


def cross(law, score):
    return sum(p * score[hs[0][-1]] * score[hs[1][-1]] for hs, p in law.items())


class StateCouplingTests(unittest.TestCase):
    def check_chain(self, kernel_for, states, horizon, size=2):
        laws = {
            mode: exact_law(
                lambda rng, mode=mode: batch.decode(
                    kernel_for, states[0], size, horizon, rng, mode=mode
                )
            )
            for mode in ("iid", "history", "state", "root")
        }
        single = {s: sum(p for hs, p in laws["iid"].items() if hs[0][-1] == s) for s in states}
        for law in laws.values():
            for label in range(size):
                for s in states:
                    self.assertEqual(
                        sum(p for hs, p in law.items() if hs[label][-1] == s), single[s]
                    )
        for bits in itertools.product((0, 1), repeat=len(states)):
            acceptable = {s for s, bit in zip(states, bits, strict=True) if bit}
            covers = {
                mode: sum(p for hs, p in law.items() if any(h[-1] in acceptable for h in hs))
                for mode, law in laws.items()
            }
            self.assertGreaterEqual(covers["state"], covers["iid"])
            if size == 2:
                self.assertGreaterEqual(covers["state"], covers["history"])
        for values in itertools.product((-1, 0, 2), repeat=len(states)):
            score = dict(zip(states, map(F, values), strict=True))
            g = continuations(kernel_for, states, horizon, tuple(score[s] for s in states))
            energy = sum(
                p
                * sum(
                    local_energy(kernel_for(t, hs[0][t]), g[t + 1], size)
                    for t in range(horizon)
                    if hs[0][t] == hs[1][t]
                )
                for hs, p in laws["state"].items()
            )
            rejoined = sum(
                p
                * sum(
                    local_energy(kernel_for(t, hs[0][t]), g[t + 1], size)
                    for t in range(horizon)
                    if hs[0][t] == hs[1][t] and hs[0][: t + 1] != hs[1][: t + 1]
                )
                for hs, p in laws["state"].items()
            )
            self.assertEqual(cross(laws["iid"], score) - cross(laws["state"], score), energy)
            self.assertEqual(cross(laws["history"], score) - cross(laws["state"], score), rejoined)
        return laws

    def test_all_binary_stationary_kernels_and_terminal_events(self):
        maps = tuple(itertools.product((0, 1), repeat=2))
        for rows in itertools.product(maps, repeat=2):
            kernels = tuple(batch.Kernel(tuple((x,) for x in row)) for row in rows)
            self.check_chain(lambda t, s, kernels=kernels: kernels[s], (0, 1), 3)

    def test_nonmonotone_three_state_kernels_and_independent_auxiliaries(self):
        rows = (
            (((0,), (1,)), ((0,), (2,)), ((1,), (2,))),
            (((2,), (0,)), ((0,), (1,)), ((2,), (1,))),
            (((0, 1), (2,)), ((2,), (0, 2)), ((1, 2), (0,))),
        )
        for specs in rows:
            kernels = tuple(batch.Kernel(row) for row in specs)
            self.check_chain(lambda t, s, kernels=kernels: kernels[s], (0, 1, 2), 3)

    def test_strict_reunion_and_async_service_without_extra_candidates(self):
        def kernel(t, s):
            return batch.Kernel(((0,), (1,))) if t in (0, 2) else batch.Kernel(((0,),))

        laws = self.check_chain(kernel, (0, 1), 3)

        def cover(law):
            return sum(p for hs, p in law.items() if any(h[-1] == 1 for h in hs))

        self.assertEqual(cover(laws["history"]), F(3, 4))
        self.assertEqual(cover(laws["state"]), 1)
        serial = [(label, t) for label in range(2) for t in range(3)]
        self.assertEqual(
            laws["state"],
            exact_law(lambda rng: batch.decode(kernel, 0, 2, 3, rng, order=serial)),
        )
        # K=3 keeps K strata even for a two-label subgroup.
        self.check_chain(kernel, (0, 1), 3, size=3)

    def test_canvas_only_summary_breaks_coverage_without_budget(self):
        # First action sets hidden budget b. At step2, two equal canvases need
        # different maps: same ticket0 means success for b0, failure for b1.
        def kernel(t, state):
            if t == 0:
                return batch.Kernel((((0, 0),), ((0, 1),)))
            _canvas, budget = state
            return (
                batch.Kernel((((0, budget),), ((1, budget),)))
                if budget == 0
                else batch.Kernel((((1, budget),), ((0, budget),)))
            )

        correct = exact_law(lambda rng: batch.decode(kernel, (0, 0), 2, 2, rng))
        unsafe = exact_law(
            lambda rng: batch.decode(kernel, (0, 0), 2, 2, rng, summary=lambda t, s, h: s[0])
        )

        def cover(law):
            return sum(p for hs, p in law.items() if any(h[-1][0] for h in hs))

        self.assertGreaterEqual(cover(correct), F(3, 4))
        self.assertLess(cover(unsafe), F(3, 4))


if __name__ == "__main__":
    unittest.main()
