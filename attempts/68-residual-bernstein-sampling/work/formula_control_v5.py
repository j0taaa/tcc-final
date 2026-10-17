"""Classical exact formula-aware and derivative controls; no novel factory claim."""

from bisect import bisect_left
from dataclasses import dataclass
from functools import cache
from itertools import pairwise
from math import comb, isqrt

from gmpy2 import mpq, mpz
from runtime_v4 import Draw, Factory, Stats, bernoulli, choose, randbelow, rational


def trim(poly):
    poly = list(poly)
    while len(poly) > 1 and not poly[-1]:
        poly.pop()
    return tuple(poly)


def add(*terms):
    result = [mpq(0)] * max(len(poly) for _, poly in terms)
    for weight, poly in terms:
        for i, value in enumerate(poly):
            result[i] += weight * value
    return trim(result)


def multiply(left, right):
    result = [mpq(0)] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            result[i + j] += a * b
    return trim(result)


def shift(poly, step):
    return trim(
        [
            sum((poly[j] * comb(j, i) * step ** (j - i) for j in range(i, len(poly))), mpq(0))
            for i in range(len(poly))
        ]
    )


def derivative(poly):
    return trim([i * poly[i] for i in range(1, len(poly))] or [mpq(0)])


def evaluate(poly, x):
    answer = mpq(0)
    for coefficient in reversed(poly):
        answer = answer * x + coefficient
    return answer


@cache
def stirling(n, r):
    if n == 0:
        return int(r == 0)
    if not 0 < r <= n:
        return 0
    return r * stirling(n - 1, r) + stirling(n - 1, r - 1)


@dataclass
class FormulaStats(Stats):
    formula_evaluations: int = 0
    interval_requests: int = 0
    interval_cache_hits: int = 0
    interval_terms: int = 0
    compilations: int = 0
    compiled_segments: int = 0
    interval_cache_entries: int = 0
    piece_cache_entries: int = 0


def hg_interval(total, successes, draws, lo, hi, stats, memo):
    if not 0 <= successes <= total or not 0 <= draws <= total:
        raise ValueError("Invalid hypergeometric parameters")
    stats.interval_requests += 1
    left, right = max(0, draws - (total - successes)), min(draws, successes)
    lo, hi = max(lo, left), min(hi, right)
    if hi < lo:
        return mpq(0)
    if (lo, hi) == (left, right):
        return mpq(1)
    key = total, successes, draws, lo, hi
    if key in memo:
        stats.interval_cache_hits += 1
        return memo[key]

    def block(a, b):
        if a > b:
            return mpq(0)

        def split(u, v):
            if u == v:
                stats.interval_terms += 1
                return mpz(1), mpz(1), mpz(1)
            mid = (u + v) // 2
            pl, ql, tl = split(u, mid)
            pr, qr, tr = split(mid + 1, v)
            ratio_a = (draws - mid) * (successes - mid)
            ratio_b = (mid + 1) * (total - draws - successes + mid + 1)
            return (
                pl * ratio_a * pr,
                ql * ratio_b * qr,
                tl * ratio_b * qr + pl * ratio_a * tr,
            )

        _, denominator, numerator = split(a, b)
        first = choose(stats, draws, a) * choose(stats, total - draws, successes - a)
        norm_key = "normalizer", total, successes
        if norm_key not in memo:
            memo[norm_key] = choose(stats, total, successes)
        return mpq(first * numerator, denominator * memo[norm_key])

    if hi - lo + 1 <= lo - left + right - hi:
        result = block(lo, hi)
    else:
        result = 1 - block(left, lo - 1) - block(hi + 1, right)
    memo[key] = result
    return result


