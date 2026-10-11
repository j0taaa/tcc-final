"""Independent rational payload enumeration, not a model-performance benchmark."""

import importlib
import itertools
import math
import unittest
from collections import Counter
from fractions import Fraction as F

reference = importlib.import_module("attempts.37-canonical-outcome-coupling.work.couple")


def fixed_bits(mask):
    offset = 0

    def take(width):
        nonlocal offset
        value = (mask >> offset) & ((1 << width) - 1)
        offset += width
        return value

    return take


def payload_law(weights, cap, mask):
    # Enumerate raw IDs, including aliases/failures, BEFORE any classification.
    keys = (b"", b"", b"\x00", b"\x01")
    payloads = tuple({"id": i, "key": k} for i, k in enumerate(keys))
    joint, work = Counter(), 0
    total = sum(weights) ** cap
    for tape in itertools.product(range(4), repeat=cap):
        weight = math.prod(weights[i] for i in tape)
        if not weight:
            continue
        items = iter(payloads[i] for i in tape)
        x, y, used = reference.pair(
            items.__next__, lambda v: v["key"], hash_bits=fixed_bits(mask), max_draws=cap
        )
        assert x is payloads[tape[0]], "first payload was not retained literally"
        joint[x["id"], y["id"]] += weight
        work += used * weight
    return {ij: F(n, total) for ij, n in joint.items()}, F(work, total)


class CanonicalOutcomeCouplingTests(unittest.TestCase):
    def test_hash_balance_aliases_and_lazy_coefficients(self):
        keys = (b"", b"\x00", b"\x01")
        disagreement = Counter()
        for mask in range(512):
            h = reference.LinearClass(fixed_bits(mask))
            # A new longer key must not change a previous key's class.
            original = h(keys[0])
            values = [h(k) for k in keys]
            self.assertEqual(h(keys[0]), original)
            self.assertEqual(h(b"\x00"), values[1])
            for i, j in itertools.combinations(range(3), 2):
                disagreement[i, j] += values[i] != values[j]
        self.assertEqual(set(disagreement.values()), {256})
        with self.assertRaises(TypeError):
            reference.LinearClass(fixed_bits(0))("not bytes")

    def test_full_payload_law_with_alias_and_failure(self):
        # Only bits0 and8 affect these three canonical keys. All four equally
        # likely class maps occur, including a dependent third hash bit.
        weights = (3, 2, 5, 2)
        probabilities = tuple(F(w, sum(weights)) for w in weights)
        keys = (b"", b"", b"\x00", b"\x01")
        for cap in (4, 6):
            averaged = Counter()
            for mask in (0, 1, 256, 257):
                joint, work = payload_law(weights, cap, mask)
                h = reference.LinearClass(fixed_bits(mask))
                classes = tuple(h(k) for k in keys)
                masses = tuple(
                    sum(p for p, c in zip(probabilities, classes, strict=True) if c == b)
                    for b in (False, True)
                )
                z = masses[0] * masses[1]
                delta = sum(z**j for j in range(2, cap // 2 + 1))
                self.assertEqual(work, 3 - z ** (cap // 2 - 1))
                for i, j in itertools.product(range(4), repeat=2):
                    ci, cj = classes[i], classes[j]
                    expected = probabilities[i] * probabilities[j]
                    correction = delta * expected / (masses[ci] * masses[cj])
                    expected += correction if ci != cj else -correction
                    self.assertEqual(joint.get((i, j), 0), expected)
                    averaged[i, j] += joint.get((i, j), 0) / 4
            for i, p in enumerate(probabilities):
                self.assertEqual(sum(averaged[i, j] for j in range(4)), p)
                self.assertEqual(sum(averaged[j, i] for j in range(4)), p)
            # A competent probability-aware control: actual half-circle
            # quantile coupling on the canonical outcomes, retaining raw IDs.
            tickets = tuple(i for i, w in enumerate(weights) for _ in range(w))
            optimal_collision = F(
                sum(
                    keys[i] == keys[tickets[(t + len(tickets) // 2) % len(tickets)]]
                    for t, i in enumerate(tickets)
                ),
                len(tickets),
            )
            canonical = tuple(
                sum(p for p, k in zip(probabilities, keys, strict=True) if k == u)
                for u in (b"", b"\x00", b"\x01")
            )
            self.assertEqual(optimal_collision, max(0, 2 * max(canonical) - 1))
            iid_collision = sum(p * p for p in canonical)
            collision = sum(v for (i, j), v in averaged.items() if keys[i] == keys[j])
            retained = 1 - F(1, 4) ** (cap // 2 - 1)
            self.assertGreaterEqual(
                iid_collision - collision,
                retained * (iid_collision - optimal_collision) / 13,
            )
            for correct in (b"", b"\x00", b"\x01"):
                success = tuple(k == correct for k in keys)
                a = sum(p for p, ok in zip(probabilities, success, strict=True) if ok)
                both = sum(v for (i, j), v in averaged.items() if success[i] and success[j])
                gain = a * a - both
                retained = 1 - F(1, 4) ** (cap // 2 - 1)
                self.assertGreaterEqual(gain, retained * a**2 * (1 - a) ** 2 / (3 + a**2))
            # Any verifier, including subsets that split a canonical alias.
            for subset in itertools.product((False, True), repeat=4):
                a = sum(p for p, ok in zip(probabilities, subset, strict=True) if ok)
                both = sum(v for (i, j), v in averaged.items() if subset[i] and subset[j])
                self.assertLessEqual(both, a * a)

    def test_cap_retains_original_second_and_refuses_invalid_budget(self):
        keys = (b"", b"") + (b"\x00", b"") * 5
        payloads = tuple({"id": i, "key": k} for i, k in enumerate(keys))
        for cap in (4, 6, 12):
            tape = iter(payloads[:cap])
            x, y, used = reference.pair(
                tape.__next__, lambda v: v["key"], hash_bits=fixed_bits(1), max_draws=cap
            )
            self.assertIs(x, payloads[0])
            self.assertIs(y, payloads[1])
            self.assertEqual(used, cap)
        for cap in (0, 2, 3, 5, True, 4.0):
            with self.assertRaises(ValueError):
                reference.pair(lambda: None, lambda _: b"", hash_bits=fixed_bits(0), max_draws=cap)

    def test_cost_and_iid3_objection_at_rational_parameters(self):
        # Algebra checks are correctness evidence, not observations of a model.
        for denominator in range(2, 41):
            for numerator in range(1, denominator):
                a = F(numerator, denominator)
                b = 1 - a
                lower = a**2 * b**2 / (3 + a**2)
                self.assertGreaterEqual(lower / min(a * a, b * b), F(1, 13))
                upper = a**2 * b**2 / (2 * (1 - a + a**2))
                self.assertLess(upper, a * b**2)
        a = F(1, 2)
        beta = a * (1 - a) / (3 + a * a)
        self.assertEqual((1 - 3 * beta) / (2 * beta), 5)


if __name__ == "__main__":
    unittest.main()
