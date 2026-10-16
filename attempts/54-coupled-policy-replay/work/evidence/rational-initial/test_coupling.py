"""Independent exact finite-table tests, not a neural advantage campaign."""

import itertools
import unittest
from collections import defaultdict
from fractions import Fraction as F

from .coupling import auxiliary_diagonal, forced_joint, maximal, prefix_process, pushforward


def marginals(joint):
    p, q = defaultdict(F), defaultdict(F)
    for (a, b), v in joint.items():
        p[a] += v
        q[b] += v
    return {a: v for a, v in p.items() if v}, {a: v for a, v in q.items() if v}


class CoupledPolicyTests(unittest.TestCase):
    def test_all_small_maximal_tables_marginals_and_rejection_law(self):
        laws = []
        for a, b in itertools.product(range(5), repeat=2):
            if a + b <= 4:
                laws.append({0: F(a, 4), 1: F(b, 4), 2: F(4 - a - b, 4)})
        for p, q in itertools.product(laws, repeat=2):
            joint = maximal(p, q)
            self.assertEqual(
                marginals(joint), tuple({a: v for a, v in r.items() if v} for r in (p, q))
            )
            common = sum(min(p[a], q[a]) for a in p)
            self.assertEqual(sum(v for (a, b), v in joint.items() if a == b), common)
            d = 1 - common
            if d:
                # Independently sum the infinite rejection series analytically.
                for a, b in itertools.product(p, repeat=2):
                    diagonal = min(p[a], q[a]) if a == b else F(0)
                    rejection_first = p[a] - min(p[a], q[a])
                    accepted_second = q[b] - min(p[b], q[b])
                    self.assertEqual(
                        joint.get((a, b), 0), diagonal + rejection_first * accepted_second / d
                    )
                self.assertEqual(1 + d * (1 / d), 2)

    def test_actual_forced_grammar_joint_and_strict_class_projection(self):
        words = {
            w: F(2 ** sum(w), 13) for w in itertools.product((0, 1), repeat=3) if sum(w) % 2 == 0
        }
        first = forced_joint(words, [{0: F(1, 4), 1: F(3, 4)}] * 3)
        second = forced_joint(words, [{0: F(1, 3), 1: F(2, 3)}] * 3)
        self.assertEqual(sum(first.values()), 1)
        self.assertEqual(sum(second.values()), 1)
        # Parity DFA effects distinguish0 from1: same lexical class path means same word.
        p = pushforward(first, lambda z: z[1])
        q = pushforward(second, lambda z: z[1])
        partial = auxiliary_diagonal(first, second, lambda z: z[1])
        exact = {a: min(p.get(a, 0), q.get(a, 0)) for a in p.keys() | q.keys()}
        self.assertTrue(all(exact[a] >= partial.get(a, 0) for a in exact))
        self.assertGreater(sum(exact.values()), sum(partial.values()))
        self.assertEqual(marginals(maximal(p, q)), (p, q))

    def test_shared_prefix_work_against_every_binary_transport_vertex(self):
        histories = [h for n in range(3) for h in itertools.product((0, 1), repeat=n)]
        p = {h: F(1 + (len(h) + sum(h)) % 3, 4) for h in histories}
        q = {h: F(1 + (2 * len(h) + sum(h) + 1) % 3, 4) for h in histories}
        cost = {h: F(1 + len(h) + 2 * sum(h)) for h in histories}
        best_joint, best = prefix_process(p, q, 3, dict.fromkeys(histories, True), cost)
        expected_p = {(): F(1)}
        expected_q = {(): F(1)}
        for _ in range(3):
            expected_p = {
                h + (b,): v * (p[h] if b else 1 - p[h])
                for h, v in expected_p.items()
                for b in (0, 1)
            }
            expected_q = {
                h + (b,): v * (q[h] if b else 1 - q[h])
                for h, v in expected_q.items()
                for b in (0, 1)
            }
        self.assertEqual(marginals(best_joint), (expected_p, expected_q))
        strict = 0
        for bits in itertools.product((False, True), repeat=len(histories)):
            joint, value = prefix_process(p, q, 3, dict(zip(histories, bits, strict=True)), cost)
            self.assertEqual(marginals(joint), (expected_p, expected_q))
            self.assertLessEqual(value, best)
            strict += value < best
        self.assertGreater(strict, 0)

    def test_nonfaithful_lookahead_and_semantic_variance_limits(self):
        p = {s: F(1, 4) for s in itertools.product((0, 1), repeat=2)}
        q = {s: F(2, 5) ** sum(s) * F(3, 5) ** (2 - sum(s)) for s in p}
        whole = maximal(p, q)
        lookahead = sum(v for (a, b), v in whole.items() if a == b)
        self.assertEqual(lookahead, F(89, 100))
        self.assertGreater(lookahead, F(9, 10) ** 2)
        p = {0: F(1, 2), 1: F(49, 100), 2: F(1, 100)}
        q = {0: F(1, 2), 1: F(1, 100), 2: F(49, 100)}
        score = {0: 0, 1: -1, 2: 1}
        coupled = maximal(p, q)
        independent = {(a, b): pa * pb for a, pa in p.items() for b, pb in q.items()}

        def variance(joint):
            mean = sum(v * (score[a] - score[b]) for (a, b), v in joint.items())
            return sum(v * (score[a] - score[b]) ** 2 for (a, b), v in joint.items()) - mean**2

        self.assertEqual(variance(coupled), F(624, 625))
        self.assertEqual(variance(independent), F(337, 625))
        self.assertGreater(variance(coupled), variance(independent))

    def test_local_total_variation_identity_by_exact_linear_laws(self):
        base = {(z, a): F(1, 6) for z, a in itertools.product(range(3), range(2))}
        derivative = {(z, a): F((1, -1, 1)[z] * (1 if a == 0 else -1), 12) for z, a in base}
        score = {z: derivative[z] / base[z] for z in base}
        visible = pushforward(base, lambda z: z[1])
        d_visible = pushforward(derivative, lambda z: z[1])
        visible_score = {a: d_visible[a] / visible[a] for a in visible}
        e_full = sum(base[z] * abs(score[z]) for z in base)
        e_observed = sum(visible[a] * abs(visible_score[a]) for a in visible)
        self.assertEqual(e_full, F(1, 2))
        self.assertEqual(e_observed, F(1, 6))
        for epsilon in (F(1, 2), F(1, 16), F(1, 256)):
            minus = {z: base[z] - epsilon * derivative[z] / 2 for z in base}
            plus = {z: base[z] + epsilon * derivative[z] / 2 for z in base}
            p = pushforward(minus, lambda z: z[1])
            q = pushforward(plus, lambda z: z[1])
            self.assertEqual(sum(abs(plus[z] - minus[z]) for z in base) / 2, epsilon * e_full / 2)
            self.assertEqual(sum(abs(p[a] - q[a]) for a in p) / 2, epsilon * e_observed / 2)

    def test_remaining_work_weight_matches_shared_prefix_derivative(self):
        histories = [h for n in range(3) for h in itertools.product((0, 1), repeat=n)]
        baseline = {h: F(1 + (len(h) + sum(h)) % 3, 4) for h in histories}
        derivative = {h: F((-1) ** sum(h), 8) for h in histories}
        costs = {h: F(1 + sum(h)) for h in histories}
        predicted = F(0)
        for path in itertools.product((0, 1), repeat=3):
            probability = F(1)
            for t, a in enumerate(path):
                h = path[:t]
                probability *= baseline[h] if a else 1 - baseline[h]
            for t in range(3):
                h = path[:t]
                score = abs(derivative[h] / (baseline[h] if path[t] else 1 - baseline[h]))
                remaining = sum(costs[path[:u]] for u in range(t + 1, 3))
                predicted += probability * score * remaining / 2
        # Independently propagate exact coefficients of product min(K_minus,K_plus).
        mass = {(): [F(1)]}
        linear = F(0)
        for depth in range(3):
            following = {}
            for h, poly in mass.items():
                if len(poly) > 1:
                    linear += poly[1] * costs[h]
                for bit in (0, 1):
                    constant = baseline[h] if bit else 1 - baseline[h]
                    slope = -abs(derivative[h]) / 2
                    out = [F(0)] * (len(poly) + 1)
                    for k, v in enumerate(poly):
                        out[k] += v * constant
                        out[k + 1] += v * slope
                    following[h + (bit,)] = out
            mass = following
        self.assertEqual(-linear, predicted)
