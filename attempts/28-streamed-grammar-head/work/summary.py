"""Integer streamed class statistics: one original-token conditional sample."""

from fractions import Fraction
from math import prod

from .frozen.posterior import Posterior


class ClassLedger:
    def __init__(self, rows, canvas, class_of, class_count, rng):
        if type(class_count) is not int or class_count <= 0:
            raise ValueError("positive class count required")
        self.class_of = tuple(class_of)
        self.canvas = tuple(canvas)
        self.vocabulary_size = len(self.class_of)
        if not self.vocabulary_size or any(
            type(c) is not int or not 0 <= c < class_count for c in self.class_of
        ):
            raise ValueError("invalid original-ID partition")
        self.sums, self.winners, self.denominators = [], [], []
        self.consumed = False
        for row, fixed in zip(rows, self.canvas, strict=True):
            sums, winners = [0] * class_count, [None] * class_count
            if fixed is not None:
                if type(fixed) is not int or not 0 <= fixed < self.vocabulary_size:
                    raise ValueError("invalid original fixed token")
                sums[self.class_of[fixed]], winners[self.class_of[fixed]] = 1, fixed
            else:
                length = 0
                for token, weight in enumerate(row):
                    if token >= self.vocabulary_size:
                        raise ValueError("stream exceeds original vocabulary")
                    if type(weight) is not int or weight < 0:
                        raise ValueError("nonnegative integer weights required")
                    length += 1
                    if not weight:
                        continue
                    cid = self.class_of[token]
                    total = sums[cid] + weight
                    if not sums[cid] or rng.randrange(total) < weight:
                        winners[cid] = token
                    sums[cid] = total
                if length != self.vocabulary_size:
                    raise ValueError("stream differs from original vocabulary")
            denominator = sum(sums)
            if not denominator:
                raise ValueError("zero original row")
            self.sums.append(tuple(sums))
            self.winners.append(tuple(winners))
            self.denominators.append(denominator)
        self.sums, self.winners, self.denominators = (
            tuple(self.sums),
            tuple(self.winners),
            tuple(self.denominators),
        )


class ClassPosterior:
    def __init__(self, prepared, ledger):
        table = prepared.table
        if tuple(table.class_of) != ledger.class_of or prepared.canvas != ledger.canvas:
            raise ValueError("summary changed partition or original frame")
        self.prepared, self.ledger = prepared, ledger
        self.leaf = {
            (p, gid): sum(ledger.sums[p][cid] for cid in table.local_to_class[gid])
            for p, gid in prepared.members
        }
        self.beta = [[0] * len(layer) for layer in prepared.layers]
        self.beta[-1] = list(map(int, prepared.accepting))
        self.arc_weights = [
            [[sum(self.leaf[p, gid] for gid in gids) for _, gids in out] for out in layer]
            for p, layer in enumerate(prepared.arcs)
        ]
        for p in reversed(range(len(prepared.arcs))):
            for a, out in enumerate(prepared.arcs[p]):
                self.beta[p][a] = sum(
                    weight * self.beta[p + 1][b]
                    for (b, _), weight in zip(out, self.arc_weights[p][a], strict=True)
                )
        self.total = self.beta[0][0]
        self.mass = Fraction(self.total, prod(ledger.denominators))
        if not 0 <= self.mass <= 1:
            raise RuntimeError("summary valid mass outside [0,1]")

    def sample(self, rng):
        if self.ledger.consumed:
            raise ValueError("summary already consumed; new independent reservoirs required")
        if not self.total:
            raise ValueError("zero_valid_mass")
        # A failing downstream RNG cannot leave a partially observed summary reusable.
        self.ledger.consumed = True
        tokens, state = [], 0
        for p, layer in enumerate(self.prepared.arcs):
            out = layer[state]
            b, gids = out[
                Posterior.choose(
                    [
                        w * self.beta[p + 1][b]
                        for (b, _), w in zip(out, self.arc_weights[p][state], strict=True)
                    ],
                    rng,
                )
            ]
            gid = gids[Posterior.choose([self.leaf[p, g] for g in gids], rng)]
            classes = self.prepared.table.local_to_class[gid]
            cid = classes[Posterior.choose([self.ledger.sums[p][c] for c in classes], rng)]
            token = self.ledger.winners[p][cid]
            if token is None:
                raise RuntimeError("positive class has no original reservoir winner")
            tokens.append(token)
            state = b
        return tuple(tokens)
