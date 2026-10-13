"""Distribution-valued outside reference; every original-ID residual marginal."""

from fractions import Fraction as F

from .residual import Residual, categorical, coarsen


class OutsideResidual(Residual):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        errors = {self.plan.root: 0}
        for node in reversed(self.plan.order):
            if node not in errors:
                continue
            if node != self.plan.root:
                errors[node] += 1
            for term in self.plan.terms[node]:
                if term.children:
                    left, right = term.children
                    for child, sibling in [(left, right), (right, left)]:
                        errors[child] = max(
                            errors.get(child, 0), errors[node] + self.costs[sibling] + 1
                        )
        self.all_depth = max(self.depth, *errors.values())

    def marginals(self, evidence=None, xi=F(1, 4), multiplier=F(1)):
        if multiplier < 0:
            raise ValueError("invalid threshold")
        evidence = {} if evidence is None else evidence
        inside, totals, factor = self._inside(evidence, xi, self.all_depth)
        eta = xi / (2 * self.all_depth)
        root = self.plan.root
        pending, scalar = {root: [(F(1), 1)]}, {root: [1, 1]}
        lower = [[F(0) for _ in row] for row in self.ids]
        threshold = multiplier * F(self.za, self.zb)
        for node in reversed(self.plan.order):
            context = coarsen(pending.get(node, []), eta)
            exact = scalar.get(node, [0, 0])
            for term in self.plan.terms[node]:
                if term.choice is not None:
                    i, j = term.choice
                    a, b = (w[i][j] for w in self.weights)
                    if i in evidence and self.ids[i][j] != evidence[i]:
                        a = b = 0
                    singular = F(a * (exact[0] - (exact[1] if b else 0)), self.za)
                    assert singular >= 0
                    common = (
                        sum((w * max(F(0), F(a, b) * r - threshold) for r, w in context), F(0))
                        * F(b, self.za)
                        if b
                        else F(0)
                    )
                    lower[i][j] += singular + common
                elif term.children:
                    left, right = term.children
                    for child, sibling in [(left, right), (right, left)]:
                        if len(context) * len(inside[sibling]) > self.max_pairs:
                            raise RuntimeError("outside product budget, not zero residual")
                        part = coarsen(
                            [(r * s, w * z) for r, w in context for s, z in inside[sibling]], eta
                        )
                        pending.setdefault(child, []).extend(part)
                        if len(pending[child]) > self.max_pairs:
                            raise RuntimeError("outside sum budget, not zero residual")
                        child_exact = scalar.setdefault(child, [0, 0])
                        child_exact[0] += exact[0] * totals[sibling][0]
                        child_exact[1] += exact[1] * totals[sibling][2]
        return tuple(tuple((value, factor * value) for value in row) for row in lower)

    def propose(self, rng):
        xi = F(1, 4 * len(self.ids))
        evidence, density = {}, F(1)
        for i, ids in enumerate(self.ids):
            weights = [interval[0] for interval in self.marginals(evidence, xi=xi)[i]]
            total = sum(weights, F(0))
            if not total:
                raise ValueError("zero residual prefix")
            j = categorical(weights, rng)
            evidence[i] = ids[j]
            density *= weights[j] / total
        return tuple(evidence[i] for i in range(len(self.ids))), density
