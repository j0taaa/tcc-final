"""Small rational references for CLASSICAL couplings and prefix cache work."""

from collections import defaultdict
from fractions import Fraction as F
from itertools import product


def probability(law):
    if (
        not law
        or any(not isinstance(v, F) or v < 0 for v in law.values())
        or sum(law.values()) != 1
    ):
        raise ValueError("normalized rational probability table required")


def maximal(p, q):
    probability(p)
    probability(q)
    alphabet = set(p) | set(q)
    common = {a: min(p.get(a, F(0)), q.get(a, F(0))) for a in alphabet}
    residual = 1 - sum(common.values())
    joint = defaultdict(F)
    for a in alphabet:
        joint[a, a] += common[a]
    if residual:
        for a, b in product(alphabet, repeat=2):
            joint[a, b] += (p.get(a, F(0)) - common[a]) * (q.get(b, F(0)) - common[b]) / residual
    return {pair: v for pair, v in joint.items() if v}


def pushforward(law, observe):
    result = defaultdict(F)
    for a, p in law.items():
        result[observe(a)] += p
    return dict(result)


def auxiliary_diagonal(first, second, observe):
    result = defaultdict(F)
    for z in first.keys() | second.keys():
        result[observe(z)] += min(first.get(z, F(0)), second.get(z, F(0)))
    return dict(result)


def forced_joint(words, gates):
    """Uniform anchor before X, forced release; fixed-length tiny reference."""
    probability(words)
    n = len(next(iter(words)))
    if any(len(w) != n for w in words) or len(gates) != n:
        raise ValueError("same original word length and per-position gates required")
    result = defaultdict(F)
    for w, p in words.items():
        for anchor in range(n):
            for bits in product((False, True), repeat=n - 1):
                keep = {anchor}
                weight = p / F(n)
                for i, bit in zip((i for i in range(n) if i != anchor), bits, strict=True):
                    g = gates[i][w[i]]
                    if not F(0) < g < F(1):
                        raise ValueError("positive rational gates required")
                    weight *= g if bit else 1 - g
                    if bit:
                        keep.add(i)
                action = tuple((i, w[i]) for i in sorted(keep))
                result[w, action] += weight
    return dict(result)


def binary_joint(p, q, upper):
    """All vertices of the 2x2 transportation interval, not a new algorithm."""
    theta = min(p, q) if upper else max(F(0), p + q - 1)
    return {(1, 1): theta, (1, 0): p - theta, (0, 1): q - theta, (0, 0): 1 - p - q + theta}


def prefix_process(p, q, horizon, choices, cost):
    joint = {((), ()): F(1)}
    shared = F(0)
    for _step in range(horizon):
        following = defaultdict(F)
        for (a, b), mass in joint.items():
            if a == b:
                shared += mass * cost[a]
                coupled = binary_joint(p[a], q[b], choices[a])
            else:
                coupled = {
                    (x, y): (p[a] if x else 1 - p[a]) * (q[b] if y else 1 - q[b])
                    for x, y in product((0, 1), repeat=2)
                }
            for (x, y), chance in coupled.items():
                following[(*a, x), (*b, y)] += mass * chance
        joint = dict(following)
    return joint, shared
