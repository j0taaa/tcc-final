"""Independent finite path/dual/AM-GM oracles; all neural heads are FAKE."""

import itertools
import json
import unittest
from collections import defaultdict
from fractions import Fraction as F
from functools import lru_cache
from math import lcm, prod

from .prefix_anchor import PrefixAnchor
from .test_numeric_json import independent_accepts
from .test_prefix_anchor import Dual, joint_law, language, make, prefixes
from .visible_elbo import (
    count_flow,
    gamma,
    reference_actions,
    reference_paths,
    reference_state_measure,
)


class World:
    def __init__(self, n, direction):
        self.n, self.direction = n, direction
        self.states = {}
        self.scores = {}
        self.output_cache = {}

    def terminal(self, fixed):
        eos = [i for i, v in fixed.items() if v == 5]
        if eos and max(fixed) == eos[0] and len(fixed) == eos[0] + 1:
            word = tuple(fixed[i] for i in range(len(fixed)))
            assert independent_accepts(language(), word)
            return word
        return None

    def kernel(self, key):
        if key in self.states:
            return self.states[key]
        fixed = dict(key)
        base, _ = make(self.n, fixed, context=True)
        gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in base.rows)
        policy = PrefixAnchor(language(), base.rows, gates, base.u, fixed)
        aa = tuple(F((i + 1) * (1 + len(fixed))) for i in range(self.n))
        rr = tuple(F(self.direction * (i + 1 + len(fixed))) for i in range(self.n))
        dg = tuple(tuple(Dual(g, g * (1 - g) * aa[i]) for g in row) for i, row in enumerate(gates))
        du = tuple(Dual(u, u * rr[i]) for i, u in enumerate(base.u))
        direct = joint_law(prefixes(language(), self.n, fixed), base.rows, dg, du, fixed)
        masses = defaultdict(lambda: Dual(F()))
        for (_, _, action), p in direct.items():
            masses[action] += p
        for action, probability in masses.items():
            p, _, hh, r = policy.action_statistics(action)
            score = sum((sum(row, F()) * aa[i] for i, row in enumerate(hh)), F())
            score += sum((r[i] * rr[i] for i in range(self.n)), F())
            assert p == probability.value and score == probability.derivative / p
            self.scores[key, action] = score
        assert sum((p.value for p in masses.values()), F()) == 1
        assert sum((p.derivative for p in masses.values()), F()) == 0
        self.states[key] = dict(masses)
        return self.states[key]

    def outputs(self, key=()):
        if key in self.output_cache:
            return self.output_cache[key]
        fixed = dict(key)
        word = self.terminal(fixed)
        if word is not None:
            return {word: Dual(F(1))}
        out = defaultdict(lambda: Dual(F()))
        for action, probability in self.kernel(key).items():
            following = tuple(sorted({**fixed, **dict(action)}.items()))
            for word, suffix in self.outputs(following).items():
                out[word] += probability * suffix
        self.output_cache[key] = dict(out)
        return self.output_cache[key]


@lru_cache(None)
def worlds():
    result = [World(2, 0), World(3, 0), World(3, 1)]
    for world in result:
        world.outputs()
    return result


def path_terms(world, target):
    out = []
    for path, q in reference_paths(target).items():
        fixed, probability, score, steps = {}, Dual(F(1)), F(), []
        for action in path:
            key = tuple(sorted(fixed.items()))
            p = world.kernel(key)[action]
            s = world.scores[key, action]
            probability *= p
            score += s
            steps.append((key, action, s))
            fixed.update(action)
        assert world.terminal(fixed) == target
        assert probability.derivative / probability.value == score
        out.append((q, probability, score, steps))
    return out


