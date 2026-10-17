"""Small rational reference; ideal unbiased randbelow, not a native dLLM law."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction as F
from functools import reduce
from math import gcd, lcm

RandBelow = Callable[[int], int]


@dataclass(frozen=True)
class Prepared:
    base: tuple[int, ...]
    ratios: tuple[tuple[F, ...], ...]
    r: F
    cumulative: tuple[tuple[int, ...], ...]

    @property
    def n(self) -> int:
        return len(self.base)

    def cheap_failure_bound(self) -> F:
        if not self.r:
            return F(0)
        largest = max(max(row) for row in self.ratios)
        return self.n * (largest * self.r / (1 - self.r)) ** 2


def prepare(weights: Sequence[Sequence[F | int]]) -> Prepared:
    """Read all entries, detect the ONLY possible strictly row-dominant base."""
    rows = tuple(tuple(F(x) for x in row) for row in weights)
    n = len(rows)
    if not n or any(len(row) != n or any(x < 0 for x in row) for row in rows):
        raise ValueError("require a nonempty nonnegative square matrix")
    base = tuple(max(range(n), key=lambda j: row[j]) for row in rows)
    if len(set(base)) != n or any(not rows[i][base[i]] for i in range(n)):
        raise ValueError("row maxima do not give a positive base matching")
    ratios = tuple(
        tuple(F(0) if i == j else rows[i][base[j]] / rows[i][base[i]] for j in range(n))
        for i in range(n)
    )
    r = max(map(sum, ratios))
    if r >= 1:
        raise ValueError("transient row-sum condition r<1 is not satisfied")
    cumulative = []
    if r:
        for row in ratios:
            probabilities = (*tuple(x / r for x in row), 1 - sum(row) / r)
            denominator = lcm(*(x.denominator for x in probabilities))
            tickets = [int(x * denominator) for x in probabilities]
            common = reduce(gcd, tickets)
            total = 0
            cdf = []
            for count in tickets:
                total += count // common
                cdf.append(total)
            cumulative.append(tuple(cdf))
    return Prepared(base, ratios, r, tuple(cumulative))


def ewens_links(n: int, m: int, randbelow: RandBelow) -> list[int]:
    """Classical insertion scheme; each of n start tickets makes a new cycle."""
    if n < 1 or m < 0:
        raise ValueError("require n>=1 and m>=0")
    following = []
    for j in range(m):
        choice = randbelow(n + j)
        if choice < n:
            following.append(j)
        else:
            previous = choice - n
            following.append(following[previous])
            following[previous] = j
    return following


def from_auxiliary_size(prepared: Prepared, m: int, randbelow: RandBelow) -> tuple[int, ...] | None:
    """One soup given M. Its accepted outputs ALONE are not the target law."""
    if m < 0 or (m and not prepared.r):
        raise ValueError("impossible auxiliary size")
    links = ewens_links(prepared.n, m, randbelow)
    inspected = [False] * m
    occupied: set[int] = set()
    assignment = list(range(prepared.n))
    for label in range(m):
        if inspected[label]:
            continue
        length = 0
        current = label
        while not inspected[current]:
            inspected[current] = True
            length += 1
            current = links[current]
        root = randbelow(prepared.n)
        vertex = root
        walk = []
        for _ in range(length):
            walk.append(vertex)
            cdf = prepared.cumulative[vertex]
            vertex = bisect_right(cdf, randbelow(cdf[-1]))
            if vertex == prepared.n:
                break
        if vertex != root:
            continue
        # Only CLOSED walks participate. A nonclosed walk can revisit vertices
        # without invalidating the soup and must not cause early rejection.
        if len(set(walk)) != len(walk) or occupied.intersection(walk):
            return None
        occupied.update(walk)
        for i, j in zip(walk, [*walk[1:], root], strict=True):
            assignment[i] = j
    return tuple(prepared.base[j] for j in assignment)


def proposal(prepared: Prepared, randbelow: RandBelow) -> tuple[tuple[int, ...] | None, int]:
    """Unlimited geometric draws for one soup; returns rejection as None."""
    if not prepared.r:
        return prepared.base, 0
    m = 0
    for _ in range(prepared.n):
        while randbelow(prepared.r.denominator) < prepared.r.numerator:
            m += 1
    return from_auxiliary_size(prepared, m, randbelow), m


def sample(prepared: Prepared, randbelow: RandBelow) -> tuple[int, ...]:
    """Unlimited retries. A time/draw cap is deliberately not hidden here."""
    while True:
        output, _ = proposal(prepared, randbelow)
        if output is not None:
            return output
