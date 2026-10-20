"""A76 frozen offline gate. No clocks, model loading, RNG, or CUDA calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from itertools import pairwise, product
from pathlib import Path

from mwpc_exact.tokenizer_bytes import byte_level_piece_to_bytes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
LLADA = Path.home() / (
    ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct/"
    "snapshots/08b83a6feb34df1a6011b80c3c00c7563e963b07"
)
QWEN = Path("/home/jota/projects/tcc-final/.cache/a52-model-metadata")
OPEN = b"([{"
CLOSE = b")]}"
MATCH = dict(zip(CLOSE, OPEN, strict=True))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def effect(raw):
    pop, push = [], []
    for c in raw:
        if c in OPEN:
            push.append(c)
        elif c in CLOSE:
            if push:
                if push.pop() != MATCH[c]:
                    return None
            else:
                pop.append(MATCH[c])
    return tuple(pop), tuple(push)


def raw_apply(raw, context=()):
    """Independent recognizer: compare byte characters, without normalization."""
    stack = list(bytes(context).decode("ascii"))
    pairs = {")": "(", "]": "[", "}": "{"}
    for c in raw.decode("ascii", errors="replace"):
        if c in "([{":
            stack.append(c)
        elif c in ")]}":
            if not stack or pairs[c] != stack.pop():
                return None
    return tuple(ord(c) for c in stack)


def effect_apply(normal, context):
    if normal is None:
        return None
    pop, push = normal
    stack = list(context)
    for c in pop:
        if not stack or stack.pop() != c:
            return None
    return tuple(stack) + push


def normalization_check():
    contexts = [c for n in range(3) for c in product(OPEN, repeat=n)]
    words = comparisons = 0
    for n in range(6):
        for w in product(b"()[]{}x", repeat=n):
            raw = bytes(w)
            normal = effect(raw)
            words += 1
            for c in contexts:
                assert raw_apply(raw, c) == effect_apply(normal, c), (raw, c)
                comparisons += 1
    assert effect(b"[](") == effect(b"{}(") == effect(b"(")
    assert effect(b"([)]") is None
    return {"words": words, "contexts": len(contexts), "comparisons": comparisons}


def extension_check():
    """Test the brief's claimed direct sum against explicit path bases."""
    systems = comparisons = counterexamples = 0
    first = None
    for m in range(6):
        for r in range(m + 1):
            for tail in product(range(r + 1), repeat=m):
                lower = (0, *tail)
                if any(lower[j] > min(j, r) for j in range(m + 1)):
                    continue
                if any(a > b for a, b in pairwise(lower)):
                    continue
                bases = [
                    frozenset(i for i, v in enumerate(x) if v)
                    for x in product((0, 1), repeat=m)
                    if sum(x) == r and all(sum(x[:j]) >= lower[j] for j in range(m + 1))
                ]
                assert bases
                systems += 1
                for assignment in product((0, 1, 2), repeat=m):
                    included = frozenset(i for i, v in enumerate(assignment) if v == 1)
                    excluded = frozenset(i for i, v in enumerate(assignment) if v == 2)
                    individual = any(included <= b for b in bases) and any(
                        not excluded & b for b in bases
                    )
                    simultaneous = any(included <= b and not excluded & b for b in bases)
                    comparisons += 1
                    if individual != simultaneous:
                        counterexamples += 1
                        if first is None:
                            first = {
                                "m": m,
                                "r": r,
                                "L": lower,
                                "I": sorted(included),
                                "Z": sorted(excluded),
                                "bases": [sorted(b) for b in bases],
                                "individual": individual,
                                "simultaneous": simultaneous,
                            }
    return {
        "systems": systems,
        "comparisons": comparisons,
        "counterexamples": counterexamples,
        "first_counterexample": first,
        "status": "FAIL" if counterexamples else "PASS_FINITE_ONLY",
    }


def value_profile(words, proposal, weights):
    values = [0] * (len(proposal) + 1)
    for word in words:
        matched = sorted(
            (weights[i] for i, token in enumerate(word) if token == proposal[i]), reverse=True
        )
        for cap in range(len(values)):
            values[cap] = max(values[cap], sum(matched[:cap]))
    return values


def maxplus(a, b):
    return [
        max(a[j] + b[cap - j] for j in range(len(a)) if 0 <= cap - j < len(b))
        for cap in range(len(a) + len(b) - 1)
    ]


