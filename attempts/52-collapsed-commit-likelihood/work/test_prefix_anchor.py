"""Independent full prefix/anchor/Bernoulli enumeration and rational derivatives."""

import itertools
import json
import unittest
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from math import prod

from .anchor import AnchorPolicy
from .numeric_json import NumericJSON
from .prefix_anchor import PrefixAnchor
from .test_numeric_json import independent_accepts


def language():
    return NumericJSON(
        (b'{"answer":0}', b'{"answer":1}', b" ", b"", b"", b"<EOT>", b"<PAD>", b"<MASK>"), 5, 6
    )


def prefixes(grammar, n, fixed):
    out = []
    ids = [v for v in range(len(grammar.emissions)) if v != grammar.eos]
    for size in range(1, n + 1):
        for body in itertools.product(ids, repeat=size - 1):
            word = (*body, grammar.eos)
            if any(i >= size or word[i] != v for i, v in fixed.items()):
                continue
            if independent_accepts(grammar, word):
                out.append(word)
    return out


def joint_law(words, rows, gates, u, fixed):
    weights = {w: prod(rows[i][v] for i, v in enumerate(w) if i not in fixed) for w in words}
    z = sum(weights.values(), F())
    result = {}
    for w, weight in weights.items():
        if not weight:
            continue
        active = [i for i in range(len(w)) if i not in fixed]
        total = sum((u[i] for i in active), F())
        for anchor in active:
            others = [i for i in active if i != anchor]
            for bits in itertools.product((0, 1), repeat=len(others)):
                selected = {anchor, *(i for i, b in zip(others, bits, strict=True) if b)}
                action = tuple((i, w[i]) for i in sorted(selected))
                result[w, anchor, action] = (
                    weight
                    / z
                    * u[anchor]
                    / total
                    * prod(
                        gates[i][w[i]] if b else 1 - gates[i][w[i]]
                        for i, b in zip(others, bits, strict=True)
                    )
                )
    return result


def make(n, fixed=None, context=False):
    fixed = dict(fixed or {})
    salt = sum(3 * i + v for i, v in fixed.items()) if context else 0
    raw = tuple(
        tuple(
            F(1 + (i * 3 + v + salt) % 7) * (1 + len(fixed)) ** 2
            if context and v == 1
            else F(1 + (i * 3 + v + salt) % 7)
            for v in range(8)
        )
        for i in range(n)
    )
    rows = tuple(tuple(v / sum(row, F()) for v in row) for row in raw)
    gates = tuple(tuple(F(1 + (i + 2 * v + salt) % 4, 5) for v in range(8)) for i in range(n))
    u = tuple(F(i + 1 + len(fixed)) for i in range(n))
    policy = PrefixAnchor(language(), rows, gates, u, fixed)
    words = prefixes(language(), n, fixed)
    return policy, joint_law(words, rows, gates, u, fixed)


def flatten(score):
    w, h, r = score
    return tuple(v for matrix in (w, h) for row in matrix for v in row) + tuple(r)


def direct_score(policy, word, anchor, action, prior):
    n, v = policy.n, policy.v
    active = [i for i in range(len(word)) if i not in policy.fixed]
    total = sum((policy.u[i] for i in active), F())
    retained = dict(action)
    counts = tuple(
        tuple(
            F(i < len(word) and word[i] == j) - prior[i][j] if i not in policy.fixed else F()
            for j in range(v)
        )
        for i in range(n)
    )
    gates = tuple(
        tuple(
            F(i < len(word) and word[i] == j) * (F(i in retained) - policy.gates[i][j])
            if i in active and i != anchor
            else F()
            for j in range(v)
        )
        for i in range(n)
    )
    rr = tuple(F(i == anchor) - (policy.u[i] / total if i in active else F()) for i in range(n))
    return counts, gates, rr


@dataclass(frozen=True)
class Dual:
    value: F
    derivative: F = F()

    @staticmethod
    def lift(value):
        return value if isinstance(value, Dual) else Dual(F(value))

    def __add__(self, other):
        b = self.lift(other)
        return Dual(self.value + b.value, self.derivative + b.derivative)

    __radd__ = __add__

    def __neg__(self):
        return Dual(-self.value, -self.derivative)

    def __sub__(self, other):
        return self + -self.lift(other)

    def __rsub__(self, other):
        return self.lift(other) + -self

    def __mul__(self, other):
        b = self.lift(other)
        return Dual(self.value * b.value, self.derivative * b.value + self.value * b.derivative)

    __rmul__ = __mul__

    def __truediv__(self, other):
        b = self.lift(other)
        return Dual(
            self.value / b.value,
            (self.derivative * b.value - self.value * b.derivative) / b.value**2,
        )

    def __rtruediv__(self, other):
        return self.lift(other) / self

    def __bool__(self):
        return bool(self.value)


