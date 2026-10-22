"""Independent CPU checks before A88's first neural call; run directly."""

from __future__ import annotations

import itertools
import json
import unittest

import analyze_v1 as analysis
import native_v1 as native
import numpy as np
import torch


def fixture(tail=0.2):
    result = []
    for t, (a5, a, w) in enumerate(
        (([0.9, 0, 0, 0, 0], 0.9, 1.0), ([tail, 1 - tail, 0, 0, 0], 1.0, 0.1))
    ):
        result.append(
            {
                "step": t,
                "a5": a5,
                "A": a,
                "W_before": w,
                "W_after": w * (1 - a),
                "state_hash": str(t),
                "profile": {
                    k: 1.0
                    for k in (
                        "model_seconds",
                        "categorical_seconds",
                        "free_rng_seconds",
                        "rank_seconds",
                        "state_seconds",
                        "cache_seconds",
                        "canvas_seconds",
                        "a5_seconds",
                        "update_seconds",
                        "f_rng_seconds",
                        "token_output_seconds",
                        "vector_output_seconds",
                    )
                },
            }
        )
    return result


class Checks(unittest.TestCase):
    def test_cdf_zero_plateaus_and_boundaries(self):
        q = torch.tensor([[0, 0.25, 0, 0.75, 0]] * 4, dtype=torch.float64)
        uniforms = torch.tensor([0.0, 0.25 - 1e-12, 0.25, 1 - 1e-12], dtype=torch.float64)
        self.assertEqual(native.select_ids(q.cumsum(-1), uniforms).tolist(), [1, 1, 3, 3])
        with self.assertRaises(ValueError):
            native.select_ids(q[:1].cumsum(-1), torch.tensor([1.0], dtype=torch.float64))

    def test_ties_both_physical_orders(self):
        scores = torch.tensor([0.5, 0.7, 0.5, 0.5], dtype=torch.float64)
        self.assertEqual(native.stable_free_order(scores, [2, 4, 7, 10]).tolist(), [1, 0, 2, 3])
        # Equal cutoff goes to the smaller ORIGINAL position, including f.
        for f, expected in ((1, True), (9, False)):
            self.assertEqual((0.5, -f) > (0.5, -7), expected)

    def test_partial_moments_independent_hit_enumeration(self):
        for tail in (0.2, 0.8):
            rows = fixture(tail)
            y = np.array([0.9 + 0.1 * tail, 0.1 * (1 - tail), 0, 0, 0])
            events = [(1.0, 0.0, 0.0, 0.0, 0.0), (tail, 1 - tail, 0.0, 0.0, 0.0)]
            expected_delta = sum(
                p * np.sum((np.array(r) - y) ** 2) for p, r in zip((0.9, 0.1), events, strict=True)
            )
            for name in analysis.VARIANTS:
                value = analysis.path_moments(rows, name)
                np.testing.assert_allclose(value["Y"], y, atol=1e-14)
                expected = 1 - y @ y if name == "MC" else (expected_delta if name == "d0" else 0.0)
                self.assertAlmostEqual(value["delta"], expected, places=13)
            np.testing.assert_allclose(analysis.path_moments(rows, "d0")["visits"], [1, 0.1])
            np.testing.assert_allclose(analysis.path_moments(rows, "full")["visits"], [1, 1])

    def test_cost_product_distinct_replicas(self):
        # Exhaustive IID population, Y and C correlated. Ordinary Vhat*Cbar is biased.
        population = [(np.array([0.1, 0.9]), 0.1, 1.0), (np.array([0.8, 0.2]), 0.3, 4.0)]
        observed = []
        for draw in itertools.product(range(2), repeat=3):
            ys, delta, costs = zip(*(population[i] for i in draw), strict=True)
            observed.append(
                analysis.unbiased_iid_product(np.array(ys), np.array(delta), np.array(costs))
            )
        true_variance = 0.245 + 0.2
        self.assertAlmostEqual(np.mean(observed), true_variance * 2.5, places=13)

    def test_global_cache_independent_visits(self):
        rows = fixture()
        value = analysis.evaluate([rows, rows, rows], "d0", 0)
        # Root certain once; tail independent .1 for each of three replicas => union .271.
        self.assertAlmostEqual(value["expected_unique_model_queries_block"], 1.271)

    def test_prepared_inputs_against_source_and_tokenizer(self):
        if not native.INPUTS.exists():
            self.skipTest("run --prepare before final pre-freeze verification")
        import pyarrow.parquet as pq
        from transformers import AutoTokenizer

        data = json.loads(native.INPUTS.read_text())
        native.validate_inputs(data)
        source = native.SOURCES / "dev.parquet"
        self.assertEqual(native.file_sha(source), data["dataset"]["sha256"])
        rows = pq.read_table(source).to_pylist()
        tokenizer = AutoTokenizer.from_pretrained(
            native.MODEL, local_files_only=True, trust_remote_code=True
        )
        # A separate membership check for EVERY original ID (not only the aliases).
        for token, group in enumerate(data["groups"]):
            emitted = tokenizer.decode(
                [token], skip_special_tokens=False, clean_up_tokenization_spaces=False
            )
            expected = next((g for g, letter in enumerate("ABCD") if emitted.strip() == letter), 4)
            self.assertEqual(group, expected)
        for case in data["cases"]:
            row = rows[case["row"]]
            for field in ("question", "choices", "answer", "subject"):
                self.assertEqual(case[field], row[field])
            ids = tokenizer.apply_chat_template(
                [{"role": "user", "content": case["prompt"]}],
                add_generation_prompt=True,
                tokenize=True,
            )
            self.assertEqual(case["input_ids"][: case["offset"]], ids)
            self.assertEqual(len(case["eligible"]), 32)
            self.assertEqual(case["input_ids"][case["observed"]], native.MASK)
            self.assertEqual(case["input_ids"][-1], native.EOT)
        self.assertEqual(data["model_files"], native.model_hashes())


if __name__ == "__main__":
    torch.set_num_threads(4)
    unittest.main(verbosity=2)