def gadget_check():
    # ID = the original ASCII byte in this declared synthetic tokenizer.
    supports = [b"([", b"()", b"()", b")]"]
    words = [w for w in product(*supports) if raw_apply(bytes(w)) == ()]
    assert {bytes(w) for w in words} == {b"(())", b"()()", b"[()]"}
    proposal, weights = b"(((]", (1, 30, 40, 30)
    selected = []
    for i in sorted(range(4), key=lambda i: (-weights[i], i)):
        test = [*selected, i]
        if any(all(w[j] == proposal[j] for j in test) for w in words):
            selected.append(i)
    profile = value_profile(words, proposal, weights)
    assert sum(weights[i] for i in selected) == 41 and profile == [0, 40, 60, 60, 60]
    repeated = []
    for faces in (1, 2, 4, 8):
        combined = [0]
        for _ in range(faces):
            combined = maxplus(combined, profile)
        # Competent control uses the same guards, local words and budget.
        assert combined == [
            40 * min(b, faces) + 20 * min(max(0, b - faces), faces) for b in range(4 * faces + 1)
        ]
        if faces <= 2:
            full = [sum((tuple(w) for w in ws), ()) for ws in product(words, repeat=faces)]
            assert combined == value_profile(full, proposal * faces, weights * faces)
        witness = b"{[()]}" * faces
        assert raw_apply(witness) == ()
        repeated.append(
            {
                "faces": faces,
                "local_Q_sum": 4 * faces,
                "global_Q": 4**faces,
                "control_local_assignments": 16 * faces,
                "profile_scaled10": combined,
                "witness_ids": list(witness),
                "witness_hex": witness.hex(),
            }
        )
    return {
        "valid_words": [list(w) for w in words],
        "proposal_ids": list(proposal),
        "weights_scaled10": weights,
        "greedy_positions_1based": [i + 1 for i in selected],
        "greedy_value_scaled10": 41,
        "optimal_positions_1based": [2, 4],
        "optimal_witness_ids": list(b"[()]"),
        "optimal_value_scaled10": 60,
        "profile_scaled10": profile,
        "guarded_repetitions": repeated,
    }


def types(e):
    return set(e[0]) | set(e[1])


def good_delta(classes, principal):
    if len(classes) == 1:
        return 0
    if len(classes) != 2 or any(types(e) - {principal} for e in classes):
        return None
    (d0, m0), (d1, m1) = sorted((len(e[1]) - len(e[0]), -len(e[0])) for e in classes)
    delta = d1 - d0
    return delta if delta > 0 and 0 <= m1 - m0 <= delta else None


def support_gate(classes, n):
    """Corpus has identical support at each unfixed slot; do not invent pins."""
    guards = sorted(types(next(iter(classes)))) if len(classes) == 1 else []
    candidates = []
    for principal in OPEN:
        delta = good_delta(classes, principal)
        k = n if delta is None else 0
        q = len(classes) ** k
        candidates.append(
            {
                "principal": chr(principal),
                "k": k,
                "Q_base": len(classes),
                "Q_exponent": k,
                "Q_bits": q.bit_length(),
                "within_limits": k <= 8 and q <= 4096,
            }
        )
    best = min(candidates, key=lambda c: (c["Q_exponent"], OPEN.index(ord(c["principal"]))))
    assert not guards, "Corpus assumption changed: guard-tree compilation not implemented"
    return {
        "slots": n,
        "pins": [],
        "guards": guards,
        "faces": 1,
        "effect_classes_per_slot": len(classes),
        "choices": candidates,
        "best": best,
        "status": "ELIGIBLE" if best["within_limits"] else "REFUSED_PARAMETER",
        "not_infeasibility": True,
    }


