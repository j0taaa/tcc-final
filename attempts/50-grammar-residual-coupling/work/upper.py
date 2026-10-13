"""One-preparation upper residual envelope with exact word provenance."""

from bisect import bisect_right
from fractions import Fraction as F
from itertools import accumulate
from math import lcm

from .residual import Residual


def cdf(weights):
    values = [F(w) for w in weights]
    scale = lcm(*(w.denominator for w in values))
    return tuple(accumulate(w.numerator * (scale // w.denominator) for w in values))


def draw(cumulative, rng):
    return bisect_right(cumulative, rng.randrange(cumulative[-1]))


def upper_groups(rows, eta):
    if not 0 < eta <= 1:
        raise ValueError("invalid upper compression tolerance")
    combined = {}
    for ratio, weight, action in rows:
        if ratio < 0 or weight < 0 or not isinstance(weight, int):
            raise ValueError("nonnegative ratio and integer mass required")
        if weight:
            combined.setdefault(ratio, []).append((weight, action))
    source = [(r, sum(w for w, _ in parts), parts) for r, parts in combined.items()]
    source.sort(reverse=True, key=lambda row: row[0])
    result, tail, i = [], 0, 0
    while i < len(source):
        ratio, weight, parts = source[i]
        parts = list(parts)
        i += 1
        if weight <= eta * tail:
            while i < len(source) and weight + source[i][1] <= eta * tail:
                weight += source[i][1]
                parts.extend(source[i][2])
                i += 1
        result.append((ratio, weight, cdf(w for w, _ in parts), tuple(a for _, a in parts)))
        tail += weight
    return result


class UpperResidual(Residual):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profiles, self.totals, self.term_totals, self.exact_cdfs = {}, {}, {}, {}
        eta = F(1, 2 * self.depth)
        self.factor = (1 + eta) ** self.depth
        assert self.factor < 2
        for node in self.plan.order:
            rows, values = [], []
            for t, term in enumerate(self.plan.terms[node]):
                if term.choice is not None:
                    i, j = term.choice
                    a, b = (w[i][j] for w in self.weights)
                    if b:
                        rows.append((F(a, b), b, (t,)))
                    values.append((a, b, a if b else 0))
                elif term.children:
                    left, right = term.children
                    first, second = self.profiles[left], self.profiles[right]
                    if len(first) * len(second) + len(rows) > self.max_pairs:
                        raise RuntimeError("upper provenance budget, not zero residual")
                    rows.extend(
                        (a[0] * b[0], a[1] * b[1], (t, i, j))
                        for i, a in enumerate(first)
                        for j, b in enumerate(second)
                    )
                    values.append(
                        tuple(self.totals[left][j] * self.totals[right][j] for j in range(3))
                    )
                else:
                    rows.append((F(1), 1, (t,)))
                    values.append((1, 1, 1))
                if len(rows) > self.max_pairs:
                    raise RuntimeError("upper provenance sum budget, not zero residual")
            self.profiles[node] = upper_groups(rows, eta)
            self.term_totals[node] = tuple(values)
            self.totals[node] = tuple(sum(v[j] for v in values) for j in range(3))
            self.exact_cdfs[node] = tuple(
                cdf(v[0] if mode == 0 else v[2] if mode == 1 else v[0] - v[2] for v in values)
                for mode in range(3)
            )
        self.threshold = F(self.za, self.zb)
        root = self.plan.root
        self.singular = self.totals[root][0] - self.totals[root][2]
        root_weights = [F(self.singular)] + [
            w * max(F(0), r - self.threshold) for r, w, _, _ in self.profiles[root]
        ]
        self.upper_raw = sum(root_weights, F(0))
        self.root_cdf = cdf(root_weights)
        self.stored_parts = sum(len(atom[3]) for row in self.profiles.values() for atom in row)

    def _finish(self, marks):
        if len(marks) != len(self.ids):
            raise AssertionError("incomplete original-token closure assignment")
        ids = tuple(self.ids[i][marks[i]] for i in range(len(self.ids)))
        a = b = 1
        for i, j in marks.items():
            a *= self.weights[0][i][j]
            b *= self.weights[1][i][j]
        return ids, a, b

    def _common(self, atom, rng):
        pending, marks = [(self.plan.root, atom)], {}
        while pending:
            node, index = pending.pop()
            _, _, cumulative, actions = self.profiles[node][index]
            action = actions[draw(cumulative, rng)]
            term = self.plan.terms[node][action[0]]
            if term.choice is not None:
                i, j = term.choice
                assert i not in marks
                marks[i] = j
            elif term.children:
                left, right = term.children
                pending.extend([(right, action[2]), (left, action[1])])
        return self._finish(marks)

    def _singular(self, rng):
        pending, marks = [(self.plan.root, 2)], {}
        while pending:
            node, mode = pending.pop()
            t = draw(self.exact_cdfs[node][mode], rng)
            term = self.plan.terms[node][t]
            if term.choice is not None:
                i, j = term.choice
                assert i not in marks
                marks[i] = j
            elif term.children:
                left, right = term.children
                if mode == 2:
                    a, b = self.totals[left], self.totals[right]
                    branch = draw(cdf([(a[0] - a[2]) * b[0], a[2] * (b[0] - b[2])]), rng)
                    pending.extend(
                        [(right, 0 if branch == 0 else 2), (left, 2 if branch == 0 else 1)]
                    )
                else:
                    pending.extend([(right, mode), (left, mode)])
        return self._finish(marks)

    def propose(self, rng):
        if not self.upper_raw:
            raise ValueError("zero residual: no conditional law")
        channel = draw(self.root_cdf, rng)
        if channel == 0:
            ids, a, b = self._singular(rng)
            assert a > 0 and b == 0
            return ids, F(1)
        atom = channel - 1
        ids, a, b = self._common(atom, rng)
        ratio = self.profiles[self.plan.root][atom][0]
        return ids, self.correction(a, b, ratio)

    def correction(self, a, b, ratio):
        numerator = max(F(0), F(a, b) - self.threshold)
        denominator = ratio - self.threshold
        accept = numerator / denominator
        assert 0 <= accept <= 1
        return accept

    def sample(self, rng, max_attempts=None):
        if not self.upper_raw:
            raise ValueError("zero residual: no conditional law")
        attempts = 0
        while max_attempts is None or attempts < max_attempts:
            ids, accept = self.propose(rng)
            attempts += 1
            if rng.randrange(accept.denominator) < accept.numerator:
                return ids, attempts
        return None, attempts
