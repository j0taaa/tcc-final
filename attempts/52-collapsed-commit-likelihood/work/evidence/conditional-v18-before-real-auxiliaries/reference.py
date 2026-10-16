"""Independent rational observed-action oracle; classical evidence inference."""

from dataclasses import dataclass
from fractions import Fraction as F


@dataclass(frozen=True)
class DAG:
    """Original-ID deterministic layers, one root, explicit accepting leaves."""

    layers: tuple
    accepting: tuple[bool, ...]

    def validate(self, rows):
        if not self.layers or len(rows) != len(self.layers) or len(self.layers[0]) != 1:
            raise ValueError("one root and one weight row per layer required")
        for i, layer in enumerate(self.layers):
            following = len(self.layers[i + 1]) if i + 1 < len(rows) else len(self.accepting)
            if not layer or not rows[i] or any(type(w) is not F or w < 0 for w in rows[i]):
                raise ValueError("nonempty layers and nonnegative rational weights required")
            for edges in layer:
                labels = [v for v, _ in edges]
                if len(set(labels)) != len(labels):
                    raise ValueError("one original ID cannot have two state traces")
                if any(not 0 <= v < len(rows[i]) or not 0 <= t < following for v, t in edges):
                    raise ValueError("edge label/target outside declared domain")

    def infer(self, rows):
        self.validate(rows)
        beta = [tuple(F(a) for a in self.accepting)]
        for i in range(len(rows) - 1, -1, -1):
            beta.append(
                tuple(
                    sum((rows[i][v] * beta[-1][t] for v, t in edges), F())
                    for edges in self.layers[i]
                )
            )
        beta.reverse()
        z = beta[0][0]
        if not z:
            return z, tuple(tuple(F() for _ in row) for row in rows)
        alpha, marginals = (F(1),), []
        for i, layer in enumerate(self.layers):
            following = [F() for _ in beta[i + 1]]
            counts = [F() for _ in rows[i]]
            for s, edges in enumerate(layer):
                for v, t in edges:
                    flow = alpha[s] * rows[i][v]
                    following[t] += flow
                    counts[v] += flow * beta[i + 1][t]
            marginals.append(tuple(c / z for c in counts))
            alpha = tuple(following)
        return z, tuple(marginals)


def _validate(scores, active, action, rule, threshold, k):
    if not active or len(set(active)) != len(active):
        raise ValueError("distinct nonempty active positions required")
    if any(not 0 <= i < len(scores) for i in active):
        raise ValueError("active position out of range")
    if any(type(c) is not F or not 0 <= c <= 1 for row in scores for c in row):
        raise ValueError("rational confidence in [0,1] required")
    if rule == "threshold":
        if type(threshold) is not F or not 0 <= threshold <= 1:
            raise ValueError("rational threshold in [0,1] required")
    elif rule != "topk" or type(k) is not int or not 1 <= k <= len(active):
        raise ValueError("threshold or valid topk rule required")
    positions = [i for i, _ in action]
    if not action or positions != sorted(set(positions)):
        raise ValueError("action must contain sorted distinct retained positions")
    if any(i not in active or not 0 <= v < len(scores[i]) for i, v in action):
        raise ValueError("action outside active/original-ID domain")


def action_filters(scores, active, action, *, rule, threshold=None, k=None):
    """Preimage, without enumerating any unretained token combination."""
    _validate(scores, active, action, rule, threshold, k)
    retained = dict(action)
    if rule == "topk":
        if len(action) != k:
            return None
        cutoff = min((scores[i][v], -i) for i, v in action)
    elif all(scores[i][v] > threshold for i, v in action):
        cutoff = None
    elif len(action) == 1 and scores[action[0][0]][action[0][1]] <= threshold:
        i, v = action[0]
        cutoff = scores[i][v], -i
    else:
        return None

    def allowed(j, v):
        return scores[j][v] <= threshold if cutoff is None else (scores[j][v], -j) < cutoff

    return tuple(
        tuple(
            v == retained[i] if i in retained else i not in active or allowed(i, v)
            for v in range(len(row))
        )
        for i, row in enumerate(scores)
    )


def action_statistics(graph, rows, scores, active, action, *, rule, threshold=None, k=None):
    """Mass and log-weight adjoint; None score for a zero-probability action."""
    if len(scores) != len(rows) or any(len(c) != len(w) for c, w in zip(scores, rows, strict=True)):
        raise ValueError("scores and original weight domain differ")
    z, prior = graph.infer(rows)
    if not z:
        raise ValueError("undefined zero-mass original posterior")
    filters = action_filters(scores, active, action, rule=rule, threshold=threshold, k=k)
    if filters is None:
        return F(), None
    selected_rows = tuple(
        tuple(w if keep else F() for w, keep in zip(row, mask, strict=True))
        for row, mask in zip(rows, filters, strict=True)
    )
    mass, conditional = graph.infer(selected_rows)
    if not mass:
        return F(), None
    score = tuple(
        tuple(a - b for a, b in zip(post, pre, strict=True))
        for post, pre in zip(conditional, prior, strict=True)
    )
    return mass / z, score
