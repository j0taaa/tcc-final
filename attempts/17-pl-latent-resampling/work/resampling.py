"""Independent rational reference for the received PL-latent construction.

Uses the maintained immutable token forest, not any semantic attempt. No float
acceptance, approximate target, neural training, or production decoder change.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
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


def dyadic_round_upper(value, tolerance):
    """Enclose a nonnegative rational with error at most tolerance."""
    if value < 0 or tolerance <= 0:
        raise ValueError("nonnegative value and positive tolerance required")
    precision = max(0, (tolerance.denominator // tolerance.numerator).bit_length())
    scale = 1 << precision
    return Q(-(-value.numerator * scale // value.denominator), scale)


@dataclass
class WeightedForest:
    plan: object
    probabilities: tuple
    inside: tuple
    integers: tuple
    mass: Q
    decision_cache: dict = field(default_factory=dict)
    fast_forced: bool = False
    forced_decisions: dict = field(default_factory=dict)

    @classmethod
    def prepare(cls, plan, probabilities, end=None, fast_forced=False):
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
        return cls(
            plan,
            probabilities,
            tuple(inside),
            weights,
            Q(total, prod(scales)),
            fast_forced=fast_forced,
        )

    def sample(self, rng):
        if not self.mass:
            raise ValueError("zero evidence mass")
        output = [None] * len(self.probabilities)
        pending = [self.plan.root]
        while pending:
            node = pending.pop()
            terms = self.plan.terms[node]
            if node not in self.decision_cache:
                cumulative, total = [], 0
                for term in terms:
                    total += self.plan.term_mass(term, self.integers, self.inside)
                    cumulative.append(total)
                self.decision_cache[node] = tuple(cumulative)
                if self.fast_forced:
                    positive = [
                        i for i, c in enumerate(cumulative) if c > (cumulative[i - 1] if i else 0)
                    ]
                    if len(positive) == 1:
                        self.forced_decisions[node] = positive[0]
            cumulative = self.decision_cache[node]
            index = self.forced_decisions.get(node)
            term = terms[
                index
                if index is not None
                else bisect_right(cumulative, rng.randrange(cumulative[-1]))
            ]
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

    def tightened(self, end=None):
        """Classical min/max sum passes; optimal constant rejection envelope."""
        p = Problem(self.plan, self.probabilities, self.rates, self.order, self.observed)
        bounds = [None] * len(self.plan.terms)
        for node in self.plan.order:
            deadline(end)
            alternatives = []
            for term in self.plan.terms[node]:
                if term.choice is not None:
                    i, index = term.choice
                    if i in self.observed and self.rows[i][index] != self.observed[i]:
                        continue
                    value = self.rates[i][index] if i in self.hidden else Q()
                    alternatives.append((value, value))
                elif not term.children:
                    alternatives.append((Q(), Q()))
                elif all(bounds[c] is not None for c in term.children):
                    alternatives.append(
                        tuple(sum((bounds[c][j] for c in term.children), Q()) for j in (0, 1))
                    )
            if alternatives:
                bounds[node] = (min(b[0] for b in alternatives), max(b[1] for b in alternatives))
        if self.plan.root is None or bounds[self.plan.root] is None:
            raise ValueError("zero structural evidence mass")
        p.L, p.H = bounds[self.plan.root]
        return p


class TangentMixture:
    def __init__(
        self,
        problem,
        end=None,
        max_components=256,
        dyadic_unaries=False,
        tight_bounds=False,
        dyadic_coefficients=False,
        certify_scale=False,
        fast_forced=False,
    ):
        if tight_bounds:
            problem = problem.tightened(end)
        self.fast_forced = fast_forced
        self.problem = p = problem
        self.components = []
        self.rejection_factor = Q(2)
        self.certificate_points = 0
        self.component_cdf = None
        self.integer_envelope = None
        if not p.order or not p.hidden or p.L == p.H:
            base = WeightedForest.prepare(p.plan, p.evidence_weights, end, fast_forced=fast_forced)
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
            alpha_error = delta_a / 2 if dyadic_coefficients else delta_a
            _, upper = exp_bounds(t * s, alpha_error / p.f(s), end)
            alpha = p.f(s) * upper
            if dyadic_coefficients:
                alpha = dyadic_round_upper(alpha, delta_a / 2)
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
            component = WeightedForest.prepare(p.plan, modified, end, fast_forced=fast_forced)
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

        if certify_scale:
            from envelope_control import scale_certificate

            self.rejection_factor, self.certificate_points = scale_certificate(p, grid, end)

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
        acceptance = self.problem.likelihood(path) / (self.rejection_factor * self.envelope(path))
        if not 0 < acceptance <= 1:
            raise AssertionError("invalid certified rejection envelope")
        return acceptance

    @property
    def rejection_normalizer(self):
        return (
            self.problem.f(self.problem.L) * self.mass
            if self.constant
            else self.rejection_factor * self.mass
        )

    def sample(self, rng, end=None):
        count = 0
        while True:
            deadline(end)
            count += 1
            index = (
                0
                if self.fast_forced and len(self.components) == 1
                else categorical([a * c.mass for a, _, c in self.components], rng)
                if self.component_cdf is None
                else bisect_right(self.component_cdf, rng.randrange(self.component_cdf[-1]))
            )
            path = self.components[index][2].sample(rng)
            probability = self.acceptance(path)
            if (self.fast_forced and probability == 1) or rng.randrange(
                probability.denominator
            ) < probability.numerator:
                return path, count


class BaseRejection:
    """Competent rejection: grammar/evidence conditioned, envelope f(L), not 1."""

    def __init__(self, problem, end=None, tight_bounds=False, fast_forced=False):
        if tight_bounds:
            problem = problem.tightened(end)
        self.problem = problem
        self.fast_forced = fast_forced
        self.base = WeightedForest.prepare(
            problem.plan, problem.evidence_weights, end, fast_forced=fast_forced
        )
        if not self.base.mass:
            raise ValueError("zero evidence mass")
        self.upper = problem.f(problem.L)

    @property
    def rejection_normalizer(self):
        return self.upper * self.base.mass

    def acceptance(self, path):
        return self.problem.likelihood(path) / self.upper

    def sample(self, rng, end=None):
        count = 0
        while True:
            deadline(end)
            count += 1
            path = self.base.sample(rng)
            probability = self.acceptance(path)
            if not 0 < probability <= 1:
                raise AssertionError("base envelope violated")
            if (self.fast_forced and probability == 1) or rng.randrange(
                probability.denominator
            ) < probability.numerator:
                return path, count


class SingleTilt(BaseRejection):
    """Classical single exponential proposal with a global endpoint majorant."""

    def __init__(
        self,
        problem,
        end=None,
        dyadic_coefficients=False,
        precise_envelope=False,
        fast_forced=False,
    ):
        self.fast_forced = fast_forced
        p = self.problem = problem.tightened(end)
        self.integer_envelope = None
        if not p.order or p.L == p.H:
            super().__init__(p, end, fast_forced=fast_forced)
            self.unaries = None
            return
        ratio = p.f(p.L) / p.f(p.H)
        log_cap = (ratio.numerator // ratio.denominator).bit_length()
        with localcontext() as context:
            context.prec = 80
            logarithm = Q((Decimal(ratio.numerator) / Decimal(ratio.denominator)).ln())
        t = min(
            len(p.order) / (p.L + p.c[-1]),
            Q(log_cap) / (p.H - p.L),
            logarithm / (p.H - p.L),
        )
        delta = p.f(p.H) / (1024 if precise_envelope else 4)
        alpha_error = delta / 2 if dyadic_coefficients else delta
        self.upper = max(
            p.f(s) * exp_bounds(t * s, alpha_error / p.f(s), end)[1] for s in (p.L, p.H)
        )
        if dyadic_coefficients:
            self.upper = dyadic_round_upper(self.upper, delta / 2)
        error = delta / (self.upper * len(p.hidden))
        self.unaries = tuple(
            tuple(
                dyadic_negative_exp_upper(t * rate, error, end) if i in p.hidden else Q(1)
                for rate in row
            )
            for i, row in enumerate(p.rates)
        )
        modified = tuple(
            tuple(q * u for q, u in zip(row, tilt, strict=True))
            for row, tilt in zip(p.evidence_weights, self.unaries, strict=True)
        )
        self.base = WeightedForest.prepare(p.plan, modified, end, fast_forced=fast_forced)
        if not self.base.mass:
            raise ValueError("zero evidence mass")
        if dyadic_coefficients:
            scales = {i: max(u.denominator for u in self.unaries[i]) for i in p.hidden}
            ticks = {
                i: tuple(u.numerator * (scales[i] // u.denominator) for u in self.unaries[i])
                for i in p.hidden
            }
            self.integer_envelope = (
                self.upper.numerator,
                ticks,
                self.upper.denominator * prod(scales.values()),
            )

    def acceptance(self, path):
        p = self.problem
        if self.integer_envelope is not None:
            coefficient, ticks, scale = self.integer_envelope
            envelope = Q(
                coefficient * prod(ticks[i][p.indices[i][path[i]]] for i in p.hidden), scale
            )
            return p.likelihood(path) / envelope
        envelope = self.upper
        if self.unaries is not None:
            envelope *= prod(self.unaries[i][p.indices[i][path[i]]] for i in p.hidden)
        return p.likelihood(path) / envelope


def select_order(free, rates, path, indices, k, rng):
    remaining, result = list(free), []
    for _ in range(k):
        weights = [rates[i][indices[i][path[i]]] for i in remaining]
        result.append(remaining.pop(categorical(weights, rng)))
    return tuple(result)


class RoundedProfiles:
    """Alternative in section 8, epsilon=1; fixed-tree rounding, not a semiring."""

    def __init__(
        self,
        problem,
        end=None,
        dyadic_root=False,
        max_cells=1000000,
        max_transitions=3000000,
        fast_forced=False,
    ):
        self.fast_forced = fast_forced
        self.problem = p = problem.tightened(end)
        self.end = end
        self.base = WeightedForest.prepare(p.plan, p.evidence_weights, end, fast_forced=fast_forced)
        if not self.base.mass:
            raise ValueError("zero evidence mass")
        k, m = len(p.order), len(p.hidden)
        self.constant = not k or not m or p.L == p.H
        self.profile_cells = self.profile_transitions = 0
        self.profile_cache = {}
        self.backpointers = {}
        if self.constant:
            return
        self.gamma = 1 + Q(1, 2 * k * m)
        self.grid = [min(min(p.rates[i]) for i in p.hidden)]
        self.profiles = [{} for _ in p.plan.terms]
        self.minima = [{} for _ in p.plan.terms]
        for node in p.plan.order:
            deadline(end)
            profile = self.profiles[node]
            for term in p.plan.terms[node]:
                if term.choice is not None:
                    i, index = term.choice
                    actual = p.rates[i][index] if i in p.hidden else Q()
                    variants = [
                        (
                            self.round(actual),
                            (),
                            self.base.integers[i][index],
                            actual,
                        )
                    ]
                elif not term.children:
                    variants = [(Q(), (), 1, Q())]
                else:
                    left, right = term.children
                    variants = (
                        (
                            self.round(a + b),
                            (a, b),
                            va * vb,
                            self.minima[left][a] + self.minima[right][b],
                        )
                        for a, va in self.profiles[left].items()
                        for b, vb in self.profiles[right].items()
                    )
                for value, children, mass, actual in variants:
                    deadline(end)
                    if not mass:
                        continue
                    self.profile_transitions += 1
                    if self.profile_transitions > max_transitions:
                        raise TimeoutError("profile transition budget; unresolved")
                    if value not in profile:
                        self.profile_cells += 1
                        if self.profile_cells > max_cells:
                            raise TimeoutError("profile cell budget; unresolved")
                    profile[value] = profile.get(value, 0) + mass
                    self.minima[node][value] = min(self.minima[node].get(value, actual), actual)
                    self.backpointers.setdefault((node, value), []).append((term, children, mass))
        self.root_profiles = tuple(self.profiles[p.plan.root])
        error = p.f(max(self.minima[p.plan.root].values())) / 1024
        self.root_upper = {
            value: dyadic_round_upper(p.f(self.minima[p.plan.root][value]), error)
            if dyadic_root
            else p.f(self.minima[p.plan.root][value])
            for value in self.root_profiles
        }
        weights = [self.profiles[p.plan.root][v] * self.root_upper[v] for v in self.root_profiles]
        scale = lcm(*(w.denominator for w in weights))
        total, self.root_cdf = 0, []
        for weight in weights:
            total += weight.numerator * (scale // weight.denominator)
            self.root_cdf.append(total)
        self.root_mass = sum(weights, Q())

    def round(self, value):
        if not value:
            return Q()
        while self.grid[-1] < value:
            deadline(self.end)
            self.grid.append(self.grid[-1] * self.gamma)
        return self.grid[bisect_left(self.grid, value)]

    @property
    def rejection_normalizer(self):
        if self.constant:
            return self.problem.f(self.problem.L) * self.base.mass
        return self.root_mass * self.base.mass / self.base.inside[self.problem.plan.root]

    def proposal(self, rng):
        if self.constant:
            return self.base.sample(rng), None
        p = self.problem
        value = self.root_profiles[
            0
            if self.fast_forced and len(self.root_profiles) == 1
            else bisect_right(self.root_cdf, rng.randrange(self.root_cdf[-1]))
        ]
        output, pending = [None] * len(p.rows), [(p.plan.root, value)]
        while pending:
            node, profile = pending.pop()
            key = (node, profile)
            alternatives = self.backpointers[key]
            if key not in self.profile_cache:
                total, cumulative = 0, []
                for _, _, mass in alternatives:
                    total += mass
                    cumulative.append(total)
                self.profile_cache[key] = tuple(cumulative)
            cdf = self.profile_cache[key]
            index = (
                0
                if self.fast_forced and len(alternatives) == 1
                else bisect_right(cdf, rng.randrange(cdf[-1]))
            )
            term, children, _ = alternatives[index]
            if term.choice is not None:
                i, index = term.choice
                if output[i] is not None:
                    raise AssertionError("nondecomposable profile choices")
                output[i] = p.rows[i][index]
            pending.extend(zip(term.children, children, strict=True))
        if any(t is None for t in output):
            raise AssertionError("missing profile token slot")
        return tuple(output), value

    def acceptance(self, path, profile):
        return Q(1) if self.constant else self.problem.likelihood(path) / self.root_upper[profile]

    def sample(self, rng, end=None):
        count = 0
        while True:
            deadline(end)
            path, value = self.proposal(rng)
            count += 1
            probability = self.acceptance(path, value)
            if not 0 < probability <= 1:
                raise AssertionError("rounded profile envelope violated")
            if (self.fast_forced and probability == 1) or rng.randrange(
                probability.denominator
            ) < probability.numerator:
                return path, count

    def law(self):
        """Exact integration of the root/profile/backpointer categorical law."""
        p, laws = self.problem, {}
        if self.constant:
            from audit import forest_law

            return forest_law(self.base)
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
        z = sum((v * self.root_upper[s] for (s, _), v in root.items()), Q())
        accepted, success = {}, Q()
        for (s, pairs), weight in root.items():
            path = tuple(token for _, token in pairs)
            actual = p.total_rate(path)
            assert actual <= s <= self.gamma ** len(p.hidden) * actual
            assert p.f(s) <= p.f(actual) <= 2 * p.f(s)
            probability = weight * self.root_upper[s] / z
            acceptance = self.acceptance(path, s)
            accepted[path] = accepted.get(path, Q()) + probability * acceptance
            success += probability * acceptance
        assert 1 / success <= 2 * (1 + Q(1, 1024))
        return {path: mass / success for path, mass in accepted.items()}


def decision_cache_statistics(sampler):
    """Logical token-forest CDF footprint, not process peak RSS."""
    forests = (
        [sampler.base]
        if hasattr(sampler, "base")
        else [component for _, _, component in getattr(sampler, "components", ())]
    )
    cdfs = [cdf for forest in forests for cdf in forest.decision_cache.values()]
    cdfs.extend(getattr(sampler, "profile_cache", {}).values())
    return {
        "forced_forest_nodes": sum(len(f.forced_decisions) for f in forests),
        "profile_cells": getattr(sampler, "profile_cells", 0),
        "profile_transitions": getattr(sampler, "profile_transitions", 0),
        "cdf_nodes": len(cdfs),
        "cdf_entries": sum(map(len, cdfs)),
        "cdf_integer_bits": sum(value.bit_length() for cdf in cdfs for value in cdf),
    }
