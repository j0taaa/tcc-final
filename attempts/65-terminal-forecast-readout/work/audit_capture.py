"""Independent retained-bit/BPE/Fraction audit, no model or neural call."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path

import numpy as np


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def digest(array, dtype, shape):
    return hashlib.sha256(f"torch.{dtype}:{shape}:".encode() + array.tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--model-metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    root = Path(__file__).parent
    summary = json.loads((args.capture / "summary.json").read_text())
    pre = json.loads((root / "evidence/v8-tokenizer/summary.json").read_text())
    inputs = json.loads((root / "inputs-v6.json").read_text())["selected"]
    byte_values = [*range(33, 127), *range(161, 173), *range(174, 256)]
    characters = byte_values[:]
    extra = 0
    for b in range(256):
        if b not in byte_values:
            byte_values.append(b)
            characters.append(256 + extra)
            extra += 1
    inverse = {chr(c): b for c, b in zip(characters, byte_values, strict=True)}
    vocab = json.loads((args.model_metadata / "vocab.json").read_text())
    added = json.loads((args.model_metadata / "added_tokens.json").read_text())
    emissions = {token: bytes(inverse[c] for c in text) for text, token in vocab.items()}
    emissions.update({token: text.encode() for text, token in added.items()})

    def raw_value(ids, labels):
        assert 151645 in ids
        stop = ids.index(151645)
        assert all(t == 151643 for t in ids[stop + 1 :])
        body = b"".join(emissions[t] for t in ids[:stop])
        obj = json.loads(body, parse_float=F, parse_int=F)
        assert set(obj) == {"probabilities"} and set(obj["probabilities"]) == set(labels)
        raw = tuple(obj["probabilities"][label] for label in labels)
        assert all(0 <= v <= 1 for v in raw)
        return raw

    def norm(raw):
        total = sum(raw)
        return tuple(v / total for v in raw) if total else (F(1, len(raw)),) * len(raw)

    assert summary["status"] == "NECESSITY_GATE_NEGATIVE"
    assert summary["forward_attempts"] == summary["forward_completions"] == 129
    assert len(summary["rows"]) == 8
    head_count = helper_count = mean_count = json_count = 0
    all_ordinals = []
    warmup = summary["warmup"][0]
    with np.load(args.capture / warmup["head_packet"]) as packet:
        assert packet["response_logits_bf16"].shape == (64, 151936)
        assert packet["input_ids"][0].tolist() == pre["rows"][0]["prompt_ids"] + [151669] * 64
        head_count += 1
        all_ordinals.append(warmup["ordinal"])
    for i, row in enumerate(summary["rows"]):
        assert row["status"] == "COMPLETE" and row["original_complete"]
        labels = inputs[i]["input"]["labels"]
        original = row["original_ids"]
        raw = raw_value(original, labels)
        assert raw == tuple(map(F, row["original_raw"]))
        json_count += 1
        prior = None
        assert len(row["forward_trace"]) == 16
        for j, call in enumerate(row["forward_trace"]):
            all_ordinals.append(call["ordinal"])
            assert call["rng_before"] == call["rng_after"]
            with np.load(args.capture / call["head_packet"]) as packet:
                ids, bits = packet["input_ids"], packet["response_logits_bf16"]
                assert ids[0, :-64].tolist() == pre["rows"][i]["prompt_ids"]
                body = ids[0, -64:]
                assert int(np.sum(body == 151669)) == 64 - 4 * j
                if prior is not None:
                    assert np.array_equal(body[prior != 151669], prior[prior != 151669])
                prior = body.copy()
                assert bits.dtype == np.uint16 and bits.shape == (64, 151936)
                assert digest(bits, "bfloat16", (1, 64, 151936)) == call["response_head_sha256"]
                head_count += 1
                if j == 15:
                    with np.load(args.capture / f"terminal-{i:02d}.npz") as terminal:
                        expanded = (bits.astype(np.uint32) << 16).view(np.float32)
                        assert np.array_equal(terminal["scores_float32"][0], expanded)
                        assert np.isfinite(expanded).all()
                        assert (
                            digest(terminal["scores_float32"], "float32", (1, 64, 151936))
                            == row["captured_sampler_scores_sha256"]
                        )
                        pins = terminal["tokens"][0]
                        assert np.array_equal(pins, np.where(body == 151669, -1, body))
                        assert np.array_equal(np.asarray(original)[pins >= 0], pins[pins >= 0])
        for readout in row["readouts"]:
            points = [norm(raw)]
            assert readout["original_ids"] == original
            helper_count += readout["helpers_called"]
            assert readout["helpers_called"] == len(readout["samples"])
            for sample in readout["samples"]:
                value = raw_value(sample["ids"], labels)
                assert value == tuple(map(F, sample["raw"]))
                points.append(norm(value))
                json_count += 1
            mean = tuple(
                sum(point[j] for point in points) / len(points) for j in range(len(labels))
            )
            assert mean == tuple(map(F, readout["mean"]))
            rendered = json.loads(readout["rendered"], parse_float=F)["probabilities"]
            assert sum(rendered.values()) == 1
            assert all(
                abs(rendered[label] - mean[j]) < F(1, 10**8) for j, label in enumerate(labels)
            )
            mean_count += 1
        alpha = row["alpha_for_binomial_formula"]
        factor = sum(
            math.comb(7, m) * alpha**m * (1 - alpha) ** (7 - m) / (m + 1) for m in range(8)
        )
        expected = row["control"]["variance"] * (1 - factor)
        assert abs(expected - row["ideal_n7_removed_risk"]) < 1e-12
    assert all_ordinals == list(range(129)) and head_count == 129
    assert helper_count == 64 and mean_count == 24 and json_count == 72
    magnitude = sum(r["ideal_n7_removed_risk"] >= 0.005 for r in summary["rows"])
    assert magnitude == summary["sufficient_ideal_variance_cases"] == 1
    result = {
        "status": "PASS",
        "scientific_decision": "NECESSITY_GATE_NEGATIVE_UNCHANGED",
        "heads_verified": head_count,
        "terminal_BF16_expansions_verified": 8,
        "valid_originals": 8,
        "independent_byte_BPE_JSON_outputs": json_count,
        "exact_means_recomputed": mean_count,
        "helper_calls_charged": helper_count,
        "sufficient_magnitude_cases": magnitude,
        "required_magnitude_cases": 4,
        "new_neural_forwards_in_audit": 0,
        "files": [
            {"file": f.name, "bytes": f.stat().st_size, "sha256": sha(f)}
            for f in sorted(args.capture.iterdir())
            if f.is_file()
        ],
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "files"}))


if __name__ == "__main__":
    main()
