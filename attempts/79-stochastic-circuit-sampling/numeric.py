"""A79-only positive dyadic arithmetic; no model, array, or hardware semantics.

Exactness assumes IID fair bits. ``Random`` supplies a reproducible finite PRNG
program, not a proof of that hypothesis. Prefix limits and exhausted test sources
raise RNGRefusal; retaining only completed runs need not preserve the output law.
"""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from fractions import Fraction
from random import Random


@dataclass(frozen=True, slots=True)
class DFloat:
    """Value ``mantissa * 2**exponent``; BinaryArithmetic enforces p-bit form."""

    mantissa: int
    exponent: int

    def __post_init__(self) -> None:
        if type(self.mantissa) is not int or type(self.exponent) is not int:
            raise TypeError("mantissa and exponent must be integers")
        if self.mantissa < 0 or (self.mantissa == 0 and self.exponent != 0):
            raise ValueError("nonnegative mantissa and canonical zero (0, 0) required")


def as_fraction(value: DFloat) -> Fraction:
    """TEST ORACLE ONLY: materializes exponents; never use on sparse huge gaps."""
    if value.exponent >= 0:
        return Fraction(value.mantissa << value.exponent)
    return Fraction(value.mantissa, 1 << -value.exponent)


class RNGRefusal(RuntimeError):
    """Resource/source refusal, neither zero mass nor a completed exact sample."""

    status = "refused_rng"

    def __init__(self, reason: str, used: int, limit: int) -> None:
        self.reason, self.used, self.limit = reason, used, limit
        super().__init__(f"{reason}: {used} bits received, limit {limit}")


@dataclass(frozen=True, slots=True)
class LazyThreshold:
    """Probability numerator / denominator * 2**(-shift), with compressed zeros.

    Only the small numerator/denominator are divided. A shift of 2**60 never
    becomes a dense integer. Adversarial bit streams may need an unbounded
    prefix; the caller's bit source must enforce its resource policy.
    """

    numerator: int
    denominator: int = 1
    shift: int = 0

    def __post_init__(self) -> None:
        n, d, s = self.numerator, self.denominator, self.shift
        if any(type(v) is not int for v in (n, d, s)):
            raise TypeError("threshold fields must be integers")
        if n < 0 or d <= 0 or s < 0:
            raise ValueError("invalid threshold")
        if n > d:
            extra = n.bit_length() - d.bit_length()
            extra += n > (d << extra)
            if extra > s:
                raise ValueError("threshold exceeds one")
            d, s = d << extra, s - extra
        if n == d and s:
            d, s = 2 * d, s - 1
        object.__setattr__(self, "denominator", d)
        object.__setattr__(self, "shift", s)

    def bits(self) -> Iterator[int]:
        """Canonical terminating expansion when dyadic; lazy otherwise."""
        for _ in range(self.shift):
            yield 0
        remainder = self.numerator
        while remainder:
            digit, remainder = divmod(2 * remainder, self.denominator)
            yield digit

    def compare_half(self) -> int:
        if self.shift:
            return 0 if self.shift == 1 and self.numerator == self.denominator else -1
        difference = 2 * self.numerator - self.denominator
        return (difference > 0) - (difference < 0)


class SharedUniformPrefix:
    """One uniform, shared across thresholds; cached bits count only once.

    A fresh instance must be supplied for each independent group. Checking group
    exclusivity/dependency order belongs to the circuit, not this numeric layer.
    """

    def __init__(self, draw_bit: Callable[[], int]) -> None:
        self.draw_bit = draw_bit
        self.prefix: list[int] = []

    def less_than(self, threshold: LazyThreshold) -> bool:
        if threshold.numerator == 0:
            return False
        if threshold.numerator == threshold.denominator and threshold.shift == 0:
            return True
        for index, digit in enumerate(threshold.bits()):
            if index == len(self.prefix):
                self.prefix.append(self.draw_bit())
            bit = self.prefix[index]
            if bit != digit:
                return bit < digit
        # Equal terminating prefix: any extension is >= this dyadic boundary.
        return False


