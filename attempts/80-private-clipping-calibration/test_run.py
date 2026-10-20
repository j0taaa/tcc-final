"""Independent finite-law checks of rejection/fallback and reporting gates."""

from __future__ import annotations

import importlib
import unittest
from dataclasses import replace
from fractions import Fraction as F
from time import perf_counter
from types import SimpleNamespace
from unittest.mock import patch

run = importlib.import_module("attempts.80-private-clipping-calibration.run")


class NeedChoice(Exception):
    def __init__(self, probability):
        self.probability = probability


class TwoAtomSampler:
    def __init__(self, probabilities):
        self.probabilities = probabilities

    def probability(self, word):
        return self.probabilities[word[0]]

    def draw(self, rng):
        return (0 if run.bernoulli(self.probabilities[0], rng) else 1,)


def exhaustive_emission(p, mu, a, R, cap):
    """Explore ideal Bernoulli branches, independently of Random and frequencies."""
    prepared = SimpleNamespace(private=TwoAtomSampler(p), reference=TwoAtomSampler(mu))
    output = [F(0), F(0)]
    fallback_mass = F(0)
    pending = [((), F(1))]
    while pending:
        path, mass = pending.pop()
        cursor = 0

        def choose(probability, _rng, path=path):
            nonlocal cursor
            if probability in (0, 1):
                return bool(probability)
            if cursor == len(path):
                raise NeedChoice(probability)
            answer = path[cursor]
            cursor += 1
            return answer

        try:
            with patch.object(run, "bernoulli", choose), patch.object(run, "REJECTION_CAP", cap):
                word, _, fallback, _ = run.emit(prepared, a, R, object())
            output[word[0]] += mass
            fallback_mass += mass if fallback else 0
        except NeedChoice as choice:
            pending.extend(
                (
                    (((*path, True), mass * choice.probability)),
                    (((*path, False), mass * (1 - choice.probability))),
                )
            )
    return tuple(output), fallback_mass


class TestEmission(unittest.TestCase):
    def test_numeric_payload_and_intermediate_width_regressions(self):
        p, mu = (F(1, 100), F(99, 100)), (F(1, 3), F(2, 3))
        self.assertEqual(run.numeric_payload_bits((p, mu)), 29)
        self.assertGreaterEqual(
            run.projection_work_bits_bound(p, mu, F(2)), run.integer_width(F(297, 400))
        )
        prepared = SimpleNamespace(private=TwoAtomSampler(mu), reference=TwoAtomSampler(mu))
        # One legal path reaches atom zero and the transient product 1/6.
        with patch.object(run, "bernoulli", return_value=True):
            word, _, _, bound = run.emit(prepared, F(1, 2), F(2), object())
        self.assertEqual(word, (0,))
        self.assertGreaterEqual(bound, run.integer_width(F(1, 6)))

    def test_entire_branch_law_matches_finite_rejection_and_fallback(self):
        for p, mu, a, R in (
            ((F(3, 4), F(1, 4)), (F(1, 2), F(1, 2)), F(1, 2), F(2)),
            ((F(1), F(0)), (F(1, 3), F(2, 3)), F(2, 3), F(2)),
            ((F(1, 4), F(3, 4)), (F(2, 3), F(1, 3)), F(1), F(3)),
        ):
            for cap in (0, 1, 2):
                with self.subTest(p=p, a=a, cap=cap):
                    c = tuple(max(a * y, min(x, R * a * y)) for x, y in zip(p, mu, strict=True))
                    z, envelope_mass = sum(c), 1 - 1 / R + a
                    failure = (1 - z / envelope_mass) ** cap
                    expected = tuple(
                        (1 - failure) * x / z + failure * y for x, y in zip(c, mu, strict=True)
                    )
                    actual, actual_fallback = exhaustive_emission(p, mu, a, R, cap)
                    self.assertEqual(actual, expected)
                    self.assertEqual(actual_fallback, failure)
                    self.assertEqual(sum(actual), 1)
                    ratios = [x / y for x, y in zip(actual, mu, strict=True)]
                    self.assertLessEqual(max(ratios), R * min(ratios))

    def test_independent_normalization_witness_accepts_zeros_and_rejects_bad_root(self):
        p, mu, R = (F(1), F(0)), (F(1, 2), F(1, 2)), F(2)
        self.assertEqual(run.verify_projection(p, mu, F(2, 3), R), (F(2, 3), F(1, 3)))
        with self.assertRaises(AssertionError):
            run.verify_projection(p, mu, F(1, 2), R)


