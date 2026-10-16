"""Independent complete pair enumeration and analytic directional derivatives."""

import itertools
import json
import random
import unittest
from collections import defaultdict
from fractions import Fraction as F
from math import prod

from .smooth import SmoothPolicy
from .test_reference import checksum, trie


def enumerate_joint(words, rows, gates, active):
    law = {}
    for w in words:
        weight = prod(rows[i][v] for i, v in enumerate(w))
        if not weight:
            continue
        for bits in itertools.product(range(2), repeat=len(active)):
            if not any(bits):
                continue
            action = tuple((i, w[i]) for i, b in zip(active, bits, strict=True) if b)
            mass = weight * prod(
                gates[i][w[i]] if b else 1 - gates[i][w[i]]
                for i, b in zip(active, bits, strict=True)
            )
            law[w, action] = mass
    total = sum(law.values(), F())
    return total, {pair: mass / total for pair, mass in law.items()}


def sampler_law(policy):
    result = {}

    def visit(i, state, seen, word, action, probability):
        if i == len(policy.rows):
            assert seen and policy.graph.accepting[state]
            result[word, action] = result.get((word, action), F()) + probability
            return
        choices = policy.choices(i, state, seen)
        total = sum((c[-1] for c in choices), F())
        for v, bit, target, new_seen, mass in choices:
            visit(
                i + 1,
                target,
                new_seen,
                (*word, v),
                (*action, (i, v)) if bit else action,
                probability * mass / total,
            )

    visit(0, 0, 0, (), (), F(1))
    return result


