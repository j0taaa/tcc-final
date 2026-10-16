"""V14's fixed nine-coordinate chain rule AT theta=0, not a trained actor."""

import numpy as np


def state_features(weights, fixed, eos):
    n = len(weights)
    if not 1 <= n <= 64 or weights.ndim != 2:
        raise ValueError("original prefix matrix with at most64 slots required")
    if not np.isfinite(weights).all() or not (weights.sum(1) > 0).all():
        raise ValueError("finite positive row masses required")
    active = np.asarray([i not in fixed for i in range(n)])
    if not active.any() or not (weights[active] > 0).all():
        raise ValueError("nonterminal positive original active head required")
    x = (2 * np.arange(n) + 1) / 64 - 1
    h = np.zeros(n)
    h[active] = np.log(weights[active].max(1)) / 10
    return {"x": x, "h": h, "m": float(active.sum() / 64), "e": float(eos in fixed.values())}


def actor_vector(score, features):
    x, h = features["x"], features["h"]
    n = len(x)
    aa, rr = np.asarray(score["alpha"]), np.asarray(score["anchor"])
    if aa.ndim != 1 or rr.ndim != 1 or min(len(aa), len(rr)) < n:
        raise ValueError("original per-slot policy score required")
    if (aa[n:] != 0).any() or (rr[n:] != 0).any():
        raise ValueError("padding after prefix extent must have zero score")
    aa, rr = aa[:n], rr[:n]
    a, r = aa.sum(), np.dot(x, rr)
    value = np.asarray(
        [
            a,
            np.dot(x, aa),
            np.dot(h, aa),
            features["m"] * a,
            features["e"] * a,
            r,
            np.dot(h, rr),
            features["m"] * r,
            float(score["beta"]),
        ]
    )
    if not np.isfinite(value).all():
        raise ValueError("finite actor gradient coordinates required")
    return value


def paired_trace(first, second):
    first, second = np.asarray(first), np.asarray(second)
    if first.shape != (9,) or second.shape != (9,):
        raise ValueError("two nine-coordinate gradients required")
    return {
        "total": float(np.sum((first - second) ** 2) / 2),
        "gate": float(np.sum((first[:5] - second[:5]) ** 2) / 2),
        "anchor": float(np.sum((first[5:8] - second[5:8]) ** 2) / 2),
        "confidence": float((first[8] - second[8]) ** 2 / 2),
    }