def tokenizer_audit(name, folder):
    from tokenizers import Tokenizer

    path = folder / "tokenizer.json"
    raw = json.loads(path.read_text())
    assert raw["model"]["type"] == "BPE" and raw["decoder"]["type"] == "ByteLevel"
    decoder = Tokenizer.from_file(str(path))
    added = {entry["id"] for entry in raw["added_tokens"]}
    classes, zeros, bytes_read, count = {}, [], 0, 0
    digest = hashlib.sha256()
    for piece, token_id in sorted(raw["model"]["vocab"].items(), key=lambda kv: kv[1]):
        if token_id in added:
            continue
        emission = byte_level_piece_to_bytes(piece)
        assert decoder.decode([token_id], skip_special_tokens=False) == emission.decode(
            "utf-8", errors="replace"
        ), (name, token_id)
        normal = effect(emission)
        count += 1
        bytes_read += len(emission)
        digest.update(json.dumps([token_id, emission.hex(), normal]).encode() + b"\n")
        if normal is None:
            zeros.append(token_id)
        else:
            classes.setdefault(normal, []).append(token_id)
    config = json.loads((folder / "config.json").read_text())
    result = {
        "name": name,
        "folder": str(folder),
        "tokenizer_sha256": sha(path),
        "config_sha256": sha(folder / "config.json"),
        "model_vocab_ids": len(raw["model"]["vocab"]),
        "ordinary_ids": count,
        "excluded_added_ids": sorted(added),
        "zero_effect_ids": zeros,
        "class_count": len(classes),
        "ordinary_bytes": bytes_read,
        "id_bytes_effect_sha256": digest.hexdigest(),
        "decoder_checks": count,
        "max_aliases_per_class": max(map(len, classes.values())),
        "controls": {k: v for k, v in config.items() if k.endswith("token_id")},
        "probes": [support_gate(classes, n) for n in (32, 128, 512)],
    }
    return result


def capture_audit():
    from fractions import Fraction

    path = ROOT / "attempts/72-recursive-syntax-factor-width/capture-v2.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    model = next(row for row in rows if row["type"] == "model")
    ids = model["token_ids"]
    assert ids == [7, 8, 58, 60, 2]
    tokenizer = json.loads((LLADA / "tokenizer.json").read_text())
    inverse = {v: k for k, v in tokenizer["model"]["vocab"].items()}
    emissions = [byte_level_piece_to_bytes(inverse[i]) for i in ids]
    assert emissions == [b"(", b")", b"[", b"]", b"#"]
    assert sha(LLADA / "tokenizer.json") == model["sources"]["tokenizer.json"]
    frames = []
    for frame in rows:
        if frame["type"] != "frame":
            continue
        weights = [
            [Fraction.from_float(float.fromhex(v)) for v in row]
            for row in frame["probabilities_hex"]
        ]
        assert len(weights) == frame["slots"] and all(len(row) == 5 for row in weights)
        proposals = [max(range(5), key=lambda i: (row[i], -ids[i])) for row in weights]
        omitted = [1 - sum(row) for row in weights]
        assert all(v >= 0 for row in weights for v in row) and min(omitted) >= 0
        frames.append(
            {
                "case": frame["case"],
                **support_gate({effect(v) for v in emissions}, frame["slots"]),
                "scope": "exact_on_support",
                "support_original_ids": ids,
                "support_bytes_hex": [v.hex() for v in emissions],
                "proposal_counts": dict(Counter(str(ids[i]) for i in proposals)),
                "proposal_ids_sha256": hashlib.sha256(
                    json.dumps([ids[i] for i in proposals]).encode()
                ).hexdigest(),
                "omitted_mass_min": str(min(omitted)),
                "omitted_mass_max": str(max(omitted)),
                "weight_max_numerator_bits": max(
                    v.numerator.bit_length() for row in weights for v in row
                ),
                "weight_max_denominator_bits": max(
                    v.denominator.bit_length() for row in weights for v in row
                ),
            }
        )
    assert [r["case"] for r in frames] == rows[0]["expected_cases"] and len(frames) == 6
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "frames": frames,
        "new_forwards": 0,
        "original_grammar_reused": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.output.open("x") as stream:
        result = {
            "protocol": "A76-V1",
            "producer_sha256": sha(Path(__file__)),
            "normalization": normalization_check(),
            "extension": extension_check(),
            "gadget": gadget_check(),
            "tokenizers": [tokenizer_audit("LLaDA", LLADA), tokenizer_audit("Qwen", QWEN)],
            "capture": capture_audit(),
            "new_forwards": 0,
            "timings": "NOT_REQUESTED_GATE",
            "gpu_use": False,
        }
        result["summary"] = {
            "tokenizer_probe_statuses": dict(
                Counter(p["status"] for t in result["tokenizers"] for p in t["probes"])
            ),
            "capture_statuses": dict(Counter(f["status"] for f in result["capture"]["frames"])),
            "contract_gate": result["extension"]["status"],
        }
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
