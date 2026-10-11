"""Offline reconstruction of ALL v6 observations and classical controls."""

import argparse
import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction as Q
from math import prod
from pathlib import Path

import numpy as np

from .count_source import CountSource
from .noise_features import classify, features, fit_proxy, roles
from .test_reductions import pivotal_companion

WORK = Path(__file__).resolve().parent


def pivotal_joint(labels):
    sizes = Counter(labels)
    m = len(labels)
    classes = Counter()
    for tape in itertools.product(sizes, repeat=4):
        probability = Q(
            prod(prod(range(sizes[c] - r + 1, sizes[c] + 1)) for c, r in Counter(tape).items()),
            prod(range(m - 3, m + 1)),
        )
        if not probability:
            continue
        for other, weight in pivotal_companion((0, 1, 2, 3), tape).items():
            classes[tape[0], tape[other]] += probability * weight
    joint = np.zeros((m, m))
    for i, j in itertools.permutations(range(m), 2):
        a, b = labels[i], labels[j]
        joint[i, j] = float(classes[a, b] / (sizes[a] * (sizes[b] - (a == b))))
    assert np.allclose(joint.sum(axis=0), 1 / m, atol=1e-14, rtol=1e-14)
    assert np.allclose(joint.sum(axis=1), 1 / m, atol=1e-14, rtol=1e-14)
    return joint


def geometry(gram, joint, order):
    m = len(gram)
    variance = np.trace(gram) / m - gram.mean()
    covariance = np.sum(joint * gram) - gram.mean()
    above = np.sum(order[None] > order[:, None], axis=1)
    below = np.sum(order[None] < order[:, None], axis=1)
    d = (above - below) / m**2
    rss_covariance = -(d @ gram @ d)
    return dict(
        source_variance=float(variance),
        c4_covariance=float(covariance),
        rss_covariance=float(rss_covariance),
        c4_fraction_below_iid2=float(-covariance / variance),
        retained_rss_fraction_below_iid2=float(-rss_covariance / variance),
    )


def run(capture, output):
    metadata = json.loads((capture / "metadata.json").read_text())
    rows = [json.loads(s) for s in (capture / "rows.jsonl").read_text().splitlines()]
    assert metadata["calls"] == len(rows) == 576
    assert metadata["completed"] == 6
    protocol = json.loads((WORK / "information-protocol-v6.json").read_text())
    assert (
        hashlib.sha256((WORK / "information-protocol-v6.json").read_bytes()).hexdigest()
        == metadata["protocol_sha256"]
    )
    offsets = json.loads((capture / "offsets.json").read_text())
    results = []
    for doc in json.loads((WORK / protocol["external_documents"]).read_text()):
        recorded = json.loads((capture / (doc["key"] + ".json")).read_text())
        observations = [r for r in rows if r["document"] == doc["key"]]
        assert [r["index"] for r in observations] == list(range(96))
        role = roles(doc["text"], offsets[doc["key"]])
        assert recorded["role_counts"] == [int(np.sum(role == c)) for c in range(4)]
        source = CountSource(len(doc["tokens"]))
        masks = []
        for r in observations:
            mask = source.decode(int(r["address"]))
            assert np.flatnonzero(mask).tolist() == r["mask"]
            assert r["source_size"] == str(source.size)
            assert r["phase"] == ("fit" if r["index"] < 32 else "evaluate")
            masks.append(mask)
        x = np.array([features(mask, role) for mask in masks])
        target = np.array([[r["score"], *r["projections"]] for r in observations])
        beta, centers = fit_proxy(x[:32], target[:32])
        labels = classify(x[32:, None], beta, centers).tolist()
        assert labels == recorded["labels"] == [r["label"] for r in observations[32:]]
        joint = pivotal_joint(labels)
        order = x[32:] @ beta[:, 0]
        score = target[32:, 0]
        bias_gram = np.array(recorded["evaluation_score_gram"])
        assert np.allclose(np.diag(bias_gram), [r["bias_squared_norm"] for r in observations[32:]])
        assert np.allclose(bias_gram, bias_gram.T, atol=1e-13, rtol=1e-13)
        assert np.linalg.eigvalsh(bias_gram).min() > -1e-10
        result = dict(document=doc["key"], class_sizes=recorded["score"]["class_sizes"])
        for name, gram in (("score", np.outer(score, score)), ("bias", bias_gram)):
            result[name] = geometry(gram, joint, order)
            assert abs(result[name]["c4_covariance"] - recorded[name]["covariance"]) < 1e-10
        prediction = order * target[:32].std(axis=0)[0]
        result["score"]["classical_same_proxy_cv_fraction_below_iid2"] = float(
            1 - np.var(score - prediction) / np.var(score)
        )
        result.update(
            wall=recorded["wall"],
            cpu=recorded["cpu"],
            fit_wall=sum(r["wall"] for r in observations[:32]),
            evaluation_wall=sum(r["wall"] for r in observations[32:]),
            costs_scope=(
                "Torch4 threads only; NumPy BLAS threads were not capped. Whole costs retained."
            ),
        )
        results.append(result)
        print(doc["key"][:12], result["score"], result["bias"], flush=True)
    output.write_text(
        json.dumps(
            dict(
                producer=metadata["source_commit"],
                scope=(
                    "ALL development observations; KNOWN-bank geometry, "
                    "NOT population/latency/novelty gate."
                ),
                neural_calls=metadata["calls"],
                results=results,
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.capture, args.output)
