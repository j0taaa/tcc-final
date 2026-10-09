"""Independent offline population moments from captured token/feature Grams.

No model, PyTorch, CFG normalizer or forward is used. Source provenance of the
Grams still requires the pinned opt-in neural capture, not this verification.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import defaultdict
from fractions import Fraction as Q
from pathlib import Path

import numpy as np

from mwpc_exact.conflict_proof import read_state


def verify(folder):
    metadata = json.loads((folder / "metadata.json").read_text())
    rows = [json.loads(s) for s in (folder / "rows.jsonl").read_text().splitlines()]
    verified = []
    for case in metadata["selected"]:
        raw = json.loads((folder / f"{case['key']}-input.json").read_text())
        state = read_state(raw["input"])
        free = tuple(i for i, t in enumerate(state.canvas) if t is None)
        probabilities = tuple(tuple(Q(*q) for q in row) for row in raw["probabilities"])
        vocabulary = sorted(set(t for i in free for t in state.support.rows[i]))
        index = {t: j for j, t in enumerate(vocabulary)}
        u = len(vocabulary)
        d = u + len(free)
        q = np.array(raw["q_selected"])
        token_gram = np.eye(d)
        token_gram[:u, u:] = q.T
        token_gram[u:, :u] = q
        token_gram[u:, u:] = raw["q_gram"]
        metric = np.kron(np.array(raw["head_feature_gram"]), token_gram)
        paths = []
        weights = []
        for choices in itertools.product(*(state.support.rows[i] for i in free)):
            path = list(case["tokens"])
            for i, t in zip(free, choices, strict=True):
                path[i] = t
            try:
                json.loads(
                    state.tokenizer_adapter.detokenize_bytes(path).decode(),
                    parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)),
                )
            except (ValueError, UnicodeDecodeError):
                continue
            weights.append(
                math.prod(probabilities[i][state.support.rows[i].index(path[i])] for i in free)
            )
            paths.append(path)
        z = sum(weights, Q())
        weights = [w / z for w in weights]
        marginal = np.zeros((len(free), d))
        for path, w in zip(paths, weights, strict=True):
            for j, i in enumerate(free):
                marginal[j, index[path[i]]] += float(w)
        for power in (1, 2):
            mean = np.zeros(len(free) * d)
            second = 0.0
            groups = defaultdict(list)
            for order in itertools.permutations(range(len(free)), 2):
                for path, w in zip(paths, weights, strict=True):
                    y = [path[i] for i in free]
                    rates = [
                        probabilities[i][state.support.rows[i].index(path[i])] ** power
                        for i in free
                    ]
                    selected = set()
                    inverse = [Q() for _ in free]
                    prob = w
                    for chosen in order:
                        denominator = sum(r for j, r in enumerate(rates) if j not in selected)
                        prob *= rates[chosen] / denominator
                        for j in range(len(free)):
                            if j not in selected:
                                inverse[j] += 1 / denominator
                        selected.add(chosen)
                    reward = sum(y[j] == case["tokens"][free[j]] for j in order) / 2
                    coeff = -marginal.copy()
                    for j, t in enumerate(y):
                        b = power * (int(j in order) - float(rates[j] * inverse[j]))
                        coeff[j, index[t]] += 1 + b
                        coeff[j, u + j] -= b
                    coeff = (reward * coeff).flatten()
                    mass = float(prob)
                    mean += mass * coeff
                    second += mass * (coeff @ metric @ coeff)
                    groups[(order, tuple(y[j] for j in order))].append((mass, coeff))
            norm = mean @ metric @ mean
            observed = 0.0
            for entries in groups.values():
                mass = sum(w for w, _ in entries)
                conditional = sum(w * c for w, c in entries) / mass
                observed += mass * (conditional @ metric @ conditional)
            expected = {
                "original": second - norm,
                "conditional_mean": observed - norm,
                "two_iid": (second + observed) / 2 - norm,
            }
            recorded = next(
                r
                for r in rows
                if r["stage"] == "variance" and r["case"] == case["key"] and r["power"] == power
            )
            errors = {
                name: abs(value - recorded["variances"][name]) / max(1, abs(value))
                for name, value in expected.items()
            }
            assert max(errors.values()) < 1e-7
            verified.append(
                dict(
                    case=case["key"],
                    power=power,
                    errors=errors,
                    events=sum(len(g) for g in groups.values()),
                )
            )
    return dict(
        scope="offline independent moments, not independent checkpoint provenance",
        verified=verified,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.evidence)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                verified=len(result["verified"]),
                max_relative_error=max(max(r["errors"].values()) for r in result["verified"]),
            )
        )
    )
