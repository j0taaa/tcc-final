"""Small independent complete-draw oracles; no favorable performance family."""

import importlib
import itertools
import math
import unittest
from collections import defaultdict
from fractions import Fraction as F

repair = importlib.import_module("attempts.32-native-oracle-antithetics.work.oracle").repair


def law(weights, classes):
    probs = [F(w, sum(weights)) for w in weights]
    joint = defaultdict(F)
    extra = F()
    for seq in itertools.product(range(len(weights)), repeat=4):
        mass = math.prod(probs[i] for i in seq)
        cursor = iter(seq[2:])
        second, calls = repair(classes[seq[0]], seq[1], cursor.__next__, classes.__getitem__)
        joint[seq[0], second] += mass
        extra += mass * calls
    return probs, joint, extra


class NativeOracleCouplingTests(unittest.TestCase):
    def test_all_small_laws_classes_events_scores_and_exact_overhead(self):
        distributions = [
            ws for n in (2, 3) for ws in itertools.product(range(3), repeat=n) if sum(ws)
        ] + [(1, 2, 1, 3), (3, 0, 2, 1)]
        for weights in distributions:
            n = len(weights)
            for classes in itertools.product((False, True), repeat=n):
                probs, joint, extra = law(weights, classes)
                p = sum((prob for c, prob in zip(classes, probs, strict=True) if c), F())
                self.assertEqual(extra, 1 - p * (1 - p))
                self.assertEqual(sum(joint.values()), 1)
                for i in range(n):
                    self.assertEqual(sum(joint[i, j] for j in range(n)), probs[i])
                    self.assertEqual(sum(joint[j, i] for j in range(n)), probs[i])
                functions = list(itertools.product((0, 1), repeat=n))
                functions += list(itertools.product((-1, 0, 2), repeat=n))
                for values in functions:
                    mean = sum(pr * v for pr, v in zip(probs, values, strict=True))
                    covariance = (
                        sum(m * values[i] * values[j] for (i, j), m in joint.items()) - mean**2
                    )
                    conditional = []
                    for c, total in ((False, 1 - p), (True, p)):
                        conditional.append(
                            sum(
                                (
                                    pr * v
                                    for cc, pr, v in zip(classes, probs, values, strict=True)
                                    if cc == c
                                ),
                                F(),
                            )
                            / total
                            if total
                            else F()
                        )
                    expected = -((p * (1 - p)) ** 2) * (conditional[1] - conditional[0]) ** 2
                    self.assertEqual(covariance, expected)
                    if set(values) <= {0, 1}:
                        coverage = sum(m for (i, j), m in joint.items() if values[i] or values[j])
                        self.assertEqual(coverage, 2 * mean - mean**2 - expected)

    def test_budget_bound_by_all_bitstrings_and_conditional_frechet(self):
        # Independent binomial sums and every bitstring: not a benchmark.
        for n in range(2, 9):
            for p in (F(0), F(1, 10), F(1, 3), F(1, 2), F(9, 10), F(1)):
                upper = sum(
                    F(math.comb(n, m)) * p**m * (1 - p) ** (n - m) * F(min(m, n - m), n)
                    for m in range(n + 1)
                )
                if n <= 3:
                    self.assertEqual(upper, p * (1 - p))
                if n == 4:
                    self.assertEqual(upper, p * (1 - p) + p**2 * (1 - p) ** 2)
                _, joint, _ = law((1, 1), (False, True))
                self.assertEqual(joint[1, 0], F(5, 16))
        strings = list(itertools.product((False, True), repeat=4))
        output = {}
        for s in strings:
            draws = iter(s[2:])
            output[s] = repair(s[0], s[1], draws.__next__, bool)[0]
        for count in range(5):
            subset = [s for s in strings if sum(s) == count]
            self.assertEqual(F(sum(output[s] for s in subset), len(subset)), F(count, 4))
            self.assertEqual(
                F(sum(s[0] and not output[s] for s in subset), len(subset)),
                F(min(count, 4 - count), 4),
            )

    def test_all_small_adaptive_kernels_and_exact_meeting_energy(self):
        possibilities = (F(0), F(1, 2), F(1))
        tables = {p: law((1 - p, p), (False, True))[1] for p in possibilities}
        for chain in itertools.product(itertools.product(possibilities, repeat=2), repeat=3):
            # Compute continuation values independently, before pair evaluation.
            continuation = [(F(), F(1))]
            for kernel in reversed(chain):
                g = continuation[-1]
                continuation.append(tuple((1 - p) * g[0] + p * g[1] for p in kernel))
            continuation.reverse()
            native_mean = continuation[0][0]
            paired = {(0, 0): F(1)}
            energy = F()
            for time, kernel in enumerate(chain):
                new = defaultdict(F)
                g = continuation[time + 1]
                for (a, b), mass in paired.items():
                    pa, pb = kernel[a], kernel[b]
                    if a == b:
                        transitions = tables[pa]
                        energy += mass * (pa * (1 - pa)) ** 2 * (g[1] - g[0]) ** 2
                    else:
                        transitions = {
                            (i, j): (pa if i else 1 - pa) * (pb if j else 1 - pb)
                            for i in (0, 1)
                            for j in (0, 1)
                        }
                    for target, probability in transitions.items():
                        new[target] += mass * probability
                paired = new
            self.assertEqual(sum(m for (i, j), m in paired.items() if i), native_mean)
            self.assertEqual(sum(m for (i, j), m in paired.items() if j), native_mean)
            self.assertEqual(paired[1, 1] - native_mean**2, -energy)
            self.assertEqual(
                sum(m for (i, j), m in paired.items() if i or j),
                2 * native_mean - native_mean**2 + energy,
            )

    def test_original_payload_aliases_and_unsafe_reroll(self):
        # IDs 0/1 render the same bytes; they are distinct native events.
        probs, joint, _ = law((1, 2, 3), (False, False, True))
        for i in range(3):
            self.assertEqual(sum(joint[j, i] for j in range(3)), probs[i])
        # Resampling collisions until opposite flips the first bit, changing
        # the second marginal from 9/10 to1/10. Our operation remains9/10.
        probs, joint, _ = law((1, 9), (False, True))
        self.assertEqual(sum(joint[i, 1] for i in range(2)), F(9, 10))
        self.assertNotEqual(1 - probs[1], probs[1])
        with self.assertRaises(ValueError):
            repair(1, 0, lambda: 0, bool)
        with self.assertRaises(ValueError):
            repair(False, 0, lambda: 0, lambda x: x)


if __name__ == "__main__":
    unittest.main()
