"""Rational smooth joint policy. Classical positive OR/evidence inference."""

from fractions import Fraction as F
from math import lcm


class SmoothPolicy:
    def __init__(self, graph, rows, gates, active):
        graph.validate(rows)
        if not active or len(set(active)) != len(active):
            raise ValueError("nonempty distinct active positions required")
        if any(not 0 <= i < len(rows) for i in active):
            raise ValueError("active position out of range")
        if len(gates) != len(rows) or any(
            len(g) != len(w) for g, w in zip(gates, rows, strict=True)
        ):
            raise ValueError("gate/original-ID domains differ")
        if any(type(g) is not F or not 0 < g < 1 for i in active for g in gates[i]):
            raise ValueError("active gates must be rational and strictly between0 and1")
        self.graph, self.rows, self.gates, self.active = graph, rows, gates, frozenset(active)
        self.beta = [[[F(), F(a)] for a in graph.accepting]]
        for i in range(len(rows) - 1, -1, -1):
            following = self.beta[-1]
            layer = []
            for edges in graph.layers[i]:
                values = []
                for seen in range(2):
                    value = F()
                    for v, target in edges:
                        if i in self.active:
                            g = gates[i][v]
                            value += rows[i][v] * (
                                (1 - g) * following[target][seen] + g * following[target][1]
                            )
                        else:
                            value += rows[i][v] * following[target][seen]
                    values.append(value)
                layer.append(values)
            self.beta.append(layer)
        self.beta.reverse()
        self.mass = self.beta[0][0][0]
        if not self.mass:
            raise ValueError("zero nonempty original-word mass")
        self.joint_marginals = self._outside()

    def choices(self, i, state, seen):
        """(original ID, release bit, target, new seen bit, conditional mass)."""
        choices = []
        for v, target in self.graph.layers[i][state]:
            for bit in range(2) if i in self.active else range(1):
                new_seen = seen | bit
                g = self.gates[i][v]
                gate = (g if bit else 1 - g) if i in self.active else F(1)
                mass = self.rows[i][v] * gate * self.beta[i + 1][target][new_seen]
                if mass:
                    choices.append((v, bit, target, new_seen, mass))
        return choices

    def _outside(self):
        alpha = [[F(1), F()]]
        result = []
        for i, layer in enumerate(self.graph.layers):
            following = [[F(), F()] for _ in self.beta[i + 1]]
            counts = [[F(), F()] for _ in self.rows[i]]
            for state, edges in enumerate(layer):
                for seen in range(2):
                    for v, target in edges:
                        for bit in range(2) if i in self.active else range(1):
                            new_seen = seen | bit
                            g = self.gates[i][v]
                            gate = (g if bit else 1 - g) if i in self.active else F(1)
                            flow = alpha[state][seen] * self.rows[i][v] * gate
                            following[target][new_seen] += flow
                            counts[v][bit] += flow * self.beta[i + 1][target][new_seen]
            result.append(tuple(tuple(x / self.mass for x in pair) for pair in counts))
            alpha = following
        return tuple(result)

    def action_statistics(self, action):
        indices = [i for i, _ in action]
        if not action or indices != sorted(set(indices)):
            raise ValueError("sorted distinct nonempty observed action required")
        if any(i not in self.active or not 0 <= v < len(self.rows[i]) for i, v in action):
            raise ValueError("observed action outside active original-ID domain")
        retained, filtered = dict(action), []
        for i, row in enumerate(self.rows):
            filtered.append(
                tuple(
                    w * self.gates[i][v] * (v == retained[i])
                    if i in retained
                    else w * (1 - self.gates[i][v])
                    if i in self.active
                    else w
                    for v, w in enumerate(row)
                )
            )
        z, posterior = self.graph.infer(tuple(filtered))
        if not z:
            return F(), None, None
        weight_score, gate_score = [], []
        for i, row in enumerate(posterior):
            ww, hh = [], []
            for v, post in enumerate(row):
                old = sum(self.joint_marginals[i][v], F())
                ww.append(post - old)
                hh.append(
                    post * (F(i in retained) - self.gates[i][v])
                    - self.joint_marginals[i][v][1]
                    + self.gates[i][v] * old
                    if i in self.active
                    else F()
                )
            weight_score.append(tuple(ww))
            gate_score.append(tuple(hh))
        return z / self.mass, tuple(weight_score), tuple(gate_score)

    def full_score(self, word, action):
        retained = dict(action)
        ww, hh = [], []
        for i, row in enumerate(self.rows):
            wr, hr = [], []
            for v in range(len(row)):
                old = sum(self.joint_marginals[i][v], F())
                wr.append(F(word[i] == v) - old)
                hr.append(
                    F(word[i] == v) * (F(i in retained) - self.gates[i][v])
                    - self.joint_marginals[i][v][1]
                    + self.gates[i][v] * old
                    if i in self.active
                    else F()
                )
            ww.append(tuple(wr))
            hh.append(tuple(hr))
        return tuple(ww), tuple(hh)

    def sample(self, rng):
        """Exact rational categorical draws, ideal fair-bit model."""
        state = seen = 0
        word, action = [], []
        for i in range(len(self.rows)):
            choices = self.choices(i, state, seen)
            denominator = lcm(*(c[-1].denominator for c in choices))
            counts = [int(c[-1] * denominator) for c in choices]
            ticket = rng.randrange(sum(counts))
            for choice, count in zip(choices, counts, strict=True):
                if ticket < count:
                    v, bit, state, seen, _ = choice
                    word.append(v)
                    if bit:
                        action.append((i, v))
                    break
                ticket -= count
        return tuple(word), tuple(action)
