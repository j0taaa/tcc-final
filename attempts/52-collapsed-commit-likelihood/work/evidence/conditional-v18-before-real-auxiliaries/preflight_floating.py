"""Opt-in finite floating checks against the independent rational anchor law."""

import argparse
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np

from .anchor import AnchorPolicy
from .floating import FloatPlan, TorchPlan
from .numeric_json import NumericJSON


def cases():
    emissions = (
        b'{"answer":',
        b"0",
        b"1",
        b"-2.0e3",
        b"}",
        b'{"answer":0}',
        b'{"answer":0}',
        b" ",
        b"",
        b"",
        b"<EOT>",
        b"<PAD>",
    )
    language, rng = NumericJSON(emissions, 10, 11), np.random.default_rng(520401)
    plan = FloatPlan(language)
    result = []
    for n in (2, 3, 4, 5):
        raw = rng.integers(1, 12, size=(n, len(emissions)))
        exact = tuple(tuple(F(int(w), int(row.sum())) for w in row) for row in raw)
        weights = np.asarray([[float(w) for w in row] for row in exact])
        gates = tuple(tuple(c / (c + F(1, 100)) for c in row) for row in exact)
        rational = AnchorPolicy(
            language.small_reference_graph(n), exact, gates, (F(1, n),) * n, tuple(range(n))
        )
        for draw in range(4):
            word = plan.sample(weights, rng)
            anchor = int(rng.integers(n))
            action = tuple(
                (i, v)
                for i, v in enumerate(word)
                if i == anchor
                or draw == 0
                or (draw == 2 and i % 2 == 0)
                or (draw == 3 and rng.random() < float(gates[i][v]))
            )
            probability, _, hh, rr = rational.action_statistics(action)
            expected = {
                "log_probability": float(np.log(float(probability))),
                "alpha": np.asarray([float(sum(row, F())) for row in hh]),
                "beta": sum(
                    float(hh[i][v]) * np.log(float(exact[i][v]))
                    for i in range(n)
                    for v in range(len(emissions))
                ),
                "anchor": np.asarray([float(r) for r in rr]),
            }
            result.append((plan, weights, word, action, expected))
    return result


def compare(actual, expected):
    errors = {}
    for name in ("log_probability", "alpha", "beta", "anchor"):
        a, b = np.asarray(actual[name]), np.asarray(expected[name])
        if not np.isfinite(a).all():
            raise AssertionError(f"nonfinite {name}")
        errors[name] = float(np.max(np.abs(a - b)))
        if not np.allclose(a, b, atol=1e-10, rtol=1e-7):
            raise AssertionError(f"floating {name} mismatch: {errors[name]}")
    return errors


def run(output):
    import torch

    output.mkdir(parents=True, exist_ok=False)
    rows = []
    items = cases()
    for case, (plan, weights, word, action, expected) in enumerate(items):
        for device in ("numpy", "cpu", "cuda"):
            if device == "numpy":
                actual = plan.action_statistics(weights, action)
            else:
                backend = TorchPlan(plan, device)
                actual = backend.action_statistics(torch.as_tensor(weights, device=device), action)
            errors = compare(actual, expected)
            if not plan.language.accepts(word):
                raise AssertionError("non-accepting original word")
            rows.append(
                {
                    "case": case,
                    "device": device,
                    "word": word,
                    "action": action,
                    "length": len(word),
                    "errors": errors,
                }
            )
    report = {
        "records": len(rows),
        "cases": len(items),
        "status": "PASS",
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(),
        "new_model_forwards": 0,
        "native_rng_exactness_claimed": False,
        "max_error": {name: max(r["errors"][name] for r in rows) for name in rows[0]["errors"]},
    }
    (output / "rows.json").write_text(json.dumps(rows, indent=2) + "\n")
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    run(ap.parse_args().output)