class Piecewise:
    def __init__(self, name, knots, polynomials, curvature, lipschitz):
        self.name, self.knots = name, tuple(map(rational, knots))
        self.polynomials = tuple(tuple(map(rational, p)) for p in polynomials)
        if (
            len(self.polynomials) != len(self.knots) + 1
            or any(not 0 < k < 1 for k in self.knots)
            or any(a >= b for a, b in pairwise(self.knots))
            or any(not p for p in self.polynomials)
        ):
            raise ValueError("Invalid piecewise polynomial")
        self.curvature, self.h = rational(curvature), rational(lipschitz)
        self.seconds = tuple(derivative(derivative(p)) for p in self.polynomials)

    def piece(self, x):
        return self.polynomials[bisect_left(self.knots, x)]

    def value(self, x):
        return evaluate(self.piece(x), x)

    def second(self, x):
        return evaluate(self.seconds[bisect_left(self.knots, x)], x)


def original_specs():
    q = mpq
    return (
        Piecewise("constant", (), ((q(1, 2),),), 0, 0),
        Piecewise("affine", (), ((q(1, 4), q(1, 2)),), 0, 0),
        Piecewise("quadratic", (), ((q(1, 4), 0, q(1, 4)),), q(1, 2), 0),
        Piecewise("cubic", (), ((q(1, 4), 0, 0, q(1, 4)),), q(3, 2), q(3, 2)),
        Piecewise(
            "spline",
            (q(1, 2),),
            ((q(1, 4), q(1, 8)), (q(7, 32), q(5, 16), -q(3, 8), q(1, 4))),
            q(3, 4),
            q(3, 2),
        ),
        Piecewise(
            "reflected_spline",
            (q(1, 2),),
            ((q(13, 32), -q(5, 16), q(3, 8), -q(1, 4)), (q(3, 8), -q(1, 8))),
            q(3, 4),
            q(3, 2),
        ),
    )


