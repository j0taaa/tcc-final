"""Independent enumeration over original words, anchors and all Bernoulli bits."""

import itertools
import json
import random
import unittest
from collections import defaultdict
from fractions import Fraction as F
from math import prod

from .anchor import AnchorPolicy
from .test_reference import checksum, trie


def full_law(words, rows, gates, anchors, active):
    weights = {w: prod(rows[i][v] for i, v in enumerate(w)) for w in words}
    z = sum(weights.values(), F())
    result = {}
    for w, weight in weights.items():
        if not weight:
            continue
        for anchor in active:
            if not anchors[anchor]:
                continue
            others = tuple(i for i in active if i != anchor)
            for bits in itertools.product(range(2), repeat=len(others)):
                selected = {anchor, *(i for i, b in zip(others, bits, strict=True) if b)}
                action = tuple((i, w[i]) for i in sorted(selected))
                probability = (
                    weight
                    / z
                    * anchors[anchor]
                    * prod(
                        gates[i][w[i]] if b else 1 - gates[i][w[i]]
                        for i, b in zip(others, bits, strict=True)
                    )
                )
                result[w, anchor, action] = probability
    return result


class AnchorActionTests(unittest.TestCase):
    def test_complete_laws_three_adjoints_and_both_collapses(self):
        words = [w for w in itertools.product(range(2), range(3), range(3)) if sum(w) % 3 == 0]
        graph, rng = checksum(2), random.Random(5204)
        count = coordinates = 0
        for _case in range(8):
            rows = tuple(
                tuple(F(rng.randrange(1, 7)) for _ in range(2 if i == 0 else 3)) for i in range(3)
            )
            gates = tuple(tuple(F(rng.randrange(1, 8), 8) for _ in row) for row in rows)
            aa = [F(rng.randrange(1, 6)) for _ in rows]
            anchors = tuple(a / sum(aa) for a in aa)
            policy = AnchorPolicy(graph, rows, gates, anchors, (0, 1, 2))
            law = full_law(words, rows, gates, anchors, (0, 1, 2))
            self.assertEqual(sum(law.values(), F()), 1)
            groups, word_mass = defaultdict(list), defaultdict(F)
            for (w, anchor, action), p in law.items():
                groups[action].append((w, anchor, p))
                word_mass[w] += p
            z = sum((prod(rows[i][v] for i, v in enumerate(w)) for w in words), F())
            for w, p in word_mass.items():
                self.assertEqual(p, prod(rows[i][v] for i, v in enumerate(w)) / z)
            self.assertEqual(
                policy.expected_releases(), sum((p * len(a) for (_, _, a), p in law.items()), F())
            )
            for action, members in groups.items():
                probability, ww, hh, rr = policy.action_statistics(action)
                mass = sum((p for _, _, p in members), F())
                self.assertEqual(probability, mass)
                for i, row in enumerate(rows):
                    for v in range(len(row)):
                        expected_w = (
                            sum((p * F(w[i] == v) for w, _, p in members), F()) / mass
                            - policy.prior[i][v]
                        )
                        expected_h = (
                            sum(
                                (
                                    p
                                    * F(w[i] == v)
                                    * F(anchor != i)
                                    * (F(i in dict(action)) - gates[i][v])
                                    for w, anchor, p in members
                                ),
                                F(),
                            )
                            / mass
                        )
                        self.assertEqual(ww[i][v], expected_w)
                        self.assertEqual(hh[i][v], expected_h)
                        coordinates += 2
                    self.assertEqual(
                        rr[i],
                        sum((p for _, anchor, p in members if anchor == i), F()) / mass
                        - anchors[i],
                    )
                    coordinates += 1

                # The intermediate estimator collapses hidden words while
                # retaining A. Verify its conditional mean collapses A too.
                def project(w_score, h_score, r_score, rows=rows):
                    return sum(
                        (
                            w_score[i][v] * (i + v + 1) + h_score[i][v] * (v - i)
                            for i, row in enumerate(rows)
                            for v in range(len(row))
                        ),
                        F(),
                    ) + sum((r_score[i] * (i + 2) for i in range(3)), F())

                collapsed = project(ww, hh, rr)
                anchor_groups = defaultdict(list)
                for w, anchor, p in members:
                    anchor_groups[anchor].append(
                        (p, project(*policy.full_score(w, anchor, action)))
                    )
                full_second = (
                    sum((p * s**2 for records in anchor_groups.values() for p, s in records), F())
                    / mass
                )
                intermediate_second = F()
                intermediate_mean = F()
                for records in anchor_groups.values():
                    pa = sum((p for p, _ in records), F())
                    mu = sum((p * s for p, s in records), F()) / pa
                    intermediate_mean += pa / mass * mu
                    intermediate_second += pa / mass * mu**2
                self.assertEqual(intermediate_mean, collapsed)
                self.assertGreaterEqual(full_second, intermediate_second)
                self.assertGreaterEqual(intermediate_second, collapsed**2)
                count += 1
        print(
            json.dumps(
                {
                    "anchor_joint_laws": 8,
                    "observed_actions": count,
                    "score_coordinates": coordinates,
                }
            )
        )

    def test_fixed_anchor_and_position_only_analytic_controls(self):
        words = list(itertools.product(range(2), repeat=3))
        graph = trie(words)
        rows = ((F(2, 5), F(3, 5)),) * 3
        gates = ((F(1, 4),) * 2, (F(2, 3),) * 2, (F(3, 5),) * 2)
        for anchors in ((F(1), F(), F()), (F(1, 3),) * 3):
            policy = AnchorPolicy(graph, rows, gates, anchors, (0, 1, 2))
            law = full_law(words, rows, gates, anchors, (0, 1, 2))
            for action in {a for _, _, a in law}:
                selected = dict(action)
                mask_weight = prod(
                    gates[i][0] if i in selected else 1 - gates[i][0] for i in range(3)
                )
                scalar = sum((anchors[i] / gates[i][0] for i in selected), F())
                # Independent-word test has a closed original-token marginal;
                # the simpler control requires NO filtered grammar query.
                expected = prod(rows[i][v] for i, v in action) * mask_weight * scalar
                self.assertEqual(policy.action_statistics(action)[0], expected)

    def test_one_active_alias_and_replay_sampler(self):
        words = [(0, 2), (1, 2)]
        graph, rows = trie(words), ((F(2), F(3), F()), (F(), F(), F(1)))
        tiny = F(1, 2**800)
        gates = ((tiny, F(3, 4), F(1, 2)), (F(1, 2),) * 3)
        policy = AnchorPolicy(graph, rows, gates, (F(1), F()), (0,))
        self.assertEqual(policy.action_statistics(((0, 1),))[0], F(3, 5))
        self.assertEqual(policy.action_statistics(((0, 1),))[2], ((F(),) * 3,) * 2)
        rng = random.Random(5205)
        for _ in range(24):
            word, anchor, action = policy.sample(rng)
            self.assertIn(word, words)
            self.assertEqual(anchor, 0)
            self.assertEqual(action, ((0, word[0]),))
        self.assertEqual(policy.expected_releases(), 1)
        with self.assertRaises(ValueError):
            AnchorPolicy(graph, rows, gates, (F(1, 2), F(1, 2)), (0,))

    def test_confidence_chain_and_two_step_observed_paths(self):
        words = list(itertools.product(range(2), repeat=2))
        graph, records, cache = trie(words), defaultdict(list), {}

        def source(canvas):
            if canvas not in cache:
                active = tuple(i for i, v in enumerate(canvas) if v is None)
                visible = sum(v for v in canvas if v is not None)
                rows = tuple(
                    tuple(
                        F(2 + i + 2 * v + visible) if old is None else F(v == old) for v in range(2)
                    )
                    for i, old in enumerate(canvas)
                )
                confidence = tuple(tuple(w / sum(row) for w in row) for row in rows)
                gates = tuple(
                    tuple(c / (c + F(1, 2)) if c else F(1, 3) for c in row) for row in confidence
                )
                anchors = tuple(F(1, len(active)) if i in active else F() for i in range(2))
                policy = AnchorPolicy(graph, rows, gates, anchors, active)
                law = full_law(words, rows, gates, anchors, active)
                cache[canvas] = policy, law, confidence
            return cache[canvas]

        def direction(ww, hh, rr, confidence):
            # Shared theta tilts all logits by their original binary ID. The
            # confidence-dependent gate contributes its true softmax derivative.
            return sum(
                (
                    ww[i][v] * v + hh[i][v] * (v - confidence[i][1])
                    for i in range(2)
                    for v in range(2)
                ),
                F(),
            ) + sum(rr, F())

        def visit(canvas, path, probability, score, observed_probability, observed_score):
            if all(v is not None for v in canvas):
                records[path].append(
                    (probability, score, observed_probability, observed_score, canvas)
                )
                return
            policy, law, confidence = source(canvas)
            # Independent unnormalized log derivative, before its word normalizer.
            # Its base expectation is known from full enumeration of X, not
            # from action_statistics or the gate-score formula.
            normalizer_derivative = sum((policy.prior[i][1] for i in policy.active), F())
            for (word, anchor, action), p in law.items():
                selected = dict(action)
                raw = sum((F(word[i]) for i in policy.active), F())
                raw += sum(
                    (
                        (F(i in selected) - policy.gates[i][word[i]]) * (word[i] - confidence[i][1])
                        for i in policy.active
                        if i != anchor
                    ),
                    F(),
                )
                true_full = raw - normalizer_derivative
                fs = direction(*policy.full_score(word, anchor, action), confidence)
                self.assertEqual(fs, true_full)
                mass, ww, hh, rr = policy.action_statistics(action)
                collapsed = direction(ww, hh, rr, confidence)
                following = list(canvas)
                for i, v in action:
                    following[i] = v
                visit(
                    tuple(following),
                    (*path, action),
                    probability * p,
                    score + true_full,
                    observed_probability * mass,
                    observed_score + collapsed,
                )

        visit((None, None), (), F(1), F(), F(1), F())
        total = full_mean = collapsed_mean = gap = noise = F()
        for path, members in records.items():
            mass = sum((r[0] for r in members), F())
            _, _, expected_mass, expected_score, final = members[0]
            self.assertEqual(mass, expected_mass)
            self.assertEqual(sum((p * s for p, s, _, _, _ in members), F()) / mass, expected_score)
            reward = F(final[0] != final[1]) * (1 - F(len(path) - 1, 10))
            for p, score, cp, cs, _ in members:
                self.assertEqual((cp, cs), (expected_mass, expected_score))
                full_mean += p * reward * score
                collapsed_mean += p * reward * cs
                gap += p * reward**2 * (score**2 - cs**2)
                noise += p * reward**2 * (score - cs) ** 2
            total += mass
        self.assertEqual(total, 1)
        self.assertEqual(full_mean, collapsed_mean)
        self.assertEqual(gap, noise)
        self.assertGreater(noise, 0)
        print(
            json.dumps(
                {
                    "anchor_fake_states": len(cache),
                    "anchor_observed_paths": len(records),
                    "anchor_full_paths": sum(len(r) for r in records.values()),
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
