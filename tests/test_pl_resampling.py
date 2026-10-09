"""Focused exact oracles for the independently preserved PL research attempt."""

import importlib.util
import itertools
import math
import sys
import unittest
from fractions import Fraction as Q
from pathlib import Path

WORK = Path(__file__).resolve().parents[1] / "attempts/17-pl-latent-resampling/work"
sys.path.insert(0, str(WORK))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, WORK / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reference = load("resampling", "resampling.py")
audit = load("pl_resampling_audit", "audit.py")
controls = load("pl_controls", "controls.py")
stationary = load("pl_stationary_control", "stationary_control.py")


class PlLatentOracleTests(unittest.TestCase):
    def test_product_proposal_separation_normalizer(self):
        # Independently integrate the proof family, including nonidentical
        # product proposals. This checks finite algebra, not asymptotic novelty.
        for m in range(1, 4):
            plan, data = audit.fixture(2 * m)
            q = tuple((Q(1, 10), Q(9, 10)) if len(row) == 2 else row for row in data.probabilities)
            data = audit.ProbabilityInput(data.state, q)
            order = tuple(i for i, t in enumerate(data.state.canvas) if t is None)[:m]
            p = reference.Problem(plan, q, q, order, dict.fromkeys(order, 4))
            paths = {
                y: w
                for y, w in audit.enumerated_paths(data).items()
                if all(y[i] == 4 for i in order)
            }
            target = {
                y: w * audit.direct_pl(y, order, p.free, q, p.indices) for y, w in paths.items()
            }
            target_mass = sum(target.values(), Q())
            binomial_mass = Q(9, 10) ** m * sum(
                (
                    math.comb(m, z)
                    * Q(1, 10) ** (m - z)
                    * Q(9, 10) ** z
                    * p.f(Q(m, 10) + Q(4 * z, 5))
                    for z in range(m + 1)
                ),
                Q(),
            )
            self.assertEqual(target_mass, binomial_mass)
            # Bound the secant's exponential through its exact m-th root.
            ratio, lower, upper = p.f(p.L) / p.f(p.H), Q(1), Q(9)
            for _ in range(80):
                middle = (lower + upper) / 2
                if middle**m <= ratio:
                    lower = middle
                else:
                    upper = middle
            optimum_lower = Q(9, 10) ** m * p.f(p.H) * (Q(9, 10) + lower / 10) ** m
            single = reference.SingleTilt(p)
            self.assertGreaterEqual(single.rejection_normalizer, optimum_lower)
            for probabilities in itertools.product((Q(1, 4), Q(1, 2), Q(3, 4)), repeat=m):
                normalizer = max(
                    w
                    / math.prod(
                        r if y[i] == 4 else 1 - r
                        for i, r in zip(p.hidden, probabilities, strict=True)
                    )
                    for y, w in target.items()
                )
                self.assertGreaterEqual(normalizer, optimum_lower)

    def test_confidence_normalizer_prime_divisors_do_not_cancel(self):
        # Finite algebra check of the new bit-cost corollary, not an
        # experimental scaling benchmark or verification of Dusart's theorem.
        for m in range(2, 7):
            plan, data = audit.fixture(m + 1)
            free = tuple(i for i, t in enumerate(data.state.canvas) if t is None)
            c = 1 << m
            q = list(data.probabilities)
            q[free[0]] = (Q(1, 2), Q(1, 2))
            for j, i in enumerate(free[1:]):
                q[i] = (Q(c - (1 << j), 2 * c), Q(c + (1 << j), 2 * c))
            q = tuple(q)
            p = reference.Problem(plan, q, q, (free[0],), {free[0]: 3})
            changed = audit.ProbabilityInput(data.state, q)
            direct = sum(
                (
                    w * audit.direct_pl(y, p.order, p.free, q, p.indices)
                    for y, w in audit.enumerated_paths(changed).items()
                    if y[free[0]] == 3
                ),
                Q(),
            )
            closed = sum(
                (
                    Q(
                        math.prod(c + (1 if b & (1 << i) else -1) * (1 << i) for i in range(m)),
                        m * c + 1 + 2 * b,
                    )
                    for b in range(c)
                ),
                Q(),
            )
            closed /= 4 * (2 * c) ** (m - 1)
            self.assertEqual(direct, closed)
            for prime in range(m * c + 1, (m + 2) * c):
                if all(prime % d for d in range(2, math.isqrt(prime) + 1)):
                    self.assertEqual(closed.denominator % prime, 0)

    def test_conditional_sampler_laws_and_token_aliases(self):
        for dyadic, tight, coefficients in (
            (False, False, False),
            (True, False, False),
            (True, True, False),
            (True, True, True),
        ):
            report = audit.correctness(
                max_n=2,
                dyadic_unaries=dyadic,
                tight_bounds=tight,
                single_tilt=tight,
                dyadic_coefficients=coefficients,
            )
            self.assertGreater(report["events"], 20)
            self.assertEqual(report["exact_mismatches"], 0)
        report = audit.correctness(
            max_n=2,
            dyadic_unaries=True,
            tight_bounds=True,
            single_tilt=True,
            dyadic_coefficients=True,
            strengthened=True,
        )
        self.assertEqual(report["exact_mismatches"], 0)

    def test_independent_gradient_and_two_replica_covariance(self):
        for power in (1, 2):
            for weighted in (False, True):
                for constrained in (False, True):
                    result = audit.gradient_case(3, weighted, power, 2, constrained)
                    self.assertGreaterEqual(Q(result["latent_fraction"]), 0)

    def test_executable_profile_categorical_law_and_resource_refusals(self):
        # Integrate the actual backpointer tables and root CDF read by sample(),
        # independently of RoundedProfiles.law() and of the CFG recognizer.
        for values in ((b"0", b"1"), (b"0", b"0", b"[1]")):
            plan, data = audit.fixture(3, True, values)
            paths = audit.enumerated_paths(data)
            p = reference.Problem(plan, data.probabilities, data.probabilities, (1,), {1: 3})
            target = {
                y: w * audit.direct_pl(y, p.order, p.free, p.rates, p.indices)
                for y, w in paths.items()
                if y[1] == 3
            }
            z = sum(target.values(), Q())
            sampler = reference.RoundedProfiles(p, dyadic_root=True)
            laws = {}
            for node in plan.order:
                for value, total in sampler.profiles[node].items():
                    result = {}
                    for term, children, mass in sampler.backpointers[node, value]:
                        probability = Q(mass, total)
                        if term.choice is not None:
                            i, j = term.choice
                            branches = [(((i, p.rows[i][j]),), Q(1))]
                        elif not children:
                            branches = [((), Q(1))]
                        else:
                            left, right = term.children
                            a, b = children
                            branches = [
                                (tuple(sorted(x + y)), px * py)
                                for x, px in laws[left, a].items()
                                for y, py in laws[right, b].items()
                            ]
                        for pairs, prob in branches:
                            result[pairs] = result.get(pairs, Q()) + probability * prob
                    laws[node, value] = result
            accepted, previous = {}, 0
            for value, cumulative in zip(sampler.root_profiles, sampler.root_cdf, strict=True):
                root_probability = Q(cumulative - previous, sampler.root_cdf[-1])
                previous = cumulative
                for pairs, probability in laws[plan.root, value].items():
                    y = tuple(t for _, t in pairs)
                    accepted[y] = accepted.get(
                        y, Q()
                    ) + root_probability * probability * sampler.acceptance(y, value)
            success = sum(accepted.values(), Q())
            self.assertEqual(
                {y: v / success for y, v in accepted.items()}, {y: w / z for y, w in target.items()}
            )
            self.assertEqual(sampler.rejection_normalizer / z, 1 / success)
            self.assertLessEqual(1 / success, 2 * (1 + Q(1, 1024)))
            for seed in range(3):
                self.assertIn(sampler.sample(audit.Random(seed))[0], target)
            with self.assertRaises(TimeoutError):
                reference.RoundedProfiles(p, max_cells=0)

    def test_stationary_metropolis_and_integrated_coin(self):
        plan, data = audit.fixture(3, True)
        paths = audit.enumerated_paths(data)
        p = reference.Problem(plan, data.probabilities, data.probabilities, (1,), {1: 4})
        weights = {
            y: w * audit.direct_pl(y, p.order, p.free, p.rates, p.indices)
            for y, w in paths.items()
            if y[1] == 4
        }
        z = sum(weights.values(), Q())
        target = {y: w / z for y, w in weights.items()}
        for constructor in (reference.BaseRejection, reference.SingleTilt):
            sampler = constructor(p)
            proposal = audit.forest_law(sampler.base)
            transition = stationary.audit_transition(sampler, target, proposal)
            # Every scalar statistic in the finite-state basis is covered.
            scores = {y: tuple(Q(y == v) for v in target) for y in target}
            pairs, integrated = [], []
            for x in target:
                for y in target:
                    pairs.append(
                        (
                            target[x] * transition[x][y],
                            tuple((a + b) / 2 for a, b in zip(scores[x], scores[y], strict=True)),
                        )
                    )
                    a = min(Q(1), sampler.acceptance(y) / sampler.acceptance(x))
                    integrated.append(
                        (
                            target[x] * proposal[y],
                            stationary.conditional_average(scores[x], scores[y], a),
                        )
                    )
            mean, original = audit.moments([(target[y], scores[y]) for y in target], len(target))
            pair_mean, pair_cov = audit.moments(pairs, len(target))
            rb_mean, rb_cov = audit.moments(integrated, len(target))
            self.assertEqual(mean, pair_mean)
            self.assertEqual(mean, rb_mean)
            # Test PSD ordering by all integer directions in {-1,0,1}^d;
            # general PSD guarantee is a written covariance identity.
            for direction in itertools.product((-1, 0, 1), repeat=len(target)):

                def quadratic(matrix, direction=direction):
                    return sum(
                        direction[i] * matrix[i][j] * direction[j]
                        for i in range(len(target))
                        for j in range(len(target))
                    )

                self.assertLessEqual(quadratic(rb_cov), quadratic(pair_cov))
                self.assertLessEqual(quadratic(pair_cov), quadratic(original))

    def test_invalid_and_impossible_evidence_is_not_sampled(self):
        plan, data = audit.fixture(2, values=(b"0", b"oops"))
        rates = data.probabilities
        with self.assertRaises(ValueError):
            reference.TangentMixture(
                reference.Problem(plan, data.probabilities, rates, (1,), {1: 4})
            )
        with self.assertRaises(ValueError):
            reference.Problem(plan, data.probabilities, rates, (1, 1), {1: 3})
        bad = tuple(tuple(Q() for _ in row) for row in rates)
        with self.assertRaises(ValueError):
            reference.Problem(plan, data.probabilities, bad, (1,), {1: 3})
        negative = tuple(tuple(-q for q in row) for row in rates)
        with self.assertRaises(ValueError):
            reference.Problem(plan, data.probabilities, negative, (1,), {1: 3})

    def test_both_utility_harness_constructor_registries(self):
        # Catches the actual partial-factory TypeError that invalidated neural v2,
        # offline, before an expensive model run. Check sampling/evidence too.
        plan, data = audit.fixture(3, True)
        p = reference.Problem(plan, data.probabilities, data.probabilities, (1,), {1: 3})
        for strengthened in (False, True):
            constructors = [
                *controls.iid_controls(strengthened).values(),
                *(factory for _, factory in controls.neural_controls(strengthened)),
            ]
            for factory in constructors:
                sampler = factory(p, end=None)
                path, _ = sampler.sample(audit.Random(19), end=None)
                self.assertEqual(path[1], 3)
                self.assertIn(path, audit.enumerated_paths(data))

    def test_fixed_slots_and_certified_extreme_exponential(self):
        plan, data = audit.fixture(2, fixed={1: 3})
        p = reference.Problem(plan, data.probabilities, data.probabilities, (), {})
        audit.check_problem(p, audit.enumerated_paths(data))
        tiny = Q(1, 2**300)
        self.assertEqual(reference.negative_exp_upper(Q(2**300), tiny), tiny)
        lower, upper = reference.exp_bounds(Q(1), tiny)
        self.assertLessEqual(upper - lower, tiny)
        self.assertGreater(lower, Q(27, 10))
        self.assertLess(upper, Q(28, 10))
        tolerance = Q(17, 13000)
        for x in (Q(1, 7), Q(12, 7), Q(11)):
            u = reference.dyadic_negative_exp_upper(x, tolerance)
            lo, hi = reference.exp_bounds(x, tolerance / 8)
            self.assertGreaterEqual(u, 1 / lo)
            self.assertLessEqual(u - 1 / hi, tolerance)
            self.assertEqual(u.denominator & (u.denominator - 1), 0)


if __name__ == "__main__":
    unittest.main()
