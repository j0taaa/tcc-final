"""Independent full rational inside/retained-prefix sampler, classical control."""

from fractions import Fraction as F

from .cdf_control import exact_with_retained_prefix


class ExactDAG:
    def __init__(self, classes, layers, accepting, rows):
        self.classes, self.layers = classes, layers
        self.rows = tuple(tuple(F(float(w)) for w in row) for row in rows)
        self.class_weights = tuple(
            tuple(sum((row[t] for t in members), F()) for members in classes) for row in self.rows
        )
        beta = [[F(int(a)) for a in accepting]]
        for p in range(len(layers) - 1, -1, -1):
            beta.append(
                [
                    sum(
                        (
                            sum((self.class_weights[p][c] for c in cids), F()) * beta[-1][target]
                            for target, cids in edges
                        ),
                        F(),
                    )
                    for edges in layers[p]
                ]
            )
        self.beta = tuple(reversed(beta))
        if not self.beta[0][0] > 0:
            raise ValueError("zero exact target mass; no word returned")

    def sample(self, source, bits, rng):
        if len(source) != len(self.layers) or any(len(r) != 3 for r in source):
            raise ValueError("one retained prefix per slot and edge/block/ID phase required")
        state, word = 0, []
        for p, layer in enumerate(self.layers):
            edges = layer[state]
            masses = [
                sum((self.class_weights[p][c] for c in cids), F()) * self.beta[p + 1][target]
                for target, cids in edges
            ]
            e = exact_with_retained_prefix(masses, int(source[p][0]), bits, rng)
            target, cids = edges[e]
            b = exact_with_retained_prefix(
                [self.class_weights[p][c] for c in cids], int(source[p][1]), bits, rng
            )
            members = self.classes[cids[b]]
            j = exact_with_retained_prefix(
                [self.rows[p][t] for t in members], int(source[p][2]), bits, rng
            )
            word.append(members[j])
            state = target
        return tuple(word)
