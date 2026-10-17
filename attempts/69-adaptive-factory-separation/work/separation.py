"""Exact adaptive confidence predicates; experimental proof reference only."""

from dataclasses import dataclass
from fractions import Fraction


def exact(value):
    if not isinstance(value, (int, Fraction)):
        raise TypeError("Exact integer/rational required")
    return Fraction(value)


def predicate(source, center, level, width=Fraction(2)):
    center, width = exact(center), exact(width)
    if not isinstance(level, int) or level < 1 or not 0 < center < 1 or width <= 0:
        raise ValueError("Invalid finite predicate")
    ones, used = 0, 0

    def advance(target):
        nonlocal ones, used
        while used < target:
            bit = source()
            if not isinstance(bit, int) or bit not in (0, 1):
                raise ValueError("Source must return an integer bit")
            ones += bit
            used += 1

    for j in range(level):
        count = 1 << (2 * j)
        advance(count)
        if abs(ones - count * center) > width * (j + 1) * (1 << j):
            return 0, used
    count = 1 << (2 * level)
    advance(count)
    return int(abs(ones - count * center) <= 1 << level), used


@dataclass(frozen=True)
class Result:
    bit: int
    source_calls: int
    auxiliary_bits: int
    selected_level: int | None
    stage: str


def sample(source, rng):
    used = 0

    def auxiliary():
        nonlocal used
        bit = rng.getrandbits(1)
        if not isinstance(bit, int) or bit not in (0, 1):
            raise ValueError("Auxiliary source must return an integer bit")
        used += 1
        return bit

    ticket = 2 * auxiliary() + auxiliary()
    if ticket != 1:
        return Result(int(ticket == 0), 0, used, None, "base")
    n = 1
    while not auxiliary():
        n += 1
    level = n * n + 4
    for _ in range(2 * level - n):
        if auxiliary():
            return Result(0, 0, used, n, "rare_gate_rejected")
    center = Fraction((1 << (n + 1)) + 1, 1 << (n + 2))
    bit, calls = predicate(source, center, level)
    return Result(bit, calls, used, n, "predicate")
