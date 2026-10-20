"""Finite rational correctness oracles for classical A79 controls; no timings."""

from __future__ import annotations

import importlib
import itertools
import json
import math
import tempfile
import unittest
from contextlib import nullcontext
from fractions import Fraction as F
from pathlib import Path
from random import Random
from unittest.mock import patch

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.limits import CompilationLimit

r = importlib.import_module("attempts.79-stochastic-circuit-sampling.run")


def fixture(rows=None, weights=None, emissions=(b"0", b"1", b"0"), source=None, canvas=None):
    rows = ((0, 1, 2),) if rows is None else rows
    weights = ((F(1, 8), F(2, 8), F(4, 8)),) if weights is None else weights
    source = r.cases.grammar("binary") if source is None else source
    data = r.cases.inputs(source, emissions, rows, weights, canvas)
    return data, compile_cfg_sampler(source, data.state)


def exact_cells(plan, rows):
    """Rational propagation independent of integer scaling/binary64 certificates."""
    values = [F()] * len(plan.terms)
    for node in plan.order:
        masses = []
        for term in plan.terms[node]:
            if term.choice is not None:
                p, j = term.choice
                masses.append(rows[p][j])
            else:
                masses.append(math.prod(values[c] for c in term.children))
        values[node] = sum(masses, F())
    return values


class NeedInteger(Exception):
    def __init__(self, total):
        self.total = total


class IntegerTranscript(Random):
    def __init__(self, draws):
        super().__init__(0)
        self.draws = iter(draws)

    def randrange(self, total):
        try:
            return next(self.draws)
        except StopIteration:
            raise NeedInteger(total) from None


class ScriptedBits(Random):
    def __init__(self, draws):
        super().__init__(0)
        self.draws, self.calls = iter(draws), []

    def getrandbits(self, k):
        expected, value = next(self.draws)
        if expected != k:
            raise AssertionError(f"redraw or discarded prefix: expected {expected}, got {k}")
        if not 0 <= value < 2**k:
            raise AssertionError("invalid test bits")
        self.calls.append(k)
        return value


