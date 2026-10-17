"""Prospective input-only selection; raw JSONL decodes discarded gold fields."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

PIN = "1bcc55eb6c8cffde2306b3db03ede39b61c6152a"
TIERS = ("easy", "original", "hard")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def select(cache, output):
    assert not output.exists(), "Preserve earlier manifests/drafts"
    cache.mkdir(parents=True, exist_ok=True)
    rows, origins, counts = [], [], {}
    for tier in TIERS:
        url = f"https://raw.githubusercontent.com/fstandhartinger/jevbench/{PIN}/datasets/public/{tier}.jsonl"
        path = cache / f"{tier}.jsonl"
        if path.exists():
            raise ValueError(
                "Use a fresh raw-data cache; do not silently replace an older exposure"
            )
        raw = urllib.request.urlopen(url, timeout=60).read()
        path.write_bytes(raw)
        origins.append(
            {"tier": tier, "url": url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        )
        total = eligible = 0
        for line in raw.splitlines():
            if not line.strip():
                continue
            # Disclosure: JSON decoding DOES load expected/gold bytes here;
            # neither the value nor any outcome-dependent field is consulted.
            record = json.loads(line)
            total += 1
            item = {key: record[key] for key in ("id", "state", "question", "labels")}
            labels = item["labels"]
            if item["id"] == "hard-sol-b-judge_hard-18":
                continue
            if not (
                2 <= len(labels) <= 6
                and all(isinstance(v, str) and v.isascii() for v in labels)
                and len(set(labels)) == len(labels)
            ):
                continue
            blob = canonical(item)
            if len(blob) > 6000:
                continue
            eligible += 1
            rows.append(
                {"input": item, "input_sha256": hashlib.sha256(blob).hexdigest(), "tier": tier}
            )
        counts[tier] = {"all": total, "eligible": eligible}
    rows.sort(key=lambda r: (r["input_sha256"], r["input"]["id"], r["tier"]))
    assert len(rows) >= 8
    assert len({r["input"]["id"] for r in rows}) == len(rows), "Ambiguous cross-tier duplicate ID"
    selected = [dict(rank=i, **row) for i, row in enumerate(rows[:8])]
    result = {
        "source": "https://github.com/fstandhartinger/jevbench",
        "revision": PIN,
        "contract": "masked-resource-contract-v6.md",
        "counts": counts,
        "source_files": origins,
        "gold_bytes_decoded_to_discard": True,
        "gold_values_used_for_selection_or_generation": False,
        "no_pristine_independent_corpus_claim": True,
        "selected": selected,
        "all_candidate_ranks": [
            {
                "rank": i,
                "id": r["input"]["id"],
                "tier": r["tier"],
                "input_sha256": r["input_sha256"],
            }
            for i, r in enumerate(rows)
        ],
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": "SELECTED_INPUT_ONLY",
                "counts": counts,
                "selected_ids": [r["input"]["id"] for r in selected],
                "new_neural_forwards": 0,
                "gold_bytes_decoded_to_discard": True,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    select(args.raw_cache, args.output)
