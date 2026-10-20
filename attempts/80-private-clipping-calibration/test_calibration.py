"""Standalone correctness oracles; no production sample budgets or benchmarks.

Run from the checkout: python -m unittest discover -s
attempts/80-private-clipping-calibration -p test_calibration.py -v
"""

from __future__ import annotations

import itertools
import json
import unittest
from array import array
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction as F
from random import Random
from unittest.mock import patch

from calibration import (
    METHODS,
    GKSummary,
    PublicGrid,
    _histogram_certificate,
    _median_threshold,
    _payload,
    _raw_score_interval,
    _sweep,
    calibrate,
    exact_projection,
    make_config,
    public_grid,
)


def clip(value: F, low: F, high: F) -> F:
    return min(high, max(low, value))


def score(a: F, gamma: F, R: F) -> F:
    return 2 * (clip(gamma, a * (1 - gamma), R * a * (1 - gamma)) - gamma)


def empirical(a: F, observations: list[tuple[int, int]], R: F) -> F:
    return sum(score(a, F(U, U + V), R) for U, V in observations) / len(observations)


def brute_minimum(gammas: list[F], weights: list[F], R: F) -> F:
    """Independent piece oracle: evaluate endpoint scores, interpolate a crossing.

    Enumerates every piece, with no sweep counts or retained-ratio bisection.
    """
    points = {1 / R, F(1)}
    for gamma in gammas:
        if gamma < 1:
            r = gamma / (1 - gamma)
            points.update(x for x in (r, r / R) if 1 / R <= x <= 1)
    points = sorted(points)

    def value(a: F) -> F:
        return sum(w * score(a, g, R) for g, w in zip(gammas, weights, strict=False))

    if value(points[0]) >= 0:
        return points[0]
    for lo, hi in itertools.pairwise(points):
        fl, fh = value(lo), value(hi)
        if fl == 0:
            return lo
        if fl < 0 <= fh:
            return lo - fl * (hi - lo) / (fh - fl)
    return F(1)


def brute_projection(p: list[F], mu: list[F], R: F) -> F:
    # E_rho g = Z-1; this independently converts the normalized laws into
    # weighted observations, then uses the piece interpolation oracle.
    return brute_minimum(
        [pi / (pi + mi) for pi, mi in zip(p, mu, strict=False)],
        [(pi + mi) / 2 for pi, mi in zip(p, mu, strict=False)],
        R,
    )


def grid_rows(grid: PublicGrid, indices: list[int]) -> list[tuple[int, int]]:
    return [(grid.numerator(i), indices.count(i)) for i in sorted(set(indices))]


class CountingSource:
    def __init__(self, values: list[tuple[int, int]]):
        self.values = values
        self.calls = 0

    def __iter__(self):
        return self

    def __next__(self):
        value = self.values[self.calls % len(self.values)]
        self.calls += 1
        return value


class Auxiliary:
    def __init__(self, values: list[int]):
        self.values = values
        self.calls = 0

    def getrandbits(self, bits: int) -> int:
        if bits != 64:
            raise AssertionError("median must use exactly 64-bit auxiliary uniforms")
        value = self.values[self.calls % len(self.values)]
        self.calls += 1
        return value


def small_config(R: int = 2, n: int = 31):
    config = make_config(R)
    # Lower sample counts are explicitly correctness fixtures and cannot acquire
    # the confidence certificate. Grid selection stays independent of samples.
    return replace(config, M=n, M_median=n if n % 2 else n + 1)


