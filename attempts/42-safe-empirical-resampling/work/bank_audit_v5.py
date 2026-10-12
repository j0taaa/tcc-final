"""All OLD known-bank geometry; no new model evaluation or victory gate."""

import argparse
import importlib
import json
from collections import Counter
from fractions import Fraction as Q
from math import comb, prod
from pathlib import Path

import numpy as np

matching = importlib.import_module("attempts.42-safe-empirical-resampling.work.matching_probe")
pivotal = importlib.import_module(
    "attempts.42-safe-empirical-resampling.work.pivotal_comparison_v5"
)
formula = importlib.import_module("attempts.42-safe-empirical-resampling.work.finite_boundary")
WORK = Path(__file__).resolve().parent


def raw_joint(labels, mode):
    classes = sorted(set(labels))
    n = [Counter(labels)[c] for c in classes]
    m = len(labels)
    sums = [sum(t**k for t in n) for k in (2, 3, 4)]
    denominator = prod(m - i for i in range(6))
    joint = [[Q(0) for _ in n] for _ in n]
    if mode == "matching":
        for i, a in enumerate(n):
            for j, b in enumerate(n):
                value = formula.diagonal(m, a) if i == j else a * b * formula.w(m, *sums, a, b)
                joint[i][j] = Q(value, denominator)
    else:
        for r in matching.pools(n, 6):
            weight = Q(prod(comb(a, b) for a, b in zip(n, r, strict=True)), comb(m, 6))
            local = pivotal.allocation_joint(tuple(Q(t, 3) for t in r))
            for i in range(len(n)):
                for j in range(len(n)):
                    joint[i][j] += weight * local[i][j]
    assert all(sum(row) == Q(t, m) for row, t in zip(joint, n, strict=True))
    raw = [[Q(0) for _ in labels] for _ in labels]
    for i, a in enumerate(labels):
        for j, b in enumerate(labels):
            if i != j:
                s, t = classes.index(a), classes.index(b)
                raw[i][j] = joint[s][t] / (n[s] * (n[t] - (s == t)))
    assert all(sum(row) == Q(1, m) for row in raw)
    return np.array(raw, dtype=float)


def run(output):
    capture = WORK / "inputs-v5"
    controls = json.loads((capture / "information-audit-v7.json").read_text())["results"]
    results = []
    for previous in controls:
        recorded = json.loads((capture / (previous["document"] + ".json")).read_text())
        candidate = raw_joint(recorded["labels"], "matching")
        classic = raw_joint(recorded["labels"], "pivotal")
        row = dict(document=previous["document"], old_controls=previous)
        for name, gram in (
            ("score", np.outer(recorded["score_values"], recorded["score_values"])),
            ("bias", np.array(recorded["evaluation_score_gram"])),
        ):
            variance = np.trace(gram) / len(gram) - gram.mean()
            assert abs(variance - previous[name]["source_variance"]) < 1e-10
            row[name] = {
                method: float((gram.mean() - np.sum(joint * gram)) / variance)
                for method, joint in (("matching6", candidate), ("pivotal6", classic))
            }
            assert row[name]["matching6"] >= -1e-10
        results.append(row)
        print(previous["document"][:12], row["score"], row["bias"], flush=True)
    assert len(results) == 6
    output.write_text(
        json.dumps(
            dict(
                scope="OLD known-bank geometry only; no population, timing or neural gate",
                new_neural_calls=0,
                results=results,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
