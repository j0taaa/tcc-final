"""Exact integer posterior for overlapping lexical groups, original marginals."""

from bisect import bisect_right
from fractions import Fraction
from math import isfinite, prod


class Weights:
    def __init__(self, rows, canvas, vocabulary_size):
        self.rows, self.denominators = [], []
        self.canvas = tuple(canvas)
        self.vocabulary_size = vocabulary_size
        if len(rows) != len(canvas):
            raise ValueError("probability rows differ from physical slots")
        for row, fixed in zip(rows, canvas, strict=True):
            if fixed is not None:
                if type(fixed) is not int or not 0 <= fixed < vocabulary_size:
                    raise ValueError("invalid original fixed token")
                self.rows.append({fixed: 1})
                self.denominators.append(1)
                continue
            if len(row) != vocabulary_size or any(not isfinite(x) or x < 0 for x in row):
                raise ValueError("invalid full-vocabulary probability row")
            ratios = [float(x).as_integer_ratio() for x in row]
            bits = max((d.bit_length() - 1 for n, d in ratios if n), default=0)
            integers = tuple(n << (bits - (d.bit_length() - 1)) if n else 0 for n, d in ratios)
            denominator = sum(integers)
            if not denominator:
                raise ValueError("zero model row")
            self.rows.append(integers)
            self.denominators.append(denominator)

    def at(self, p, t):
        row = self.rows[p]
        return row.get(t, 0) if isinstance(row, dict) else row[t]


class Posterior:
    def __init__(self, prepared, weights):
        if weights.vocabulary_size != prepared.table.adapter.vocabulary_size:
            raise ValueError("weights changed original vocabulary")
        if any(t is not None and t != weights.canvas[p] for p, t in enumerate(prepared.canvas)):
            raise ValueError("weights changed initial fixed original frame")
        self.prepared, self.weights = prepared, weights
        self.leaf, self.inside, self.cdf = {}, [0] * len(prepared.plan.terms), {}
        table = prepared.table
        self.class_weights = []
        if prepared.kind != "raw":
            for row in weights.rows:
                sums = [0] * len(table.classes)
                if isinstance(row, dict):
                    for t, w in row.items():
                        sums[table.class_of[t]] += w
                else:
                    for t, w in enumerate(row):
                        sums[table.class_of[t]] += w
                self.class_weights.append(sums)
        for p, c in prepared.members:
            if prepared.kind == "raw":
                mass = weights.at(p, c)
            elif prepared.kind == "global":
                mass = self.class_weights[p][c]
            else:
                mass = sum(self.class_weights[p][cid] for cid in table.local_to_class[c])
            self.leaf[p, c] = mass
        plan = prepared.plan
        for node in plan.order:
            self.inside[node] = sum(self.term_mass(term) for term in plan.terms[node])
        self.total = 0 if plan.root is None else self.inside[plan.root]
        self.mass = Fraction(self.total, prod(weights.denominators))
        if not 0 <= self.mass <= 1:
            raise RuntimeError("valid probability outside [0,1]")

    def term_mass(self, term):
        if term.choice is not None:
            p, i = term.choice
            return self.leaf[p, self.prepared.rows[p][i]]
        return prod(self.inside[c] for c in term.children)

    @staticmethod
    def choose(masses, rng):
        total = sum(masses)
        if total <= 0:
            raise ValueError("zero conditional choice")
        positive = [i for i, m in enumerate(masses) if m]
        if len(positive) == 1:
            return positive[0]
        point = rng.randrange(total)
        for i, m in enumerate(masses):
            if point < m:
                return i
            point -= m
        raise RuntimeError("integer choice lost probability")

    def sample(self, rng):
        if not self.total:
            raise ValueError("zero_valid_mass")
        plan = self.prepared.plan
        tokens = [None] * len(self.weights.canvas)
        pending = [plan.root]
        while pending:
            node = pending.pop()
            terms = plan.terms[node]
            term = terms[self.choose([self.term_mass(t) for t in terms], rng)]
            if term.choice is None:
                pending.extend(term.children)
                continue
            p, i = term.choice
            code = self.prepared.rows[p][i]
            key = p, code
            if self.weights.canvas[p] is not None:
                if tokens[p] is not None:
                    raise RuntimeError("sample repeated physical slot")
                tokens[p] = self.weights.canvas[p]
                continue
            if key not in self.cdf:
                members = self.prepared.members[key]
                cumulative, total = [], 0
                for t in members:
                    total += self.weights.at(p, t)
                    cumulative.append(total)
                self.cdf[key] = members, tuple(cumulative)
            members, cumulative = self.cdf[key]
            if tokens[p] is not None:
                raise RuntimeError("sample repeated physical slot")
            tokens[p] = (
                members[0]
                if len(members) == 1
                else members[bisect_right(cumulative, rng.randrange(cumulative[-1]))]
            )
        if any(t is None for t in tokens):
            raise RuntimeError("sample omitted physical slot")
        return tuple(tokens)

    def marginals(self):
        if not self.total:
            raise ValueError("zero_valid_mass")
        plan, table = self.prepared.plan, self.prepared.table
        outside = [0] * len(plan.terms)
        outside[plan.root] = 1
        coefficient = {key: 0 for key in self.prepared.members}
        for node in reversed(plan.order):
            if not outside[node]:
                continue
            for term in plan.terms[node]:
                if term.choice is not None:
                    p, i = term.choice
                    coefficient[p, self.prepared.rows[p][i]] += outside[node]
                elif term.children:
                    a, b = term.children
                    outside[a] += outside[node] * self.inside[b]
                    outside[b] += outside[node] * self.inside[a]
        numerators = []
        for p, fixed in enumerate(self.weights.canvas):
            if fixed is not None:
                conservation = sum(
                    self.leaf[key] * value for key, value in coefficient.items() if key[0] == p
                )
                if conservation != self.total:
                    raise RuntimeError("outside lost fixed original conservation")
                numerators.append({fixed: self.total})
                continue
            if self.prepared.kind == "local":
                factors = [
                    sum(
                        coefficient.get((p, gid), 0)
                        for q in table.by_state
                        if (gid := table.class_to_local[q][cid]) >= 0
                    )
                    for cid in range(len(table.classes))
                ]
            elif self.prepared.kind == "global":
                factors = [coefficient.get((p, cid), 0) for cid in range(len(table.classes))]
            else:
                factors = None
            row = tuple(
                self.weights.at(p, t)
                * (coefficient.get((p, t), 0) if factors is None else factors[table.class_of[t]])
                for t in range(self.weights.vocabulary_size)
            )
            if sum(row) != self.total or (fixed is not None and row[fixed] != self.total):
                raise RuntimeError("outside lost original-token marginal conservation")
            numerators.append(row)
        # Consumers receive exact numerator vectors and common denominator.
        return tuple(numerators), self.total
