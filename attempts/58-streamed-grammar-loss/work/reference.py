"""Independent rational expectation-semiring reference for a tiny JSON grammar.

J ::= 0 | 1 | '[' J ']'; original IDs include aliases and epsilon. Classical
semiring inference supplies mass/occupancy. This is not a production compiler.
"""

from fractions import Fraction as F

EMISSIONS = ("0", "0", "1", "[", "]", "", "<EOS>")
EOS = 6
CLASSES = tuple(dict.fromkeys(EMISSIONS))
MAPPING = tuple(CLASSES.index(e) for e in EMISSIONS)


def transition(state, emission):
    depth, complete = state
    if emission == "":
        return state
    if not complete:
        if emission == "[":
            return depth + 1, False
        if emission in ("0", "1"):
            return depth, True
    elif depth and emission == "]":
        return depth - 1, True
    return None


def moments(probabilities, fixed):
    n, nc = len(probabilities), len(CLASSES)
    size = n * nc
    zero = (F(),) * size
    messages = {(0, False): (F(1), zero)}
    total, counts = F(), zero
    minimum = max(fixed, default=-1)
    for i, p in enumerate(probabilities):
        row = (
            tuple(F(c == MAPPING[fixed[i]]) for c in range(nc))
            if i in fixed
            else tuple(
                sum((p[v] for v, c in enumerate(MAPPING) if c == cls), F()) for cls in range(nc)
            )
        )
        nxt = {}
        for state, (mass, prior) in messages.items():
            for cls, weight in enumerate(row):
                if not weight:
                    continue
                is_eos = CLASSES[cls] == "<EOS>"
                if is_eos:
                    if state != (0, True) or i < minimum:
                        continue
                    target = None
                else:
                    target = transition(state, CLASSES[cls])
                    if target is None:
                        continue
                edge_mass = mass * weight
                edge_counts = tuple(
                    value * weight + edge_mass * (i not in fixed and j == i * nc + cls)
                    for j, value in enumerate(prior)
                )
                old_mass, old_counts = (total, counts) if is_eos else nxt.get(target, (F(), zero))
                merged = tuple(a + b for a, b in zip(old_counts, edge_counts, strict=True))
                if is_eos:
                    total, counts = old_mass + edge_mass, merged
                else:
                    nxt[target] = old_mass + edge_mass, merged
        messages = nxt
    if not total:
        raise ValueError("positive grammatical prefix mass required")
    nu = tuple(tuple(counts[i * nc + c] / total for c in range(nc)) for i in range(n))
    return total, nu


def gradients(raw, fixed, targets, weights, lam):
    n, v = len(raw), len(EMISSIONS)
    if (
        not n
        or len(targets) != n
        or len(weights) != n
        or lam < 0
        or any(len(row) != v or min(row) < 0 or sum(row) <= 0 for row in raw)
        or any(not 0 <= i < n or not 0 <= t < v for i, t in fixed.items())
        or any(
            w < 0 or not 0 <= t < v or (w and not raw[i][t]) or (i in fixed and w)
            for i, (t, w) in enumerate(zip(targets, weights, strict=True))
        )
    ):
        raise ValueError(
            "finite positive rows, supported targets and inactive fixed-row CE required"
        )
    p = tuple(tuple(a / sum(row) for a in row) for row in raw)
    mass, nu = moments(p, fixed)
    occupancy = tuple(sum(row, F()) for row in nu)
    pi = tuple(
        tuple(sum((p[i][j] for j in range(v) if MAPPING[j] == c), F()) for c in range(len(CLASSES)))
        for i in range(n)
    )
    class_adjoints = tuple(
        tuple(
            (weights[i] + lam * occupancy[i]) * pi[i][c] - lam * nu[i][c] if i not in fixed else F()
            for c in range(len(CLASSES))
        )
        for i in range(n)
    )
    result = tuple(
        tuple(
            (
                class_adjoints[i][MAPPING[j]] * p[i][j] / pi[i][MAPPING[j]]
                if pi[i][MAPPING[j]]
                else F()
            )
            - weights[i] * (targets[i] == j)
            for j in range(v)
        )
        for i in range(n)
    )
    return {
        "mass": mass,
        "gradient": result,
        "nu": nu,
        "occupancy": occupancy,
        "class_adjoints": class_adjoints,
        "p": p,
    }
