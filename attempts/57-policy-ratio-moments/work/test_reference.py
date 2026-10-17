"""Enumerate original JSON IDs/anchors/masks independently of the inside circuit."""

import itertools
import json
import unittest
from collections import defaultdict
from fractions import Fraction as F
from functools import lru_cache
from math import prod

from .reference import readout

EMISSIONS = ("0", "0", "1", "[", "]", "", "<EOS>")
EOS = 6


def valid(body):
    try:
        obj = json.loads("".join(EMISSIONS[v] for v in body))
    except (ValueError, TypeError):
        return False
    while isinstance(obj, list) and len(obj) == 1:
        obj = obj[0]
    return type(obj) is int and obj in (0, 1)


@lru_cache(None)
def words(n, fixed):
    fixed = dict(fixed)
    return tuple(
        (*body, EOS)
        for t in range(1, n + 1)
        for body in itertools.product(range(EOS), repeat=t - 1)
        if all(i < t and (*body, EOS)[i] == v for i, v in fixed.items()) and valid(body)
    )


def parameters(n, salt=0, zero=False):
    raw = tuple(
        tuple(F(1 + (3 * i + v + salt) % 7) if not (zero and v == 1) else F() for v in range(7))
        for i in range(n)
    )
    rows = tuple(tuple(v / sum(row, F()) for v in row) for row in raw)
    gates = tuple(
        tuple(tuple(F(1 + (i + 2 * v + salt + k) % 5, 6) for v in range(7)) for i in range(n))
        for k in range(2)
    )
    anchors = tuple(tuple(F(1 + (i + 2 * k + salt) % 4) for i in range(n)) for k in range(2))
    return rows, gates, anchors


@lru_cache(None)
def joint(n, salt, zero, fixed_tuple, k):
    rows, gates, anchors = parameters(n, salt, zero)
    fixed, raw = dict(fixed_tuple), {}
    for word in words(n, fixed_tuple):
        weight = prod(rows[i][v] for i, v in enumerate(word) if i not in fixed)
        if weight:
            raw[word] = weight
    z = sum(raw.values(), F())
    out = {}
    for word, weight in raw.items():
        active = tuple(i for i in range(len(word)) if i not in fixed)
        if not active:
            continue
        for anchor in active:
            others = tuple(i for i in active if i != anchor)
            for bits in itertools.product((0, 1), repeat=len(others)):
                selected = {anchor, *(i for i, b in zip(others, bits, strict=True) if b)}
                action = tuple((i, word[i]) for i in sorted(selected))
                out[word, anchor, action] = (
                    weight
                    / z
                    * anchors[k][anchor]
                    / sum((anchors[k][i] for i in active), F())
                    * prod(
                        gates[k][i][word[i]] if b else 1 - gates[k][i][word[i]]
                        for i, b in zip(others, bits, strict=True)
                    )
                )
    return out


def grouped(law, key):
    out = defaultdict(F)
    for latent, mass in law.items():
        out[key(latent)] += mass
    return out


KEYS = {
    "full": lambda y: (y[2], y[0], y[1]),
    "anchor": lambda y: (y[2], y[0]),
    "class": lambda y: (y[2], tuple(EMISSIONS[v] for v in y[0]), y[1]),
    "combined": lambda y: (y[2], tuple(EMISSIONS[v] for v in y[0])),
    "length": lambda y: (y[2], len(y[0])),
    "visible": lambda y: (y[2],),
}


