"""Small rational conditional-law reference; no full or fast-bit factory."""

from fractions import Fraction as F
from math import comb, isqrt


def check(m, k, h):
    root = isqrt(m) if isinstance(m, int) and m >= 16 else 0
    if not root or root * root != m or root & (root - 1):
        raise ValueError("Old degree must be a power of four >=16")
    if not isinstance(k, int) or not 0 <= k <= 4 * m or h <= 0:
        raise ValueError("Invalid index or nonpositive Lipschitz bound")


def jets(function, degree, x):
    h = F(1, isqrt(degree))
    sign = 1 if x <= 1 - 2 * h else -1
    f0, f1, f2 = (F(function(x + i * sign * h)) for i in range(3))
    slope = sign * (-3 * f0 + 4 * f1 - f2) / (2 * h)
    second = degree * (f0 - 2 * f1 + f2)
    return f0, slope, second


def envelope(m, z):
    root = isqrt(m)
    return (
        abs(z) / (3 * m)
        + z * z / (2 * root)
        + abs(z) ** 3 / 6
        + (abs(z) + F(2, root)) / (8 * (m - 1))
    )


class KnownProposal:
    """No callback argument: all preparation is independent of f-values."""

    def __init__(self, m, k, h):
        check(m, k, h)
        self.m, self.x, self.h = m, F(k, 4 * m), F(h)
        self.indices = tuple(range(max(0, k - 3 * m), min(m, k) + 1))
        self.nu = tuple(F(comb(m, i) * comb(3 * m, k - i), comb(4 * m, k)) for i in self.indices)
        self.bounds = tuple(self.h * envelope(m, F(i, m) - self.x) for i in self.indices)
        self.mass = sum((v * b for v, b in zip(self.nu, self.bounds, strict=True)), F())
        self.proposal = tuple(v * b / self.mass for v, b in zip(self.nu, self.bounds, strict=True))
        self.weight = 7 * self.h / (4 * m * isqrt(m))
        self.branch_probability = 2 * self.mass / self.weight


class Increment:
    def __init__(self, function, proposal):
        self.function, self.proposal = function, proposal
        m, x = proposal.m, proposal.x
        self.f0, self.slope, self.second = jets(function, m, x)
        _, _, new_second = jets(function, 4 * m, x)
        self.term = x * (1 - x) * (self.second - new_second) / (2 * (4 * m - 1))
        self.offset = proposal.weight / 2 + self.term
        self.baseline = (self.offset - proposal.mass) / (proposal.weight - 2 * proposal.mass)

    def optional_branch(self, index):
        if index not in self.proposal.indices:
            raise ValueError("Index outside hypergeometric support")
        m, x = self.proposal.m, self.proposal.x
        y, z = F(index, m), F(index, m) - x
        fy, _, second_y = jets(self.function, m, y)
        remainder = fy - self.f0 - self.slope * z - self.second * z * z / 2
        residual = -remainder + y * (1 - y) * (second_y - self.second) / (2 * (m - 1))
        bound = self.proposal.h * envelope(m, z)
        return F(1, 2) + residual / (2 * bound), residual