class TestProtocolReporting(unittest.TestCase):
    def specifications(self):
        cases = SimpleNamespace(
            cases=lambda: tuple(
                SimpleNamespace(family=f, n=n) for f in ("dyck", "expr") for n in (8, 16, 32)
            )
        )
        calibration = SimpleNamespace(
            METHODS=("ratio_bisection", "indices", "grid", "gk", "median")
        )
        return list(run.configuration_order(cases, calibration))

    def rows(self):
        return [
            dict(
                spec,
                status="ok",
                total_first_output_seconds=0.75 if spec["method"] == "grid" else 1.0,
            )
            for spec in self.specifications()
        ]

    def test_order_is_fixed_all_methods_once_with_cyclic_rotation(self):
        specs = self.specifications()
        self.assertEqual(len(specs), 144)
        self.assertEqual(
            [x["method"] for x in specs[:6]],
            ["ratio_bisection", "indices", "grid", "gk", "median", "exact"],
        )
        self.assertEqual(
            [x["method"] for x in specs[6:12]],
            ["indices", "grid", "gk", "median", "ratio_bisection", "exact"],
        )
        self.assertEqual(specs[0]["family"], "dyck")
        self.assertEqual(specs[-1]["family"], "expr")

    def test_gate_requires_both_complete_families_and_best_applicable_control(self):
        rows = self.rows()
        self.assertEqual(run.decision(rows)["gate"], "pass_restricted_offline_gate")
        rows[-1]["total_first_output_seconds"] = 0.1
        # A single stronger control does not change a family median; all do.
        for row in rows:
            if row["method"] == "exact":
                row["total_first_output_seconds"] = 0.1
        self.assertEqual(run.decision(rows)["gate"], "fail_restricted_offline_gate")
        rows[0]["status"] = "timeout"
        self.assertEqual(run.decision(rows)["gate"], "inconclusive_incomplete_comparisons")

    def test_predeclared_enumeration_refusal_is_not_a_negative_mass_result(self):
        rows = self.rows()
        for row in rows:
            if row["method"] == "exact":
                row["status"] = "resource_refusal_enumeration"
        self.assertEqual(run.decision(rows)["gate"], "pass_restricted_offline_gate")
        self.assertEqual(run.decision(rows[:-1])["gate"], "inconclusive_incomplete_comparisons")


class TestSmallPipeline(unittest.TestCase):
    def test_mandatory_diagnostics_precede_first_output_event(self):
        cases, calibration = run.modules()
        case = cases.Case("dyck", 2)
        original = cases.prepare(case)
        prepared = replace(
            original, private=original.reference, min_ratio_product=1, max_ratio_product=1
        )
        registry = SimpleNamespace(cases=lambda: (case,), prepare=lambda _: prepared)
        order = []
        actual_diagnostics = run.diagnostics

        def check(*args):
            order.append("diagnostics")
            return actual_diagnostics(*args)

        arguments = SimpleNamespace(
            family="dyck", n=2, R=2, seed=11, method="grid", launch_start=perf_counter()
        )
        with (
            patch.object(run, "modules", return_value=(registry, calibration)),
            patch.object(run.resource, "setrlimit"),
            patch.object(run, "diagnostics", side_effect=check),
            patch.object(run, "write_event", side_effect=lambda event: order.append(event["kind"])),
        ):
            row = run.worker(arguments)
        self.assertEqual(order, ["diagnostics", "first_output"])
        self.assertEqual(row["validated_output_words"], 16)
        self.assertEqual(row["status"], "ok_precheck_exact_P")

    def test_all_calibrators_feed_the_same_exact_original_id_emitter(self):
        cases, calibration = run.modules()
        prepared = cases.prepare(cases.Case("dyck", 2))
        # A correctness fixture, deliberately below the statistical budget.
        # It does not claim the production confidence guarantee or time a case.
        config = replace(calibration.make_config(2), M=31, M_median=31)
        self.assertEqual(prepared.valid_count, 3)
        for method in calibration.METHODS:
            with self.subTest(method=method):
                source = run.CountingRandom("pipeline|source")
                result = calibration.calibrate(
                    method,
                    prepared.observations(source),
                    config,
                    run.CountingRandom("pipeline|aux"),
                )
                self.assertTrue(result.certificate["valid"])
                self.assertFalse(result.certificate["conditional_budget_certified"])
                quality = run.diagnostics(prepared, result.a, F(2), calibration, False)
                self.assertEqual(quality["sum_output"], 1)
                self.assertLessEqual(quality["ratio_amplitude"], 2)
                emission = run.CountingRandom("pipeline|emit")
                for _ in range(3):
                    word, _, _, _ = run.emit(prepared, result.a, F(2), emission)
                    prepared.validate(word)
                    self.assertGreater(prepared.private.probability(word), 0)


if __name__ == "__main__":
    unittest.main()
