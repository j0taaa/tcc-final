"""Classical ratio range and precision doubling; no marginal tables required."""

from fractions import Fraction as F
from math import prod

from .rounded import RoundedResidual


class PrecisionResidual(RoundedResidual):
    def select_grid(self, plan, target, draft, grid):
        common, ranges = {}, {}
        for node in plan.order:
            parts, endpoints = [], []
            for term in plan.terms[node]:
                if term.choice is not None:
                    i, j = term.choice
                    a, b = (w[i][j] for w in self.weights)
                    parts.append((a if b else 0, b if a else 0))
                    if a and b:
                        endpoints.append((F(a, b), F(a, b)))
                else:
                    parts.append(tuple(prod(common[c][k] for c in term.children) for k in [0, 1]))
                    if all(ranges[c] is not None for c in term.children):
                        endpoints.append(
                            tuple(prod(ranges[c][k] for c in term.children) for k in [0, 1])
                        )
            common[node] = tuple(sum(p[k] for p in parts) for k in [0, 1])
            ranges[node] = (
                (min(x for x, _ in endpoints), max(y for _, y in endpoints)) if endpoints else None
            )
        self.ratio_range = ranges[plan.root]
        self.equal = common[plan.root] == (self.za, self.zb) and self.ratio_range == (
            F(self.za, self.zb),
            F(self.za, self.zb),
        )
        self.precision_passes = 0
        if grid is not None or self.equal:
            return 2 if grid is None else grid
        bits = 1
        while True:
            s, counts = 1 << bits, {}
            self.precision_passes += 1
            for node in plan.order:
                a_total, b_total = self.totals[node]
                u = 0
                for term in plan.terms[node]:
                    raw = (
                        tuple(w[term.choice[0]][term.choice[1]] for w in self.weights)
                        if term.choice is not None
                        else tuple(prod(self.totals[c][k] for c in term.children) for k in [0, 1])
                    )
                    u += (
                        min(raw[0] * b_total, raw[1] * a_total)
                        * prod(counts[c] for c in term.children)
                        * s ** (2 - len(term.children))
                    )
                counts[node] = u // (a_total * b_total * s) if a_total and b_total else 0
            if 2 * self.trace_bound <= s - counts[plan.root]:
                return s
            bits *= 2
