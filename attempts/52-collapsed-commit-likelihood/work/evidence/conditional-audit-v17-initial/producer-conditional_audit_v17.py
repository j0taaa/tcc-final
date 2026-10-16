"""AFTER-data independent scalar score/tokenizer audit, zero model calls."""

import argparse
import json
import math
from decimal import Decimal
from pathlib import Path

import numpy as np

from .consumer_resource import write_json
from .llada_tokenizer_v10 import EOS


def actor_scalar(score, extent, fixed, confidence_max_logs):
    a, r, b = score["alpha"], score["anchor"], score["beta"]
    x = [(2 * i + 1) / 64 - 1 for i in range(extent)]
    h = [confidence_max_logs[i] / 10 if i not in fixed else 0.0 for i in range(extent)]
    m = (extent - len(fixed)) / 64
    return [
        sum(a),
        sum(x[i] * a[i] for i in range(extent)),
        sum(h[i] * a[i] for i in range(extent)),
        m * sum(a),
        float(EOS in fixed.values()) * sum(a),
        sum(x[i] * r[i] for i in range(extent)),
        sum(h[i] * r[i] for i in range(extent)),
        m * sum(x[i] * r[i] for i in range(extent)),
        b,
    ]


def run(capture, analysis, auxiliary, model_dir):
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    rows = [json.loads(s) for s in (capture / "rows.jsonl").read_text().splitlines()]
    data = [json.loads(s) for s in (auxiliary / "records.jsonl").read_text().splitlines()]
    labels = json.loads((analysis / "known-labels-provenance.json").read_text())["labels"]
    summary = json.loads((auxiliary / "summary.json").read_text())
    assert len(data) == 560 and summary["status"] == "PASS"
    assert (
        summary["new_model_forwards"]
        == summary["updates"]
        == summary["new_decoder_trajectories"]
        == 0
    )
    assert summary["global_Python_NumPy_RNG_unchanged"] and not summary["CUDA_used"]
    assert summary["peak_CPU_process_RSS_bytes"] <= 2 * 1024**3
    maximal, coordinates, verifiers, states = 0.0, 0, 0, 0
    seen = set()

    def compare(a, b):
        nonlocal maximal, coordinates
        a, b = np.asarray(a), np.asarray(b)
        assert a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
        delta = float(np.max(np.abs(a - b)))
        maximal = max(maximal, delta)
        coordinates += a.size
        assert delta <= 1e-10

    for row in rows:
        for transition in row["transitions"]:
            fixed, retained = dict(transition["fixed_before"]), dict(transition["action"])
            extent = transition["prefix_extent"]
            packet = np.load(capture / "heads" / (transition["head"] + ".npz"))
            bits, positions = packet["logits_bf16"], packet["positions"].tolist()
            logits = (bits.astype(np.uint32) << 16).view(np.float32).astype(np.float64)
            logits -= logits.max(axis=1, keepdims=True)
            logden = np.log(np.exp(logits).sum(axis=1))
            lookup = {i: j for j, i in enumerate(positions)}
            max_logs = {i: -float(logden[j]) for i, j in lookup.items()}

            def token_log(i, v):
                return float(logits[lookup[i], v] - logden[lookup[i]])

            def gate(i, v):
                z = row["root_feature"] + token_log(i, v) - math.log(0.01)
                return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))

            terms = {i: 1 / gate(i, v) for i, v in retained.items()}
            total = sum(terms.values())
            rho = {i: p / total for i, p in terms.items()}
            subset = [
                r
                for r in data
                if (r["case"], r["replica"], r["step"])
                == (row["case"], row["replica"], transition["step"])
            ]
            assert len(subset) == 8
            assert {(r["method"], r["auxiliary_index"]) for r in subset} == {
                (m, j) for m in ("iid", "prefix_stratified") for j in range(4)
            }
            for record in subset:
                assert record["status"] == "PASS" and record["head"] == transition["head"]
                word, anchor = record["word"], record["anchor"]
                assert word[-1] == EOS and EOS not in word[:-1]
                assert all(
                    i < len(word) and word[i] == v for i, v in (*fixed.items(), *retained.items())
                )
                assert anchor in retained and record["word"][anchor] == retained[anchor]
                decoded = tokenizer.decode(
                    [12657, 31113, 2275, *word[:-1]], skip_special_tokens=False
                )
                assert decoded == record["json"]
                numeric = json.loads(decoded, parse_int=Decimal, parse_float=Decimal)
                assert set(numeric) == {"answer"}
                assert (numeric["answer"] == Decimal(labels[row["case"]]["answer"])) == record[
                    "semantic_correct_proposal"
                ]
                assert record["secondary_Decimal_representable"]
                active = [i for i in range(len(word)) if i not in fixed]
                for name in ("full_triple", "anchor_integrated"):
                    aa, rr, bb = [0.0] * 64, [0.0] * 64, 0.0
                    for i in active:
                        g = gate(i, word[i])
                        nonanchor = (
                            float(i != anchor) if name == "full_triple" else 1 - rho.get(i, 0.0)
                        )
                        aa[i] = nonanchor * (float(i in retained) - g)
                        bb += aa[i] * token_log(i, word[i])
                        rr[i] = (
                            float(i == anchor) if name == "full_triple" else rho.get(i, 0.0)
                        ) - 1 / len(active)
                    score = {"alpha": aa, "beta": bb, "anchor": rr}
                    for key in score:
                        compare(score[key], record["scores"][name][key])
                    compare(
                        actor_scalar(score, extent, fixed, max_logs), record["actor_scores"][name]
                    )
                for scores in (record["scores"], record["actor_scores"]):
                    assert len(scores) == 7
                key = (
                    record["case"],
                    record["replica"],
                    record["step"],
                    record["method"],
                    record["auxiliary_index"],
                )
                assert key not in seen
                seen.add(key)
                verifiers += 1
            states += 1
    assert states == 70 and verifiers == 560
    result = {
        "status": "PASS",
        "scope": "AFTER-data consistency, not a variance/cost evaluation",
        "states": states,
        "official_tokenizer_Decimal_answers": verifiers,
        "independent_full_and_anchor_score_coordinates": coordinates,
        "maximum_absolute_difference": maximal,
        "new_model_forwards": 0,
        "updates": 0,
        "new_auxiliary_words": 0,
    }
    write_json(auxiliary / "post-capture-independent-audit.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("capture", "analysis", "auxiliary", "model-dir"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.capture, a.analysis, a.auxiliary, a.model_dir)
