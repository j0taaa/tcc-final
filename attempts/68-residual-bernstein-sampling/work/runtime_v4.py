"""GMP-backed exact-bit factory and matched dense kernel; experimental runtime."""

import random
from dataclasses import dataclass
from math import comb as small_comb
from math import isqrt

from gmpy2 import mpq, mpz


def rational(value):
    if isinstance(value, (int, mpz, mpq)):
        return mpq(value)
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        return mpq(value.numerator, value.denominator)
    raise TypeError("Exact rational input required; floating probabilities refused")


class Bits:
    """Reproducible test stream; the mathematical interface is iid fair bits."""

    def __init__(self, seed):
        self.random = random.Random(seed)
        self.used = 0

    def getrandbits(self, count):
        self.used += count
        return self.random.getrandbits(count)


def randbelow(rng, bound):
    bound = mpz(bound)
    if bound <= 0:
        raise ValueError("Positive integer bound required")
    width = int((bound - 1).bit_length())
    while True:
        draw = rng.getrandbits(width)
        if draw < bound:
            return int(draw)


def bernoulli(rng, probability):
    p = rational(probability)
    if not 0 <= p <= 1:
        raise ValueError("Probability outside[0,1]")
    numerator, denominator = p.numerator, p.denominator
    if numerator == denominator:
        return 1
    while numerator:
        numerator *= 2
        digit = int(numerator >= denominator)
        if digit:
            numerator -= denominator
        bit = rng.getrandbits(1)
        if bit != digit:
            return int(bit < digit)
    return 0


class LazyUniform:
    def __init__(self, rng):
        self.rng, self.prefix, self.scale = rng, mpz(0), mpz(1)

    def less(self, probability):
        p = rational(probability)
        if not 0 <= p <= 1:
            raise ValueError("Probability outside[0,1]")
        while True:
            threshold = p.numerator * self.scale
            if (self.prefix + 1) * p.denominator <= threshold:
                return True
            if self.prefix * p.denominator >= threshold:
                return False
            self.prefix = 2 * self.prefix + self.rng.getrandbits(1)
            self.scale *= 2


def geometric(rng, survival):
    r = rational(survival)
    if not 0 <= r < 1:
        raise ValueError("Geometric survival must be in[0,1)")
    if not r:
        return 0
    uniform = LazyUniform(rng)
    lo, hi = 0, 1
    while uniform.less(rational_power(r, hi)):
        lo, hi = hi, 2 * hi
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if uniform.less(rational_power(r, mid)):
            lo = mid
        else:
            hi = mid
    return lo


def rational_power(base, exponent):
    result = mpq(1)
    while exponent:
        if exponent & 1:
            result *= base
        exponent >>= 1
        if exponent:
            base *= base
    return result


def product_tree(lo, hi):
    if hi < lo:
        return mpz(1)
    if hi - lo < 16:
        result = mpz(1)
        for i in range(lo, hi + 1):
            result *= i
        return result
    mid = (lo + hi) // 2
    return product_tree(lo, mid) * product_tree(mid + 1, hi)


def binomial(n, k):
    if n < 0 or k < 0:
        raise ValueError("Nonnegative binomial arguments required")
    if k > n:
        return mpz(0)
    k = min(k, n - k)
    return product_tree(n - k + 1, n) // product_tree(1, k)


@dataclass
class Stats:
    source_calls: int = 0
    level_bits: int = 0
    auxiliary_bits: int = 0
    f_requests: int = 0
    f_evaluations: int = 0
    value_cache_hits: int = 0
    scalar_cache_hits: int = 0
    coefficient_cache_hits: int = 0
    proposal_cache_hits: int = 0
    dense_terms: int = 0
    known_weights: int = 0
    mode_ratios: int = 0
    binomial_evaluations: int = 0
    rejection_attempts: int = 0
    component: str = ""
    value_cache_entries: int = 0
    scalar_cache_entries: int = 0
    coefficient_cache_entries: int = 0
    proposal_cache_entries: int = 0


def choose(stats, n, k):
    stats.binomial_evaluations += 1
    return binomial(n, k)


def jets(value, degree, x):
    step = mpq(1, isqrt(degree))
    if x > 1 - 2 * step:
        step = -step
    f0, f1, f2 = (value(x + i * step) for i in range(3))
    return f0, (-3 * f0 + 4 * f1 - f2) / (2 * step), degree * (f0 - 2 * f1 + f2)


def weighted_elevation(m, k, coefficient, stats):
    left, right = max(0, k - 3 * m), min(m, k)

    def split(lo, hi):
        if lo == hi:
            stats.dense_terms += 1
            c = rational(coefficient(lo))
            return c.denominator, c.denominator, c.numerator
        mid = (lo + hi) // 2
        pl, ql, tl = split(lo, mid)
        pr, qr, tr = split(mid + 1, hi)
        a = (m - mid) * (k - mid)
        b = (mid + 1) * (3 * m - k + mid + 1)
        return pl * a * pr, ql * b * qr, tl * b * qr + pl * a * tr

    _, denominator, numerator = split(left, right)
    first = choose(stats, m, left) * choose(stats, 3 * m, k - left)
    normalizer = choose(stats, 4 * m, k)
    return mpq(first * numerator, normalizer * denominator)


