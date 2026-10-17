"""Classical retrospective control with exact residual bounds and partial caches."""

from dataclasses import dataclass
from math import isqrt

from runtime_v4 import Draw, Factory, LazyUniform, Proposal, Stats, jets, mpq, rational


@dataclass
class LazyStats(Stats):
    refined_points: int = 0
    bound_cache_hits: int = 0


class Bounds:
    def __init__(self, m, k, h, stats):
        self.m, self.k, self.h = m, k, h
        self.x, self.root = mpq(k, 4 * m), isqrt(m)
        self.proposal = Proposal(m, k, h, stats)
        self.remaining = self.proposal.mass
        self.total = mpq(0)
        self.term = self.jet = None
        self.frontiers = None
        self.visited = []

    def interval(self):
        term = self.term if self.term is not None else mpq(0)
        radius = self.remaining
        if self.term is None:
            radius += self.proposal.term_bound
        center = mpq(1, 2) + (term + self.total) / self.proposal.weight
        return center - radius / self.proposal.weight, center + radius / self.proposal.weight

    def compute_term(self, value):
        self.jet = jets(value, self.m, self.x)
        new = jets(value, 4 * self.m, self.x)[2]
        self.term = self.x * (1 - self.x) * (self.jet[2] - new) / (2 * (4 * self.m - 1))

    def prepare_frontiers(self, stats):
        p = self.proposal
        p.stats = stats
        left, right = p.left, p.right
        while left < right:
            mid = (left + right) // 2
            if p.ratio(mid) >= 1:
                left = mid + 1
            else:
                right = mid
        mode = left
        self.frontiers = [(mode, p.point_weight(mode))]

    def refine(self, value, stats):
        if self.term is None:
            self.compute_term(value)
            return "term"
        if self.frontiers is None:
            self.prepare_frontiers(stats)
        p = self.proposal
        p.stats = stats
        selected = max(range(len(self.frontiers)), key=lambda j: self.frontiers[j][1])
        i, weight = self.frontiers.pop(selected)
        if not self.visited:
            if i > p.left:
                self.frontiers.append((i - 1, weight / p.ratio(i - 1)))
            if i < p.right:
                self.frontiers.append((i + 1, weight * p.ratio(i)))
        elif i < self.visited[0]:
            if i > p.left:
                self.frontiers.append((i - 1, weight / p.ratio(i - 1)))
        elif i > self.visited[0]:
            if i < p.right:
                self.frontiers.append((i + 1, weight * p.ratio(i)))
        f0, slope, second = self.jet
        y, z = mpq(i, self.m), mpq(i, self.m) - self.x
        fy, _, second_y = jets(value, self.m, y)
        remainder = fy - f0 - slope * z - second * z * z / 2
        residual = -remainder + y * (1 - y) * (second_y - second) / (2 * (self.m - 1))
        envelope = self.h * p.point_polynomial(i) / (self.m * self.root)
        if abs(residual) > envelope:
            raise ValueError("Supplied smoothness bound violated")
        probability = weight / p.point_polynomial(i)
        self.total += probability * residual
        self.remaining -= probability * envelope
        if self.remaining < 0:
            raise ArithmeticError("Negative remaining exact envelope mass")
        self.visited.append(i)
        stats.refined_points += 1
        if not self.frontiers:
            assert self.remaining == 0
        return i


class RetrospectiveFactory(Factory):
    label = "retrospective"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bounds = {}

    def vote(self, n, k, rng, method="dense"):
        if (
            method not in ("dense", "sparse")
            or not isinstance(n, int)
            or n < self.n0
            or not isinstance(k, int)
            or not 0 <= k <= n
        ):
            raise ValueError("Invalid retrospective method/index")
        level, degree = 0, n
        while degree > self.n0 and degree % 4 == 0:
            degree //= 4
            level += 1
        if degree != self.n0 or (not self.h and level):
            raise ValueError("Degree outside factory support")
        if not self.reuse:
            self.bounds = {}
        if not level or k in (0, n):
            return super().vote(n, k, rng, "dense")
        if not self.reuse:
            self.values, self.scalars, self.coefficients, self.proposals = {}, {}, {}, {}
        stats, initial = LazyStats(component="retrospective"), rng.used

        def value(x):
            stats.f_requests += 1
            if x in self.values:
                stats.value_cache_hits += 1
                return self.values[x]
            if not 0 <= x <= 1:
                raise ValueError("Query outside[0,1]")
            result = rational(self.function(x))
            self.values[x] = result
            stats.f_evaluations += 1
            return result

        key = n, k
        if key not in self.bounds:
            self.bounds[key] = Bounds(n // 4, k, self.h, stats)
        else:
            stats.bound_cache_hits += 1
        state, uniform = self.bounds[key], LazyUniform(rng)
        while True:
            lower, upper = state.interval()
            if uniform.less(lower):
                bit = 1
                break
            if not uniform.less(upper):
                bit = 0
                break
            state.refine(value, stats)
        stats.auxiliary_bits = rng.used - initial
        stats.value_cache_entries = len(self.values)
        stats.proposal_cache_entries = len(self.bounds)
        return Draw(bit, n, k, level, stats)
