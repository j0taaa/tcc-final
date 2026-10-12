"""Direct RSS source-product oracle for full-vector audit bookkeeping."""

import argparse
import json
from itertools import product
from pathlib import Path

import numpy as np
import torch

from .full_gradient import geometry


def run(output):
    checks = 0
    rng = np.random.default_rng(202610120440)
    for labels in ([0, 1, 2, 2, 0], [0, 0, 1, 1, 1], [2] * 5):
        g = rng.normal(size=(5, 7))
        h = np.array([0.0, 1.0, 0.0, 4.0, -2.0])
        n = len(h)
        weights = [(np.sum(h > v) - np.sum(h < v)) / n**2 for v in h]
        sums = np.zeros((5, g.shape[1]))
        for i in range(n):
            sums[labels[i]] += g[i]
            sums[3] += weights[i] * g[i]
            sums[4] += (h[i] - h.mean()) / n * g[i]
        observed = geometry(
            [torch.tensor(sums)], np.bincount(labels, minlength=3), np.sum(g**2), n, np.var(h)
        )
        mean = g.mean(0)
        variance = np.mean(np.sum((g - mean) ** 2, axis=1))
        np.testing.assert_allclose(observed["pair_trace"]["iid2"], variance / 2, atol=1e-12)
        rss = 0.0
        for a, b, c, d in product(range(n), repeat=4):
            low = [i for i in (a, b) if h[i] == min(h[a], h[b])]
            high = [i for i in (c, d) if h[i] == max(h[c], h[d])]
            for i, j in product(low, high):
                rss += np.sum(((g[i] + g[j]) / 2 - mean) ** 2) / (n**4 * len(low) * len(high))
        np.testing.assert_allclose(observed["pair_trace"]["continuous_rss"], rss, atol=1e-12)
        centered = h - h.mean()
        coefficient = centered @ g / (centered @ centered)
        residual = g - centered[:, None] * coefficient
        expected_cv = np.mean(np.sum((residual - residual.mean(0)) ** 2, axis=1)) / 2
        np.testing.assert_allclose(
            observed["pair_trace"]["oracle_scalar_cv"], expected_cv, atol=1e-12
        )
        checks += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "source_product_families": checks,
                "RSS_tapes_each": 625,
                "scope": "Independent bookkeeping oracle; no neural/benchmark evidence.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
