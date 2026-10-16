"""AFTER-data consistency audit; known labels, no model or new gradient queries."""

import argparse
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

import numpy as np

from .consumer_resource import sha, write_json
from .llada_tokenizer_v10 import EOS


def run(capture, replay, model_dir):
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    original = [json.loads(x) for x in (capture / "rows.jsonl").read_text().splitlines()]
    entries = [(r, t) for r in original for t in r["transitions"]]
    records = [json.loads(x) for x in (replay / "records.jsonl").read_text().splitlines()]
    summary = json.loads((replay / "summary.json").read_text())
    protocol = json.loads((capture / "protocol.json").read_text())
    manifest = json.loads((replay / "manifest.json").read_text())
    for name, data in manifest.items():
        assert sha(replay / name) == data["sha256"]
    assert len(entries) == len(records) == 70 and summary["status"] == "PASS"
    assert not summary["gpu_used"] and summary["execution_device"] == "cpu"
    assert summary["peak_process_rss_bytes"] <= 2 * 1024**3
    statuses, posteriors, correct, missed, maximal = Counter(), [], 0, 0, 0.0
    for (row, transition), record in zip(entries, records, strict=True):
        for k in ("case", "replica"):
            assert row[k] == record[k]
        for k in ("step", "head"):
            assert transition[k] == record[k]
        assert record["status"] == "PASS"
        proxy = record["proxy"]
        statuses[proxy["status"]] += 1
        assert all(np.isfinite(v).all() for v in map(np.asarray, proxy["correction"].values()))
        for k in ("alpha", "anchor"):
            assert len(proxy["correction"][k]) == transition["prefix_extent"]
        if proxy["status"] == "POSITIVE":
            assert 0 < proxy["posterior"] <= 1 + 1e-7
            posteriors.append(proxy["posterior"])
        else:
            assert proxy["posterior"] == 0
            assert all((np.asarray(v) == 0).all() for v in proxy["correction"].values())
        for errors in (record["independent_errors"], record["original_base_errors"]):
            assert max(errors.values()) <= 1e-7
            maximal = max(maximal, max(errors.values()))
        word = transition["proposal_prefix"]
        assert word[-1] == EOS and EOS not in word[:-1]
        text = tokenizer.decode(
            protocol["supplied_prefix_ids"] + word[:-1], skip_special_tokens=False
        )
        value = json.loads(text, parse_int=Decimal, parse_float=Decimal)
        assert set(value) == {"answer"}
        digits = record["target_digits"]
        semantic = value["answer"] == Decimal(digits)
        suffix = text[len('{"answer":') :]
        match = (
            re.fullmatch(
                r"[ \t\r\n]*" + digits + r"(?:\.0+)?(?:[eE][+-]?0+)?[ \t\r\n]*}[ \t\r\n]*", suffix
            )
            is not None
        )
        assert semantic == record["proposal_semantic_correct"]
        assert match == record["proposal_proxy_match"]
        assert not match or (semantic and proxy["status"] == "POSITIVE")
        correct += int(semantic)
        missed += int(semantic and not match)
    result = {
        "status": "PASS",
        "scope": "AFTER-data independent consistency only",
        "transitions": 70,
        "official_tokenizer_json_decimal_checks": 70,
        "support_status_counts": dict(statuses),
        "positive_posterior_range": [min(posteriors), max(posteriors)],
        "semantic_correct_proposals": correct,
        "semantic_correct_proxy_missed": missed,
        "maximum_numeric_error": maximal,
        "new_model_forwards": 0,
        "updates": 0,
        "new_proxy_gradient_queries": 0,
        "peak_process_rss_bytes": summary["peak_process_rss_bytes"],
    }
    write_json(replay / "post-capture-consistency.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("capture", "replay", "model-dir"):
        ap.add_argument("--" + name, type=Path, required=True)
    a = ap.parse_args()
    run(a.capture, a.replay, a.model_dir)
