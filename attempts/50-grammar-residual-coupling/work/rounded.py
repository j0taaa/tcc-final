"""Exact residual law; dyadic common totals and integer channel CDFs only."""

from fractions import Fraction as F
from math import prod

from .residual import Residual
from .upper import cdf, draw


class RoundedResidual(Residual):
    def __init__(self, plan, target, draft, grid=None, **kwargs):
        super().__init__(plan, target, draft, **kwargs)
        sizes = {}
        for node in plan.order:
            sizes[node] = 1 + max(sum(sizes[c] for c in t.children) for t in plan.terms[node])
        self.trace_bound = sizes[plan.root]
        self.grid = self.select_grid(plan, target, draft, grid)
        if self.grid < 2 or self.grid & (self.grid - 1):
            raise ValueError("grid must be a power of two >=2")
        s = self.grid
        self.kernels, self.common, self.channels = {}, {}, {}
        totals, integers = {}, {}
        for node in plan.order:
            raw = [
                tuple(w[t.choice[0]][t.choice[1]] for w in self.weights)
                if t.choice is not None
                else tuple(prod(totals[c][j] for c in t.children) for j in [0, 1])
                for t in plan.terms[node]
            ]
            a_total, b_total = totals[node] = tuple(sum(row[j] for row in raw) for j in [0, 1])
            minimum = [min(a * b_total, b * a_total) for a, b in raw]
            common_weights = [
                m * prod(integers[c] for c in t.children) * s ** (2 - len(t.children))
                for m, t in zip(minimum, plan.terms[node], strict=True)
            ]
            u = sum(common_weights)
            count = integers[node] = u // (a_total * b_total * s) if a_total and b_total else 0
            self.common[node] = F(count, s)
            masses = [[a for a, _ in raw], common_weights if count else [0] * len(raw), []]
            actions = [
                [(t, (0,) * len(term.children)) for t, term in enumerate(plan.terms[node])],
                [(t, (1,) * len(term.children)) for t, term in enumerate(plan.terms[node])],
                [],
            ]
            kernels = []
            for t, (term, (a, b), m) in enumerate(zip(plan.terms[node], raw, minimum, strict=True)):
                p, q = F(a, a_total) if a_total else F(0), F(b, b_total) if b_total else F(0)
                beta = F(count * s * m, u) if u else F(0)
                assert beta <= min(p, q)
                kernels.append((p, q, beta))
                if not u:
                    masses[2].append(a)
                    actions[2].append((t, (0,) * len(term.children)))
                    continue
                masses[2].append(a * u * s - a_total * count * s * s * m)
                actions[2].append((t, (0,) * len(term.children)))
                if term.children:
                    left, right = (integers[c] for c in term.children)
                    masses[2].extend(
                        [
                            a_total * count * s * m * (s - left),
                            a_total * count * m * left * (s - right),
                        ]
                    )
                    actions[2].extend([(t, (2, 0)), (t, (1, 2))])
            assert all(value >= 0 for row in masses for value in row)
            self.kernels[node] = tuple(kernels)
            self.channels[node] = tuple(
                (cdf(row), tuple(a)) for row, a in zip(masses, actions, strict=True)
            )
        self.envelope = 1 - self.common[plan.root]
        if self.equal:
            assert self.envelope == 0, "equal-marginal product posteriors must agree"

    def select_grid(self, plan, target, draft, grid):
        first, second = plan.evaluate(target).marginals, plan.evaluate(draft).marginals
        self.lower = max(
            abs(a - b)
            for x, y in zip(first, second, strict=True)
            for a, b in zip(x, y, strict=True)
        )
        self.equal = not self.lower
        need = F(2 * self.trace_bound) / self.lower if self.lower else F(2)
        ceiling = (need.numerator + need.denominator - 1) // need.denominator
        return (1 << (ceiling - 1).bit_length()) if grid is None else grid

    def correction(self, p, q, common):
        accept = max(F(0), p - q) / (p - common)
        assert 0 <= accept <= 1
        return accept

    def propose(self, rng):
        if not self.envelope:
            raise ValueError("zero residual: no conditional law")
        pending, marks = [(self.plan.root, 2)], {}
        p = q = common = F(1)
        while pending:
            node, mode = pending.pop()
            cumulative, actions = self.channels[node][mode]
            t, child_modes = actions[draw(cumulative, rng)]
            term = self.plan.terms[node][t]
            a, b, c = self.kernels[node][t]
            p *= a
            q *= b
            common *= c
            if term.choice is not None:
                i, j = term.choice
                assert i not in marks
                marks[i] = self.ids[i][j]
            else:
                pending.extend(reversed(tuple(zip(term.children, child_modes, strict=True))))
        if len(marks) != len(self.ids):
            raise AssertionError("incomplete original-token assignment")
        return tuple(marks[i] for i in range(len(self.ids))), self.correction(p, q, common)

    def sample(self, rng, max_attempts=None):
        if not self.envelope:
            raise ValueError("zero residual: no conditional law")
        attempts = 0
        while max_attempts is None or attempts < max_attempts:
            ids, accept = self.propose(rng)
            attempts += 1
            if rng.randrange(accept.denominator) < accept.numerator:
                return ids, attempts
        return None, attempts