class PrefixAnchorTests(unittest.TestCase):
    def test_complete_laws_occupancy_and_all_score_coordinates(self):
        actions = coordinates = triples = 0
        for n, fixed in ((2, {}), (3, {}), (4, {}), (3, {0: 0}), (4, {3: 5})):
            policy, law = make(n, fixed)
            self.assertEqual(sum(law.values(), F()), 1)
            prior = [[F() for _ in range(8)] for _ in range(n)]
            lengths = [F() for _ in range(n)]
            groups = defaultdict(list)
            for (w, a, b), p in law.items():
                groups[b].append((w, a, p))
                lengths[len(w) - 1] += p
                for i, v in enumerate(w):
                    prior[i][v] += p
                self.assertTrue(
                    all(i < len(w) and w[i] == v for i, v in {**fixed, **dict(b)}.items())
                )
            self.assertEqual(policy.prior, tuple(map(tuple, prior)))
            self.assertEqual(policy.prior_lengths, tuple(lengths))
            for b, entries in groups.items():
                probability, *score = policy.action_statistics(b)
                total = sum((p for _, _, p in entries), F())
                expected = [F() for _ in flatten(score)]
                for w, a, p in entries:
                    direct = direct_score(policy, w, a, b, prior)
                    self.assertEqual(policy.full_score(w, a, b), direct)
                    for j, value in enumerate(flatten(direct)):
                        expected[j] += p / total * value
                self.assertEqual(probability, total)
                self.assertEqual(flatten(score), tuple(expected))
                actions += 1
                coordinates += len(expected)
            triples += len(law)
        print(
            json.dumps(
                {
                    "prefix_joint_laws": 5,
                    "prefix_triples": triples,
                    "prefix_actions": actions,
                    "prefix_coordinate_scores": coordinates,
                }
            )
        )

    def test_cheap_class_length_combination_means_and_reward_trace(self):
        policy, law = make(3)
        prior = policy.prior
        by_action = defaultdict(list)
        by_word = defaultdict(list)
        by_class = defaultdict(list)
        _, _, mapping = policy.language.classes()
        for (w, a, b), p in law.items():
            by_action[b].append((w, a, p))
            by_word[w, b].append((a, p))
            by_class[tuple(mapping[v] for v in w), b].append((w, a, p))
        for (w, b), entries in by_word.items():
            mass = sum((p for _, p in entries), F())
            expected = tuple(
                sum(
                    (
                        p / mass * s
                        for a, p in entries
                        for s in [flatten(direct_score(policy, w, a, b, prior))[j]]
                    ),
                    F(),
                )
                for j in range(2 * policy.n * policy.v + policy.n)
            )
            self.assertEqual(flatten(policy.cheap_anchor_score(w, b)), expected)
        for (_, b), entries in by_class.items():
            mass = sum((p for _, _, p in entries), F())
            expected = tuple(
                sum(
                    (
                        p / mass * flatten(direct_score(policy, w, a, b, prior))[j]
                        for w, a, p in entries
                    ),
                    F(),
                )
                for j in range(2 * policy.n * policy.v + policy.n)
            )
            self.assertEqual(flatten(policy.class_score(entries[0][0], b)), expected)
        names = ("full", "cheap", "class", "length", "combined", "collapsed")
        means = {name: [F() for _ in range(2 * policy.n * policy.v + policy.n)] for name in names}
        seconds = dict.fromkeys(names, F())
        planner_seconds = dict.fromkeys(names, F())
        for (w, a, b), p in law.items():
            _, *collapsed = policy.action_statistics(b)
            cheap = policy.cheap_anchor_score(w, b)
            classed = policy.class_score(w, b)
            estimates = {
                "full": direct_score(policy, w, a, b, prior),
                "cheap": cheap,
                "class": classed,
                "length": (*cheap[:2], collapsed[2]),
                "combined": (*classed[:2], collapsed[2]),
                "collapsed": collapsed,
            }
            reward = F((len(b) + sum(v == 1 for _, v in b)) % 2) - F(1, 3)
            for name, score in estimates.items():
                values = flatten(score)
                for j, value in enumerate(values):
                    means[name][j] += p * reward * value
                seconds[name] += p * reward**2 * sum((value**2 for value in values), F())
                _, gate_score, anchor_score = score
                planner = tuple(sum(row, F()) for row in gate_score) + tuple(anchor_score)
                planner_seconds[name] += p * reward**2 * sum((value**2 for value in planner), F())
        for name in names:
            self.assertEqual(means[name], means["full"])
        for x, y in (
            ("full", "cheap"),
            ("cheap", "class"),
            ("class", "combined"),
            ("cheap", "length"),
            ("length", "combined"),
            ("combined", "collapsed"),
        ):
            self.assertGreaterEqual(seconds[x], seconds[y], (x, y))
            self.assertGreaterEqual(planner_seconds[x], planner_seconds[y], (x, y))
        self.assertGreater(planner_seconds["combined"], planner_seconds["collapsed"])

    def test_fixed_stop_reduces_to_prior_policy_and_domain_refusals(self):
        policy, law = make(4, {3: 5})
        rows = tuple(
            tuple(F(v == 5) for v in range(8)) if i == 3 else row
            for i, row in enumerate(policy.rows)
        )
        anchors = tuple(policy.u[i] / sum(policy.u[:3], F()) if i < 3 else F() for i in range(4))
        old = AnchorPolicy(
            policy.language.small_reference_graph(4), rows, policy.gates, anchors, (0, 1, 2)
        )
        for action in {b for _, _, b in law}:
            self.assertEqual(policy.action_statistics(action), old.action_statistics(action))
        with self.assertRaises(ValueError):
            policy.action_statistics(())
        with self.assertRaises(ValueError):
            policy.action_statistics(((3, 5),))
        self.assertEqual(policy.action_statistics(((0, 7),))[0], 0)
        with self.assertRaises(ValueError):
            PrefixAnchor(policy.language, policy.rows, policy.gates, policy.u, {0: 0, 1: 5})
        with self.assertRaises(ValueError):
            PrefixAnchor(policy.language, policy.rows, policy.gates, policy.u, {0: 0, 1: 5, 2: 2})
        zero = tuple(tuple(F(v == 7) for v in range(8)) for _ in range(4))
        with self.assertRaises(ValueError):
            PrefixAnchor(policy.language, zero, policy.gates, policy.u)

    def test_exact_dual_original_head_chain_and_latent_length_normalizer(self):
        policy, _ = make(3)
        words = prefixes(policy.language, 3, {})
        rows = policy.rows
        gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in rows)
        policy = PrefixAnchor(policy.language, rows, gates, policy.u)
        coordinate = (2, 0)
        dual_rows = []
        for i, row in enumerate(rows):
            raw = [Dual(c, c * F((i, v) == coordinate)) for v, c in enumerate(row)]
            total = sum(raw, Dual(F()))
            dual_rows.append(tuple(c / total for c in raw))
        dual_gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in dual_rows)
        head = joint_law(words, tuple(dual_rows), dual_gates, policy.u, {})
        du = tuple(Dual(u, u * F(i == 0)) for i, u in enumerate(policy.u))
        anchor = joint_law(words, rows, gates, du, {})
        hg = defaultdict(lambda: Dual(F()))
        ag = defaultdict(lambda: Dual(F()))
        for (_, _, b), p in head.items():
            hg[b] += p
        for (_, _, b), p in anchor.items():
            ag[b] += p
        witnessed = False
        for b, mass in hg.items():
            p, counts, hh, rr = policy.action_statistics(b)
            self.assertEqual(p, mass.value)
            i, v = coordinate
            projected = (
                counts[i][v] + hh[i][v] - rows[i][v] * (sum(counts[i], F()) + sum(hh[i], F()))
            )
            self.assertEqual(projected, mass.derivative / p)
            self.assertEqual(rr[0], ag[b].derivative / ag[b].value)
            detached = counts[i][v] + hh[i][v] - rows[i][v] * sum(hh[i], F())
            witnessed |= detached != projected
        self.assertTrue(witnessed, "variable occupancy must expose missing head-normalizer term")

    def test_adaptive_fake_heads_preserve_fixed_ids_and_path_score_mean(self):
        grammar = language()
        states = {}

        def terminal(fixed):
            for i, v in fixed.items():
                if v == grammar.eos and i == max(fixed) and all(j in fixed for j in range(i + 1)):
                    return tuple(fixed[j] for j in range(i + 1))
            return None

        @lru_cache(None)
        def moments(key, kind):
            fixed = dict(key)
            word = terminal(fixed)
            if word is not None:
                self.assertTrue(independent_accepts(grammar, word))
                reward = F(1 in word) - F(1, 3)
                return reward, reward**2, F(), F(), F()
            if key not in states:
                states[key] = make(3, fixed, context=True)
            policy, law = states[key]
            total = [F() for _ in range(5)]
            for (w, a, b), p in law.items():
                following = {**fixed, **dict(b)}
                self.assertGreater(len(following), len(fixed))
                self.assertTrue(all(i < len(w) and w[i] == v for i, v in following.items()))
                if kind == "full":
                    score = direct_score(policy, w, a, b, policy.prior)
                else:
                    _, *score = policy.action_statistics(b)
                _, hh, rr = score
                current = sum(
                    (hh[i][v] * (1 + i + 2 * v) for i in range(3) for v in range(8)), F()
                ) + sum((r * (i + 1) for i, r in enumerate(rr)), F())
                er, er2, eg, ers, egs2 = moments(tuple(sorted(following.items())), kind)
                values = (
                    er,
                    er2,
                    current * er + eg,
                    current * er2 + ers,
                    current**2 * er2 + 2 * current * ers + egs2,
                )
                for j, value in enumerate(values):
                    total[j] += p * value
            return tuple(total)

        full = moments((), "full")
        collapsed = moments((), "collapsed")
        self.assertEqual(full[:4], collapsed[:4])
        self.assertGreaterEqual(full[4], collapsed[4])
        self.assertNotEqual(full[2], F())
        print(
            json.dumps(
                {
                    "prefix_fake_states": len(states),
                    "neural_forwards": 0,
                    "full_path_second": str(full[4]),
                    "collapsed_path_second": str(collapsed[4]),
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
