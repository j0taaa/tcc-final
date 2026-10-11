"""Independent exact laws/controls; constructed inputs are not neural benchmarks."""

import importlib
import itertools
import math
import unittest
from collections import Counter
from fractions import Fraction as F

reference = importlib.import_module("attempts.38-empirical-pool-coupling.work.couple")
KEYS = (b"json-A", b"json-A", b"json-B", b"json-C", b"FAIL")


def enumerated_law(weights):
    joint, calls = Counter(), 0
    total = 6 * sum(weights) ** 4
    for tape in itertools.product(range(len(weights)), repeat=4):
        weight = math.prod(weights[i] for i in tape)
        if not weight:
            continue
        for uniform in range(6):
            # New object per iid occurrence: retain literal first, never its index.
            payloads = [{"id": i, "key": KEYS[i]} for i in tape]
            iterator = iter(payloads)
            seen = []

            def draw(iterator=iterator, seen=seen):
                item = next(iterator)
                seen.append(item)
                return item

            x, y, used = reference.pair(draw, lambda v: v["key"], lambda n, u=uniform: u % n)
            assert x is payloads[0]
            assert y is not x and any(y is v for v in seen[1:])
            assert used == len(seen)
            joint[x["id"], y["id"]] += weight
            calls += used * weight
    return {ij: F(n, total) for ij, n in joint.items()}, F(calls, total)


def grouped_rank_rotation(weights):
    # Independent classical control: randomly order empirical class blocks,
    # uniformly rank the first occurrence within its block, rotate by two.
    joint = Counter()
    total = sum(weights) ** 4
    for tape in itertools.product(range(len(weights)), repeat=4):
        weight = math.prod(weights[i] for i in tape)
        if not weight:
            continue
        counts = Counter(KEYS[i] for i in tape)
        first = KEYS[tape[0]]
        for ordering in itertools.permutations(counts):
            ranks = tuple(k for k in ordering for _ in range(counts[k]))
            for rank in (r for r, k in enumerate(ranks) if k == first):
                other = ranks[(rank + 2) % 4]
                joint[first, other] += F(
                    weight, total * math.factorial(len(counts)) * counts[first]
                )
    return joint


