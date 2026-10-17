"""Finite exact response with a charged compact binary parameter; proof reference."""

from fractions import Fraction

from separation import Result, predicate


def parse_limit(binary):
    if (
        not isinstance(binary, str)
        or not binary
        or any(ch not in "01" for ch in binary)
        or (len(binary) > 1 and binary[0] == "0")
    ):
        raise ValueError("Canonical nonnegative binary R required")
    return int(binary, 2)


def sample_finite(source, rng, binary_limit):
    limit = parse_limit(binary_limit)
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
    if n > limit:
        return Result(0, 0, used, n, "cap_rejected")
    level = n * n + 4
    for _ in range(2 * level - n):
        if auxiliary():
            return Result(0, 0, used, n, "rare_gate_rejected")
    center = Fraction((1 << (n + 1)) + 1, 1 << (n + 2))
    bit, calls = predicate(source, center, level)
    return Result(bit, calls, used, n, "predicate")