def polynomial(t):
    return mpq(9, 20) + mpq(21, 20) * t * t + t**4 / 12


class Proposal:
    def __init__(self, m, k, h, stats):
        self.m, self.k, self.h, self.stats = m, k, h, stats
        self.root, self.x = isqrt(m), mpq(k, 4 * m)
        self.left, self.right = max(0, k - 3 * m), min(m, k)
        factorial = [mpq(1)]
        for j in range(1, 5):
            factorial.append(factorial[-1] * (m - j + 1) * (k - j + 1) / (4 * m - j + 1))
        raw = (
            mpq(1),
            factorial[1],
            factorial[1] + factorial[2],
            factorial[1] + 3 * factorial[2] + factorial[3],
            factorial[1] + 7 * factorial[2] + 6 * factorial[3] + factorial[4],
        )
        mean = mpq(k, 4)
        second = raw[2] - mean**2
        fourth = sum((small_comb(4, j) * (-mean) ** (4 - j) * raw[j] for j in range(5)), mpq(0))
        self.total = mpq(9, 20) + mpq(21, 20) * second / m + fourth / (12 * m * m)
        self.mass = h * self.total / (m * self.root)
        self.term_bound = h / (21 * m * self.root)
        self.weight = 7 * h / (4 * m * self.root)
        self.term_probability = 2 * self.term_bound / self.weight
        self.residual_probability = 2 * self.mass / self.weight
        self.normalizer = self.plan = None

    def point_polynomial(self, i):
        return polynomial((mpq(i) - mpq(self.k, 4)) / self.root)

    def point_weight(self, i):
        self.stats.known_weights += 1
        if not self.left <= i <= self.right:
            return mpq(0)
        if self.normalizer is None:
            self.normalizer = choose(self.stats, 4 * self.m, self.k)
        return mpq(
            choose(self.stats, self.m, i) * choose(self.stats, 3 * self.m, self.k - i),
            self.normalizer,
        ) * self.point_polynomial(i)

    def ratio(self, i):
        self.stats.mode_ratios += 1
        return (
            mpq((self.m - i) * (self.k - i), (i + 1) * (3 * self.m - self.k + i + 1))
            * self.point_polynomial(i + 1)
            / self.point_polynomial(i)
        )

    def prepare(self):
        lo, hi = self.left, self.right
        while lo < hi:
            mid = (lo + hi) // 2
            if self.ratio(mid) >= 1:
                lo = mid + 1
            else:
                hi = mid
        mode, mode_weight = lo, self.point_weight(lo)
        cutoffs = []
        for sign in (-1, 1):
            distance = 1
            while self.point_weight(mode + sign * distance) > mode_weight / 2:
                distance *= 2
            cutoffs.append(distance)
        self.plan = mode, mode_weight, *cutoffs

    def draw_index(self, rng):
        if self.plan is None:
            self.prepare()
        mode, mode_weight, left, right = self.plan
        central, total = left + right - 1, 2 * left + 2 * right - 1
        while True:
            self.stats.rejection_attempts += 1
            ticket = randbelow(rng, total)
            if ticket < central:
                i, height = mode - left + 1 + ticket, mpq(1)
            else:
                cutoff, sign = (left, -1) if ticket < central + left else (right, 1)
                survival = 1 - mpq(1, 2 * cutoff)
                extra = geometric(rng, survival)
                i = mode + sign * (cutoff + extra)
                if not self.left <= i <= self.right:
                    continue
                height = rational_power(survival, extra) / 2
            target = self.point_weight(i)
            if bernoulli(rng, target / (mode_weight * height)):
                return i


class ResourceFail(RuntimeError):
    def __init__(self, n, level, limit, level_bits):
        self.n, self.level, self.limit, self.level_bits = n, level, limit, level_bits
        super().__init__(f"RESOURCE_FAIL: selected N={n} exceeds limit={limit}; no source calls")


@dataclass
class Draw:
    bit: int
    n: int
    k: int
    level: int
    stats: Stats


