"""Small rational arithmetic model; no GPU implementation or timing claim."""

from dataclasses import dataclass
from fractions import Fraction as F


class Refusal(ValueError):
    """The fast relative certificate is unavailable, not zero target mass."""


def power2(exponent):
    return F(2) ** exponent


def log2floor(value):
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    return exponent - (value < power2(exponent))


@dataclass(frozen=True)
class Format:
    precision: int
    emin: int
    emax: int

    def __post_init__(self):
        if self.precision < 2 or self.emin >= self.emax:
            raise ValueError("nontrivial binary format required")

    @property
    def epsilon(self):
        return power2(1 - self.precision)

    @property
    def maximum(self):
        return (2 - power2(1 - self.precision)) * power2(self.emax)

    def round(self, value, direction="nearest"):
        value = F(value)
        if value < 0 or direction not in ("nearest", "down", "up"):
            raise ValueError("nonnegative arithmetic/explicit rounding required")
        if value == 0:
            return F(0)
        quantum = power2(max(self.emin, log2floor(value)) - self.precision + 1)
        ratio = value / quantum
        floor = ratio.numerator // ratio.denominator
        remainder = ratio - floor
        if direction == "up":
            floor += remainder > 0
        elif direction == "nearest":
            floor += remainder > F(1, 2) or (remainder == F(1, 2) and floor % 2 == 1)
        result = floor * quantum
        if result > self.maximum:
            raise Refusal("overflow of the declared format")
        return result

    def guarded(self, operation_result):
        result = self.round(operation_result)
        if operation_result > 0 and result < power2(self.emin):
            raise Refusal("positive underflow/subnormal: refine, never drop")
        return result


@dataclass(frozen=True)
class Node:
    exact: F
    rounded: F
    budget: int


def convert(value, fmt):
    value = F(value)
    return Node(value, fmt.guarded(value), 1)


def add(left, right, fmt):
    return Node(
        left.exact + right.exact,
        fmt.guarded(left.rounded + right.rounded),
        max(left.budget, right.budget) + 1,
    )


def multiply(left, right, fmt):
    return Node(
        left.exact * right.exact,
        fmt.guarded(left.rounded * right.rounded),
        left.budget + right.budget + 1,
    )


def scale(node, observed_scale, fmt):
    observed_scale = F(observed_scale)
    if observed_scale <= 0 or fmt.round(observed_scale) != observed_scale:
        raise ValueError("positive observed representable scale required")
    return Node(
        node.exact / observed_scale, fmt.guarded(node.rounded / observed_scale), node.budget + 1
    )


def enclosure(node, fmt, materialize=False):
    low_factor = 1 / (1 + fmt.epsilon) ** node.budget
    high_factor = 1 / (1 - fmt.epsilon) ** node.budget
    if materialize:
        low_factor = fmt.round(low_factor, "down")
        high_factor = fmt.round(high_factor, "up")
        return (
            fmt.round(node.rounded * low_factor, "down"),
            fmt.round(node.rounded * high_factor, "up"),
        )
    return node.rounded * low_factor, node.rounded * high_factor


def prefix_interval(weights, boundary):
    before = weights[:boundary]
    after = weights[boundary:]
    low_a, high_a = (sum(x[i] for x in before) for i in (0, 1))
    low_b, high_b = (sum(x[i] for x in after) for i in (0, 1))
    if not before:
        return F(0), F(0)
    if not after:
        return F(1), F(1)
    if low_a + high_b == 0 or high_a + low_b == 0:
        raise Refusal("unresolved zero denominator")
    return low_a / (low_a + high_b), high_a / (high_a + low_b)


def certified_choice(weights, uniform_low, uniform_high):
    for i in range(len(weights)):
        if (
            prefix_interval(weights, i)[1] <= uniform_low
            and uniform_high <= prefix_interval(weights, i + 1)[0]
        ):
            return i
    return None