class ConfigAndGridTests(unittest.TestCase):
    def test_frozen_public_production_constants_without_sampling(self):
        expected = {2: (4801, 4800, "uniform"), 16: (26881, 143360, "dyadic")}
        for R, (H, D, kind) in expected.items():
            c = make_config(R)
            self.assertEqual((c.R, c.xi, c.beta), (F(R), F(1, 50), F(1, 20)))
            self.assertEqual(c.bar_b, F(7, 10) if R == 2 else F(14, 5))
            self.assertEqual((len(c.grid), c.grid.D, c.grid.kind), (H, D, kind))
            self.assertIs(public_grid(c), c.grid)
            saa = 2 * (32 + 56 * c.bar_b / 3) * F(37, 10) / c.xi
            self.assertLess(c.M - 1, saa)
            self.assertGreaterEqual(c.M, saa)
            eta = c.xi / (c.bar_b + c.xi)
            median = F(74, 10) / (eta - F(1, 1 << 63)) ** 2
            self.assertEqual(c.M_median % 2, 1)
            self.assertLess(c.M_median - 2, median)
            self.assertGreaterEqual(c.M_median, median)
            self.assertGreaterEqual(c.J, 1)
            with self.assertRaises(FrozenInstanceError):
                c.M = 1
        for R in (1, 3, 2.0, True):
            with self.assertRaises(ValueError):
                make_config(R)

    def test_dyadic_points_against_explicit_band_definition(self):
        for m, h in itertools.product((1, 2, 3, 7), (1, 2, 3, 5)):
            grid = PublicGrid("dyadic", m << h, m * (h + 1) + 1, m, h)
            t = {F(j, m * (1 << h)) for j in range(m + 1)}
            for k in range(h):
                lo, hi = F(1, 1 << (k + 1)), F(1, 1 << k)
                t.update(lo + (hi - lo) * F(j, m) for j in range(m + 1))
            expected = sorted(1 - x for x in t)
            self.assertEqual([F(grid.numerator(i), grid.D) for i in range(len(grid))], expected)
            for gamma in [*expected, *(F(i, 97) for i in range(97)), F(0), F(1)]:
                # The quantizer's contract includes gamma=1 as a public-grid
                # endpoint although V>0 makes it unreachable from raw sources.
                U, V = gamma.numerator, gamma.denominator - gamma.numerator
                idx = grid.quantize(U, V)
                oracle = max(i for i, g in enumerate(expected) if g <= gamma)
                self.assertEqual(idx, oracle)
            for idx in (-1, grid.H):
                with self.assertRaises(IndexError):
                    grid.numerator(idx)

    def test_uniform_score_bound_on_every_piece(self):
        for R in (F(2), F(16)):
            grid = PublicGrid("uniform", 19, 20)
            for gamma in (F(0), F(1), F(1, 97), F(3, 7), F(96, 97)):
                idx = grid.quantize(gamma.numerator, gamma.denominator - gamma.numerator)
                quantized = F(grid.numerator(idx), grid.D)
                points = {1 / R, F(1)}
                for g in (gamma, quantized):
                    if g < 1:
                        points.update(
                            x for x in (g / (1 - g), g / ((1 - g) * R)) if 1 / R <= x <= 1
                        )
                self.assertTrue(
                    all(
                        abs(score(a, gamma, R) - score(a, quantized, R)) <= 2 * (R + 1) / grid.D
                        for a in points
                    )
                )

    def test_dyadic_cell_bound_including_gamma_one(self):
        for R in (F(2), F(16)):
            h = 2 if R == 2 else 5
            m = 3
            grid = PublicGrid("dyadic", m << h, m * (h + 1) + 1, m, h)
            for i in range(grid.H - 1):
                left, right = F(grid.numerator(i), grid.D), F(grid.numerator(i + 1), grid.D)
                points = {1 / R, F(1)}
                for gamma in (left, right):
                    if gamma < 1:
                        r = gamma / (1 - gamma)
                        points.update(x for x in (r, r / R) if 1 / R <= x <= 1)
                self.assertTrue(
                    all(abs(score(a, left, R) - score(a, right, R)) <= F(2, m) for a in points)
                )


