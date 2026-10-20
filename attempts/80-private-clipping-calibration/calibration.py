"""Attempt-local rational calibration; no model, emission, or benchmark driver.

The numerical certificates concern a frozen empirical objective. The confidence
statement additionally assumes normalized evaluators, IID mixture observations,
and the public sample budget. A seeded Random is only a reproduction device.
Object payloads are not RSS. Work widths are conservative bounds for arithmetic
here, excluding the source/evaluators and Python's internal multiplication/GCD.
"""

from __future__ import annotations

import sys
from array import array
from bisect import bisect_right
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import groupby, pairwise
from random import Random
from time import perf_counter

METHODS = ("ratio_bisection", "indices", "grid", "gk", "median")
_U64 = 1 << 64


def _ceil(x: Fraction) -> int:
    return -(-x.numerator // x.denominator)


def _ceil_log2(x: Fraction) -> int:
    k = max(0, x.numerator.bit_length() - x.denominator.bit_length())
    return k + (Fraction(1 << k) < x)


@dataclass(frozen=True)
class PublicGrid:
    """Implicit, increasing gamma grid; no array of public rational points.

    quantize floors gamma to a grid point. The dyadic path performs one large
    division, then bit lengths, shifts and a bounded number of comparisons.
    """

    kind: str
    D: int
    H: int
    m: int = 0
    h: int = 0

    def __post_init__(self) -> None:
        uniform = self.kind == "uniform" and self.D > 0 and self.H == self.D + 1
        dyadic = (
            self.kind == "dyadic"
            and self.m > 0
            and self.h > 0
            and self.D == self.m << self.h
            and self.H == self.m * (self.h + 1) + 1
        )
        if not (uniform or dyadic):
            raise ValueError("invalid public grid description")

    def __len__(self) -> int:
        return self.H

    def numerator(self, index: int) -> int:
        if not 0 <= index < self.H:
            raise IndexError(index)
        if self.kind == "uniform":
            return index
        if index == self.H - 1:
            return self.D
        block, offset = divmod(index, self.m)
        if block >= self.h:
            return self.D - self.m + offset
        return self.D - (self.D >> block) + (offset << (self.h - block - 1))

    def quantize(self, U: int, V: int) -> int:
        u = (self.D * U) // (U + V)
        if self.kind == "uniform":
            return u
        t = self.D - u
        s = max(0, t.bit_length() - self.m.bit_length())
        if t > self.m << s:
            s += 1
        block = self.h - s
        if block >= self.h:
            return self.h * self.m + u - (self.D - self.m)
        base = self.D - (self.D >> block)
        return block * self.m + ((u - base) >> (self.h - block - 1))


@dataclass(frozen=True)
class Config:
    R: Fraction
    xi: Fraction
    beta: Fraction
    bar_b: Fraction
    M: int
    M_median: int
    J: int
    delta: Fraction
    grid: PublicGrid

    @property
    def eps(self) -> Fraction:
        return self.xi / (128 * max(1, self.bar_b))


def _saa_budget(xi: Fraction, bar_b: Fraction) -> int:
    return _ceil(2 * (32 + 56 * bar_b / 3) * Fraction(37, 10) / xi)


def _median_budget(xi: Fraction, bar_b: Fraction) -> int:
    eta = xi / (bar_b + xi)
    corrected = eta - Fraction(1, 1 << 63)
    if corrected <= 0:
        raise ValueError("median eta must exceed the public U64 correction")
    n = _ceil(Fraction(74, 10) / corrected**2)
    return n if n % 2 else n + 1


def make_config(R: int) -> Config:
    """Frozen V1 production parameters, only R=2 and R=16."""
    if type(R) is not int or R not in (2, 16):
        raise ValueError("V1 production R must be 2 or 16")
    r, xi, beta = Fraction(R), Fraction(1, 50), Fraction(1, 20)
    bar_b = Fraction(7, 10) if R == 2 else Fraction(14, 5)
    B = max(1, bar_b)
    Q = _ceil(32 * (r + 1) * B / xi)
    m, h = _ceil(32 * B / xi), _ceil_log2(r + 1)
    if Q <= m * (h + 1):
        grid = PublicGrid("uniform", Q, Q + 1)
        delta = 2 * (r + 1) / Q
    else:
        grid = PublicGrid("dyadic", m << h, m * (h + 1) + 1, m, h)
        delta = Fraction(2, m)
    J = _ceil_log2(2 * r * (1 - 1 / r) / delta) + 1
    return Config(
        r, xi, beta, bar_b, _saa_budget(xi, bar_b), _median_budget(xi, bar_b), J, delta, grid
    )


def public_grid(config: Config) -> PublicGrid:
    return config.grid


@dataclass(frozen=True)
class CalibrationResult:
    a: Fraction
    samples: int
    collection_seconds: float
    solve_seconds: float
    state_numeric_bits: int
    state_storage_bytes: int
    max_work_bits: int
    certificate: dict


def _payload(state: object) -> tuple[int, int]:
    """Logical numeric bits and recursively owned Python storage, outside timers.

    Repeated numeric entries count separately in logical bits; shared Python
    objects count once in storage. Container capacities come from getsizeof.
    """
    seen: set[int] = set()

    def visit(value: object) -> tuple[int, int]:
        size = 0 if id(value) in seen else sys.getsizeof(value)
        seen.add(id(value))
        if isinstance(value, int):
            return max(1, abs(value).bit_length()), size
        if isinstance(value, Fraction):
            nb, ns = visit(value.numerator)
            db, ds = visit(value.denominator)
            return nb + db, size + ns + ds
        if isinstance(value, array):
            return sum(max(1, x.bit_length()) for x in value), size
        if isinstance(value, (list, tuple)):
            values = [visit(x) for x in value]
            return sum(x[0] for x in values), size + sum(x[1] for x in values)
        raise TypeError(f"unsupported payload object {type(value)!r}")

    return visit(state)


def _unsigned_array(max_value: int, values: Iterable[int] = ()) -> array:
    for kind in ("I", "Q"):
        if max_value < 1 << (8 * array(kind).itemsize):
            return array(kind, values)
    raise ValueError("calibration array exceeds unsigned 64-bit capacity")


class GKSummary:
    """Deterministic Greenwald--Khanna tuples (value, g, delta).

    Right insertion handles ties as separate observations. Compression preserves
    the first/last ranks and g+delta <= max(1,floor(2 eps n)). Representatives
    with weights g have total n and CDF error at most 2 eps. No original stream
    is retained; independent tests check that claim against original ranks.
    """

    def __init__(self, eps: Fraction):
        if not 0 < eps < Fraction(1, 2):
            raise ValueError("GK epsilon must lie in (0,1/2)")
        self.eps = eps
        self.n = 0
        self.entries: list[tuple[int, int, int]] = []
        self.period = max(1, (eps.denominator // (2 * eps.numerator)))

    def insert(self, value: int) -> None:
        self.n += 1
        pos = bisect_right(self.entries, value, key=lambda entry: entry[0])
        cap = (2 * self.eps.numerator * self.n) // self.eps.denominator
        delta = 0 if pos in (0, len(self.entries)) else max(0, cap - 1)
        self.entries.insert(pos, (value, 1, delta))
        if self.n % self.period == 0:
            self.compress()

    def compress(self) -> None:
        cap = (2 * self.eps.numerator * self.n) // self.eps.denominator
        # A backwards pass merges into the representative on the right.
        for i in range(len(self.entries) - 2, 0, -1):
            _, g, _ = self.entries[i]
            v1, g1, d1 = self.entries[i + 1]
            if g + g1 + d1 <= cap:
                self.entries[i + 1] = (v1, g + g1, d1)
                del self.entries[i]

    def validate(self) -> bool:
        cap = max(1, (2 * self.eps.numerator * self.n) // self.eps.denominator)
        return (
            bool(self.entries)
            and self.entries[0][2] == self.entries[-1][2] == 0
            and sum(g for _, g, _ in self.entries) == self.n
            and all(g > 0 and d >= 0 and g + d <= cap for _, g, d in self.entries)
            and all(a[0] <= b[0] for a, b in pairwise(self.entries))
        )


def _sweep(rows: Sequence[tuple[int, int]], D: int, R: Fraction) -> Fraction:
    """Exact minimizer for increasing (gamma numerator, positive count) rows."""
    a0 = 1 / R
    rn, rd = R.numerator, R.denominator
    lower = upper = active = 0
    for u, count in rows:
        if R.numerator * u <= R.denominator * (D - u):
            lower += count * (D - u)
            active += count * u
        elif u > D - u:
            upper += count * (D - u)
            active += count * u
    A = rd * lower + rn * upper
    if A >= rn * active:
        return a0
    # r/R events remove upper bins, r events add lower bins. Both event lists
    # are already ordered, including the constant gamma=0 and gamma=1 bins.
    i = j = 0
    while i < len(rows) and (rows[i][0] <= D - rows[i][0]):
        i += 1
    while j < len(rows) and R.numerator * rows[j][0] <= R.denominator * (D - rows[j][0]):
        j += 1
    current = a0
    while True:
        u_i = rows[i][0] if i < len(rows) else D
        u_j = rows[j][0] if j < len(rows) else D
        exit_upper = Fraction(u_i, D - u_i) / R if u_i < D else Fraction(2)
        enter_lower = Fraction(u_j, D - u_j) if u_j < D else Fraction(2)
        event = min(exit_upper, enter_lower, Fraction(1))
        if A:
            root = Fraction(rd * active, A)
            if current <= root <= event:
                return root
        elif active == 0:
            return current
        if event == 1:
            return Fraction(1)
        # Process all ties at once, maintaining the interval to the right.
        while i < len(rows) and rows[i][0] < D:
            u, count = rows[i]
            if Fraction(u, D - u) / R != event:
                break
            upper -= count * (D - u)
            active -= count * u
            i += 1
        while j < len(rows) and rows[j][0] < D:
            u, count = rows[j]
            if Fraction(u, D - u) != event:
                break
            lower += count * (D - u)
            active += count * u
            j += 1
        A = rd * lower + rn * upper
        current = event


def _histogram_certificate(
    rows: Sequence[tuple[int, int]], D: int, R: Fraction, a: Fraction, samples: int
) -> dict:
    """Independent direct score/sign check, without the sweep accumulators."""
    n, d, rn, rd = a.numerator, a.denominator, R.numerator, R.denominator
    score = 0
    for u, count in rows:
        clipped = max(n * rd * (D - u), min(u * d * rd, rn * n * (D - u)))
        score += 2 * count * (clipped - u * d * rd)
    sign_ok = score == 0 or (a == 1 / R and score > 0) or (a == 1 and score < 0)
    valid = (
        sum(count for _, count in rows) == samples
        and all(0 <= u <= D and count > 0 for u, count in rows)
        and all(x[0] < y[0] for x, y in pairwise(rows))
        and 1 / R <= a <= 1
        and sign_ok
    )
    if not valid:
        raise ArithmeticError("independent histogram root/sign validation failed")
    return {
        "valid": True,
        "counts_nonnegative": True,
        "counts_sum": samples,
        "representatives": len(rows),
        "threshold_in_range": True,
        "root_or_boundary_sign": True,
        "score_numerator": str(score),
        "score_denominator": str(samples * D * d * rd),
    }


def _raw_score_interval(
    observations: Sequence[tuple[int, int]], a: Fraction, R: Fraction, scale: int
) -> tuple[int, int]:
    """Floor every exact score times scale; no Fraction/GCD per summand.

    Return integer bounds in units 1/(M*scale). The width is at most 1/scale,
    including negative scores, because Python // rounds towards minus infinity.
    """
    n, d, rn, rd = a.numerator, a.denominator, R.numerator, R.denominator
    den = d * rd
    low = 0
    for U, V in observations:
        clipped = max(n * rd * V, min(U * den, rn * n * V))
        low += (2 * scale * (clipped - U * den)) // (den * (U + V))
    return low, low + len(observations)


def _bisect_raw(
    observations: Sequence[tuple[int, int]], config: Config
) -> tuple[Fraction, int, int]:
    R, delta = config.R, config.delta
    scale = _ceil(4 / delta)
    lo, hi = 1 / R, Fraction(1)
    for a, is_lower in ((lo, True), (hi, False)):
        low, high = _raw_score_interval(observations, a, R, scale)
        if (is_lower and low >= 0) or (not is_lower and high <= 0) or low <= 0 <= high:
            return a, scale, 0
    for iteration in range(1, config.J + 1):
        mid = (lo + hi) / 2
        low, high = _raw_score_interval(observations, mid, R, scale)
        if low <= 0 <= high:
            return mid, scale, iteration
        if low > 0:
            hi = mid
        else:
            lo = mid
        if 2 * R * (hi - lo) <= delta:
            return (lo + hi) / 2, scale, iteration
    raise ValueError("config.J is insufficient for the certified bisection width")


def _median_threshold(U: int, V: int, k: int, R: Fraction) -> Fraction:
    """Inverse CDF of clip(gamma,a(1-gamma),Ra(1-gamma)).

    k/2**64 is the frozen auxiliary uniform, including zero. Equality to gamma
    takes the left edge of the plateau; clipping thresholds to [1/R,1] handles
    the CDF's endpoint atoms. No logarithm of a rounded ratio is taken.
    """
    n, d = k * (U + V), _U64 * V
    if n <= _U64 * U:
        n *= R.denominator
        d *= R.numerator
    if n * R.numerator <= d * R.denominator:
        return 1 / R
    if n >= d:
        return Fraction(1)
    return Fraction(n, d)


def _observation(value: tuple[int, int]) -> tuple[int, int]:
    U, V = value
    if type(U) is not int or type(V) is not int or U < 0 or V <= 0:
        raise ValueError("observations require integer U>=0 and V>0")
    return U, V


def calibrate(
    method: str, observations: Iterable[tuple[int, int]], config: Config, aux_rng: Random
) -> CalibrationResult:
    """Consume exactly M (or M_median) complete observations, retaining no words.

    Collection includes iterator generation/evaluation and state updates. Solve
    includes sorting/compression and numerical minimization. Payload diagnostics
    and independent certificates run after both clocks; the outer first-output
    wall clock must include them. Quantized methods discard U,V immediately.
    """
    if method not in METHODS:
        raise ValueError(f"unknown calibration method: {method}")
    if (
        config.R <= 1
        or config.xi <= 0
        or config.bar_b <= 0
        or config.delta <= 0
        or config.M <= 0
        or config.M_median <= 0
        or config.M_median % 2 != 1
    ):
        raise ValueError("invalid calibration config")
    grid, R = config.grid, config.R
    if grid.kind == "dyadic" and (1 << grid.h) < R + 1:
        raise ValueError("dyadic tail is too wide for the score-error certificate")
    n = config.M_median if method == "median" else config.M
    started = perf_counter()
    source = iter(observations)
    raw: list[tuple[int, int]] = []
    thresholds: list[Fraction] = []
    indices = _unsigned_array(grid.H - 1)
    counts = _unsigned_array(n, [0] * grid.H) if method == "grid" else None
    summary = GKSummary(config.eps) if method == "gk" else None
    input_bits = 1
    for _ in range(n):
        U, V = _observation(next(source))
        input_bits = max(input_bits, U.bit_length(), V.bit_length())
        if method == "ratio_bisection":
            raw.append((U, V))
        elif method == "median":
            thresholds.append(_median_threshold(U, V, aux_rng.getrandbits(64), R))
        else:
            index = grid.quantize(U, V)
            if method == "grid":
                assert counts is not None
                counts[index] += 1
            elif method == "indices":
                indices.append(index)
            else:
                assert summary is not None
                summary.insert(index)
    del U, V
    collected = perf_counter()
    rows: list[tuple[int, int]] = []
    ordered: list[int] = []
    if method == "ratio_bisection":
        a, scale, iterations = _bisect_raw(raw, config)
        retained: object = raw
    elif method == "median":
        thresholds.sort()
        a = thresholds[n // 2]
        retained = thresholds
    else:
        if method == "grid":
            assert counts is not None
            rows = [(grid.numerator(i), count) for i, count in enumerate(counts) if count]
            retained = (counts, rows)
        elif method == "indices":
            # array has no sort; account for the standard sort's Python list
            # workspace as well as the compact retained collection array.
            ordered = sorted(indices)
            rows = [(grid.numerator(i), sum(1 for _ in group)) for i, group in groupby(ordered)]
            retained = (indices, ordered, rows)
        else:
            assert summary is not None
            summary.compress()
            # Equal representative values are merged only for the root solver.
            rows = [
                (grid.numerator(i), sum(row[1] for row in group))
                for i, group in groupby(summary.entries, key=lambda row: row[0])
            ]
            retained = (summary.entries, summary.n, summary.period, summary.eps, rows)
        a = _sweep(rows, grid.D, R)
    solved = perf_counter()

    # Diagnostics below are deliberately outside collection/solve clocks.
    bits, storage = _payload(retained)
    numeric_width = max(
        input_bits + grid.D.bit_length() + 1, n.bit_length() + grid.D.bit_length() + 2
    )
    certificate: dict = {
        "method": method,
        "arithmetic": "integer/Fraction",
        "diagnostics_outside_component_timers": True,
        "state_scope": "retained collection state and live solve workspace; not RSS",
        "work_bits_kind": "conservative arithmetic bound; excludes source and Python internals",
        "sample_budget_met": n
        >= (
            _median_budget(config.xi, config.bar_b)
            if method == "median"
            else _saa_budget(config.xi, config.bar_b)
        ),
        "statistical_assumptions": (
            "IID rho=(P+mu)/2; normalized P, full-support mu; ideal fresh noise"
        ),
        "executable_privacy_certified": False,
        "auxiliary_rng_bits": 0,
    }
    if method == "ratio_bisection":
        low, high = _raw_score_interval(raw, a, R, scale)
        denom = n * scale
        # For a constrained optimum only the score pointing into the interval
        # matters. This also covers a true flat minimum and endpoint roots.
        residual = max(
            Fraction(0),
            Fraction(-low, denom)
            if a == 1 / R
            else Fraction(high, denom)
            if a == 1
            else max(abs(Fraction(low, denom)), abs(Fraction(high, denom))),
        )
        if residual > config.delta:
            raise ArithmeticError("independent fixed-point residual check failed")
        error = config.bar_b * residual
        certificate.update(
            valid=True,
            threshold_in_range=1 / R <= a <= 1,
            score_interval=[str(Fraction(low, denom)), str(Fraction(high, denom))],
            score_error_bound=str(residual),
            fixed_point_scale=scale,
            bisection_iterations=iterations,
        )
        # Covers products, the per-score division and the signed sum, including
        # temporary rational cross-products used in bisection and diagnostics.
        numeric_width += (
            2 * (config.J + R.numerator.bit_length() + R.denominator.bit_length() + 4)
            + scale.bit_length()
        )
    elif method == "median":
        eta = config.xi / (config.bar_b + config.xi)
        error = None
        certificate.update(
            valid=1 / R <= a <= 1,
            threshold_in_range=1 / R <= a <= 1,
            eta=str(eta),
            corrected_eta=str(eta - Fraction(1, 1 << 63)),
            auxiliary_rng_bits=64 * n,
            uniform_cdf_error_bound=str(Fraction(1, _U64)),
            confidence_correction=str(Fraction(1, 1 << 63)),
            guarantee_kind="median CDF concentration, not an empirical ERM gap",
        )
        numeric_width = max(
            numeric_width,
            2 * (input_bits + 65 + R.numerator.bit_length() + R.denominator.bit_length() + 2),
        )
    else:
        certificate.update(_histogram_certificate(rows, grid.D, R, a, n))
        grid_error = 2 * (R + 1) / grid.D if grid.kind == "uniform" else Fraction(2, grid.m)
        summary_error = 8 * config.eps if method == "gk" else Fraction(0)
        if summary is not None:
            if not summary.validate():
                raise ArithmeticError("GK rank invariant failed; no CDF certificate")
            certificate.update(
                gk_rank_invariant=True,
                eps=str(config.eps),
                cdf_error_bound=str(2 * config.eps),
                cdf_bound_basis="GK rank invariant; original ranks are not retained",
            )
        error = config.bar_b * (grid_error + summary_error)
        certificate.update(
            grid_kind=grid.kind,
            grid_points=grid.H,
            grid_denominator=grid.D,
            quantization_score_error_bound=str(grid_error),
            summary_score_error_bound=str(summary_error),
        )
        # Sweep cross-products: root numerator/denominator are themselves sums
        # of M*D terms; independent checks multiply by another grid numerator.
        numeric_width = max(
            numeric_width,
            2
            * (
                n.bit_length()
                + grid.D.bit_length()
                + R.numerator.bit_length()
                + R.denominator.bit_length()
                + 4
            ),
        )
    if error is not None:
        certificate.update(
            empirical_loss_gap_upper=str(error),
            empirical_loss_gap_certified=error <= config.xi / 4,
            guarantee_kind="conditional Bernstein SAA with certified empirical error",
        )
    certificate["conditional_budget_certified"] = (
        certificate["valid"]
        and certificate["sample_budget_met"]
        and config.beta == Fraction(1, 20)
        and (
            (R == 2 and config.bar_b >= Fraction(7, 10))
            or (R == 16 and config.bar_b >= Fraction(14, 5))
        )
        and (error is None or error <= config.xi / 4)
    )
    return CalibrationResult(
        a, n, collected - started, solved - collected, bits, storage, numeric_width, certificate
    )


def exact_projection(p: Sequence[Fraction], mu: Sequence[Fraction], R: Fraction) -> Fraction:
    """Small-enumeration control: smallest root of sum clip(P,a mu,Ra mu)=1.

    Input laws must already be normalized; there is no silent renormalization.
    Weighted events cost O(N log N), independently of the sample calibrators.
    """
    R = Fraction(R)
    p, mu = tuple(map(Fraction, p)), tuple(map(Fraction, mu))
    if (
        R <= 1
        or not p
        or len(p) != len(mu)
        or any(x < 0 for x in p)
        or any(x <= 0 for x in mu)
        or sum(p) != 1
        or sum(mu) != 1
    ):
        raise ValueError("projection requires normalized P>=0, mu>0 and R>1")
    a0, slope, intercept = 1 / R, Fraction(0), Fraction(0)
    events: list[tuple[Fraction, Fraction, Fraction]] = []
    for pi, mi in zip(p, mu, strict=False):
        ratio = pi / mi
        if ratio <= a0:
            slope += mi
        elif ratio > 1:
            slope += R * mi
        else:
            intercept += pi
        if a0 < ratio <= 1:
            events.append((ratio, mi, -pi))
        if a0 < ratio / R <= 1:
            events.append((ratio / R, -R * mi, pi))
    events.sort(key=lambda row: row[0])
    current = a0
    for event, group in groupby(events, key=lambda row: row[0]):
        if slope * current + intercept == 1:
            return current
        if slope and current <= (root := (1 - intercept) / slope) <= event:
            return root
        for _, ds, di in group:
            slope += ds
            intercept += di
        current = event
    if slope * current + intercept == 1:
        return current
    if slope and current <= (root := (1 - intercept) / slope) <= 1:
        return root
    raise ArithmeticError("normalized projection has no root: implementation error")
