"""Independent finite law checks, not model benchmarks or a novelty proof."""

import importlib
import itertools
import math
import unittest
from collections import Counter
from fractions import Fraction as F

reference = importlib.import_module("attempts.38-empirical-pool-coupling.work.couple")
observers = importlib.import_module("attempts.38-empirical-pool-coupling.work.observers")


def law(weights, keys, budgeted=False):
    joint, work = Counter(), 0
    coins = tuple(itertools.product(range(2), range(6))) if budgeted else ((0, u) for u in range(6))
    coins = tuple(coins)
    denominator = len(coins) * sum(weights) ** 4
    for tape in itertools.product(range(len(weights)), repeat=4):
        mass = math.prod(weights[i] for i in tape)
        for outer, inner in coins:
            seen = []
            original = iter(tape)
            random = iter((outer, inner) if budgeted else (inner,))

            def draw(original=original, seen=seen):
                item = next(original)
                seen.append(item)
                return item

            sampler = reference.pair_mean_three if budgeted else reference.pair
            x, y, calls = sampler(
                draw, lambda i, keys=keys: keys[i], lambda n, r=random: next(r) % n
            )
            assert x == tape[0] and calls == len(seen)
            joint[x, y] += mass
            work += mass * calls
    return {pair: F(mass, denominator) for pair, mass in joint.items()}, F(work, denominator)


def partitions(n):
    def extend(prefix):
        if len(prefix) == n:
            yield tuple(prefix)
        else:
            for label in range(max(prefix) + 2):
                yield from extend([*prefix, label])

    yield from extend([0])


class SemanticCoarseningTests(unittest.TestCase):
    def test_all_four_class_partitions_verifiers_and_complete_call_cost(self):
        all_partitions = tuple(partitions(4))
        self.assertEqual(len(all_partitions), 15)
        for weights, budgeted in itertools.product(((1, 1, 1, 1), (1, 2, 3, 5)), (False, True)):
            p = tuple(F(w, sum(weights)) for w in weights)
            fine, original_work = law(weights, tuple(range(4)), budgeted)
            for keys in all_partitions:
                coarse, work = law(weights, keys, budgeted)
                self.assertLessEqual(work, original_work)
                if len(set(keys)) < 4:
                    self.assertLess(work, original_work)
                for i in range(4):
                    self.assertEqual(sum(v for (x, _), v in coarse.items() if x == i), p[i])
                    self.assertEqual(sum(v for (_, y), v in coarse.items() if y == i), p[i])
                for mask in range(2 ** len(set(keys))):
                    f = tuple((mask >> k) & 1 for k in keys)
                    a = sum(p[i] * f[i] for i in range(4))
                    fine_both = sum(v * f[x] * f[y] for (x, y), v in fine.items())
                    coarse_both = sum(v * f[x] * f[y] for (x, y), v in coarse.items())
                    self.assertLessEqual(coarse_both, fine_both)
                    c_a = sum(p[i] ** 2 for i in range(4) if f[i])
                    c_b = sum(p[i] ** 2 for i in range(4) if not f[i])
                    gain = (1 - a) ** 2 * c_a + a**2 * c_b - c_a * c_b
                    self.assertEqual(a**2 - fine_both, gain / (2 if budgeted else 1))

    def test_every_threshold_of_common_semantic_scores_and_variance_counterexample(self):
        fine, _ = law((1, 1, 1, 1), (0, 1, 2, 3))
        coarse, _ = law((1, 1, 1, 1), (0, 0, 1, 2))
        scores = (0, 0, 1, -1)
        for threshold in (-2, -1, 0, 1, 2):
            before = sum(v for (x, y), v in fine.items() if max(scores[x], scores[y]) > threshold)
            after = sum(v for (x, y), v in coarse.items() if max(scores[x], scores[y]) > threshold)
            self.assertGreaterEqual(after, before)

        def covariance(joint):
            return sum(v * scores[x] * scores[y] for (x, y), v in joint.items())

        self.assertEqual(covariance(fine), -F(3, 32))
        self.assertEqual(covariance(coarse), -F(5, 64))
        self.assertEqual((covariance(coarse) - covariance(fine)) / 2, F(1, 128))

    def test_interpreter_observation_has_sound_aliases_errors_and_length_guard(self):
        def payload(text, status="COMPLETE"):
            return {"status": status, "text": text}

        base = '{"op":"add","args":[1,2]}'
        alias = '{ "args": [1e0,2.00], "op": "add" }'
        same_value = '{"op":"sub","args":[5,2]}'
        self.assertEqual(observers.fine(payload(base)), observers.fine(payload(alias)))
        self.assertEqual(observers.semantic(payload(base)), "VALUE:3")
        self.assertEqual(
            observers.semantic(payload(alias)), observers.semantic(payload(same_value))
        )
        self.assertNotEqual(observers.fine(payload(base)), observers.fine(payload(same_value)))
        too_long = payload(" " * 65536 + base)
        self.assertNotEqual(observers.fine(too_long), observers.fine(payload(base)))
        self.assertEqual(observers.semantic(too_long), "FAIL")
        for text in (
            "NaN",
            "null",
            '{"op":"div","args":[1,0]}',
            '{"op":"add","op":"mul","args":[1,2]}',
            '{"op":"add","args":[1e999999,2]}',
        ):
            self.assertEqual(observers.semantic(payload(text)), "FAIL")
        for status in ("ERROR", "INCOMPLETE"):
            self.assertEqual(observers.semantic(payload(base, status)), "FAIL")
        # Same typed AST must give the same observation even at an admitted
        # resource boundary; the long-text counterexample above needs its guard.
        corpus = (base, alias, same_value, "null", " null ", "NaN", "1e999999")
        mapped = {}
        for text in corpus:
            item = payload(text)
            key, value = observers.fine(item), observers.semantic(item)
            self.assertEqual(mapped.setdefault(key, value), value)


if __name__ == "__main__":
    unittest.main()