class SweepTests(unittest.TestCase):
    def test_exhaustive_three_bin_counts_and_edge_events(self):
        for R, D in itertools.product((F(2), F(3, 2), F(16)), (2, 3, 6)):
            for us in itertools.combinations_with_replacement(range(D + 1), 3):
                rows = [(u, us.count(u)) for u in sorted(set(us))]
                expected = brute_minimum([F(u, D) for u in us], [F(1, 3)] * 3, R)
                actual = _sweep(rows, D, R)
                self.assertEqual(actual, expected, (R, D, us))
                self.assertTrue(_histogram_certificate(rows, D, R, actual, 3)["valid"])

    def test_flat_minimum_and_initial_boundary_ties(self):
        # R=2, gamma=1/3 has r=1/R and gamma=1/2 has r=1.
        # gamma=0 and 1 have no finite breakpoints. Equal r and r/R events
        # occur at a=2/3 for gamma=2/5 and gamma=4/7.
        fixtures = [
            ([(1, 1)], 2, F(1, 2)),
            ([(0, 1)], 1, F(1, 2)),
            ([(1, 1)], 1, F(1)),
            ([(2, 1), (3, 1)], 6, F(1, 2)),
            ([(14, 3), (20, 3)], 35, None),
            ([(0, 2), (2, 1), (3, 2), (6, 2)], 6, None),
        ]
        for rows, D, known in fixtures:
            actual = _sweep(rows, D, F(2))
            expected = brute_minimum([F(u, D) for u, _ in rows], [F(c) for _, c in rows], F(2))
            self.assertEqual(actual, expected)
            if known is not None:
                self.assertEqual(actual, known)
        with self.assertRaises(ArithmeticError):
            _histogram_certificate([(0, 1)], 1, F(2), F(3, 4), 1)
        with self.assertRaises(ArithmeticError):
            _histogram_certificate([(0, -1)], 1, F(2), F(1, 2), 1)


class ProjectionTests(unittest.TestCase):
    def assert_kkt(self, p: list[F], mu: list[F], R: F, a: F):
        q = [clip(pi, a * mi, R * a * mi) for pi, mi in zip(p, mu, strict=False)]
        self.assertEqual(sum(q), 1)
        alpha = [max(F(0), 1 - pi / qi) for pi, qi in zip(p, q, strict=False)]
        beta = [max(F(0), pi / qi - 1) for pi, qi in zip(p, q, strict=False)]
        for pi, mi, qi, al, be in zip(p, mu, q, alpha, beta, strict=False):
            self.assertGreater(qi, 0)
            self.assertLessEqual(a * mi, qi)
            self.assertLessEqual(qi, R * a * mi)
            self.assertEqual(-pi / qi + 1 - al + be, 0)
            self.assertEqual(al * (qi - a * mi), 0)
            self.assertEqual(be * (R * a * mi - qi), 0)
        self.assertEqual(
            sum(mi * (al - R * be) for mi, al, be in zip(mu, alpha, beta, strict=False)), 0
        )

    def test_all_small_closed_laws_exact_normalization_kkt_and_first_root(self):
        for total in (2, 4):
            laws = [
                [F(a, total), F(b, total), F(total - a - b, total)]
                for a in range(total + 1)
                for b in range(total - a + 1)
            ]
            references = [
                [F(a, a + b + c), F(b, a + b + c), F(c, a + b + c)]
                for a, b, c in itertools.product((1, 2, 3), repeat=3)
            ]
            for p, mu, R in itertools.product(laws, references, (F(2), F(16), F(3, 2))):
                a = exact_projection(p, mu, R)
                self.assertEqual(a, brute_projection(p, mu, R), (p, mu, R))
                self.assert_kkt(p, mu, R, a)

    def test_theory_three_atom_family_and_plateau(self):
        for p in (F(1, 100), F(1, 1000)):
            target = [5 * p / 3, 1 - 14 * p / 3, 3 * p]
            reference = [5 * p, 1 - 6 * p, p]
            self.assertEqual(exact_projection(target, reference, F(2)), F(2, 3))
            a = F(5, 6)
            z = sum(clip(pi, a * mi, 2 * a * mi) for pi, mi in zip(target, reference, strict=False))
            self.assertEqual(z, 1 + 7 * p / 6)
        self.assertEqual(exact_projection([F(1)], [F(1)], F(2)), F(1, 2))
        # Every threshold in [9/16,3/4] has exactly the original law.
        self.assertEqual(exact_projection([F(1, 4), F(3, 4)], [F(1, 3), F(2, 3)], F(2)), F(9, 16))

    def test_rejects_missing_mass_and_unsupported_laws(self):
        for p, mu, R in (
            ([], [], F(2)),
            ([F(0)], [F(1)], F(2)),
            ([F(1)], [F(0)], F(2)),
            ([F(1)], [F(1)], F(1)),
            ([F(-1), F(2)], [F(1, 2)] * 2, F(2)),
            ([F(1)], [F(1, 2)] * 2, F(2)),
        ):
            with self.assertRaises(ValueError):
                exact_projection(p, mu, R)


