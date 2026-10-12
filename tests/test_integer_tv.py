"""Small independent correctness regressions for the A49 integer reference."""

import importlib
import itertools
import random
import unittest
from fractions import Fraction as F
from math import prod

core = importlib.import_module("attempts.49-rational-grammar-drift.work.optimal_planar_fast")
ordered_core = importlib.import_module("attempts.49-rational-grammar-drift.work.ordered_planar")
product = importlib.import_module("attempts.49-rational-grammar-drift.work.product")
overlap = importlib.import_module("attempts.49-rational-grammar-drift.work.sampler_overlap")
word_oracle = importlib.import_module("attempts.49-rational-grammar-drift.work.verify_forest")


class IntegerTvTests(unittest.TestCase):
    def test_known_root_query_on_original_json_macros(self):
        _, kind, emissions, rows = list(word_oracle.fixtures())[2]
        source = word_oracle.json_source_grammar()
        rng = random.Random(202610120492)
        for mode in ["equal", "zero", "different"]:
            first, second = word_oracle.make_inputs(source, emissions, rows, mode, rng)
            plan = word_oracle.compile_cfg_sampler(source, first.state)
            truth = word_oracle.expected(first, second, emissions, kind)
            for name in [
                "adaptive_angular",
                "calibrated_endpoint",
                "hybrid_endpoint",
                "ordered_planar",
            ]:
                engine = importlib.import_module("attempts.49-rational-grammar-drift.work." + name)
                with self.subTest(mode=mode, engine=name):
                    result = word_oracle.certificate(
                        plan,
                        first,
                        second,
                        F(1, 10),
                        compressor=engine,
                        exact_passthrough=True,
                        known_root_query=True,
                    )
                    if truth is None:
                        self.assertEqual(result["status"], "ZERO_VALID_MASS_UNDEFINED_TV")
                    else:
                        self.assertLessEqual(result["lower"], truth)
                        self.assertGreaterEqual(result["upper"], truth)
                        self.assertLessEqual(result["upper"], F(11, 10) * result["lower"])
                        self.assertEqual(result["root_rows"], 0)
                        self.assertGreaterEqual(result["root_lower_factor"], F(10, 11))

    def test_scalar_coupling_on_original_ids_and_nontrivial_node_order(self):
        _, kind, emissions, rows = list(word_oracle.fixtures())[1]
        source = word_oracle.dyck_source()
        rng = random.Random(202610120492)
        for mode in ["equal", "tiny-scale", "zero", "near-equal", "different"]:
            with self.subTest(mode=mode):
                first, second = word_oracle.make_inputs(source, emissions, rows, mode, rng)
                plan = word_oracle.compile_cfg_sampler(source, first.state)
                self.assertNotEqual(plan.order, tuple(range(len(plan.terms))))
                truth = word_oracle.expected(first, second, emissions, kind)
                result = overlap.controls(plan, first, second)
                if truth is None:
                    self.assertEqual(result["status"], "ZERO_VALID_MASS_UNDEFINED_TV")
                else:
                    for bound in result["bounds"].values():
                        self.assertLessEqual(truth, bound)
                        self.assertLessEqual(bound, 1)
                    if mode in ["equal", "tiny-scale"]:
                        self.assertEqual(result["upper"], 0)

    def test_signed_core_at_all_piecewise_linear_breakpoints(self):
        rows = [(i, (i * i) % 17 - 8) for i in range(-25, 26)]
        for engine in [core, ordered_core]:
            with self.subTest(engine=engine.__name__):
                reduced = engine.compress(rows, 1)
                self.assertLessEqual(len(reduced), 64)
                for w in [(1, 0), (0, 1), *((-b, a) for a, b in rows + reduced)]:
                    exact = sum(abs(a * w[0] + b * w[1]) for a, b in rows)
                    actual = sum(abs(a * w[0] + b * w[1]) for a, b in reduced)
                    self.assertLessEqual(actual, exact)
                    self.assertGreaterEqual(16 * actual, 15 * exact)

    def test_ordered_singular_images_preserve_minimum_angle(self):
        # The first nonempty V19 oracle failed here, before all product tests.
        diagonals = [(0, 0), (1, 0), (0, 1), (2, 3), (4, 1), (1, 7)]
        expected = [(1, 0), (4, 1), (2, 3), (1, 7), (0, 1)]
        self.assertEqual(ordered_core.compress_images([(1, 1)], diagonals, 1), expected)

    def test_original_choice_product_against_enumeration(self):
        p = [[F(3, 8), F(1, 4), F(3, 8)]] * 5
        q = [[F(1, 2), F(3, 10), F(1, 5)]] * 5
        truth = (
            sum(
                abs(
                    prod(p[i][v] for i, v in enumerate(word))
                    - prod(q[i][v] for i, v in enumerate(word))
                )
                for word in itertools.product(range(3), repeat=5)
            )
            / 2
        )
        for engine in [core, ordered_core]:
            with self.subTest(engine=engine.__name__):
                result = product.certificate(p, q, F(1, 10), compressor=engine)
                self.assertLessEqual(result["lower"], truth)
                self.assertGreaterEqual(result["upper"], truth)
                self.assertLessEqual(result["upper"], F(11, 10) * result["lower"])

    def test_tiny_exact_input_extreme_precision_and_zero_mass(self):
        p, q = [[F(1, 3), F(2, 3)]], [[F(1, 4), F(3, 4)]]
        for engine in [core, ordered_core]:
            with self.subTest(engine=engine.__name__):
                result = product.certificate(p, q, F(1, 1 << 1024), compressor=engine)
                self.assertEqual(result["lower"], F(1, 12))
                self.assertEqual(
                    product.certificate([], [], F(1, 10), compressor=engine)["lower"], F()
                )
                self.assertEqual(
                    product.certificate([[F()]], [[F(1)]], compressor=engine)["status"],
                    "ZERO_VALID_MASS_UNDEFINED_TV",
                )
                with self.assertRaises(ValueError):
                    product.certificate([[0.5]], [[F(1)]], compressor=engine)
