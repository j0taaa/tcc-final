"""Independent finite-bit/payload oracles, including an adverse trajectory."""

import importlib
import itertools
import math
import unittest
from collections import defaultdict
from fractions import Fraction as F

walk = importlib.import_module("attempts.32-native-oracle-antithetics.work.walk").repair
four = importlib.import_module("attempts.32-native-oracle-antithetics.work.oracle").repair
pool = importlib.import_module("attempts.32-native-oracle-antithetics.work.pool").repair


def bound(n, p):
    return sum(
        F(math.comb(n, m) * min(m, n - m), n) * p**m * (1 - p) ** (n - m) for m in range(n + 1)
    )


def catalan_gain(n, p):
    return sum(
        F(math.comb(2 * k, k), k + 1) * (p * (1 - p)) ** (k + 1) for k in range(1, (n - 2) // 2 + 1)
    )


def payload_law(weights, classes, n):
    probs = [F(w, sum(weights)) for w in weights]
    joint, extra = defaultdict(F), F()
    for seq in itertools.product(range(len(weights)), repeat=n):
        mass = math.prod(probs[i] for i in seq)
        cursor = iter(seq[2:])
        y, calls = walk(classes[seq[0]], seq[1], cursor.__next__, classes.__getitem__, budget=n)
        joint[seq[0], y] += mass
        extra += calls * mass
    return probs, joint, extra


class NativeOracleWalkTests(unittest.TestCase):
    def test_every_small_bitstring_conditional_frechet_and_four_draw_identity(self):
        for n in range(2, 13):
            groups = defaultdict(lambda: [0, 0, 0, 0])
            for seq in itertools.product((False, True), repeat=n):
                cursor = iter(seq[2:])
                y, calls = walk(seq[0], seq[1], cursor.__next__, bool, budget=n)
                self.assertLessEqual(calls, n - 2)
                group = groups[sum(seq)]
                group[0] += 1
                group[1] += y
                group[2] += seq[0] and not y
                group[3] += calls
                if n == 4:
                    self.assertEqual((y, calls), four(seq[0], seq[1], iter(seq[2:]).__next__, bool))
            for m, (count, ones, disagreement, _) in groups.items():
                self.assertEqual(count, math.comb(n, m))
                self.assertEqual(F(ones, count), F(m, n))
                self.assertEqual(F(disagreement, count), F(min(m, n - m), n))
            for p in (F(0), F(1, 10), F(1, 3), F(1, 2), F(9, 10), F(1)):
                flow = sum(group[2] * p**m * (1 - p) ** (n - m) for m, group in groups.items())
                self.assertEqual(flow, bound(n, p))
                self.assertEqual(flow, p * (1 - p) + catalan_gain(n, p))
                expected = sum(group[3] * p**m * (1 - p) ** (n - m) for m, group in groups.items())
                self.assertLessEqual(expected, (n - 2) // 2)
                if n == 4:
                    self.assertEqual(expected, 1 - p * (1 - p))
        for n in range(2, 33, 2):
            for p in (F(0), F(1, 10), F(1, 3), F(1, 2), F(9, 10), F(1)):
                self.assertEqual(bound(n, p), bound(n + 1, p))
                self.assertEqual(bound(n, p), p * (1 - p) + catalan_gain(n, p))

    def test_full_original_payload_law_aliases_all_events_and_scores(self):
        # IDs0/1 may render the same text; neither event is collapsed.
        for n, weights in ((2, (1, 2, 3)), (4, (1, 2, 3)), (6, (1, 2, 3)), (8, (1, 0, 2))):
            for classes in itertools.product((False, True), repeat=3):
                probs, joint, _ = payload_law(weights, classes, n)
                p = sum(pr for c, pr in zip(classes, probs, strict=True) if c)
                delta = bound(n, p) - p * (1 - p)
                for i in range(3):
                    self.assertEqual(sum(joint[i, j] for j in range(3)), probs[i])
                    self.assertEqual(sum(joint[j, i] for j in range(3)), probs[i])
                for values in itertools.product((-2, 0, 1), repeat=3):
                    mean = sum(pr * v for pr, v in zip(probs, values, strict=True))
                    mus = [
                        sum(
                            pr * v
                            for c, pr, v in zip(classes, probs, values, strict=True)
                            if c == cls
                        )
                        / total
                        if total
                        else F()
                        for cls, total in ((False, 1 - p), (True, p))
                    ]
                    covariance = (
                        sum(m * values[i] * values[j] for (i, j), m in joint.items()) - mean**2
                    )
                    self.assertEqual(covariance, -delta * (mus[1] - mus[0]) ** 2)
                for event in itertools.product((False, True), repeat=3):
                    mean = sum(pr for pr, v in zip(probs, event, strict=True) if v)
                    covered = sum(m for (i, j), m in joint.items() if event[i] or event[j])
                    self.assertGreaterEqual(covered, 2 * mean - mean**2)

    def test_stronger_local_coupling_can_worsen_terminal_coverage(self):
        def joint(n):
            return payload_law((1, 1), (False, True), n)[1]

        root4, root8, root16 = (joint(n) for n in (4, 8, 16))
        value4 = root4

        def covered(root, value):
            total = F()
            for (style_a, style_b), mass in root.items():
                # Whole JSON output retains style: different styles cannot merge.
                next_law = value if style_a == style_b else {(a, b): F(1, 4) for a, b in root}
                total += mass * sum(m for (a, b), m in next_law.items() if a or b)
            return total

        weaker = covered(root4, value4)
        stronger_root = covered(root16, value4)
        self.assertLess(stronger_root, weaker)
        self.assertGreater(stronger_root, F(3, 4))
        self.assertLess(covered(root16, root16), covered(root8, root8))
        self.assertEqual(weaker, F(3, 4) + (F(1, 2) - 2 * F(1, 16)) * F(1, 16))

    def test_total_budget_validation_and_unreachable_tail(self):
        for budget in (True, 1, 0, -3, 4.0):
            with self.assertRaises(ValueError):
                walk(False, False, lambda: False, bool, budget=budget)
        with self.assertRaises(ValueError):
            walk(1, False, lambda: False, bool, budget=4)
        with self.assertRaises(ValueError):
            walk(False, 0, lambda: False, lambda x: x, budget=4)
        with self.assertRaises(ValueError):
            walk(False, False, lambda: 1, lambda x: x, budget=4)
        self.assertEqual(walk(False, False, lambda: False, bool, budget=2), (False, 0))
        self.assertEqual(walk(False, False, lambda: False, bool, budget=4), (False, 1))
        self.assertEqual(walk(False, False, lambda: False, bool, budget=8), (False, 3))
        self.assertEqual(walk(False, False, lambda: True, bool, budget=8), (True, 2))

    def test_compact_pool_every_rng_branch_matches_full_walk_kernel(self):
        class NeedChoice(Exception):
            pass

        def choices(seq, classes, prefix=()):
            cursor = iter(seq[2:])
            used = 0

            def randbelow(k):
                nonlocal used
                if used == len(prefix):
                    raise NeedChoice(k)
                value = prefix[used]
                used += 1
                return value

            try:
                value, calls = pool(
                    classes[seq[0]],
                    seq[1],
                    cursor.__next__,
                    classes.__getitem__,
                    randbelow,
                    budget=4,
                )
                self.assertEqual(calls, 2)
                return {value: F(1)}
            except NeedChoice as request:
                k = request.args[0]
                total = defaultdict(F)
                for choice in range(k):
                    for value, mass in choices(seq, classes, (*prefix, choice)).items():
                        total[value] += mass / k
                return total

        for weights in ((1, 2, 3), (1, 0, 2)):
            for classes in itertools.product((False, True), repeat=3):
                probs, expected, _ = payload_law(weights, classes, 4)
                actual = defaultdict(F)
                for seq in itertools.product(range(3), repeat=4):
                    mass = math.prod(probs[i] for i in seq)
                    for value, conditional in choices(seq, classes).items():
                        actual[seq[0], value] += mass * conditional
                self.assertEqual(dict(actual), dict(expected))

    def test_compact_pool_validation_and_constant_class_original_aliases(self):
        for budget in (True, 1, 4.0):
            with self.assertRaises(ValueError):
                pool(False, 0, lambda: 0, bool, lambda k: 0, budget=budget)
        with self.assertRaises(ValueError):
            pool(False, 0, lambda: 0, lambda x: x, lambda k: 0, budget=4)
        value, calls = pool(
            False, "original", lambda: "alias", lambda x: False, lambda k: 0, budget=8
        )
        self.assertEqual(value, "alias")
        self.assertEqual(calls, 6)


if __name__ == "__main__":
    unittest.main()