class Factory:
    def __init__(self, function, epsilon, curvature, lipschitz, reuse=False):
        self.function = function
        self.epsilon, self.curvature, self.h = map(rational, (epsilon, curvature, lipschitz))
        if not 0 < self.epsilon <= mpq(1, 2) or min(self.curvature, self.h) < 0:
            raise ValueError("Invalid range/curvature metadata")
        self.n0 = 16
        while (
            self.curvature / (8 * (self.n0 - 1)) + 17 * self.h / (15 * self.n0 * isqrt(self.n0))
            > self.epsilon
        ):
            self.n0 *= 4
        self.reuse = reuse
        self.values, self.scalars, self.coefficients, self.proposals = {}, {}, {}, {}

    def level(self, rng):
        if not self.h or not bernoulli(rng, 2 * self.h / (self.n0 * isqrt(self.n0))):
            return 0
        level = 1
        while rng.getrandbits(3) == 0:
            level += 1
        return level

    def vote(self, n, k, rng, method="sparse"):
        if (
            method not in ("sparse", "dense")
            or not isinstance(n, int)
            or n < self.n0
            or not isinstance(k, int)
            or not 0 <= k <= n
        ):
            raise ValueError("Invalid method/index")
        level, check_n = 0, n
        while check_n > self.n0 and check_n % 4 == 0:
            check_n //= 4
            level += 1
        if check_n != self.n0 or (not self.h and level):
            raise ValueError("Degree is not in this factory's level support")
        if not self.reuse:
            self.values, self.scalars, self.coefficients, self.proposals = {}, {}, {}, {}
        stats, start_bits = Stats(), rng.used

        def value(x):
            stats.f_requests += 1
            if x in self.values:
                stats.value_cache_hits += 1
                return self.values[x]
            if not 0 <= x <= 1:
                raise ValueError("Value query outside[0,1]")
            answer = rational(self.function(x))
            stats.f_evaluations += 1
            self.values[x] = answer
            return answer

        def coefficient(d, x):
            key = d, x
            if key in self.coefficients:
                stats.coefficient_cache_hits += 1
                return self.coefficients[key]
            f0, _, second = jets(value, d, x)
            answer = f0 - x * (1 - x) * second / (2 * (d - 1))
            self.coefficients[key] = answer
            return answer

        key, x = (n, k), mpq(k, n)
        if key in self.scalars:
            stats.component = "memoized_scalar"
            stats.scalar_cache_hits += 1
            bit = bernoulli(rng, self.scalars[key])
        elif level and k in (0, n):
            stats.component = "endpoint"
            self.scalars[key] = mpq(1, 2)
            bit = rng.getrandbits(1)
        elif not level:
            stats.component = "base"
            delta = self.h / (n * isqrt(n))
            probability = (coefficient(n, x) - delta) / (1 - 2 * delta)
            self.scalars[key] = probability
            bit = bernoulli(rng, probability)
        elif method == "dense":
            stats.component = "dense"
            m = n // 4
            elevated = weighted_elevation(m, k, lambda i: coefficient(m, mpq(i, m)), stats)
            probability = mpq(1, 2) + (coefficient(n, x) - elevated) / (
                7 * self.h / (4 * m * isqrt(m))
            )
            self.scalars[key] = probability
            bit = bernoulli(rng, probability)
        else:
            m = n // 4
            if key not in self.proposals:
                self.proposals[key] = Proposal(m, k, self.h, stats)
            else:
                stats.proposal_cache_hits += 1
            proposal = self.proposals[key]
            proposal.stats = stats
            if bernoulli(rng, proposal.term_probability):
                stats.component = "term"
                _, _, old = jets(value, m, x)
                _, _, new = jets(value, n, x)
                term = x * (1 - x) * (old - new) / (2 * (n - 1))
                bit = bernoulli(rng, mpq(1, 2) + term / (2 * proposal.term_bound))
            elif bernoulli(rng, proposal.residual_probability / (1 - proposal.term_probability)):
                stats.component = "residual"
                i = proposal.draw_index(rng)
                f0, slope, second = jets(value, m, x)
                y, z = mpq(i, m), mpq(i, m) - x
                fy, _, second_y = jets(value, m, y)
                remainder = fy - f0 - slope * z - second * z * z / 2
                residual = -remainder + y * (1 - y) * (second_y - second) / (2 * (m - 1))
                envelope = self.h * proposal.point_polynomial(i) / (m * isqrt(m))
                bit = bernoulli(rng, mpq(1, 2) + residual / (2 * envelope))
            else:
                stats.component = "fair"
                bit = rng.getrandbits(1)
        stats.auxiliary_bits = rng.used - start_bits
        stats.value_cache_entries, stats.scalar_cache_entries = len(self.values), len(self.scalars)
        stats.coefficient_cache_entries = len(self.coefficients)
        stats.proposal_cache_entries = len(self.proposals)
        return Draw(bit, n, k, level, stats)

    def sample(self, source_coin, rng, method="sparse", level_rng=None, max_coins=None):
        level_rng = rng if level_rng is None else level_rng
        if method not in ("sparse", "dense"):
            raise ValueError("Invalid method")
        if max_coins is not None and (not isinstance(max_coins, int) or max_coins < 0):
            raise ValueError("Invalid explicit resource limit")
        initial = level_rng.used
        level = self.level(level_rng)
        level_bits = level_rng.used - initial
        n = self.n0 * 4**level
        if max_coins is not None and n > max_coins:
            raise ResourceFail(n, level, max_coins, level_bits)
        k = 0
        for _ in range(n):
            value = source_coin()
            if not isinstance(value, (int, bool, mpz)) or value not in (0, 1):
                raise ValueError("Input coin must return an integer bit")
            k += int(value)
        draw = self.vote(n, k, rng, method)
        draw.stats.source_calls, draw.stats.level_bits = n, level_bits
        return draw
