"""Rational auxiliary-anchor reference, preserving the current word proposal."""

from fractions import Fraction as F
from math import lcm


def categorical(weights, rng):
    denominator = lcm(*(w.denominator for w in weights))
    counts = [int(w * denominator) for w in weights]
    ticket = rng.randrange(sum(counts))
    for i, count in enumerate(counts):
        if ticket < count:
            return i
        ticket -= count
    raise AssertionError("integer category did not cover its source")


class AnchorPolicy:
    def __init__(self, graph, rows, gates, anchors, active):
        graph.validate(rows)
        if not active or len(set(active)) != len(active):
            raise ValueError("nonempty distinct active positions required")
        self.active = frozenset(active)
        if any(not 0 <= i < len(rows) for i in active):
            raise ValueError("active position outside original canvas")
        if len(gates) != len(rows) or any(
            len(g) != len(w) for g, w in zip(gates, rows, strict=True)
        ):
            raise ValueError("gate/original-ID domains differ")
        if any(type(g) is not F or not 0 < g < 1 for i in active for g in gates[i]):
            raise ValueError("rational gates strictly between0 and1 required")
        if (
            len(anchors) != len(rows)
            or any(
                type(p) is not F or p < 0 or (i not in self.active and p != 0)
                for i, p in enumerate(anchors)
            )
            or sum(anchors, F()) != 1
        ):
            raise ValueError("anchor probabilities must sum to1 on active positions")
        self.graph, self.rows, self.gates, self.anchors = graph, rows, gates, anchors
        self.mass, self.prior = graph.infer(rows)
        if not self.mass:
            raise ValueError("zero original proposal mass")
        # Minimal sampler reference; a performance backend must share this
        # inside pass with its base outside, rather than charging duplicates.
        self.beta = [tuple(F(a) for a in graph.accepting)]
        for i in range(len(rows) - 1, -1, -1):
            self.beta.append(
                tuple(
                    sum((rows[i][v] * self.beta[-1][t] for v, t in edges), F())
                    for edges in graph.layers[i]
                )
            )
        self.beta.reverse()

    def action_statistics(self, action):
        positions = [i for i, _ in action]
        if not action or positions != sorted(set(positions)):
            raise ValueError("sorted distinct nonempty action required")
        if any(i not in self.active or not 0 <= v < len(self.rows[i]) for i, v in action):
            raise ValueError("action outside active original-ID domain")
        retained = dict(action)
        terms = {i: self.anchors[i] / self.gates[i][v] for i, v in action}
        scalar = sum(terms.values(), F())
        if not scalar:
            return F(), None, None, None
        filtered = tuple(
            tuple(
                w * self.gates[i][v] * (v == retained[i])
                if i in retained
                else w * (1 - self.gates[i][v])
                if i in self.active
                else w
                for v, w in enumerate(row)
            )
            for i, row in enumerate(self.rows)
        )
        mass, posterior = self.graph.infer(filtered)
        if not mass:
            return F(), None, None, None
        rho = tuple(terms.get(i, F()) / scalar for i in range(len(self.rows)))
        ww = tuple(
            tuple(post - pre for post, pre in zip(a, b, strict=True))
            for a, b in zip(posterior, self.prior, strict=True)
        )
        hh = tuple(
            tuple(
                post * (1 - rho[i]) * (F(i in retained) - self.gates[i][v])
                if i in self.active
                else F()
                for v, post in enumerate(row)
            )
            for i, row in enumerate(posterior)
        )
        rr = tuple(a - b for a, b in zip(rho, self.anchors, strict=True))
        return mass * scalar / self.mass, ww, hh, rr

    def full_score(self, word, anchor, action):
        retained = dict(action)
        if anchor not in retained or not self.anchors[anchor]:
            raise ValueError("retained positive-probability anchor required")
        ww = tuple(
            tuple(F(word[i] == v) - pre for v, pre in enumerate(row))
            for i, row in enumerate(self.prior)
        )
        hh = tuple(
            tuple(
                F(word[i] == v) * (F(i in retained) - self.gates[i][v])
                if i in self.active and i != anchor
                else F()
                for v in range(len(row))
            )
            for i, row in enumerate(self.rows)
        )
        rr = tuple(F(anchor == i) - p for i, p in enumerate(self.anchors))
        return ww, hh, rr

    def sample(self, rng):
        anchor = categorical(self.anchors, rng)
        state, word = 0, []
        for i, layer in enumerate(self.graph.layers):
            edges = layer[state]
            masses = [self.rows[i][v] * self.beta[i + 1][target] for v, target in edges]
            v, state = edges[categorical(masses, rng)]
            word.append(v)
        action = []
        for i in sorted(self.active):
            g = self.gates[i][word[i]]
            if i == anchor or rng.randrange(g.denominator) < g.numerator:
                action.append((i, word[i]))
        return tuple(word), anchor, tuple(action)

    def expected_releases(self):
        return 1 + sum(
            (
                (1 - self.anchors[i])
                * sum((self.prior[i][v] * self.gates[i][v] for v in range(len(self.rows[i]))), F())
                for i in self.active
            ),
            F(),
        )