class GKTests(unittest.TestCase):
    def assert_original_cdf(self, summary: GKSummary, original: list[int]):
        self.assertTrue(summary.validate(), (summary.n, summary.entries))
        self.assertEqual(sum(g for _, g, _ in summary.entries), len(original))
        # Both sides of every jump, including runs of equal values, suffice
        # for all real cutoffs in this integer-valued stream.
        for cutoff in range(-1, 34):
            represented = sum(g for v, g, _ in summary.entries if v <= cutoff)
            actual = sum(v <= cutoff for v in original)
            self.assertLessEqual(
                F(abs(actual - represented), len(original)),
                2 * summary.eps,
                (cutoff, original, summary.entries),
            )

    def test_original_ranks_ties_and_adversarial_arrivals_after_every_insert(self):
        base = list(range(33)) * 3
        rng = Random(101)
        shuffled = base.copy()
        rng.shuffle(shuffled)
        outside_in = [x for pair in zip(range(17), range(32, 15, -1), strict=False) for x in pair]
        streams = [
            base,
            sorted(base),
            sorted(base, reverse=True),
            shuffled,
            [16] * 101,
            [0, 32] * 61,
            outside_in * 3,
        ]
        for eps, values in itertools.product((F(1, 4), F(1, 10), F(1, 37)), streams):
            summary = GKSummary(eps)
            seen = []
            for value in values:
                summary.insert(value)
                seen.append(value)
                self.assert_original_cdf(summary, seen)
                if len(seen) % 7 == 0:
                    summary.compress()
                    self.assert_original_cdf(summary, seen)

    def test_summary_score_bound_on_all_pieces(self):
        R, D, eps = F(16), 32, F(1, 20)
        values = [*range(D + 1), *range(D, -1, -1), *([0, D, D // 2] * 12)]
        summary = GKSummary(eps)
        for value in values:
            summary.insert(value)
        summary.compress()
        self.assert_original_cdf(summary, values)
        points = {1 / R, F(1)}
        for u in range(D):
            ratio = F(u, D - u)
            points.update(a for a in (ratio, ratio / R) if 1 / R <= a <= 1)
        for a in points:
            actual = sum(score(a, F(u, D), R) for u in values) / len(values)
            represented = sum(g * score(a, F(u, D), R) for u, g, _ in summary.entries) / len(values)
            self.assertLessEqual(abs(actual - represented), 8 * eps)


class CalibrationTests(unittest.TestCase):
    def test_exact_consumption_component_timers_and_confidence_separation(self):
        for method in METHODS:
            source = CountingSource([(0, 3), (7, 2), (1 << 257, 13), (2, 2)])
            rng = Auxiliary([0, (1 << 63), (1 << 64) - 1])
            c = small_config(n=9)
            with patch("calibration.perf_counter", side_effect=(10.0, 13.0, 18.0)):
                result = calibrate(method, source, c, rng)
            self.assertEqual(source.calls, c.M_median if method == "median" else c.M)
            self.assertEqual(rng.calls, source.calls if method == "median" else 0)
            self.assertEqual((result.collection_seconds, result.solve_seconds), (3.0, 5.0))
            self.assertTrue(F(1, 2) <= result.a <= 1)
            self.assertTrue(result.certificate["valid"])
            self.assertFalse(result.certificate["sample_budget_met"])
            self.assertFalse(result.certificate["conditional_budget_certified"])
            self.assertFalse(result.certificate["executable_privacy_certified"])
            json.dumps(result.certificate)
            self.assertGreater(result.state_storage_bytes, 0)
            self.assertGreater(result.state_numeric_bits, 0)
            self.assertGreaterEqual(result.max_work_bits, 258)

    def test_quantized_methods_and_uniform_gradient_gap_certificate(self):
        observations = [
            (0, 1),
            (1, 3),
            (1, 2),
            (1, 1),
            (2, 1),
            (7, 1),
            (31, 1),
            ((1 << 300) - 1, 1),
        ]
        for R, method in itertools.product((2, 16), ("grid", "indices", "gk")):
            c = small_config(R, 47)
            source = CountingSource(observations)
            result = calibrate(method, source, c, Random(3))
            actual = [observations[i % len(observations)] for i in range(c.M)]
            quantized = [c.grid.quantize(U, V) for U, V in actual]
            rows = grid_rows(c.grid, quantized)
            expected = brute_minimum(
                [F(u, c.grid.D) for u, _ in rows], [F(n, c.M) for _, n in rows], c.R
            )
            # With production epsilon and these small fixtures, GK is exact.
            self.assertEqual(result.a, expected)
            points = {1 / c.R, F(1)}
            for U, V in actual:
                points.update(x for x in (F(U, V), F(U, V) / c.R) if 1 / c.R <= x <= 1)
            for u, _ in rows:
                if u < c.grid.D:
                    points.update(
                        x
                        for x in (F(u, c.grid.D - u), F(u, c.grid.D - u) / c.R)
                        if 1 / c.R <= x <= 1
                    )
            sup = max(
                abs(
                    empirical(a, actual, c.R)
                    - sum(n * score(a, F(u, c.grid.D), c.R) for u, n in rows) / c.M
                )
                for a in points
            )
            certified_score = F(result.certificate["quantization_score_error_bound"])
            self.assertLessEqual(sup, certified_score)
            # Uniform derivative error integrated over the entire tau interval
            # is a rigorous empirical loss-gap bound, using public log(R)<=bbar.
            self.assertLessEqual(c.bar_b * sup, F(result.certificate["empirical_loss_gap_upper"]))
            self.assertTrue(result.certificate["empirical_loss_gap_certified"])

    def test_compressed_gk_output_has_independent_empirical_score_bound(self):
        # Larger public epsilon solely to exercise actual compression in a
        # small correctness fixture; no production confidence is measured.
        c = replace(small_config(R=16, n=401), xi=F(4))
        values = [(i, 33 - i) for i in range(33)]
        values.extend([(0, 1)] * 11 + [(99, 1)] * 7)
        result = calibrate("gk", CountingSource(values), c, Random(5))
        expanded = [values[i % len(values)] for i in range(c.M)]
        exact = empirical(result.a, expanded, c.R)
        residual = max(
            F(0), -exact if result.a == 1 / c.R else exact if result.a == 1 else abs(exact)
        )
        bound = F(result.certificate["quantization_score_error_bound"]) + 8 * c.eps
        self.assertLessEqual(residual, bound)
        self.assertLessEqual(c.bar_b * residual, F(result.certificate["empirical_loss_gap_upper"]))
        self.assertTrue(result.certificate["gk_rank_invariant"])
        self.assertLess(result.certificate["representatives"], c.M)
        with patch.object(GKSummary, "validate", return_value=False):
            with self.assertRaisesRegex(ArithmeticError, "no CDF certificate"):
                calibrate("gk", CountingSource(values), c, Random(5))

    def test_fixed_point_interval_signed_floor_and_unreduced_large_inputs(self):
        values = [(0, 1), (1, 3), (9, 1), (1 << 400, (1 << 399) - 1)]
        for R, a, scale in itertools.product((F(2), F(16)), (F(1, 2), F(2, 3), F(1)), (3, 17)):
            low, high = _raw_score_interval(values, a, R, scale)
            exact = empirical(a, values, R)
            self.assertLessEqual(F(low, len(values) * scale), exact)
            self.assertLessEqual(exact, F(high, len(values) * scale))
            self.assertEqual(F(high - low, len(values) * scale), F(1, scale))
        for R in (2, 16):
            c = small_config(R, 19)
            for values in ([(0, 1)], [(9, 1)], [(1, 1)], [(1, 2), (4, 3), (19, 7)]):
                result = calibrate("ratio_bisection", CountingSource(values), c, Random(0))
                expanded = [values[i % len(values)] for i in range(c.M)]
                exact = empirical(result.a, expanded, c.R)
                residual = max(
                    F(0), -exact if result.a == 1 / c.R else exact if result.a == 1 else abs(exact)
                )
                self.assertLessEqual(residual, c.delta)
                self.assertLessEqual(
                    c.bar_b * residual, F(result.certificate["empirical_loss_gap_upper"])
                )
                # Multiplying numerator and denominator must not alter gamma
                # or the bisection's exact integer floor decisions.
                factor = (1 << 127) - 1
                scaled = [(U * factor, V * factor) for U, V in values]
                other = calibrate("ratio_bisection", CountingSource(scaled), c, Random(0))
                self.assertEqual(result.a, other.a)

    def test_median_inverse_cdf_with_u64_endpoints_plateaus_and_zero_p(self):
        R = F(2)
        # At U=V and u=gamma=1/2, the plateau starts at r/R=1/2.
        self.assertEqual(_median_threshold(1, 1, 1 << 63, R), F(1, 2))
        self.assertEqual(_median_threshold(0, 1, 0, R), F(1, 2))
        self.assertEqual(_median_threshold(0, 1, (1 << 64) - 1, R), F((1 << 64) - 1, 1 << 64))
        for R, (U, V) in itertools.product((F(2), F(16)), ((0, 1), (1, 3), (7, 3), (1 << 300, 1))):
            gamma = F(U, U + V)
            for k in (0, 1, (1 << 63) - 1, 1 << 63, (1 << 64) - 1):
                threshold = _median_threshold(U, V, k, R)
                uniform = F(k, 1 << 64)
                for a in (1 / R, F(1, 2), F(2, 3), F(1)):
                    if a < 1 / R or a == 1:
                        continue
                    cdf = clip(gamma, a * (1 - gamma), R * a * (1 - gamma))
                    self.assertEqual(threshold <= a, uniform <= cdf, (R, U, V, k, a, threshold))
        source = CountingSource([(0, 1), (1, 2), (8, 1)])
        auxiliary = Auxiliary([0, 1 << 63, (1 << 64) - 1])
        c = small_config(n=7)
        result = calibrate("median", source, c, auxiliary)
        thresholds = [
            _median_threshold(*source.values[i % 3], auxiliary.values[i % 3], c.R)
            for i in range(c.M_median)
        ]
        self.assertEqual(result.a, sorted(thresholds)[c.M_median // 2])
        self.assertEqual(result.certificate["auxiliary_rng_bits"], 64 * c.M_median)
        self.assertEqual(F(result.certificate["confidence_correction"]), F(1, 1 << 63))

    def test_median_u64_cdf_error_against_exact_three_atom_law(self):
        p, a, R, N = F(1, 100), F(5, 6), F(2), 1 << 64
        target, reference = [5 * p / 3, 1 - 14 * p / 3, 3 * p], [5 * p, 1 - 6 * p, p]
        ideal, discrete = F(0), F(0)
        for pi, mi in zip(target, reference, strict=True):
            gamma, rho = pi / (pi + mi), (pi + mi) / 2
            cdf = clip(gamma, a * (1 - gamma), R * a * (1 - gamma))
            x = N * cdf
            last = x.numerator // x.denominator
            discrete += rho * F(last + 1, N)
            ideal += rho * cdf
            r = pi / mi
            for k in (last, last + 1):
                self.assertEqual(
                    _median_threshold(r.numerator, r.denominator, k, R) <= a, F(k, N) <= cdf
                )
        self.assertEqual(ideal, F(1, 2) + 7 * p / 12)
        self.assertLessEqual(ideal, discrete)
        self.assertLessEqual(discrete - ideal, F(1, N))

    def test_rejects_bad_input_and_does_not_silently_shorten_stream(self):
        c = small_config(n=3)
        for observation in ((-1, 1), (1, 0), (1.0, 1), (True, 1)):
            with self.assertRaises(ValueError):
                calibrate("grid", itertools.repeat(observation), c, Random(0))
        with self.assertRaises(StopIteration):
            calibrate("grid", [(1, 1)], c, Random(0))
        with self.assertRaises(ValueError):
            calibrate("unknown", itertools.repeat((1, 1)), c, Random(0))
        with self.assertRaises(ValueError):
            calibrate("median", itertools.repeat((1, 1)), replace(c, M_median=2), Random(0))
        with self.assertRaises(ValueError):
            calibrate(
                "ratio_bisection", itertools.cycle([(1, 4), (11, 1)]), replace(c, J=0), Random(0)
            )

    def test_payload_counts_logical_duplicates_but_storage_once(self):
        big = 1 << 200
        bits_one, size_one = _payload([big])
        bits_two, size_two = _payload([big, big])
        self.assertEqual(bits_two, 2 * bits_one)
        self.assertGreater(size_two, size_one)
        fraction = F(5, 7)
        self.assertEqual(_payload([fraction])[0], 6)
        values = array("I", [0, 7, 7])
        self.assertEqual(_payload(values)[0], 7)


if __name__ == "__main__":
    unittest.main()
