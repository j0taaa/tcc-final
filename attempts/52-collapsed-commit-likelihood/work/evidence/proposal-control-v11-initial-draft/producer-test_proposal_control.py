"""Independent original-word/anchor/path oracle; no real neural computation."""

import json
import unittest
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction as F

from .numeric_json import TAIL, NumericJSON
from .prefix_anchor import PrefixAnchor
from .proposal_control import ProposalControl, policy_score
from .test_prefix_anchor import direct_score, language, make
from .test_visible_elbo import World


@dataclass(frozen=True)
class LiteralProxy(NumericJSON):
    literal: bytes = b'{"answer":1}'

    def __post_init__(self):
        super().__post_init__()
        if not 0 < len(self.literal) <= 20:
            raise ValueError("literal must fit the small oracle DFA")

    def step(self, state, token):
        if state == TAIL:
            return TAIL if token == self.pad else -1
        if token == self.eos:
            return TAIL if state == 20 else -1
        for byte in self.emissions[token]:
            if state == 20 or byte != self.literal[state]:
                return -1
            state += 1
            if state == len(self.literal):
                state = 20
        return state


def proxy(base, literal=b'{"answer":1}'):
    return LiteralProxy(base.language.emissions, base.language.eos, base.language.pad, literal)


def good(base, word):
    return b"".join(base.language.emissions[v] for v in word[:-1]) == b'{"answer":1}'


def add(a, b):
    return tuple(x + y for x, y in zip(a, b, strict=True))


def scale(a, factor):
    return tuple(factor * x for x in a)


def groups(policy, law):
    result = defaultdict(list)
    for (word, anchor, action), probability in law.items():
        score = policy_score(direct_score(policy, word, anchor, action, policy.prior))
        result[action].append((word, probability, score))
    return result


def moments(entries):
    zero = (F(), F())
    mean = zero
    second = [[F(), F()], [F(), F()]]
    for probability, vector in entries:
        mean = add(mean, scale(vector, probability))
        for i in range(2):
            for j in range(2):
                second[i][j] += probability * vector[i] * vector[j]
    return mean, [[second[i][j] - mean[i] * mean[j] for j in range(2)] for i in range(2)]


