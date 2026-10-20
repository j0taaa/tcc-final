"""Finite original-ID witnesses for the written unrestricted-JSON obstruction."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from itertools import product
from pathlib import Path

from operational import MODEL, sha_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(MODEL / "tokenizer.json"))

    tokenizer_hash = sha_file(MODEL / "tokenizer.json")
    assert tokenizer_hash == "6d55810de1daf81d1d1259355b4b85810385022ab745be68029295935a4eacf0"
    raw = json.loads((MODEL / "tokenizer.json").read_text())["model"]["vocab"]
    words = {v: text for text, v in raw.items() if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text)}
    chars = {}
    for char in set('" 01abtruefalsnE'):
        encoded = tokenizer.encode(char, add_special_tokens=False).ids
        assert len(encoded) == 1
        assert tokenizer.decode(encoded, skip_special_tokens=False) == char
        chars[char] = encoded[0]
    text_by_id = words | {v: c for c, v in chars.items()}
    counts, boundary_counts = [], {}
    digest = hashlib.sha256()
    for n in (6, 8, 16, 32):
        witnesses = total_q = prefixes = suffixes = 0
        for token, text in sorted(words.items()):
            anchor = [chars["0"]] + [chars[" "]] * (n - 1)
            assert token not in anchor and json.loads("0" + " " * (n - 1)) == 0

            def check(word, n=n, token=token):
                nonlocal witnesses
                assert len(word) == n
                emitted = "".join(text_by_id[v] for v in word)
                json.loads(emitted)
                witnesses += 1
                digest.update(json.dumps([n, token, word], separators=(",", ":")).encode())
                return [int(v == token) for v in word]

            for position in range(1, n - 1):
                filler = "b" if token == chars["a"] else "a"
                word = [chars['"']] + [chars[filler]] * (n - 2) + [chars['"']]
                word[position] = token
                vector = check(word)
                assert vector == [int(i == position) for i in range(n)]
            prefix = next((lit for lit in ("true", "false", "null") if lit.startswith(text)), None)
            suffix = next((lit for lit in ("true", "false", "null") if lit.endswith(text)), None)
            if prefix:
                word = [token] + [chars[c] for c in prefix[len(text) :]]
                word += [chars[" "]] * (n - len(word))
                vector = check(word)
                assert vector[0] == 1 and vector[-1] == 0
                prefixes += 1
            if suffix:
                word = [chars[c] for c in suffix[: -len(text)]] + [token]
                word = [chars[" "]] * (n - len(word)) + word
                vector = check(word)
                assert vector[0] == 0 and vector[-1] == 1
                suffixes += 1
            elif re.fullmatch(r"[eE][0-9]+", text):
                word = [chars[" "]] * (n - 2) + [chars["1"], token]
                vector = check(word)
                assert vector[0] == 0 and vector[-1] == 1
                suffixes += 1
            total_q += n - 2 + bool(prefix) + bool(suffix or re.fullmatch(r"[eE][0-9]+", text))
        record = {
            "slots": n,
            "ids": len(words),
            "valid_witnesses": witnesses,
            "first_position_ids": prefixes,
            "last_position_ids": suffixes,
            "sum_q": total_q,
            "sparse_variable_pairs": total_q,
        }
        counts.append(record)
        print(json.dumps(record, sort_keys=True), flush=True)
    # Independent direct parse attack on endpoint necessity over small alphabets.
    ordinary_by_text = {text: token for token, text in words.items()}
    for text in ("a", "b", "t", "true", "e", "e1", "l", "_"):
        if text not in ordinary_by_text:
            continue
        token = ordinary_by_text[text]
        alphabet = sorted(set([token] + [chars[c] for c in " 01truefalsn"]))
        # Only endpoints fixed to v; enumerate five other slots, at most 13^5.
        observed = [False, False]
        for side in (0, 1):
            for rest in product(alphabet, repeat=5):
                word = (token, *rest) if side == 0 else (*rest, token)
                try:
                    json.loads("".join(text_by_id[v] for v in word))
                except (ValueError, UnicodeError):
                    continue
                observed[side] = True
                break
        predicted = [
            any(lit.startswith(text) for lit in ("true", "false", "null")),
            any(lit.endswith(text) for lit in ("true", "false", "null"))
            or bool(re.fullmatch(r"[eE][0-9]+", text)),
        ]
        assert observed == predicted, (text, observed, predicted)
        boundary_counts[text] = observed
    report = {
        "tokenizer_sha256": tokenizer_hash,
        "witnesses_sha256": digest.hexdigest(),
        "counts": counts,
        "endpoint_attacks": boundary_counts,
        "gpu_used": False,
        "timings": "not measured",
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
