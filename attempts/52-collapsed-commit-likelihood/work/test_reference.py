"""Enumerate the complete independent law, not samples from the candidate."""

import itertools
import json
import random
import unittest
from collections import defaultdict
from fractions import Fraction as F
from math import prod

from .reference import DAG, action_statistics


def trie(words):
    depth = len(words[0])
    prefixes = [[()]]
    for i in range(1, depth + 1):
        prefixes.append(sorted({w[:i] for w in words}))
    layers = []
    for i in range(depth):
        targets = {p: s for s, p in enumerate(prefixes[i + 1])}
        layers.append(
            tuple(
                tuple((p[-1], targets[p]) for p in prefixes[i + 1] if p[:-1] == s)
                for s in prefixes[i]
            )
        )
    return DAG(tuple(layers), tuple(True for _ in prefixes[-1]))


def direct_action(word, scores, active, rule, threshold, k):
    """Execute selection first, without a preimage/evidence calculation."""
    candidates = [(scores[i][word[i]], i) for i in active]
    ordered = sorted(candidates, key=lambda x: (-x[0], x[1]))
    if rule == "topk":
        chosen = ordered[:k]
    else:
        chosen = [pair for pair in candidates if pair[0] > threshold]
        if not chosen:
            chosen = ordered[:1]
    return tuple(sorted((i, word[i]) for _, i in chosen))


def checksum(m):
    layers = []
    for i in range(m + 1):
        states = range(1) if i == 0 else range(3)
        alphabet = range(2) if i == 0 else range(3)
        layers.append(tuple(tuple((v, (s + v) % 3) for v in alphabet) for s in states))
    return DAG(tuple(layers), (True, False, False))


