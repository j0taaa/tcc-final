"""Minimal rational reference. Classical tail sparsification and exact correction."""

from fractions import Fraction as F
from math import lcm, prod


def coarsen(atoms, eta):
    if not 0 < eta <= 1:
        raise ValueError("tail tolerance must be in (0,1]")
    combined = {}
    for ratio, weight in atoms:
        if ratio < 0 or weight < 0 or not isinstance(weight, int):
            raise ValueError("nonnegative ratios and integer masses required")
        if weight:
            combined[ratio] = combined.get(ratio, 0) + weight
    rows = sorted(combined.items(), reverse=True)
    result, tail, i = [], 0, 0
    while i < len(rows):
        ratio, weight = rows[i]
        i += 1
        if weight <= eta * tail:
            while i < len(rows) and weight + rows[i][1] <= eta * tail:
                ratio = rows[i][0]
                weight += rows[i][1]
                i += 1
        result.append((ratio, weight))
        tail += weight
    return result


def categorical(weights, rng):
    scale = lcm(*(p.denominator for p in weights))
    integers = [p.numerator * (scale // p.denominator) for p in weights]
    draw = rng.randrange(sum(integers))
    for index, weight in enumerate(integers):
        if draw < weight:
            return index
        draw -= weight
    raise AssertionError("categorical draw out of range")


class Residual:
    def __init__(self, plan, target, draft, max_pairs=1_000_000):
        if target.state != plan.state or draft.state != plan.state:
            raise ValueError("same immutable state and original-ID support required")
        self.plan, self.max_pairs = plan, max_pairs
        self.weights = []
        for data in [target, draft]:
            scaled = []
            for row in data.probabilities:
                scale = lcm(*(p.denominator for p in row))
                scaled.append(tuple(p.numerator * (scale // p.denominator) for p in row))
            self.weights.append(tuple(scaled))
        self.ids = plan.state.support.rows
        if not self.ids:
            raise ValueError("at least one original position required")
        self.scopes, self.costs = {}, {}
        totals = {}
        for node in plan.order:
            scopes, costs, terms = [], [], []
            for term in plan.terms[node]:
                if term.choice is not None:
                    position, index = term.choice
                    scopes.append(frozenset([position]))
                    costs.append(0)
                    terms.append(tuple(w[position][index] for w in self.weights))
                elif term.children:
                    left, right = term.children
                    if self.scopes[left] & self.scopes[right]:
                        raise ValueError("repeated position in product")
                    scopes.append(self.scopes[left] | self.scopes[right])
                    costs.append(self.costs[left] + self.costs[right] + 1)
                    terms.append(tuple(totals[left][j] * totals[right][j] for j in [0, 1]))
                else:
                    scopes.append(frozenset())
                    costs.append(0)
                    terms.append((1, 1))
            if not scopes or any(s != scopes[0] for s in scopes):
                raise ValueError("inconsistent scopes")
            self.scopes[node] = scopes[0]
            totals[node] = tuple(sum(t[j] for t in terms) for j in [0, 1])
            if not scopes[0] and totals[node] != (1, 1):
                raise ValueError("empty-scope multiplicity")
            self.costs[node] = max(costs) + 1 if scopes[0] else 0
        if plan.root is None or not all(totals[plan.root]):
            raise ValueError("undefined posterior: zero valid mass")
        if self.scopes[plan.root] != frozenset(range(len(self.ids))):
            raise ValueError("root does not consume every original position")
        self.za, self.zb = totals[plan.root]
        self.totals = totals
        self.depth = max(1, self.costs[plan.root])
        self.profile_queries = 0

    def _inside(self, evidence, xi, depth):
        if not 0 < xi <= 1:
            raise ValueError("invalid accuracy")
        evidence = {} if evidence is None else evidence
        if any(i not in range(len(self.ids)) or v not in self.ids[i] for i, v in evidence.items()):
            raise ValueError("evidence outside declared original support")
        eta = xi / (2 * depth)
        factor = (1 + eta) ** depth
        assert factor <= 1 + xi
        profiles, totals = {}, {}
        self.profile_queries += 1
        for node in self.plan.order:
            atoms, term_totals = [], []
            for term in self.plan.terms[node]:
                if term.choice is not None:
                    i, j = term.choice
                    a, b = (w[i][j] for w in self.weights)
                    if i in evidence and self.ids[i][j] != evidence[i]:
                        a = b = 0
                    part = [(F(a, b), b)] if b else []
                    term_totals.append((a, b, a if b else 0))
                elif term.children:
                    left, right = term.children
                    if len(profiles[left]) * len(profiles[right]) > self.max_pairs:
                        raise RuntimeError("profile resource budget, not zero residual")
                    part = coarsen(
                        [(r * s, w * z) for r, w in profiles[left] for s, z in profiles[right]], eta
                    )
                    term_totals.append(tuple(totals[left][j] * totals[right][j] for j in range(3)))
                else:
                    part = [(F(1), 1)]
                    term_totals.append((1, 1, 1))
                atoms.extend(part)
                if len(atoms) > self.max_pairs:
                    raise RuntimeError("profile sum budget, not zero residual")
            profiles[node] = coarsen(atoms, eta)
            totals[node] = tuple(sum(t[j] for t in term_totals) for j in range(3))
        return profiles, totals, factor

    def bound(self, evidence=None, xi=F(1, 4), multiplier=F(1)):
        if multiplier < 0:
            raise ValueError("invalid threshold")
        profiles, totals, factor = self._inside(evidence, xi, self.depth)
        a, _, common_a = totals[self.plan.root]
        singular = F(a - common_a, self.za)
        threshold = multiplier * F(self.za, self.zb)
        common = (
            sum((w * max(F(0), r - threshold) for r, w in profiles[self.plan.root]), F(0)) / self.za
        )
        return singular + common, singular + factor * common

    def point(self, ids, which):
        if len(ids) != len(self.ids):
            raise ValueError("wrong number of original positions")
        present = {}
        for node in self.plan.order:
            present[node] = any(
                ids[term.choice[0]] == self.ids[term.choice[0]][term.choice[1]]
                if term.choice is not None
                else all(present[child] for child in term.children)
                for term in self.plan.terms[node]
            )
        if not present[self.plan.root]:
            return F(0)
        raw = prod(self.weights[which][i][self.ids[i].index(v)] for i, v in enumerate(ids))
        return F(raw, self.za if which == 0 else self.zb)

    def propose(self, rng):
        xi = F(1, 4 * len(self.ids))
        evidence, density = {}, F(1)
        for i, ids in enumerate(self.ids):
            weights = [self.bound({**evidence, i: v}, xi=xi)[0] for v in ids]
            total = sum(weights, F(0))
            if not total:
                raise ValueError("zero residual prefix")
            j = categorical(weights, rng)
            evidence[i] = ids[j]
            density *= weights[j] / total
        return tuple(evidence[i] for i in range(len(self.ids))), density

    def sample(self, rng, max_attempts=None):
        xi = F(1, 4 * len(self.ids))
        lower, upper = self.bound(xi=xi)
        if not lower:
            raise ValueError("zero residual: no conditional law")
        envelope = (1 + xi) ** len(self.ids) * upper
        attempts = 0
        while max_attempts is None or attempts < max_attempts:
            ids, proposal = self.propose(rng)
            weight = max(F(0), self.point(ids, 0) - self.point(ids, 1))
            accept = weight / (envelope * proposal)
            assert 0 <= accept <= 1
            attempts += 1
            if rng.randrange(accept.denominator) < accept.numerator:
                return ids, attempts
        return None, attempts  # explicit FAIL; never substitute an uncorrected draw

    def correct_draft(self, ids, rng, max_attempts=None):
        p, q = self.point(ids, 0), self.point(ids, 1)
        if not q:
            raise ValueError("draft has zero declared density")
        accept = min(F(1), p / q)
        if rng.randrange(accept.denominator) < accept.numerator:
            return ids, 0
        return self.sample(rng, max_attempts)
