"""Classical retained-uniform interval decision and exact fallback reference."""

from fractions import Fraction as F


def certified_index(lower, upper, prefix, bits):
    if (
        len(lower) != len(upper)
        or not lower
        or any(not 0 <= a <= b for a, b in zip(lower, upper, strict=True))
        or type(bits) is not int
        or bits < 1
        or not 0 <= prefix < 1 << bits
    ):
        raise ValueError("valid nonnegative interval weights and fair-bit prefix required")
    u0, u1 = F(prefix, 1 << bits), F(prefix + 1, 1 << bits)
    answer = None
    for j in range(len(lower)):
        if j == 0:
            left_hi = F(0)
        else:
            a, b = sum(upper[:j], F()), sum(lower[j:], F())
            left_hi = a / (a + b) if a + b else F(1)
        if j + 1 == len(lower):
            right_lo = F(1)
        else:
            a, b = sum(lower[: j + 1], F()), sum(upper[j + 1 :], F())
            right_lo = a / (a + b) if a + b else F(0)
        if left_hi <= u0 and u1 <= right_lo:
            if answer is not None:
                raise RuntimeError("overlapping certified uniform intervals")
            answer = j
    return answer


def exact_with_retained_prefix(weights, prefix, bits, rng):
    if not weights or any(w < 0 for w in weights) or sum(weights, F()) <= 0:
        raise ValueError("positive exact categorical total required")
    total = sum(weights, F())
    while True:
        u0, u1, left = F(prefix, 1 << bits), F(prefix + 1, 1 << bits), F()
        for j, weight in enumerate(weights):
            right = left + weight / total
            if left <= u0 and u1 <= right:
                return j
            left = right
        prefix = (prefix << 32) | rng.getrandbits(32)
        bits += 32