class CollapsedActionTests(unittest.TestCase):
    def test_complete_laws_scores_and_covariance(self):
        rng = random.Random(5201)
        words = [w for w in itertools.product(range(3), repeat=4) if sum(w) % 3 == 0]
        graph = checksum(3)
        words = [w for w in words if w[0] < 2]
        checks = actions = 0
        for _case in range(12):
            rows = tuple(
                tuple(F(rng.randrange(1, 8)) for _ in range(2 if i == 0 else 3)) for i in range(4)
            )
            scores = tuple(tuple(F(rng.randrange(5), 4) for _ in row) for row in rows)
            weights = {w: prod(rows[i][v] for i, v in enumerate(w)) for w in words}
            z = sum(weights.values(), F())
            prior = [
                [
                    sum((mass for w, mass in weights.items() if w[i] == v), F()) / z
                    for v in range(len(row))
                ]
                for i, row in enumerate(rows)
            ]
            for rule, threshold, k in [("threshold", F(t, 4), None) for t in range(5)] + [
                ("topk", None, k) for k in range(1, 5)
            ]:
                groups = defaultdict(list)
                for w in words:
                    groups[direct_action(w, scores, tuple(range(4)), rule, threshold, k)].append(w)
                total, mean_full, mean_collapsed = F(), [F(), F()], [F(), F()]
                second_full = [[F(), F()], [F(), F()]]
                second_collapsed = [[F(), F()], [F(), F()]]
                conditional_noise = [[F(), F()], [F(), F()]]
                for action, members in groups.items():
                    probability, score = action_statistics(
                        graph,
                        rows,
                        scores,
                        tuple(range(4)),
                        action,
                        rule=rule,
                        threshold=threshold,
                        k=k,
                    )
                    event_mass = sum((weights[w] for w in members), F())
                    self.assertEqual(probability, event_mass / z)
                    total += probability
                    for i, row in enumerate(rows):
                        for v in range(len(row)):
                            count = (
                                sum((weights[w] for w in members if w[i] == v), F()) / event_mass
                            )
                            self.assertEqual(score[i][v], count - prior[i][v])
                            checks += 1
                    # Two distinct Jacobian directions and action-only scalar reward.
                    directions = [
                        [[F((i + 1) * (v + 1)), F((-1) ** (i + v))] for v in range(len(row))]
                        for i, row in enumerate(rows)
                    ]
                    multiplier = F(sum((i + 1) * (v + 2) for i, v in action), 7)
                    collapsed = [
                        multiplier
                        * sum(
                            (
                                score[i][v] * directions[i][v][d]
                                for i, row in enumerate(rows)
                                for v in range(len(row))
                            ),
                            F(),
                        )
                        for d in range(2)
                    ]
                    for d in range(2):
                        mean_collapsed[d] += probability * collapsed[d]
                        for e in range(2):
                            second_collapsed[d][e] += probability * collapsed[d] * collapsed[e]
                    for w in members:
                        p = weights[w] / z
                        full = [
                            multiplier
                            * sum(
                                (
                                    (F(w[i] == v) - prior[i][v]) * directions[i][v][d]
                                    for i, row in enumerate(rows)
                                    for v in range(len(row))
                                ),
                                F(),
                            )
                            for d in range(2)
                        ]
                        for d in range(2):
                            mean_full[d] += p * full[d]
                            for e in range(2):
                                second_full[d][e] += p * full[d] * full[e]
                                conditional_noise[d][e] += (
                                    p * (full[d] - collapsed[d]) * (full[e] - collapsed[e])
                                )
                    actions += 1
                self.assertEqual(total, 1)
                self.assertEqual(mean_full, mean_collapsed)
                gap = [
                    [second_full[d][e] - second_collapsed[d][e] for e in range(2)] for d in range(2)
                ]
                self.assertEqual(gap, conditional_noise)
                self.assertGreaterEqual(gap[0][0], 0)
                self.assertGreaterEqual(gap[1][1], 0)
                self.assertGreaterEqual(gap[0][0] * gap[1][1] - gap[0][1] ** 2, 0)
        print(json.dumps({"complete_laws": 108, "actions": actions, "coordinate_scores": checks}))

    def test_original_aliases_fixed_ids_and_json_termination(self):
        spellings = (b"[", b"[", b"0", b"1", b",", b"]", b"null", b"<EOT>", b"<PAD>")
        words = [(a, b, 4, c, 5, 7, 8, 8) for a in (0, 1) for b in (2, 3, 6) for c in (2, 3, 6)]
        for w in words:
            self.assertEqual(len(json.loads(b"".join(spellings[v] for v in w[: w.index(7)]))), 2)
            self.assertTrue(all(v == 8 for v in w[w.index(7) + 1 :]))
        graph = trie(words)
        domains = [(0, 1), (2, 3, 6), (4,), (2, 3, 6), (5,), (7,), (8,), (8,)]
        rows = tuple(
            tuple(F(v + 1) if v in allowed else F() for v in range(9)) for allowed in domains
        )
        scores = tuple(tuple(F(v + 1, 10) for v in range(9)) for _ in rows)
        for active in [(0, 1, 3), (1, 3)]:
            fixed_rows = rows if 0 in active else ((F(1), *(F() for _ in range(8))), *rows[1:])
            z = sum((prod(fixed_rows[i][v] for i, v in enumerate(w)) for w in words), F())
            for tau in (F(), F(2, 5), F(7, 10), F(1)):
                groups = defaultdict(F)
                for w in words:
                    a = direct_action(w, scores, active, "threshold", tau, None)
                    groups[a] += prod(fixed_rows[i][v] for i, v in enumerate(w)) / z
                for a, expected in groups.items():
                    actual, score = action_statistics(
                        graph, fixed_rows, scores, active, a, rule="threshold", threshold=tau
                    )
                    self.assertEqual(actual, expected)
                    if actual:
                        for i in (2, 4, 5, 6, 7):
                            self.assertTrue(all(g == 0 for g in score[i]))
        self.assertNotEqual(rows[0][0], rows[0][1])  # no alias-mass collapse

    def test_connected_family_even_best_full_baseline(self):
        p, q = F(3, 5), F(6, 25)
        for m in range(3, 7):
            rows = ((1 - p, p), *((F(1, 3),) * 3 for _ in range(m)))
            graph = checksum(m)
            z, prior = graph.infer(rows)
            self.assertEqual(z, F(1, 3))
            variance = F(2 * m, 3)
            aa, bb = p * ((1 - p) ** 2 + variance), (1 - p) * (p**2 + variance)
            best_b = aa / (aa + bb)
            full_mean = full_second = F()
            for w in itertools.product(range(2), *([range(3)] * m)):
                if sum(w) % 3:
                    continue
                probability = prod(rows[i][v] for i, v in enumerate(w)) / z
                s = F(w[0]) - p + sum(v - 1 for v in w[1:])
                full_mean += probability * (w[0] - best_b) * s
                full_second += probability * ((w[0] - best_b) * s) ** 2
            self.assertEqual(full_mean, q)
            expected = q * variance * (variance + 1 - 3 * q) / (variance + q)
            self.assertEqual(full_second - q**2, expected)
            for bit in range(2):
                mass, score = action_statistics(
                    graph,
                    rows,
                    rows,
                    tuple(range(m + 1)),
                    ((0, bit),),
                    rule="threshold",
                    threshold=F(9, 10),
                )
                self.assertEqual(mass, p if bit else 1 - p)
                direction = sum((score[0][v] * v for v in range(2)), F())
                direction += sum(
                    (score[i][v] * (v - 1) for i in range(1, m + 1) for v in range(3)), F()
                )
                self.assertEqual((bit - (1 - p)) * direction, q)
                self.assertTrue(all(x == F(1, 3) for row in prior[1:] for x in row))
        print(json.dumps({"connected_sizes": [3, 4, 5, 6], "optimized_full_baseline": True}))

    def test_moving_confidence_boundary_is_a_real_jump(self):
        words = list(itertools.product(range(2), repeat=2))
        graph = trie(words)
        for p in (F(749, 1000), F(751, 1000)):
            rows = ((1 - p, p), (F(1, 4), F(3, 4)))
            probability, _ = action_statistics(
                graph, rows, rows, (0, 1), ((0, 1),), rule="threshold", threshold=F(9, 10)
            )
            self.assertEqual(probability, p / 4 if p < F(3, 4) else p)
        # Thus no false globally differentiable-policy conclusion is permitted.

    def test_retained_token_only_score_misses_a_real_gradient(self):
        graph = trie(list(itertools.product(range(2), repeat=2)))
        rows = ((F(2, 5), F(3, 5)), (F(3, 10), F(7, 10)))
        total = first_exposed = derivative = naive_mass = F()
        for action in (((0, 0),), ((0, 1),), ((1, 1),)):
            probability, score = action_statistics(
                graph, rows, rows, (0, 1), action, rule="threshold", threshold=F(9, 10)
            )
            total += probability
            naive_mass += rows[action[0][0]][action[0][1]]
            if action[0][0] == 0:
                first_exposed += probability
                derivative += probability * score[1][1]
                # Reward is zero on the only action exposing position1. A score
                # using just retained-token logits therefore gives gradient0.
        self.assertEqual(total, 1)
        self.assertEqual(first_exposed, F(3, 10))
        self.assertEqual(derivative, -F(21, 100))
        self.assertEqual(naive_mass, F(17, 10))

    def test_impossible_actions_zero_target_and_bad_traces(self):
        graph = trie([(0, 0), (1, 1)])
        rows = ((F(1, 2),) * 2,) * 2
        scores = ((F(1, 4), F(3, 4)),) * 2
        probability, score = action_statistics(
            graph, rows, scores, (0, 1), ((1, 0),), rule="threshold", threshold=F(1)
        )
        self.assertEqual(probability, 0)  # first physical index wins tied fallback
        self.assertIsNone(score)
        for action in (((0, 0), (1, 1)), ((0, 1), (1, 0))):
            self.assertEqual(
                action_statistics(
                    graph, rows, scores, (0, 1), action, rule="threshold", threshold=F(1, 2)
                )[0],
                0,
            )
        with self.assertRaises(ValueError):
            action_statistics(
                graph,
                ((F(), F()), *rows[1:]),
                scores,
                (0, 1),
                ((0, 0),),
                rule="threshold",
                threshold=F(1, 2),
            )
        with self.assertRaises(ValueError):
            DAG(((((0, 0), (0, 1)),),), (True, True)).infer(((F(1),),))
        with self.assertRaises(ValueError):
            action_statistics(
                graph, rows, scores, (0, 1), ((0, 0), (0, 1)), rule="threshold", threshold=F(1, 2)
            )


if __name__ == "__main__":
    unittest.main()
