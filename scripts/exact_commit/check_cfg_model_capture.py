"""Opt-in independent full-logit check for every fresh M34 JSON capture."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from fractions import Fraction
from pathlib import Path


def main():
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (args.capture / "rows.jsonl").read_text().splitlines()]
    profile = json.loads((args.capture / "config.json").read_text())["fresh_model_demonstration"]
    expected_names = {
        f"json-context{context}-{slots}"
        for context in range(len(profile["prefix_suffix"]))
        for slots in profile["slots"]
    }
    if {row["case"] for row in rows} != expected_names or len(rows) != len(expected_names):
        raise ValueError("incomplete/duplicate capture cohort")
    for row in rows:
        path = args.capture / f"{row['case']}.npz"
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["source_array_sha256"]:
            raise ValueError("changed full-logit source")
        with np.load(path, allow_pickle=False) as arrays:
            logits, probability = arrays["logits"].astype(np.float64), arrays["probabilities"]
        logits[:, 50257] = -np.inf
        logits -= logits.max(axis=1, keepdims=True)
        expected = np.exp(logits)
        expected /= expected.sum(axis=1, keepdims=True)
        if not np.allclose(probability, expected, rtol=2e-14, atol=0):
            raise ValueError("non-mask full softmax mismatch")
        with gzip.open(args.capture / f"{row['case']}-input.json.gz", "rt") as stream:
            raw = json.load(stream)
        if raw["source_array_sha256"] != row["source_array_sha256"]:
            raise ValueError("input source hash mismatch")
        state = raw["input"]["selection"]
        free = [i for i, token in enumerate(state["canvas"]) if token is None]
        if probability.shape != (len(free), 50258):
            raise ValueError("original vocabulary/slot shape mismatch")
        for offset, position in enumerate(free):
            full = tuple(Fraction(float(p)) for p in probability[offset])
            total = sum(full, Fraction())
            support = state["support"]["rows"][position]
            top = np.argsort(-logits[offset], kind="stable")[: profile["top_k"]]
            if (
                total != Fraction(*raw["normalization"][offset])
                or sorted(top) != support
                or tuple(full[t] / total for t in support)
                != tuple(Fraction(*p) for p in raw["probabilities"][position])
            ):
                raise ValueError("original full-normalization/top-K unary mismatch")
    print(
        json.dumps(
            {
                "verification": "PASS",
                "full_logit_cases": len(rows),
                "scope": "source hashes, full non-mask softmax, rational normalization "
                "and original top-K",
            }
        )
    )


if __name__ == "__main__":
    main()
