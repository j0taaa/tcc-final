"""Independent rational reference for the received PL-latent construction.

Uses the maintained immutable token forest, not any semantic attempt. No float
acceptance, approximate target, neural training, or production decoder change.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from fractions import Fraction as Q
from math import isqrt, lcm, prod
from time import monotonic


def deadline(end):
    if end is not None and monotonic() > end:
        raise TimeoutError("resource refusal; no infeasibility or conditional-output-law claim")


def categorical(weights, rng):
    scale = lcm(*(x.denominator for x in weights))
    integers = [x.numerator * (scale // x.denominator) for x in weights]
    if not integers or min(integers) < 0 or sum(integers) <= 0:
        raise ValueError("categorical requires nonnegative weights and positive mass")
    draw = rng.randrange(sum(integers))
    for i, value in enumerate(integers):
        if draw < value:
            return i
        draw -= value
    raise AssertionError("categorical range invariant")


def exp_bounds(x, tolerance, end=None):
    """Certified rational enclosure of exp(x), x >= 0, using integer intervals.

    Every recurrence is rounded outward. After degree N, x/(N+2) <= 1/2
    bounds the remaining positive series by twice its first omitted term.
    """
    if x < 0 or tolerance <= 0:
        raise ValueError("positive exponential argument/tolerance required")
    if not x:
        return Q(1), Q(1)
    ceil_x = -(-x.numerator // x.denominator)
    precision = max(1, (tolerance.denominator // tolerance.numerator).bit_length())
    precision += 2 * ceil_x + 16
    while True:
        scale = 1 << precision
        lo = hi = sum_lo = sum_hi = scale
        for n in range(1, precision + 4 * ceil_x + 128):
            deadline(end)
            divisor = x.denominator * n
            lo = lo * x.numerator // divisor
            hi = -(-hi * x.numerator // divisor)
            sum_lo += lo
            sum_hi += hi
            divisor = x.denominator * (n + 1)
            next_hi = -(-hi * x.numerator // divisor)
            if n + 2 >= 2 * x:
                lower, upper = Q(sum_lo, scale), Q(sum_hi + 2 * next_hi, scale)
                if upper - lower <= tolerance:
                    return lower, upper
        precision *= 2


def negative_exp_upper(x, tolerance, end=None):
    p = max(0, (tolerance.denominator // tolerance.numerator).bit_length())
    if x >= p and Q(1, 1 << p) <= tolerance:
        return min(Q(1), tolerance)
    lower, _ = exp_bounds(x, tolerance, end)
    return min(Q(1), 1 / lower)


def dyadic_negative_exp_upper(x, tolerance, end=None):
    """Same certified error; a common dyadic denominator avoids coprime LCMs."""
    upper = negative_exp_upper(x, tolerance / 2, end)
    precision = max(0, (tolerance.denominator // tolerance.numerator).bit_length() + 1)
    scale = 1 << precision
    return min(Q(1), Q(-(-upper.numerator * scale // upper.denominator), scale))


@dataclass
class WeightedForest:
    plan: object
    probabilities: tuple
    inside: tuple
    integers: tuple
    mass: Q

    @classmethod
    def prepare(cls, plan, probabilities, end=None):
        scales = tuple(lcm(*(p.denominator for p in row)) for row in probabilities)
        weights = tuple(
            tuple(p.numerator * (scale // p.denominator) for p in row)
            for row, scale in zip(probabilities, scales, strict=True)
        )
        inside = [0] * len(plan.terms)
        for node in plan.order:
            deadline(end)
            inside[node] = sum(plan.term_mass(t, weights, inside) for t in plan.terms[node])
        total = inside[plan.root] if plan.root is not None else 0
        return cls(plan, probabilities, tuple(inside), weights, Q(total, prod(scales)))

    def sample(self, rng):
        if not self.mass:
            raise ValueError("zero evidence mass")
        output = [None] * len(self.probabilities)
        pending = [self.plan.root]
        while pending:
            node = pending.pop()
            terms = self.plan.terms[node]
            values = [self.plan.term_mass(t, self.integers, self.inside) for t in terms]
            term = terms[categorical([Q(v) for v in values], rng)]
            if term.choice is not None:
                position, index = term.choice
                if output[position] is not None:
                    raise AssertionError("nondecomposable token choices")
                output[position] = self.plan.state.support.rows[position][index]
            pending.extend(term.children)
        if any(x is None for x in output):
            raise AssertionError("missing original token slot")
        return tuple(output)


@dataclass
class Problem:
    plan: object
    probabilities: tuple
    rates: tuple
    order: tuple
    observed: dict

    def __post_init__(self):
        self.rows = self.plan.state.support.rows
        self.indices = [dict((t, j) for j, t in enumerate(row)) for row in self.rows]
        self.free = tuple(i for i, t in enumerate(self.plan.state.canvas) if t is None)
        if len(set(self.order)) != len(self.order) or any(i not in self.free for i in self.order):
            raise ValueError("PL order must contain distinct initially free positions")
        if set(self.observed) != set(self.order):
            raise ValueError("evidence must specify exactly the selected original tokens")
        if len(self.rates) != len(self.rows) or len(self.probabilities) != len(self.rows):
            raise ValueError("unaligned rows")
        for row, p, rate in zip(self.rows, self.probabilities, self.rates, strict=True):
            if len(row) != len(p) or len(row) != len(rate) or any(x <= 0 for x in (*p, *rate)):
                raise ValueError("positive aligned rational weights/rates required")
        if any(t not in self.indices[i] for i, t in self.observed.items()):
            raise ValueError("evidence token outside original support")
        self.hidden = tuple(i for i in self.free if i not in self.observed)
        selected_rates = [self.rates[i][self.indices[i][self.observed[i]]] for i in self.order]
        self.c = tuple(sum(selected_rates[j:], Q()) for j in range(len(selected_rates)))
        self.b = tuple(selected_rates)
        self.evidence_weights = tuple(
            tuple(
                p if i not in self.observed or t == self.observed[i] else Q()
                for t, p in zip(row, probabilities, strict=True)
            )
            for i, (row, probabilities) in enumerate(
                zip(self.rows, self.probabilities, strict=True)
            )
        )
        self.L = sum((min(self.rates[i]) for i in self.hidden), Q())
        self.H = sum((max(self.rates[i]) for i in self.hidden), Q())

    def f(self, s):
        return prod((b / (s + c) for b, c in zip(self.b, self.c, strict=True)), start=Q(1))

    def total_rate(self, path):
        return sum((self.rates[i][self.indices[i][path[i]]] for i in self.hidden), Q())

    def likelihood(self, path):
        return self.f(self.total_rate(path))

    def weight(self, path):
        return prod(
            (self.probabilities[i][self.indices[i][t]] for i, t in enumerate(path)), start=Q(1)
        )


class TangentMixture:
    def __init__(self, problem, end=None, max_components=256, dyadic_unaries=False):
        self.problem = p = problem
        self.components = []
        self.component_cdf = None
        self.integer_envelope = None
        if not p.order or not p.hidden or p.L == p.H:
            base = WeightedForest.prepare(p.plan, p.evidence_weights, end)
            if not base.mass:
                raise ValueError("zero evidence mass")
            self.components = [(Q(1), None, base)]
            self.mass = base.mass
            self.constant = True
            return
        self.constant = False
        k, m = len(p.order), len(p.hidden)
        d = isqrt(k) + (isqrt(k) ** 2 < k)
        grid, s = [], p.L
        while s <= p.H:
            grid.append(s)
            if len(grid) > max_components:
                raise TimeoutError("component cap; unresolved, not zero target mass")
            s = (s + p.c[-1]) * Q(d + 1, d) - p.c[-1]
        j_count = len(grid)
        f_min = p.f(p.H)
        delta_a = f_min / (4 * j_count)
        delta_u = f_min / (4 * j_count * 3**k * m)
        upper_unary = dyadic_negative_exp_upper if dyadic_unaries else negative_exp_upper
        for s in grid:
            deadline(end)
            t = sum((1 / (s + c) for c in p.c), Q())
            _, upper = exp_bounds(t * s, delta_a / p.f(s), end)
            alpha = p.f(s) * upper
            unary = tuple(
                tuple(
                    upper_unary(t * rate, delta_u, end) if i in p.hidden else Q(1) for rate in row
                )
                for i, row in enumerate(p.rates)
            )
            modified = tuple(
                tuple(q * u for q, u in zip(row, tilt, strict=True))
                for row, tilt in zip(p.evidence_weights, unary, strict=True)
            )
            component = WeightedForest.prepare(p.plan, modified, end)
            self.components.append((alpha, unary, component))
        self.mass = sum((a * component.mass for a, _, component in self.components), Q())
        if not self.mass:
            raise ValueError("zero evidence mass")
        if dyadic_unaries:
            masses = [a * c.mass for a, _, c in self.components]
            scale = lcm(*(value.denominator for value in masses))
            total, self.component_cdf = 0, []
            for value in masses:
                deadline(end)
                total += value.numerator * (scale // value.denominator)
                self.component_cdf.append(total)
            coefficient_scale = lcm(*(a.denominator for a, _, _ in self.components))
            unary_scale = 1 << max(0, (delta_u.denominator // delta_u.numerator).bit_length() + 1)
            coefficients, ticks = [], []
            for a, unaries, _ in self.components:
                deadline(end)
                coefficients.append(a.numerator * (coefficient_scale // a.denominator))
                ticks.append(
                    {
                        i: tuple(u.numerator * (unary_scale // u.denominator) for u in unaries[i])
                        for i in p.hidden
                    }
                )
            self.integer_envelope = (coefficients, ticks, coefficient_scale * unary_scale**m)

    def envelope(self, path):
        p = self.problem
        if self.integer_envelope is not None:
            coefficients, ticks, scale = self.integer_envelope
            value = sum(
                a * prod(row[i][p.indices[i][path[i]]] for i in p.hidden)
                for a, row in zip(coefficients, ticks, strict=True)
            )
            return Q(value, scale)
        return sum(
            (
                alpha * prod((unary[i][p.indices[i][path[i]]] for i in p.hidden), start=Q(1))
                for alpha, unary, _ in self.components
            ),
            Q(),
        )

    def acceptance(self, path):
        if self.constant:
            return Q(1)
        acceptance = self.problem.likelihood(path) / (2 * self.envelope(path))
        if not 0 < acceptance <= 1:
            raise AssertionError("invalid certified rejection envelope")
        return acceptance

    def sample(self, rng, end=None):
        count = 0
        while True:
            deadline(end)
            count += 1
            index = (
                categorical([a * c.mass for a, _, c in self.components], rng)
                if self.component_cdf is None
                else bisect_right(self.component_cdf, rng.randrange(self.component_cdf[-1]))
            )
            path = self.components[index][2].sample(rng)
            probability = self.acceptance(path)
            if rng.randrange(probability.denominator) < probability.numerator:
                return path, count


class BaseRejection:
    """Competent rejection: grammar/evidence conditioned, envelope f(L), not 1."""

    def __init__(self, problem, end=None):
        self.problem = problem
        self.base = WeightedForest.prepare(problem.plan, problem.evidence_weights, end)
        if not self.base.mass:
            raise ValueError("zero evidence mass")
        self.upper = problem.f(problem.L)

    def sample(self, rng, end=None):
        count = 0
        while True:
            deadline(end)
            count += 1
            path = self.base.sample(rng)
            probability = self.problem.likelihood(path) / self.upper
            if not 0 < probability <= 1:
                raise AssertionError("base envelope violated")
            if rng.randrange(probability.denominator) < probability.numerator:
                return path, count


def select_order(free, rates, path, indices, k, rng):
    remaining, result = list(free), []
    for _ in range(k):
        weights = [rates[i][indices[i][path[i]]] for i in remaining]
        result.append(remaining.pop(categorical(weights, rng)))
    return tuple(result)


class RoundedProfiles:
    """Alternative in section 8, epsilon=1; fixed-tree rounding, not a semiring."""

    def __init__(self, problem):
        self.problem = p = problem
        k, m = len(p.order), len(p.hidden)
        if not k or not m:
            raise ValueError("profile oracle requires selected and hidden positions")
        self.gamma = 1 + Q(1, 2 * k * m)
        self.grid = [min(min(p.rates[i]) for i in p.hidden)]
        self.base = WeightedForest.prepare(p.plan, p.evidence_weights)
        self.profiles = [{} for _ in p.plan.terms]
        for node in p.plan.order:
            profile = self.profiles[node]
            for term in p.plan.terms[node]:
                if term.choice is not None:
                    i, index = term.choice
                    value = self.round(p.rates[i][index]) if i in p.hidden else Q()
                    profile[value] = profile.get(value, 0) + self.base.integers[i][index]
                elif not term.children:
                    profile[Q()] = profile.get(Q(), 0) + 1
                else:
                    left, right = term.children
                    for a, va in self.profiles[left].items():
                        for b, vb in self.profiles[right].items():
                            value = self.round(a + b)
                            profile[value] = profile.get(value, 0) + va * vb
            self.profiles[node] = {s: v for s, v in profile.items() if v}

    def round(self, value):
        if not value:
            return Q()
        while self.grid[-1] < value:
            self.grid.append(self.grid[-1] * self.gamma)
        return self.grid[bisect_left(self.grid, value)]

    def law(self):
        """Exact integration of the root/profile/backpointer categorical law."""
        p, laws = self.problem, {}
        for node in p.plan.order:
            result = {}
            for term in p.plan.terms[node]:
                if term.choice is not None:
                    i, index = term.choice
                    value = self.round(p.rates[i][index]) if i in p.hidden else Q()
                    pairs = ((i, p.rows[i][index]),)
                    key = (value, pairs)
                    result[key] = result.get(key, 0) + self.base.integers[i][index]
                elif not term.children:
                    result[(Q(), ())] = result.get((Q(), ()), 0) + 1
                else:
                    left, right = term.children
                    for (a, pairs_a), va in laws[left].items():
                        for (b, pairs_b), vb in laws[right].items():
                            key = (self.round(a + b), tuple(sorted(pairs_a + pairs_b)))
                            result[key] = result.get(key, 0) + va * vb
            laws[node] = {key: mass for key, mass in result.items() if mass}
        root = laws[p.plan.root]
        z = sum((v * p.f(s) for (s, _), v in root.items()), Q())
        accepted, success = {}, Q()
        for (s, pairs), weight in root.items():
            path = tuple(token for _, token in pairs)
            actual = p.total_rate(path)
            assert actual <= s <= self.gamma ** len(p.hidden) * actual
            assert p.f(s) <= p.f(actual) <= 2 * p.f(s)
            probability = weight * p.f(s) / z
            acceptance = p.f(actual) / (2 * p.f(s))
            accepted[path] = accepted.get(path, Q()) + probability * acceptance
            success += probability * acceptance
        assert 1 / success <= 2
        return {path: mass / success for path, mass in accepted.items()}