class VisibleELBOTests(unittest.TestCase):
    def test_reference_actions_against_independent_anchor_coins(self):
        checks = 0
        for m in range(1, 8):
            target = tuple(range(m))
            direct = defaultdict(F)
            g = gamma(m)
            for anchor in range(m):
                others = [i for i in range(m) if i != anchor]
                for coins in itertools.product((False, True), repeat=len(others)):
                    selected = sorted(
                        [anchor, *(i for i, b in zip(others, coins, strict=True) if b)]
                    )
                    probability = F(1, m) * prod(g if b else 1 - g for b in coins)
                    action = tuple((i, target[i]) for i in selected)
                    direct[action] += probability
            self.assertEqual(dict(direct), reference_actions(target, {}))
            self.assertEqual(sum(direct.values(), F()), 1)
            checks += len(direct)
        print(json.dumps({"reference_count_laws": 7, "original_actions": checks}))

    def test_full_target_path_support_exact_bound_and_strict_variational_gap(self):
        targets, paths, strict = 0, 0, 0
        for world in worlds():
            outputs = world.outputs()
            self.assertEqual(sum((p.value for p in outputs.values()), F()), 1)
            self.assertEqual(sum((p.derivative for p in outputs.values()), F()), 0)
            for target, total in outputs.items():
                terms = path_terms(world, target)
                self.assertEqual(sum((q for q, _, _, _ in terms), F()), 1)
                self.assertEqual(sum((p.value for _, p, _, _ in terms), F()), total.value)
                self.assertEqual(sum((p.derivative for _, p, _, _ in terms), F()), total.derivative)
                denominator = lcm(*(q.denominator for q, _, _, _ in terms))
                powered_bound = prod((p.value / q) ** int(denominator * q) for q, p, _, _ in terms)
                self.assertLessEqual(powered_bound, total.value**denominator)
                differs = any(q * total.value != p.value for q, p, _, _ in terms)
                self.assertEqual(powered_bound < total.value**denominator, differs)
                strict += int(differs)
                targets += 1
                paths += len(terms)
        self.assertGreater(strict, 0)
        print(json.dumps({"full_target_laws": targets, "reference_paths": paths, "strict": strict}))

    def test_bound_gradient_three_time_estimators_and_not_exact_mle(self):
        checks, not_mle, wrong_factor = 0, False, False
        for world in worlds():
            for target, total in world.outputs().items():
                terms = path_terms(world, target)
                whole = sum((q * score for q, _, score, _ in terms), F())
                fixed_time = sum(
                    (
                        q * F(1, len(target)) * len(target) * s
                        for q, _, _, ss in terms
                        for _, _, s in ss
                    ),
                    F(),
                )
                active_time = sum(
                    (q * F(1, len(ss)) * len(ss) * s for q, _, _, ss in terms for _, _, s in ss),
                    F(),
                )
                expected, measure = reference_state_measure(target)
                occupancy = F()
                for key, mass in measure.items():
                    world.kernel(key)
                    for action, probability in reference_actions(target, dict(key)).items():
                        occupancy += expected * mass * probability * world.scores[key, action]
                self.assertEqual(whole, fixed_time)
                self.assertEqual(whole, active_time)
                self.assertEqual(whole, occupancy)
                not_mle |= whole != total.derivative / total.value
                wrong = sum(
                    (q * F(len(target), len(ss)) * s for q, _, _, ss in terms for _, _, s in ss),
                    F(),
                )
                wrong_factor |= wrong != whole
                checks += 1
        self.assertTrue(not_mle, "a fixed reference bound is not exact target MLE")
        self.assertTrue(wrong_factor, "discarding absorbing zeros needs corrected weights")
        print(json.dumps({"exact_gradient_time_checks": checks, "new_model_forwards": 0}))

    def test_occupancy_against_full_reference_paths_aliases_eos_and_refusals(self):
        checks = 0
        for target in ((0, 5), (0, 3, 5), (0, 4, 5), (2, 0, 3, 5)):
            self.assertTrue(independent_accepts(language(), target))
            visits = defaultdict(F)
            paths = reference_paths(target)
            for path, q in paths.items():
                fixed = {}
                for action in path:
                    visits[tuple(sorted(fixed.items()))] += q
                    self.assertTrue(all(target[i] == v for i, v in action))
                    fixed.update(action)
                self.assertEqual(fixed, dict(enumerate(target)))
            expected, measure = reference_state_measure(target)
            self.assertEqual(sum(visits.values(), F()), expected)
            self.assertEqual({k: p / expected for k, p in visits.items()}, measure)
            flow, _ = count_flow(len(target))
            self.assertEqual(flow[0], 1)
            self.assertEqual(sum(measure.values(), F()), 1)
            checks += len(visits)
        self.assertNotEqual(reference_paths((0, 3, 5)), reference_paths((0, 4, 5)))
        for target, fixed in (((), {}), ((0, 5), {0: 1}), ((0, 5), {2: 5})):
            with self.assertRaises(ValueError):
                reference_actions(target, fixed)
        with self.assertRaises(ValueError):
            reference_paths(tuple(range(5)))
        with self.assertRaises(ValueError):
            count_flow(0)
        print(json.dumps({"exact_reference_occupancy_states": checks, "parameter_updates": 0}))


if __name__ == "__main__":
    unittest.main()