class SmoothActionTests(unittest.TestCase):
    def test_complete_joint_action_and_both_scores(self):
        words = [w for w in itertools.product(range(2), range(3), range(3)) if sum(w) % 3 == 0]
        graph, rng = checksum(2), random.Random(5202)
        count = coordinates = 0
        for _case in range(8):
            rows = tuple(
                tuple(F(rng.randrange(1, 8)) for _ in range(2 if i == 0 else 3)) for i in range(3)
            )
            gates = tuple(tuple(F(rng.randrange(1, 8), 8) for _ in row) for row in rows)
            active = (0, 1, 2)
            policy = SmoothPolicy(graph, rows, gates, active)
            z, law = enumerate_joint(words, rows, gates, active)
            self.assertEqual(policy.mass, z)
            self.assertEqual(sampler_law(policy), law)
            groups = defaultdict(list)
            for (w, action), p in law.items():
                groups[action].append((w, p))
            # Enumerated derivatives of unnormalized K wrt each independent
            # log weight and log gate-odds, before subtracting the normalizer.
            expected_w = [[F() for _ in row] for row in rows]
            expected_h = [[F() for _ in row] for row in rows]
            for (w, action), p in law.items():
                retained = dict(action)
                for i, row in enumerate(rows):
                    for v in range(len(row)):
                        expected_w[i][v] += p * (w[i] == v)
                        expected_h[i][v] += p * (w[i] == v) * (F(i in retained) - gates[i][v])
            mean = [[F(), F()] for _ in range(2)]
            gap = [[F(), F()] for _ in range(2)]
            noise = [[F(), F()] for _ in range(2)]
            for action, members in groups.items():
                probability, ww, hh = policy.action_statistics(action)
                q = sum((p for _, p in members), F())
                self.assertEqual(probability, q)
                retained = dict(action)
                for i, row in enumerate(rows):
                    for v in range(len(row)):
                        post = sum((p for w, p in members if w[i] == v), F()) / q
                        self.assertEqual(ww[i][v], post - expected_w[i][v])
                        self.assertEqual(
                            hh[i][v], post * (F(i in retained) - gates[i][v]) - expected_h[i][v]
                        )
                        coordinates += 2
                multiplier = F(sum(v + i + 1 for i, v in action), 5)
                collapsed = [
                    multiplier
                    * sum(
                        (
                            ww[i][v] * (v + 1) + hh[i][v] * (i + d + 1) ** (d + 1)
                            for i, row in enumerate(rows)
                            for v in range(len(row))
                        ),
                        F(),
                    )
                    for d in range(2)
                ]
                for w, p in members:
                    fw, fh = policy.full_score(w, action)
                    full = [
                        multiplier
                        * sum(
                            (
                                fw[i][v] * (v + 1) + fh[i][v] * (i + d + 1) ** (d + 1)
                                for i, row in enumerate(rows)
                                for v in range(len(row))
                            ),
                            F(),
                        )
                        for d in range(2)
                    ]
                    for d in range(2):
                        mean[0][d] += p * full[d]
                        mean[1][d] += p * collapsed[d]
                        for e in range(2):
                            gap[d][e] += p * (full[d] * full[e] - collapsed[d] * collapsed[e])
                            noise[d][e] += p * (full[d] - collapsed[d]) * (full[e] - collapsed[e])
                count += 1
            self.assertEqual(mean[0], mean[1])
            self.assertEqual(gap, noise)
            self.assertGreaterEqual(gap[0][0] * gap[1][1] - gap[0][1] ** 2, 0)
        print(
            json.dumps(
                {
                    "smooth_joint_laws": 8,
                    "observed_actions": count,
                    "score_coordinates": coordinates,
                }
            )
        )

    def test_confidence_chain_rule_without_detaching_head(self):
        words = [w for w in itertools.product(range(2), repeat=3) if sum(w) % 2 == 0]
        graph = trie(words)
        rows = ((F(2), F(3)), (F(4), F(1)), (F(3), F(7)))
        confidence = tuple(tuple(w / sum(row) for w in row) for row in rows)
        # h=log(confidence)-log(1/2), so sigmoid(h)=c/(c+1/2).
        gates = tuple(tuple(c / (c + F(1, 2)) for c in row) for row in confidence)
        policy = SmoothPolicy(graph, rows, gates, (0, 1, 2))
        _, law = enumerate_joint(words, rows, gates, (0, 1, 2))
        base = [[F() for _ in row] for row in rows]
        raw = {}
        for (w, action), probability in law.items():
            retained = dict(action)
            values = []
            for i, row in enumerate(rows):
                factor = F(i in retained) - gates[i][w[i]]
                values.append(
                    tuple(
                        F(w[i] == v) + factor * (F(w[i] == v) - confidence[i][v])
                        for v in range(len(row))
                    )
                )
                for v, value in enumerate(values[-1]):
                    base[i][v] += probability * value
            raw[w, action] = values
        for action in {a for _, a in law}:
            q, ww, hh = policy.action_statistics(action)
            for i, row in enumerate(rows):
                for v in range(len(row)):
                    chain = ww[i][v] + hh[i][v] - confidence[i][v] * sum(hh[i], F())
                    direct = (
                        sum((p * raw[w, a][i][v] for (w, a), p in law.items() if a == action), F())
                        / q
                        - base[i][v]
                    )
                    self.assertEqual(chain, direct)

    def test_position_only_reduction_and_wrong_bit_retry(self):
        graph = trie([(0,), (1,)])
        rows, gates = ((F(1, 2), F(1, 2)),), ((F(1, 4), F(3, 4)),)
        policy = SmoothPolicy(graph, rows, gates, (0,))
        self.assertEqual(policy.action_statistics(((0, 1),))[0], F(3, 4))
        self.assertNotEqual(policy.action_statistics(((0, 1),))[0], F(1, 2))
        words = [w for w in itertools.product(range(2), repeat=3) if sum(w) % 2 == 0]
        graph = trie(words)
        rows = ((F(2), F(3)),) * 3
        gates = ((F(1, 4),) * 2, (F(2, 3),) * 2, (F(4, 5),) * 2)
        policy = SmoothPolicy(graph, rows, gates, (0, 1, 2))
        z, prior = graph.infer(rows)
        nonempty = 1 - prod(1 - row[0] for row in gates)
        self.assertEqual(policy.mass, z * nonempty)
        for i, row in enumerate(prior):
            for v, probability in enumerate(row):
                self.assertEqual(sum(policy.joint_marginals[i][v], F()), probability)

    def test_adaptive_markov_path_collapse_with_fresh_fake_heads(self):
        words = [w for w in itertools.product(range(2), repeat=3) if sum(w) % 2 == 0]
        graph, groups, cache = trie(words), defaultdict(list), {}

        def source(canvas, step):
            key = canvas, step
            if key not in cache:
                fixed_sum = sum(v for v in canvas if v is not None)
                active = tuple(i for i, v in enumerate(canvas) if v is None)
                rows = tuple(
                    tuple(
                        F(2 + i + 2 * v + fixed_sum + step) if old is None else F(v == old)
                        for v in range(2)
                    )
                    for i, old in enumerate(canvas)
                )
                gates = tuple(
                    tuple(F(v + 1, v + i + 4 + fixed_sum + step) for v in range(2))
                    for i in range(3)
                )
                policy = SmoothPolicy(graph, rows, gates, active)
                _, law = enumerate_joint(words, rows, gates, active)
                cache[key] = policy, law
            return cache[key]

        def project(ww, hh, canvas, step):
            fixed_sum = sum(v for v in canvas if v is not None)
            return tuple(
                sum(
                    (
                        ww[i][v] * (i + 1) * (v + d + 1)
                        + hh[i][v] * (fixed_sum + step + 1) * (v + 1) ** (d + 1)
                        for i in range(3)
                        for v in range(2)
                    ),
                    F(),
                )
                for d in range(2)
            )

        def visit(canvas, path, p, full, collapsed_p, collapsed):
            if all(v is not None for v in canvas):
                groups[path].append((p, full, collapsed_p, collapsed, canvas))
                return
            policy, law = source(canvas, len(path))
            for (word, action), probability in law.items():
                mass, ww, hh = policy.action_statistics(action)
                cf = project(ww, hh, canvas, len(path))
                ff = project(*policy.full_score(word, action), canvas, len(path))
                following = list(canvas)
                for i, v in action:
                    following[i] = v
                visit(
                    tuple(following),
                    (*path, action),
                    p * probability,
                    tuple(a + b for a, b in zip(full, ff, strict=True)),
                    collapsed_p * mass,
                    tuple(a + b for a, b in zip(collapsed, cf, strict=True)),
                )

        visit((None,) * 3, (), F(1), (F(), F()), F(1), (F(), F()))
        mean_full = [F(), F()]
        mean_collapsed = [F(), F()]
        gap = [[F(), F()], [F(), F()]]
        noise = [[F(), F()], [F(), F()]]
        total = F()
        for path, records in groups.items():
            mass = sum((r[0] for r in records), F())
            cp, cs, final = records[0][2:]
            self.assertEqual(mass, cp)
            self.assertEqual(
                tuple(sum((r[0] * r[1][d] for r in records), F()) / mass for d in range(2)), cs
            )
            self.assertTrue(all((r[2], r[3], r[4]) == (cp, cs, final) for r in records))
            reward = F(sum(final) == 2) * (1 - F(len(path) - 1, 10))
            total += mass
            for p, full, _, _, _ in records:
                for d in range(2):
                    mean_full[d] += p * reward * full[d]
                    mean_collapsed[d] += p * reward * cs[d]
                    for e in range(2):
                        gap[d][e] += p * reward**2 * (full[d] * full[e] - cs[d] * cs[e])
                        noise[d][e] += p * reward**2 * (full[d] - cs[d]) * (full[e] - cs[e])
        self.assertEqual(total, 1)
        self.assertEqual(mean_full, mean_collapsed)
        self.assertEqual(gap, noise)
        self.assertGreater(gap[0][0], 0)
        self.assertGreaterEqual(gap[0][0] * gap[1][1] - gap[0][1] ** 2, 0)
        print(
            json.dumps(
                {
                    "fake_head_states": len(cache),
                    "observed_paths": len(groups),
                    "full_auxiliary_paths": sum(len(r) for r in groups.values()),
                }
            )
        )

    def test_tiny_positive_exit_mass_and_fixed_aliases(self):
        graph = trie([(0, 2, 3), (1, 2, 3)])
        rows = ((F(2), F(3), F(), F()), (F(), F(), F(1), F()), (F(), F(), F(), F(1)))
        tiny = F(1, 2**1000)
        gates = ((tiny,) * 4,) * 3
        policy = SmoothPolicy(graph, rows, gates, (0,))
        self.assertEqual(policy.mass, 5 * tiny)
        self.assertEqual(policy.action_statistics(((0, 1),))[0], F(3, 5))
        rng = random.Random(5203)
        for _ in range(16):
            word, action = policy.sample(rng)
            self.assertIn(word, ((0, 2, 3), (1, 2, 3)))
            self.assertEqual(action, ((0, word[0]),))
        for gate in (F(), F(1)):
            with self.assertRaises(ValueError):
                SmoothPolicy(graph, rows, ((gate,) * 4,) * 3, (0,))


if __name__ == "__main__":
    unittest.main()