class PolicyRatioTests(unittest.TestCase):
    def test_every_action_against_independent_full_joint(self):
        checks, actions = 0, 0
        cases = ((4, (), False), (4, ((2, 0),), False), (4, ((2, EOS),), False), (3, (), True))
        for n, fixed_tuple, zero in cases:
            salt = len(fixed_tuple)
            rows, gates, anchors = parameters(n, salt, zero)
            laws = [joint(n, salt, zero, fixed_tuple, k) for k in range(2)]
            self.assertEqual(sum(laws[0].values(), F()), 1)
            self.assertEqual(laws[0].keys(), laws[1].keys())
            observed = [grouped(p, KEYS["visible"]) for p in laws]
            grouped_laws = {name: [grouped(p, key) for p in laws] for name, key in KEYS.items()}
            for (action,), mass0 in observed[0].items():
                r = readout(rows, EMISSIONS, EOS, gates, anchors, dict(fixed_tuple), dict(action))
                self.assertEqual(r["masses"], (mass0, observed[1][action,]))
                self.assertEqual(r["visible"], observed[1][action,] / mass0)
                for name, (g0, g1) in grouped_laws.items():
                    exact = sum(
                        (g1[key] ** 2 / p for key, p in g0.items() if key[0] == action), F()
                    )
                    self.assertEqual(r["second"][name], exact / mass0)
                    checks += 1
                m = r["second"]
                for lower, upper in (
                    ("visible", "length"),
                    ("visible", "combined"),
                    ("combined", "class"),
                    ("combined", "anchor"),
                    ("class", "full"),
                    ("anchor", "full"),
                ):
                    self.assertLessEqual(m[lower], m[upper])
                actions += 1
        print(json.dumps({"local_actions": actions, "exact_second_moment_checks": checks}))

    def test_unchanged_policy_and_rejected_zero_mass_or_support(self):
        rows, gates, anchors = parameters(3)
        result = readout(rows, EMISSIONS, EOS, (gates[0],) * 2, (anchors[0],) * 2, {}, {0: 0})
        self.assertTrue(all(v == 1 for v in result["second"].values()))
        for action in ({}, {0: 4}, {0: 99}):
            with self.assertRaises(ValueError):
                readout(rows, EMISSIONS, EOS, gates, anchors, {}, action)
        with self.assertRaises(ValueError):
            readout(rows, EMISSIONS, EOS, gates, anchors, {0: 0}, {0: 0})
        bad = tuple(tuple(F() for _ in row) for row in gates[0])
        with self.assertRaises(ValueError):
            readout(rows, EMISSIONS, EOS, (bad, gates[1]), anchors, {}, {0: 0})

    def test_adaptive_complete_path_product_and_reward(self):
        # Enumerate every full latent path, with heads AND planners changing
        # with the visible original-ID state. No formula supplies those masses.
        n, path_laws = 3, [defaultdict(F), defaultdict(F)]

        def walk(k, fixed_tuple, visible_path, latent_path, mass):
            fixed = dict(fixed_tuple)
            if EOS in fixed.values() and all(i in fixed for i in range(max(fixed) + 1)):
                path_laws[k][visible_path, latent_path] += mass
                return
            salt = sum(i + v + 1 for i, v in fixed_tuple)
            for (word, anchor, action), p in joint(n, salt, False, fixed_tuple, k).items():
                new = tuple(sorted({**fixed, **dict(action)}.items()))
                self.assertGreater(len(new), len(fixed))
                walk(k, new, (*visible_path, action), (*latent_path, (word, anchor)), mass * p)

        for k in range(2):
            walk(k, (), (), (), F(1))
            self.assertEqual(sum(path_laws[k].values(), F()), 1)
        self.assertEqual(path_laws[0].keys(), path_laws[1].keys())
        observed = [defaultdict(F), defaultdict(F)]
        second = defaultdict(F)
        for key, p0 in path_laws[0].items():
            second[key[0]] += path_laws[1][key] ** 2 / p0
        for k in range(2):
            for (path, _), mass in path_laws[k].items():
                observed[k][path] += mass
        expected_target, reweighted = F(), F()
        for path, mass0 in observed[0].items():
            fixed, mean, moment = {}, F(1), F(1)
            for action in path:
                salt = sum(i + v + 1 for i, v in fixed.items())
                rows, gates, anchors = parameters(n, salt)
                r = readout(rows, EMISSIONS, EOS, gates, anchors, fixed, dict(action))
                mean *= r["visible"]
                moment *= r["second"]["full"]
                fixed.update(action)
            self.assertEqual(mean, observed[1][path] / mass0)
            self.assertEqual(moment, second[path] / mass0)
            # Literal first original ID (including epsilon) is observable.
            reward = F(fixed[0] == 2)
            expected_target += observed[1][path] * reward
            reweighted += mass0 * mean * reward
        self.assertEqual(reweighted, expected_target)
        print(
            json.dumps({"visible_paths": len(observed[0]), "full_latent_paths": len(path_laws[0])})
        )

    def test_changed_hard_preimage_can_break_augmented_is(self):
        # Uniform bit proposal; policy0 exposes x, policy1 exposes1-x.
        # Visible laws agree but their augmented supports are disjoint.
        behavior = {(0, 0): F(1, 2), (1, 1): F(1, 2)}
        target = {(0, 1): F(1, 2), (1, 0): F(1, 2)}
        naive_mean = sum((p * target.get(y, F()) / p for y, p in behavior.items()), F())
        self.assertEqual(naive_mean, 0)
        self.assertEqual(grouped(behavior, lambda y: y[1]), grouped(target, lambda y: y[1]))
        self.assertNotEqual(naive_mean, 1)


if __name__ == "__main__":
    unittest.main()
