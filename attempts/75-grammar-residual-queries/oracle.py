"""A75 finite rational oracle and outward intervals. No Torch/model claims.

The sampler sees only query(mask, values), n and the reference conditional.
The enumerated target formula is confined to test-fixture construction.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from fractions import Fraction as F
from functools import cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / "protocol.json").read_text())
SCALE = 10**100


def floor(q: F) -> int:
    return q.numerator // q.denominator


def ceil(q: F) -> int:
    return -floor(-q)


@dataclass(frozen=True)
class Interval:
    lo: int
    hi: int

    def __post_init__(self):
        if self.lo > self.hi:
            raise ValueError("empty interval")

    @classmethod
    def of(cls, q):
        q = F(q) * SCALE
        return cls(floor(q), ceil(q))

    def __add__(self, other):
        if not isinstance(other, Interval):
            other = Interval.of(other)
        return Interval(self.lo + other.lo, self.hi + other.hi)

    __radd__ = __add__

    def __neg__(self):
        return Interval(-self.hi, -self.lo)

    def __sub__(self, other):
        return self + (-other if isinstance(other, Interval) else -F(other))

    def __mul__(self, other):
        if not isinstance(other, Interval):
            q = F(other)
            ends = (F(self.lo) * q, F(self.hi) * q)
            return Interval(floor(min(ends)), ceil(max(ends)))
        ends = [a * b for a in (self.lo, self.hi) for b in (other.lo, other.hi)]
        return Interval(min(ends) // SCALE, -(-max(ends) // SCALE))

    __rmul__ = __mul__

    def __truediv__(self, other):
        if not isinstance(other, Interval):
            return self * (1 / F(other))
        if other.lo <= 0 <= other.hi:
            raise ZeroDivisionError("interval contains zero")
        return self * Interval(floor(F(SCALE**2, other.hi)), ceil(F(SCALE**2, other.lo)))

    def absolute(self):
        return Interval(
            0 if self.lo <= 0 <= self.hi else min(abs(self.lo), abs(self.hi)),
            max(abs(self.lo), abs(self.hi)),
        )

    def clip(self, bound):
        b = Interval.of(bound)
        assert b.lo == b.hi and b.lo > 0
        return Interval(max(-b.lo, min(b.lo, self.lo)), max(-b.lo, min(b.lo, self.hi)))

    def contains(self, q):
        return F(self.lo, SCALE) <= q <= F(self.hi, SCALE)

    def result(self):
        # Integer endpoints are the certificate; floats are display only.
        return {
            "lo": str(self.lo),
            "hi": str(self.hi),
            "scale": str(SCALE),
            "display_midpoint": (self.lo + self.hi) / (2 * SCALE),
        }


@cache
def log(q: F) -> Interval:
    if q <= 0:
        raise ValueError("log outside support")
    if q < 1:
        return -log(1 / q)
    t = (q - 1) / (q + 1)
    z = Interval.of(t)
    power, square, total = z, z * z, Interval.of(0)
    for j in range(PROTOCOL["arithmetic"]["log_atanh_terms"]):
        total += power / (2 * j + 1)
        power *= square
    m = PROTOCOL["arithmetic"]["log_atanh_terms"]
    tail = 2 * t ** (2 * m + 1) / ((2 * m + 1) * (1 - t * t))
    total *= 2
    return Interval(total.lo, total.hi + ceil(tail * SCALE))


def _exp_point(q: F) -> Interval:
    if q < 0:
        return Interval.of(1) / _exp_point(-q)
    if q > 1:
        raise ValueError("finite protocol only supports exp arguments <= 1")
    x, term, total = Interval.of(q), Interval.of(1), Interval.of(1)
    m = PROTOCOL["arithmetic"]["exp_taylor_terms"]
    for k in range(1, m + 1):
        term = term * x / k
        total += term
    # Taylor remainder <= e^q q^(m+1)/(m+1)!; e^q <= e < 3.
    tail = 3 * q ** (m + 1) / math.factorial(m + 1)
    return Interval(total.lo, total.hi + ceil(tail * SCALE))


def exp(x: Interval) -> Interval:
    return Interval(_exp_point(F(x.lo, SCALE)).lo, _exp_point(F(x.hi, SCALE)).hi)


def integer_weights(values):
    denominator = math.lcm(*(q.denominator for q in values))
    weights = [q.numerator * (denominator // q.denominator) for q in values]
    common = math.gcd(*weights)
    return [w // common for w in weights]


def cylinders(n, words, weights):
    result = {}
    for mask in range(1 << n):
        for x, w in zip(words, weights, strict=True):
            key = mask, x & mask
            result[key] = result.get(key, 0) + w
    return result


class Oracle:
    def __init__(self, n, words, weights):
        self.n = n
        self.table = cylinders(n, words, integer_weights(weights))
        self.queries = 0
        self.max_bits = max(v.bit_length() for v in self.table.values())

    def marginal(self, mask, values, i):
        total = self.table.get((mask, values), 0)
        if not total:
            raise ValueError("unsupported pin")
        bit = 1 << i
        one = self.table.get((mask | bit, values | bit), 0)
        p = F(one, total)
        self.max_bits = max(self.max_bits, p.numerator.bit_length(), p.denominator.bit_length())
        return p

    def query(self, mask, values):
        self.queries += 1
        return tuple(self.marginal(mask, values, i) for i in range(self.n))


@dataclass
class Case:
    n: int
    alpha: F
    name: str
    words: list[int]
    r: list[F]
    p: list[F]
    oracle: Oracle
    reference: Oracle


def cases():
    for n in PROTOCOL["balance"]["n"]:
        for alpha in PROTOCOL["balance"]["alpha"]:
            for name in PROTOCOL["balance"]["targets"]:
                yield n, F(alpha), name
    h = PROTOCOL["hard_core_reproduction"]
    yield h["n"], F(h["alpha"]), "hard_core"


def make_case(n, alpha, name):
    words = [
        x
        for x in range(1 << n)
        if (not (x & (x << 1)) if name == "hard_core" else x.bit_count() == n // 2)
    ]
    r = [F(1, 3 ** x.bit_count()) if name == "hard_core" else F(1) for x in words]
    r = [q / sum(r) for q in r]
    f = []
    for x in words:
        if name == "hard_core":
            g = F(n, n + 9 * (x.bit_count() - 1) ** 2)
        elif name == "adjacent_equal":
            g = F(1 + sum(((x >> i) & 1) == ((x >> (i + 1)) & 1) for i in range(n - 1)), n)
        else:
            t = (x & ((1 << (n // 2)) - 1)).bit_count()
            g = F(n, n + 9 * (F(t) - F(n, 4)) ** 2)
            if name == "witness_minus":
                g = 1 - g
        f.append(1 + alpha * g)
    p = [a * b for a, b in zip(r, f, strict=True)]
    p = [q / sum(p) for q in p]
    return Case(n, alpha, name, words, r, p, Oracle(n, words, p), Oracle(n, words, r))


def increment(n, x, mask, p_ones, r_ones):
    terms = []
    for i in range(n):
        if not mask & (1 << i):
            p, r = p_ones[i], r_ones[i]
            if not x & (1 << i):
                p, r = 1 - p, 1 - r
            if p == 0:
                return None  # -infinity, only used for original SIRS control
            terms.append(log(p / r))
    return sum(terms, Interval.of(0)) * F(n, n - mask.bit_count())


def law(case, original_sirs=False):
    """Exhaust masks; mass exact, transcendental results certified intervals."""
    n, b = case.n, case.alpha
    root = tuple(case.oracle.marginal(0, 0, i) for i in range(n))
    words = list(range(1 << n)) if original_sirs else case.words
    proposal = (
        [math.prod(root[i] if x & (1 << i) else 1 - root[i] for i in range(n)) for x in words]
        if original_sirs
        else case.r
    )
    h, hb = [], []
    for x in words:
        hx, bx = Interval.of(0), Interval.of(0)
        for mask in range((1 << n) - 1):
            values = x & mask
            supported = case.oracle.table.get((mask, values), 0)
            # Explicit extension on zero-P cylinders: use the root head.
            p = (
                tuple(case.oracle.marginal(mask, values, i) for i in range(n))
                if supported
                else root
            )
            r = (
                root
                if original_sirs
                else tuple(case.reference.marginal(mask, values, i) for i in range(n))
            )
            w = increment(n, x, mask, p, r)
            weight = F(1, n * math.comb(n, mask.bit_count()))
            if w is not None:
                hx += w * weight
            bx += (w.clip(b) if w is not None else Interval.of(-b)) * weight
        h.append(hx)
        hb.append(bx)
    raw = [exp(v) * r for v, r in zip(hb, proposal, strict=True)]
    z = sum(raw, Interval.of(0))
    q = [v / z for v in raw]
    truth = dict(zip(case.words, case.p, strict=True))
    tv = (
        sum(
            ((v - truth.get(x, F())).absolute() for x, v in zip(words, q, strict=True)),
            Interval.of(0),
        )
        / 2
    )
    leaked = sum((v for x, v in zip(words, q, strict=True) if x not in truth), Interval.of(0))
    proposals = exp(Interval.of(b)) / z
    return {
        "words": words,
        "h": h,
        "hb": hb,
        "q": q,
        "z": z,
        "tv": tv,
        "leaked": leaked,
        "proposals": proposals,
        "queries": proposals * (2 * b) + (1 if original_sirs else 0),
    }


def tv(p, q):
    return sum(abs(a - b) for a, b in zip(p, q, strict=True)) / 2


def sequential_cost(case):
    cost = F()
    for i in range(case.n):
        mask = (1 << i) - 1
        for (m, v), mass in case.oracle.table.items():
            if m == mask and 0 < case.reference.marginal(m, v, i) < 1:
                cost += F(mass, case.oracle.table[0, 0])
    return cost


def pair_control(case):
    """Exact moving pair heat bath; sparse kernel and n-update law."""
    n, full = case.n, (1 << case.n) - 1
    index = {x: i for i, x in enumerate(case.words)}
    kernel = []
    for x in case.words:
        row = {}
        for i in range(n):
            for j in range(i + 1, n):
                y = x ^ (1 << i) ^ (1 << j)
                if y not in index:
                    row[x] = row.get(x, F()) + F(1, math.comb(n, 2))
                    continue
                mask = full ^ (1 << i) ^ (1 << j)
                total = case.oracle.table[mask, x & mask]
                for z in (x, y):
                    probability = F(case.oracle.table[full, z], total * math.comb(n, 2))
                    row[z] = row.get(z, F()) + probability
        assert sum(row.values()) == 1
        kernel.append(row)
    for x, row in zip(case.words, kernel, strict=True):
        for y, probability in row.items():
            assert case.p[index[x]] * probability == case.p[index[y]] * kernel[index[y]][x]
    q = list(case.r)
    for _ in range(n):
        updated = [F() for _ in q]
        for mass, row in zip(q, kernel, strict=True):
            for y, probability in row.items():
                updated[index[y]] += mass * probability
        q = updated
    return q, F(n * n, 2 * (n - 1))