class BinaryArithmetic:
    """Unbounded integer exponents, p-bit significands, exact conditional races.

    Call start_group before each stochastic group; without it, all rounded gates
    share the initial lazy uniform. Choose uses only its supplied independent RNG.
    Counters belong to this instance/query: random_bits is arithmetic noise,
    choose_bits is reconstruction noise, random_calls counts actual getrandbits
    invocations (including a failed source call), and exact_rounds counts gates
    whose exact result was representable. RNG bits are not a work/memory metric.
    """

    def __init__(self, p: int, mode: str, rng: Random, *, max_random_bits: int = 1_000_000) -> None:
        if type(p) is not int or p < 2:
            raise ValueError("p must be an integer >= 2")
        if mode not in ("nearest", "stochastic"):
            raise ValueError("mode must be nearest or stochastic")
        if type(max_random_bits) is not int or max_random_bits < 1:
            raise ValueError("max_random_bits must be a positive integer")
        self.p, self.mode, self.rng = p, mode, rng
        self.max_random_bits = max_random_bits
        self.stats = dict.fromkeys(
            (
                "random_bits",
                "choose_bits",
                "random_calls",
                "exact_rounds",
                "groups",
                "arithmetic_comparisons",
                "choose_comparisons",
                "choose_attempts",
                "conversions",
                "additions",
                "multiplications",
            ),
            0,
        )
        self.counts = self.stats
        self._uniform: SharedUniformPrefix | None = None

    def _bit(self, rng: Random, key: str) -> int:
        used = self.stats["random_bits"] + self.stats["choose_bits"]
        if used >= self.max_random_bits:
            raise RNGRefusal("bit_limit", used, self.max_random_bits)
        self.stats["random_calls"] += 1
        try:
            bit = rng.getrandbits(1)
        except (EOFError, StopIteration) as error:
            raise RNGRefusal("source_exhausted", used, self.max_random_bits) from error
        if type(bit) is not int or bit not in (0, 1):
            raise ValueError("getrandbits(1) must return a single bit")
        self.stats[key] += 1
        return bit

    def start_group(self) -> None:
        self._uniform = SharedUniformPrefix(lambda: self._bit(self.rng, "random_bits"))
        self.stats["groups"] += 1

    def _check(self, value: DFloat) -> None:
        if value.mantissa and value.mantissa.bit_length() != self.p:
            raise ValueError("operand is not normalized to this precision")

    def _finish(self, lower: int, exponent: int, threshold: LazyThreshold) -> DFloat:
        if threshold.numerator == 0:
            self.stats["exact_rounds"] += 1
            up = False
        elif self.mode == "nearest":
            relation = threshold.compare_half()
            up = relation > 0 or (relation == 0 and bool(lower & 1))
        else:
            if self._uniform is None:
                self.start_group()
            self.stats["arithmetic_comparisons"] += 1
            assert self._uniform is not None
            up = self._uniform.less_than(threshold)
        mantissa = lower + up
        if mantissa.bit_length() > self.p:
            mantissa, exponent = mantissa >> 1, exponent + 1
        return DFloat(mantissa, exponent)

    def _round(self, mantissa: int, exponent: int) -> DFloat:
        if not mantissa:
            self.stats["exact_rounds"] += 1
            return DFloat(0, 0)
        shift = mantissa.bit_length() - self.p
        if shift <= 0:
            self.stats["exact_rounds"] += 1
            return DFloat(mantissa << -shift, exponent + shift)
        lower = mantissa >> shift
        remainder = mantissa - (lower << shift)
        return self._finish(lower, exponent + shift, LazyThreshold(remainder, 1, shift))

    def convert(self, value: Fraction) -> DFloat:
        if not isinstance(value, Fraction):
            raise TypeError("convert accepts an explicit Fraction")
        denominator = value.denominator
        if value < 0 or denominator & (denominator - 1):
            raise ValueError("only nonnegative dyadic inputs are supported")
        self.stats["conversions"] += 1
        return self._round(value.numerator, -(denominator.bit_length() - 1))

    def add(self, left: DFloat, right: DFloat) -> DFloat:
        self._check(left)
        self._check(right)
        self.stats["additions"] += 1
        if not left.mantissa or not right.mantissa:
            self.stats["exact_rounds"] += 1
            return right if not left.mantissa else left
        if left.exponent < right.exponent:
            left, right = right, left
        gap = left.exponent - right.exponent
        if gap < self.p:
            return self._round((left.mantissa << gap) + right.mantissa, right.exponent)
        return self._finish(left.mantissa, left.exponent, LazyThreshold(right.mantissa, 1, gap))

    def mul(self, left: DFloat, right: DFloat) -> DFloat:
        self._check(left)
        self._check(right)
        self.stats["multiplications"] += 1
        return self._round(left.mantissa * right.mantissa, left.exponent + right.exponent)

    def choose(self, left: DFloat, right: DFloat, rng: Random) -> int:
        """Return 0/1 with masses left/right via a fresh exact Bernoulli race.

        No sum, dense exponent alignment, or arithmetic-noise prefix is used.
        Its supplied random stream must be independent of the arithmetic noise.
        """
        self._check(left)
        self._check(right)
        if not left.mantissa and not right.mantissa:
            raise ValueError("cannot choose from zero total mass")
        if not left.mantissa or not right.mantissa:
            return int(not left.mantissa)
        masses = (left, right)
        maximum = int((right.exponent, right.mantissa) > (left.exponent, left.mantissa))
        small, large = masses[1 - maximum], masses[maximum]
        threshold = LazyThreshold(small.mantissa, large.mantissa, large.exponent - small.exponent)
        while True:
            self.stats["choose_attempts"] += 1
            candidate = self._bit(rng, "choose_bits")
            if candidate == maximum:
                return candidate
            self.stats["choose_comparisons"] += 1
            uniform = SharedUniformPrefix(lambda: self._bit(rng, "choose_bits"))
            if uniform.less_than(threshold):
                return candidate