class CompiledFactory(Factory):
    """Reuse V4's outer loop; replace its vote dispatch by a classical formula."""

    def __init__(self, spec, analytic=False, reuse=False):
        super().__init__(spec.value, mpq(1, 4), spec.curvature, spec.h, reuse)
        self.spec, self.analytic = spec, analytic
        self.label = "derivative" if analytic else "formula"
        self.piece_cache, self.interval_cache = {}, {}
        if analytic:
            self.n0 = 16
            while (
                self.curvature / (8 * (self.n0 - 1)) + self.h / (self.n0 * isqrt(self.n0))
                > self.epsilon
            ):
                self.n0 *= 4

    def center(self, degree, x, stats):
        if self.analytic:
            stats.formula_evaluations += 2
            return self.spec.value(x) - x * (1 - x) * self.spec.second(x) / (2 * (degree - 1))
        stats.formula_evaluations += 3
        step = mpq(1, isqrt(degree))
        if x > 1 - 2 * step:
            step = -step
        f0 = self.spec.value(x)
        second = degree * (f0 - 2 * self.spec.value(x + step) + self.spec.value(x + 2 * step))
        return f0 - x * (1 - x) * second / (2 * (degree - 1))

    def compile(self, m, stats):
        if m in self.piece_cache:
            return self.piece_cache[m]
        root, h = isqrt(m), mpq(1, isqrt(m))
        cuts = {0, m + 1}
        shifts = (0,) if self.analytic else (-2 * h, -h, 0, h, 2 * h)
        for knot in self.spec.knots:
            for offset in shifts:
                threshold = m * (knot - offset)
                cuts.add(int(threshold.numerator // threshold.denominator) + 1)
        if not self.analytic:
            cuts.add(m - 2 * root + 1)
        cuts = sorted(c for c in cuts if 0 <= c <= m + 1)
        pieces = []
        for lo, after in pairwise(cuts):
            y = mpq(lo, m)
            f0 = self.spec.piece(y)
            if self.analytic:
                correction = derivative(derivative(f0))
                scale = mpq(1, 2 * (m - 1))
            else:
                step = h if y <= 1 - 2 * h else -h
                f1 = shift(self.spec.piece(y + step), step)
                f2 = shift(self.spec.piece(y + 2 * step), 2 * step)
                correction = add((1, f0), (-2, f1), (1, f2))
                scale = mpq(m, 2 * (m - 1))
            poly = add((1, f0), (-scale, multiply((mpq(0), mpq(1), -mpq(1)), correction)))
            pieces.append((lo, after - 1, poly))
        stats.compilations += 1
        stats.compiled_segments += len(pieces)
        self.piece_cache[m] = pieces
        return pieces

    def elevated(self, m, k, stats):
        answer = mpq(0)
        for lo, hi, poly in self.compile(m, stats):
            if hi < max(0, k - 3 * m) or lo > min(m, k):
                continue
            factorial_moments, prefactor = [], mpq(1)
            for r in range(len(poly)):
                if r:
                    prefactor *= mpq((m - r + 1) * (k - r + 1), 4 * m - r + 1)
                moment = mpq(0)
                if prefactor:
                    moment = prefactor * hg_interval(
                        4 * m - r, k - r, m - r, lo - r, hi - r, stats, self.interval_cache
                    )
                factorial_moments.append(moment)
            for j, coefficient in enumerate(poly):
                answer += (
                    coefficient
                    / m**j
                    * sum((stirling(j, r) * factorial_moments[r] for r in range(j + 1)), mpq(0))
                )
        return answer

    def vote(self, n, k, rng, method="dense"):
        if method not in ("dense", self.label) or not isinstance(n, int) or not isinstance(k, int):
            raise ValueError("Invalid formula dispatch")
        if not 0 <= k <= n:
            raise ValueError("Index outside canvas")
        degree, level = n, 0
        while degree > self.n0 and degree % 4 == 0:
            degree //= 4
            level += 1
        if degree != self.n0 or (not self.h and level):
            raise ValueError("Invalid formula level")
        if not self.reuse:
            self.scalars, self.piece_cache, self.interval_cache = {}, {}, {}
        stats, start = FormulaStats(component=self.label), rng.used
        key, x = (n, k), mpq(k, n)
        if key in self.scalars:
            probability = self.scalars[key]
            stats.scalar_cache_hits += 1
        elif level and k in (0, n):
            probability = mpq(1, 2)
        elif not level:
            delta = self.h / (n * isqrt(n))
            probability = (self.center(n, x, stats) - delta) / (1 - 2 * delta)
        else:
            m = n // 4
            probability = mpq(1, 2) + (self.center(n, x, stats) - self.elevated(m, k, stats)) / (
                7 * self.h / (4 * m * isqrt(m))
            )
        self.scalars[key] = probability
        bit = bernoulli(rng, probability)
        stats.auxiliary_bits = rng.used - start
        stats.scalar_cache_entries = len(self.scalars)
        stats.interval_cache_entries, stats.piece_cache_entries = (
            len(self.interval_cache),
            len(self.piece_cache),
        )
        return Draw(bit, n, k, level, stats)

    def sample(self, source_coin, rng, method=None, level_rng=None, max_coins=None):
        if method not in (None, self.label):
            raise ValueError("Invalid formula method")
        # The validated outer loop calls self.vote(..., 'dense'); this explicit
        # subclass dispatch executes the formula kernel, never dense elevation.
        return super().sample(source_coin, rng, "dense", level_rng, max_coins)


def direct_plan(name, ticket, padded=False):
    if name == "constant":
        return int(padded), ticket, False
    if name == "affine":
        return (1, None, True) if ticket >= 2 else (int(padded), int(ticket == 0), False)
    if name in ("quadratic", "cubic"):
        if ticket == 1:
            return (2 if name == "quadratic" else 3), None, True
        return int(padded), int(ticket == 0), False
    raise ValueError("No finite polynomial control for this nonpolynomial link")


def direct_sample(name, source_coin, rng, padded=False, short_circuit=False):
    if padded and short_circuit:
        raise ValueError("Padded parent count must be non-adaptive")
    ticket = randbelow(rng, 2 if name == "constant" else 4)
    planned, fixed, product = direct_plan(name, ticket, padded)
    parents = []
    for _ in range(planned):
        bit = source_coin()
        if bit not in (0, 1):
            raise ValueError("Invalid input bit")
        parents.append(int(bit))
        if product and short_circuit and not bit:
            break
    return (int(all(parents)) if product else fixed), len(parents), planned
