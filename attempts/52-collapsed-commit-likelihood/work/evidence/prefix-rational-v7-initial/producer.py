"""Minimal rational weighted-prefix reference. Not a production/new compiler."""

from fractions import Fraction as F

from .numeric_json import STATE_COUNT, TAIL


class PrefixAnchor:
    def __init__(self, language, rows, gates, u, fixed=None):
        self.language, self.rows, self.gates, self.u = language, rows, gates, u
        self.n, self.v = len(rows), len(language.emissions)
        self.fixed = dict(fixed or {})
        if self.v > 256 or self.n > 64:
            raise ValueError("this explicit rational compiler is a small-oracle API")
        if not self.n or any(len(row) != self.v for row in rows):
            raise ValueError("nonempty original-ID head rows required")
        if any(type(c) is not F or c < 0 for row in rows for c in row):
            raise ValueError("nonnegative rational original head required")
        if any(sum(row, F()) != 1 for row in rows):
            raise ValueError("original full-V rows must normalize to1")
        if any(
            type(i) is not int or type(v) is not int or not 0 <= i < self.n or not 0 <= v < self.v
            for i, v in self.fixed.items()
        ):
            raise ValueError("fixed original IDs outside canvas")
        self.active = tuple(i for i in range(self.n) if i not in self.fixed)
        if not self.active:
            raise ValueError("terminal/no-active state has no release action")
        if len(gates) != self.n or any(len(row) != self.v for row in gates):
            raise ValueError("gate domain differs from original vocabulary")
        if any(type(g) is not F or not 0 < g < 1 for i in self.active for g in gates[i]):
            raise ValueError("active rational gates strictly between0 and1 required")
        if len(u) != self.n or any(type(u[i]) is not F or u[i] <= 0 for i in self.active):
            raise ValueError("positive rational active anchor weights required")
        self.h = tuple(sum((u[j] for j in self.active if j <= i), F()) for i in range(self.n))
        for i, v in self.fixed.items():
            if (
                v == language.eos
                and i == max(self.fixed)
                and all(j in self.fixed for j in range(i + 1))
            ):
                if language.accepts(tuple(self.fixed[j] for j in range(i + 1))):
                    raise ValueError("already complete prefix must terminate before release")
        self.mass, self.prior, self.prior_lengths = self._infer(None)
        if not self.mass:
            raise ValueError("zero compatible prefix mass")

    def pi(self, stop):
        denominator = self.h[stop - 1]
        if not denominator:
            raise ValueError("nonterminal prefix has no eligible anchor")
        return tuple(
            self.u[i] / denominator if i in self.active and i < stop else F() for i in range(self.n)
        )

    def _infer(self, action):
        """A None-labelled accepting edge is an integrated suffix, not a model ID."""
        retained = {} if action is None else dict(action)
        minimum = max((*self.fixed, *retained), default=-1)
        layers = []
        for i in range(self.n):
            layer = []
            for state in range(STATE_COUNT):
                if state == TAIL:
                    layer.append(((None, TAIL, F(1)),))
                    continue
                edges = []
                for token in range(self.v):
                    if i in self.fixed:
                        weight = F(token == self.fixed[i])
                    else:
                        weight = self.rows[i][token]
                        if action is not None:
                            weight *= (
                                self.gates[i][token] * F(token == retained[i])
                                if i in retained
                                else 1 - self.gates[i][token]
                            )
                    if not weight:
                        continue
                    target = self.language.step(state, token)
                    if target < 0:
                        continue
                    if target == TAIL:
                        if i < minimum:
                            continue
                        if action is not None:
                            if not self.h[i]:
                                continue
                            weight /= self.h[i]
                    edges.append((token, target, weight))
                layer.append(tuple(edges))
            layers.append(tuple(layer))
        beta = [[F(s == TAIL) for s in range(STATE_COUNT)]]
        for layer in reversed(layers):
            beta.append(
                [
                    sum((weight * beta[-1][target] for _, target, weight in edges), F())
                    for edges in layer
                ]
            )
        beta.reverse()
        mass = beta[0][0]
        counts = [[F() for _ in range(self.v)] for _ in range(self.n)]
        stops = [F() for _ in range(self.n)]
        if not mass:
            return mass, tuple(map(tuple, counts)), tuple(stops)
        alpha = [F(s == 0) for s in range(STATE_COUNT)]
        for i, layer in enumerate(layers):
            following = [F() for _ in range(STATE_COUNT)]
            for s, edges in enumerate(layer):
                if not alpha[s]:
                    continue
                for token, target, weight in edges:
                    flow = alpha[s] * weight
                    following[target] += flow
                    if token is not None:
                        contribution = flow * beta[i + 1][target] / mass
                        counts[i][token] += contribution
                        if target == TAIL:
                            stops[i] += contribution
            alpha = following
        return mass, tuple(map(tuple, counts)), tuple(stops)

    def _action(self, action):
        positions = [i for i, _ in action]
        if not action or positions != sorted(set(positions)):
            raise ValueError("sorted distinct nonempty action required")
        if any(
            type(i) is not int or type(v) is not int or i not in self.active or not 0 <= v < self.v
            for i, v in action
        ):
            raise ValueError("action outside active original IDs")
        terms = {i: self.u[i] / self.gates[i][v] for i, v in action}
        scalar = sum(terms.values(), F())
        return scalar, tuple(terms.get(i, F()) / scalar for i in range(self.n))

    def action_statistics(self, action):
        scalar, rho = self._action(action)
        z, nu, stops = self._infer(action)
        if not z:
            return F(), None, None, None
        retained = dict(action)
        counts = tuple(
            tuple(nu[i][v] - self.prior[i][v] if i in self.active else F() for v in range(self.v))
            for i in range(self.n)
        )
        gates = tuple(
            tuple(
                nu[i][v] * (1 - rho[i]) * (F(i in retained) - self.gates[i][v])
                if i in self.active
                else F()
                for v in range(self.v)
            )
            for i in range(self.n)
        )
        anchor = tuple(
            rho[i] - sum((p * self.pi(t + 1)[i] for t, p in enumerate(stops) if p), F())
            if i in self.active
            else F()
            for i in range(self.n)
        )
        return scalar * z / self.mass, counts, gates, anchor

    def _compatible(self, word, action):
        self._action(action)
        if (
            not word
            or word[-1] != self.language.eos
            or self.language.eos in word[:-1]
            or not self.language.accepts(word)
        ):
            raise ValueError("valid original first-EOT prefix required")
        if any(i >= len(word) or word[i] != v for i, v in (*self.fixed.items(), *action)):
            raise ValueError("prefix must preserve all original fixed/retained IDs")
        if any(not self.rows[i][v] for i, v in enumerate(word) if i in self.active):
            raise ValueError("prefix outside positive proposal support")

    def full_score(self, word, anchor, action):
        self._compatible(word, action)
        stop = len(word)
        retained = dict(action)
        if anchor not in retained or not anchor < stop or retained[anchor] != word[anchor]:
            raise ValueError("original eligible anchor must be retained")
        counts = tuple(
            tuple(
                F(i < stop and word[i] == v) - self.prior[i][v] if i in self.active else F()
                for v in range(self.v)
            )
            for i in range(self.n)
        )
        gates = tuple(
            tuple(
                F(i < stop and word[i] == v) * (F(i in retained) - self.gates[i][v])
                if i in self.active and i != anchor
                else F()
                for v in range(self.v)
            )
            for i in range(self.n)
        )
        pi = self.pi(stop)
        return (
            counts,
            gates,
            tuple(F(i == anchor) - pi[i] if i in self.active else F() for i in range(self.n)),
        )

    def cheap_anchor_score(self, word, action):
        self._compatible(word, action)
        _, rho = self._action(action)
        stop, retained = len(word), dict(action)
        counts = tuple(
            tuple(
                F(i < stop and word[i] == v) - self.prior[i][v] if i in self.active else F()
                for v in range(self.v)
            )
            for i in range(self.n)
        )
        gates = tuple(
            tuple(
                F(i < stop and word[i] == v) * (1 - rho[i]) * (F(i in retained) - self.gates[i][v])
                if i in self.active
                else F()
                for v in range(self.v)
            )
            for i in range(self.n)
        )
        pi = self.pi(stop)
        return (
            counts,
            gates,
            tuple(rho[i] - pi[i] if i in self.active else F() for i in range(self.n)),
        )

    def class_score(self, word, action):
        """Conditional ID mean given the sampled global class path and action."""
        self._compatible(word, action)
        _, rho = self._action(action)
        _, members, mapping = self.language.classes()
        retained = dict(action)
        counts = [[F() for _ in range(self.v)] for _ in range(self.n)]
        gates = [[F() for _ in range(self.v)] for _ in range(self.n)]
        for i in self.active:
            q = [F() for _ in range(self.v)]
            if i < len(word):
                if i in retained:
                    q[retained[i]] = F(1)
                else:
                    group = members[mapping[word[i]]]
                    mass = sum((self.rows[i][v] * (1 - self.gates[i][v]) for v in group), F())
                    for v in group:
                        q[v] = self.rows[i][v] * (1 - self.gates[i][v]) / mass
            for v in range(self.v):
                counts[i][v] = q[v] - self.prior[i][v]
                gates[i][v] = q[v] * (1 - rho[i]) * (F(i in retained) - self.gates[i][v])
        pi = self.pi(len(word))
        return (
            tuple(map(tuple, counts)),
            tuple(map(tuple, gates)),
            tuple(rho[i] - pi[i] if i in self.active else F() for i in range(self.n)),
        )
