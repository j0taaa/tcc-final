"""Classical local common submeasure and subtraction-free residual proposal."""

from fractions import Fraction as F

from .residual import Residual
from .upper import cdf, draw


class ScalarResidual(Residual):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kernels, self.common, self.channels = {}, {}, {}
        totals = {}
        for node in self.plan.order:
            raw = []
            for term in self.plan.terms[node]:
                if term.choice is not None:
                    i, j = term.choice
                    raw.append(tuple(w[i][j] for w in self.weights))
                else:
                    raw.append(
                        tuple(
                            self._product(totals[child][j] for child in term.children)
                            for j in [0, 1]
                        )
                    )
            totals[node] = tuple(sum(row[j] for row in raw) for j in [0, 1])
            kernels = [
                (
                    F(a, totals[node][0]) if totals[node][0] else F(0),
                    F(b, totals[node][1]) if totals[node][1] else F(0),
                )
                for a, b in raw
            ]
            self.kernels[node] = tuple((p, q, min(p, q)) for p, q in kernels)
            masses = [[], [], []]
            actions = [[], [], []]
            for t, (term, (p, _, m)) in enumerate(
                zip(self.plan.terms[node], self.kernels[node], strict=True)
            ):
                masses[0].append(p)
                actions[0].append((t, (0,) * len(term.children)))
                masses[1].append(m * self._product(self.common[child] for child in term.children))
                actions[1].append((t, (1,) * len(term.children)))
                masses[2].append(p - m)
                actions[2].append((t, (0,) * len(term.children)))
                if term.children:
                    left, right = term.children
                    masses[2].extend(
                        [
                            m * (1 - self.common[left]),
                            m * self.common[left] * (1 - self.common[right]),
                        ]
                    )
                    actions[2].extend([(t, (2, 0)), (t, (1, 2))])
            self.common[node] = sum(masses[1], F(0))
            assert 0 <= self.common[node] <= (1 if totals[node][0] else 0)
            assert sum(masses[2], F(0)) == (1 if totals[node][0] else 0) - self.common[node]
            self.channels[node] = tuple(
                (cdf(row), tuple(a)) for row, a in zip(masses, actions, strict=True)
            )
        self.envelope = 1 - self.common[self.plan.root]

    @staticmethod
    def _product(values):
        product = F(1)
        for value in values:
            product *= value
        return product

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