class ControlTests(unittest.TestCase):
    def test_decision_uses_all_cases_and_the_strongest_control(self):
        rows = []
        for case in r.cases.cases():
            for method in r.METHODS:
                elapsed = 0.5 if method == "sr_singleton" else 1.0
                if method == r.CANDIDATE:
                    elapsed = 0.8 if case.family == "dyck" else 0.35
                rows.extend(
                    dict(
                        phase="query",
                        case=case.name,
                        method=method,
                        query=j,
                        status="completed",
                        validated=True,
                        wall_seconds=elapsed,
                    )
                    for j in range(16)
                )
        result = r.summarize(rows)
        self.assertTrue(result["time_gate_pass"])
        self.assertEqual(set(result["time_gate_families"]), {"binary", "modes"})
        self.assertEqual(result["family_median_ratios"]["dyck"], 1.6)
        self.assertEqual(result["memory_gate"], "inconclusive_no_isolated_RSS")
        rows[0]["status"] = "timeout_unresolved"
        result = r.summarize(rows)
        self.assertFalse(result["time_gate_pass"])
        self.assertEqual(result["decision"], "inconclusive_unresolved")

    def test_integer_law_against_original_id_enumeration(self):
        data, plan = fixture()
        e = r.ExactPlan(plan, data.probabilities)
        law, pending = {}, [((), F(1))]
        while pending:
            draws, probability = pending.pop()
            try:
                word = e.sample(IntegerTranscript(draws))
            except NeedInteger as decision:
                pending.extend(
                    ((*draws, i), probability / decision.total) for i in range(decision.total)
                )
            else:
                law[word] = law.get(word, F()) + probability
        self.assertEqual(law, {(0,): F(1, 7), (1,): F(2, 7), (2,): F(4, 7)})
        self.assertEqual(F(e.values[plan.root], math.prod(e.scales)), F(7, 8))
        self.assertFalse(hasattr(e, "marginals"))

    def test_native_mass_and_conditional_enclosures_are_rationally_safe(self):
        for bits, length in itertools.product((4, 54, 80), (1, 2, 3)):
            weights = tuple(
                (F(2**bits + 1, 2 ** (bits + 2)), F(2**bits - 1, 2 ** (bits + 2)))
                for _ in range(length)
            )
            data, plan = fixture(rows=((0, 1),) * length, weights=weights)
            e = r.Interval64(plan, data.probabilities)
            self.assertIsNone(e.exact)
            exact = exact_cells(plan, data.probabilities)
            for node in e.order:
                lo, hi = r.enclosure(e.values[node], e.budgets[node])
                self.assertLessEqual(F(lo), exact[node])
                self.assertLessEqual(exact[node], F(hi))
                bounds, masses = [], []
                for term in plan.terms[node]:
                    bounds.append(
                        r.enclosure(e.mass(term, e.values), r.term_budget(term, e.budgets))
                    )
                    masses.append(
                        data.probabilities[term.choice[0]][term.choice[1]]
                        if term.choice is not None
                        else math.prod(exact[c] for c in term.children)
                    )
                cumulative = F()
                for boundary, mass in zip(r.cdf_bounds(bounds)[1:], masses, strict=True):
                    cumulative += mass
                    self.assertLessEqual(F(boundary[0]), cumulative / sum(masses))
                    self.assertLessEqual(cumulative / sum(masses), F(boundary[1]))

    def test_retained_prefix_fallback_preserves_boundary_and_prior_choices(self):
        close = (F(2**54 + 1, 2**55), F(2**54 - 1, 2**55))
        data, plan = fixture(rows=((0, 1),) * 2, weights=((F(1, 2), F(1, 2)), close))
        e = r.Interval64(plan, data.probabilities)
        rng = ScriptedBits([(32, 1 << 30), (32, 1 << 31), *[(1, 0)] * 23])
        self.assertEqual(e.sample(rng), (0, 0))
        self.assertEqual(rng.calls, [32, 32] + [1] * 23)
        self.assertEqual(e.stats["exact_preparations"], 1)
        self.assertEqual(e.stats["conditional_refinements"], 1)
        self.assertGreaterEqual(e.stats["certified_choices"], 1)
        saved = e.exact
        self.assertEqual(e.sample(ScriptedBits([(32, 3 << 30)] * 2)), (1, 1))
        self.assertIs(e.exact, saved)
        self.assertEqual(e.stats["exact_preparations"], 1)

    def test_huge_gap_positive_input_and_product_never_disappear(self):
        for length, tiny in ((1, F(1, 2**2000)), (2, F(1, 2**600))):
            data, plan = fixture(rows=((0, 1),) * length, weights=((tiny, F()),) * length)
            e = r.Interval64(plan, data.probabilities)
            self.assertIsNotNone(e.exact)
            self.assertEqual(e.stats["exact_preparations"], 1)
            self.assertEqual(e.sample(ScriptedBits([(32, 0)] * length)), (0,) * length)
            self.assertEqual(F(e.exact.values[plan.root], math.prod(e.exact.scales)), tiny**length)

    def test_zero_mass_is_distinct_and_zero_alternatives_not_selected(self):
        data, plan = fixture(weights=((F(), F(), F()),))
        for control in (r.ExactPlan, r.Interval64):
            with self.assertRaises(r.circuit.ZeroMass):
                control(plan, data.probabilities)
        data, plan = fixture(weights=((F(), F(1, 8), F()),))
        e = r.Interval64(plan, data.probabilities)
        for prefix in (0, 2**31, 2**32 - 1):
            self.assertEqual(e.sample(ScriptedBits([(32, prefix)])), (1,))
        source = r.cases.grammar("dyck")
        data, plan = fixture(rows=((0,),), weights=((F(1),),), emissions=(b"]",), source=source)
        for control in (r.ExactPlan, r.Interval64):
            with self.assertRaises(r.circuit.ZeroMass):
                control(plan, data.probabilities)

    def test_multibyte_aliases_pins_unary_and_epsilon(self):
        b = _SourceGrammarBuilder(("S", "T", "A", "B"), start="S")
        b.rule("S", "T")
        b.rule("T", "A", "B")
        b.rule("A", b"a", "A")
        b.rule("A")
        b.rule("B", b"b")
        data, plan = fixture(
            rows=((0, 1, 2), (0,), (3, 4)),
            weights=((F(1, 4), F(1, 8), F(1, 8)), (F(1),), (F(1, 2), F(1, 4))),
            emissions=(b"a", b"a", b"aa", b"b", b"ab"),
            source=b.build(),
            canvas=(None, 0, None),
        )
        expected = exact_cells(plan, data.probabilities)[plan.root]
        for control in (r.ExactPlan, r.Interval64):
            e = control(plan, data.probabilities)
            for seed in range(12):
                word = e.sample(Random(seed))
                raw = data.state.tokenizer_adapter.detokenize_bytes(word)
                self.assertTrue(raw.endswith(b"b") and set(raw[:-1]) <= {97})
                self.assertEqual(word[1], 0)
            if control is r.ExactPlan:
                self.assertEqual(F(e.values[plan.root], math.prod(e.scales)), expected)
            with self.assertRaises(ValueError):
                control(plan, (data.probabilities[0], (F(1, 2),), data.probabilities[2]))

    def test_exact_prefix_choice_partitions_entire_small_uniform_grid(self):
        masses = (0, 1, 2, 0, 5)
        counts = [0] * len(masses)
        for ticket in range(8):
            uniform = r.UniformPrefix(ScriptedBits([(32, ticket << 29)]))
            counts[uniform.exact(masses)] += 1
        self.assertEqual(counts, list(masses))
        for weights in ((F(1, 8), F(2, 8), F(4, 8)), (F(), F(1, 2), F(1, 4))):
            bounds = r.cdf_bounds([(float(x), float(x)) for x in weights])
            total = sum(weights)
            for prefix in (0, 1, 2**31, 2**32 - 2, 2**32 - 1):
                uniform = r.UniformPrefix(ScriptedBits([(32, prefix)]))
                side = uniform.certified(bounds)
                if side is not None:
                    self.assertGreater(weights[side], 0)
                    self.assertGreaterEqual(F(prefix, 2**32), sum(weights[:side]) / total)
                    self.assertLessEqual(F(prefix + 1, 2**32), sum(weights[: side + 1]) / total)

    def test_postprocessing_original_confidence_threshold_and_leftmost_tie(self):
        data, _ = fixture(
            rows=((0, 1),) * 3,
            weights=((F(31, 32), F(1, 32)), (F(1, 2), F(1, 2)), (F(1, 2), F(1, 2))),
        )
        confidence, mask = r.select(data, (0, 1, 0))
        self.assertEqual(confidence, (F(31, 32), F(1, 2), F(1, 2)))
        self.assertEqual(mask, (True, False, False))
        self.assertEqual(r.select(data, (1, 1, 0))[1], (False, True, False))
        data, _ = fixture(
            rows=((0,), (0, 1)), weights=((F(1),), (F(1, 2), F(1, 2))), canvas=(0, None)
        )
        self.assertEqual(r.select(data, (0, 0))[1], (False, True))

    def test_rng_resource_refusal_is_not_zero_mass_or_completion(self):
        rng = r.CountingRandom(81)
        with patch.object(r, "BIT_CAP", 2):
            rng.getrandbits(2)
            with self.assertRaises(r.numeric.RNGRefusal) as raised:
                rng.getrandbits(1)
        self.assertEqual(r.status(raised.exception), "refused_rng")
        self.assertEqual((rng.bits, rng.calls), (2, 1))
        self.assertEqual(r.status(TimeoutError()), "timeout_unresolved")
        self.assertEqual(r.status(AssertionError()), "implementation_error")

    def test_query_interfaces_with_clocks_stubbed_are_correctness_only(self):
        data, plan = fixture()
        binary, order = r.circuit.build(plan), r.reachable_order(plan)
        precisions = {
            k: r.circuit.precision_for(binary.stats["K"], control=k)
            for k in ("sr", "nearest", "moments")
        }
        for method in r.METHODS:
            with (
                patch.object(r, "perf_counter", return_value=0),
                patch.object(r, "process_time", return_value=0),
                patch.object(r, "deadline", side_effect=lambda _: nullcontext()),
            ):
                result = r.query(
                    method,
                    plan,
                    binary,
                    data,
                    order,
                    r.static_budgets(plan, order),
                    precisions,
                    r.BASE_SEED,
                )
            self.assertEqual(result["status"], "completed", result)
            self.assertEqual(result["wall_seconds"], 0)
            self.assertNotEqual(result["arithmetic_seed"], result["reconstruction_seed"])
            self.assertIn(result["word"], ((0,), (1,), (2,)))
            self.assertIsNone(result["observations"]["rss_bytes"])

    def test_runner_labels_all_trials_and_preserves_interrupts_without_measurement(self):
        data, plan = fixture()
        source, case = r.cases.grammar("binary"), r.cases.Case("binary", 1, "uniform")
        completed = dict(status="completed", word=(0,), wall_seconds=0, cpu_seconds=0)
        for failure in (None, CompilationLimit("fixture refusal"), KeyboardInterrupt()):
            with tempfile.TemporaryDirectory(prefix="a79-unit-") as temporary:
                target = Path(temporary) / "new"
                compile_error = failure if isinstance(failure, CompilationLimit) else None
                response = (
                    dict(status="interrupted")
                    if isinstance(failure, KeyboardInterrupt)
                    else dict(completed)
                )
                with (
                    patch.object(r, "source_manifest", return_value={"fixture": True}),
                    patch.object(r.cases, "cases", return_value=(case,)),
                    patch.object(r.cases, "head", return_value=(source, data)),
                    patch.object(
                        r, "compile_cfg_sampler", return_value=plan, side_effect=compile_error
                    ),
                    patch.object(r, "query", return_value=response),
                    patch.object(r, "perf_counter", return_value=0),
                    patch.object(r, "process_time", return_value=0),
                    patch.object(r, "deadline", side_effect=lambda _: nullcontext()),
                ):
                    code = r.main(["--output", str(target)])
                    with self.assertRaises(FileExistsError):
                        r.main(["--output", str(target)])
                lines = [json.loads(x) for x in (target / "rows.jsonl").read_text().splitlines()]
                ending = json.loads((target / "completion.json").read_text())
                if isinstance(failure, KeyboardInterrupt):
                    self.assertEqual(code, 130)
                    self.assertEqual(ending["state"], "interrupted")
                    self.assertEqual(lines[-1]["status"], "interrupted")
                    continue
                self.assertEqual(code, 0)
                trials = [x for x in lines if x["phase"] == "query"]
                self.assertEqual(len(trials), 80)
                for j in range(16):
                    block = trials[5 * j : 5 * j + 5]
                    self.assertEqual(
                        [x["method"] for x in block], [r.METHODS[(j + i) % 5] for i in range(5)]
                    )
                    self.assertEqual({x["seed"] for x in block}, {r.BASE_SEED + j})
                    if failure:
                        self.assertTrue(
                            all(
                                x["status"] == "compilation_resource_refusal_unresolved"
                                for x in block
                            )
                        )


if __name__ == "__main__":
    unittest.main()