class EmpiricalPoolCouplingTests(unittest.TestCase):
    def test_exact_reduction_to_classical_grouped_rank_rotation(self):
        # This equality credits the empirical-rank construction as a PRIOR,
        # and tests a genuinely different implementation of the same joint law.
        weights = (3, 2, 4, 2, 1)
        law, calls = enumerated_law(weights)
        canonical = Counter()
        for (i, j), value in law.items():
            canonical[KEYS[i], KEYS[j]] += value
        self.assertEqual(dict(canonical), dict(grouped_rank_rotation(weights)))
        self.assertLess(calls, 4)

    def test_exact_payload_law_and_pointwise_cost_with_aliases_failures(self):
        for weights in ((3, 2, 4, 2, 1), (1, 0, 1, 1, 1), (1, 0, 1, 0, 0), (9, 1, 0, 0, 0)):
            p = tuple(F(w, sum(weights)) for w in weights)
            mass = {k: sum(p[i] for i in range(5) if KEYS[i] == k) for k in set(KEYS)}
            collision = sum(v**2 for v in mass.values())
            cubic = sum(v**3 for v in mass.values())
            law, calls = enumerated_law(weights)
            self.assertEqual(calls, 4 - 2 * collision + cubic)
            for i, j in itertools.product(range(5), repeat=2):
                a, b = mass[KEYS[i]], mass[KEYS[j]]
                if not a or not b:
                    expected = 0
                elif KEYS[i] == KEYS[j]:
                    expected = (a**2 - a**2 * (1 - a) ** 2) * p[i] * p[j] / (a * b)
                else:
                    expected = p[i] * p[j] * (1 + a + b - a * b - collision)
                self.assertEqual(law.get((i, j), 0), expected)
            for i in range(5):
                self.assertEqual(sum(law.get((i, j), 0) for j in range(5)), p[i])
                self.assertEqual(sum(law.get((j, i), 0) for j in range(5)), p[i])
            gain = sum(v**2 * (1 - v) ** 2 for v in mass.values())
            informed_gain = collision - max(0, 2 * max(mass.values()) - 1)
            self.assertGreaterEqual(gain, informed_gain / 4)
            # Each canonical indicator attains the classical cap-four clipping bound.
            for k, a in mass.items():
                diagonal = sum(v for (i, j), v in law.items() if KEYS[i] == KEYS[j] == k)
                self.assertEqual(diagonal, 2 * a**3 * (1 - a) + a**4)

    def test_all_raw_verifiers_and_nonmonotone_scores(self):
        weights = (3, 2, 4, 2, 1)
        p = tuple(F(w, sum(weights)) for w in weights)
        mass = {k: sum(p[i] for i in range(5) if KEYS[i] == k) for k in set(KEYS)}
        collision = sum(v**2 for v in mass.values())
        law, _ = enumerated_law(weights)
        scores = [tuple((mask >> i) & 1 for i in range(5)) for mask in range(32)]
        scores += [(3, -2, 1, 7, 0), (2, -3, 9, -5, 4)]
        for f in scores:
            mu = sum(p[i] * f[i] for i in range(5))
            centered = {
                k: sum(p[i] * f[i] for i in range(5) if KEYS[i] == k) / a - mu
                for k, a in mass.items()
            }
            covariance = sum(v * f[i] * f[j] for (i, j), v in law.items()) - mu**2
            expected = (
                -(1 - collision) * sum(mass[k] ** 2 * g**2 for k, g in centered.items())
                - sum(mass[k] ** 2 * g for k, g in centered.items()) ** 2
            )
            self.assertEqual(covariance, expected)
            self.assertLessEqual(covariance, 0)

    def test_probability_aware_rotation_is_kept_as_a_stronger_diversity_control(self):
        # This classical known-law control reaches the full atom diagonal bound,
        # whereas cap4 only reaches its declared fraction. It can have positive
        # covariance for a nonmonotone predicate; do not call it weak or invalid.
        law, _ = enumerated_law((1, 0, 1, 1, 1))
        categories = (0, 2, 3, 4)
        informed = Counter(
            {(i, categories[(t + 2) % 4]): F(1, 4) for t, i in enumerate(categories)}
        )
        self.assertEqual(sum(v for (i, j), v in informed.items() if i == j), 0)
        self.assertGreater(sum(v for (i, j), v in law.items() if i == j), 0)
        selected = {0, 3}
        informed_both = sum(v for (i, j), v in informed.items() if i in selected and j in selected)
        candidate_both = sum(v for (i, j), v in law.items() if i in selected and j in selected)
        self.assertEqual(informed_both, F(1, 2))
        self.assertLessEqual(candidate_both, F(1, 4))

    def test_known_uniform_derangement_is_stronger_for_every_score(self):
        # Informed controls also can combine zero collisions with covariance<=0
        # for EVERY predicate, using two outputs and no auxiliary iid calls.
        law, _ = enumerated_law((1, 0, 1, 1, 1))
        categories = (0, 2, 3, 4)
        informed = {(i, j): F(1, 12) for i, j in itertools.permutations(categories, 2)}
        for mask in range(16):
            f = {i: (mask >> t) & 1 for t, i in enumerate(categories)}
            mu = F(sum(f.values()), 4)
            variance = mu * (1 - mu)
            covariance = sum(v * f[i] * f[j] for (i, j), v in informed.items()) - mu**2
            candidate_covariance = sum(v * f[i] * f[j] for (i, j), v in law.items()) - mu**2
            self.assertEqual(covariance, -variance / 3)
            self.assertLessEqual(covariance, candidate_covariance)


if __name__ == "__main__":
    unittest.main()