class ProposalControlTests(unittest.TestCase):
    def test_exact_projection_aliases_variable_stop_and_zero_events(self):
        checked = triples = zero_actions = 0
        for n, fixed in ((2, {}), (3, {}), (4, {3: 5}), (3, {0: 0})):
            base, law = make(n, fixed)
            control = ProposalControl(base, proxy(base))
            for action, entries in groups(base, law).items():
                p = sum((q for _, q, _ in entries), F())
                expected = control.zero
                posterior = F()
                for word, q, score in entries:
                    if good(base, word):
                        posterior += q / p
                        expected = add(expected, scale(score, q / p))
                actual_p, actual = control(action)
                self.assertEqual((actual_p, actual), (posterior, expected))
                zero_actions += int(not actual_p)
                checked += 1
            triples += len(law)
            impossible = ProposalControl(base, proxy(base, b'{"answer":2}'))
            self.assertIsNone(impossible.proxy)
            for action in groups(base, law):
                self.assertEqual(impossible(action), (F(), control.zero))
        self.assertGreater(zero_actions, 0)
        # All compatible segmentations/empty aliases, not one canonical ID word.
        base, law = make(3)
        accepted = {word for word, _, _ in law if good(base, word)}
        self.assertIn((1, 3, 5), accepted)
        self.assertIn((4, 1, 5), accepted)
        self.assertIn((1, 5), accepted)
        print(json.dumps({"proposal_control_laws": 4, "triples": triples,
                          "actions": checked, "zero_proxy_actions": zero_actions}))

    def test_full_and_projected_zero_mean_but_naive_collapses_are_biased(self):
        base, law = make(3)
        control = ProposalControl(base, proxy(base))
        full = projected = naive = naive_class = naive_head = control.zero
        head = [[F() for _ in range(base.v)] for _ in range(base.n)]
        for (word, anchor, action), p in law.items():
            counts, gates, rr = direct_score(base, word, anchor, action, base.prior)
            if good(base, word):
                full = add(full, scale(policy_score((counts, gates, rr)), p))
                naive = add(naive, scale(policy_score(base.action_statistics(action)[1:]), p))
                naive_class = add(naive_class, scale(policy_score(base.class_score(word, action)), p))
                for i in range(base.n):
                    for v in range(base.v):
                        head[i][v] += p * counts[i][v]
        for action, entries in groups(base, law).items():
            p = sum((q for _, q, _ in entries), F())
            z, correction = control(action)
            projected = add(projected, scale(correction, p))
            naive_head = add(
                naive_head, scale(policy_score(base.action_statistics(action)[1:]), p * z)
            )
        self.assertEqual(full, control.zero)
        self.assertEqual(projected, control.zero)
        self.assertEqual(naive, naive_head)
        self.assertNotEqual(naive, control.zero)
        self.assertNotEqual(naive_class, control.zero)
        self.assertTrue(any(value for row in head for value in row))
        print(json.dumps({"naive_visible_bias_max": str(max(map(abs, naive))),
                          "naive_class_bias_max": str(max(map(abs, naive_class))),
                          "frozen_head_restriction_witness": True}))

    def test_matched_conditional_covariance_identity(self):
        base, law = make(3)
        control = ProposalControl(base, proxy(base))
        full_entries, visible_entries = [], []
        hidden_cov = [[F(), F()], [F(), F()]]
        baseline, coefficient = F(1, 3), F(2, 3)

        def project(vector):
            return (sum(vector[:base.n * base.v], F()),
                    sum(((i + 1) * vector[base.n * base.v + i] for i in range(base.n)), F()))

        for action, entries in groups(base, law).items():
            p = sum((q for _, q, _ in entries), F())
            reward = F(any(i == 0 and v == 1 for i, v in action))
            _, correction = control(action)
            s = policy_score(base.action_statistics(action)[1:])
            visible = project(add(scale(s, reward - baseline), scale(correction, -coefficient)))
            conditional = []
            for word, q, score in entries:
                vector = project(scale(score, reward - baseline - coefficient * good(base, word)))
                full_entries.append((q, vector))
                conditional.append((q / p, vector))
            mean, covariance = moments(conditional)
            self.assertEqual(mean, visible)
            for i in range(2):
                for j in range(2):
                    hidden_cov[i][j] += p * covariance[i][j]
            visible_entries.append((p, visible))
        fm, fc = moments(full_entries)
        vm, vc = moments(visible_entries)
        self.assertEqual(fm, vm)
        difference = [[fc[i][j] - vc[i][j] for j in range(2)] for i in range(2)]
        self.assertEqual(difference, hidden_cov)
        self.assertTrue(all(difference[i][i] >= 0 for i in range(2)))
        self.assertGreaterEqual(difference[0][0] * difference[1][1] - difference[0][1] ** 2, 0)

    def test_adaptive_visible_paths_and_exact_reward_derivative(self):
        total_paths = total_states = 0
        for n in (2, 3):
            world = World(n, 1)
            outputs = world.outputs()
            local = {}
            for key in world.states:
                fixed = dict(key)
                original, law = make(n, fixed, context=True)
                gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in original.rows)
                base = PrefixAnchor(language(), original.rows, gates, original.u, fixed)
                control = ProposalControl(base, proxy(base))
                aa = tuple(F((i + 1) * (1 + len(fixed))) for i in range(n))
                rr = tuple(F(i + 1 + len(fixed)) for i in range(n))

                def direction(vector, aa=aa, rr=rr):
                    return sum((aa[i] * sum(vector[i * 8:(i + 1) * 8], F())
                                + rr[i] * vector[n * 8 + i] for i in range(n)), F())

                for action, probability in world.kernel(key).items():
                    _, correction = control(action)
                    score = direction(policy_score(base.action_statistics(action)[1:]))
                    self.assertEqual(score, world.scores[key, action])
                    local[key, action] = score, direction(correction), F(len(key), n + 1)
                total_states += 1
            result = [F(), F(), F()]

            def visit(key, mass, score, correction, baseline_score):
                nonlocal total_paths
                terminal = world.terminal(dict(key))
                if terminal is not None:
                    reward = F(good(original, terminal))
                    result[0] += mass * reward * score
                    result[1] += mass * correction
                    result[2] += mass * (reward * score - baseline_score - F(2, 3) * correction)
                    total_paths += 1
                    return
                for action, p in world.kernel(key).items():
                    s, c, v = local[key, action]
                    following = tuple(sorted({**dict(key), **dict(action)}.items()))
                    visit(following, mass * p.value, score + s, correction + c, baseline_score + v * s)

            visit((), F(1), F(), F(), F())
            true = sum((p.derivative for word, p in outputs.items() if good(original, word)), F())
            self.assertEqual(result, [true, F(), true])
        print(json.dumps({"adaptive_proxy_states": total_states, "visible_paths": total_paths}))

    def test_original_id_and_subset_contract_failures_remain_explicit(self):
        base, law = make(2)
        wrong = LiteralProxy((*base.language.emissions, b""), 5, 6)
        with self.assertRaisesRegex(ValueError, "every original ID"):
            ProposalControl(base, wrong)
        control = ProposalControl(base, proxy(base))
        with self.assertRaisesRegex(ValueError, "positive visible"):
            control(((0, 5),))
        with self.assertRaisesRegex(ValueError, "sorted distinct"):
            control(())
        self.assertTrue(law)


if __name__ == "__main__":
    unittest.main()
