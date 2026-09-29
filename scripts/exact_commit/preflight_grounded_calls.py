#!/usr/bin/env python3
"""Check every frozen grounded support with the pinned, locally cached tokenizer."""

import argparse
import hashlib
import json
from pathlib import Path

from mwpc_research.catalog_tokens import encode_call
from mwpc_research.grounded_calls import grounded_catalog


def main():
    from transformers import AutoTokenizer

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--configs", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    rows, hashes = [], {}
    tokenizer = None
    for path in args.configs:
        raw = path.read_bytes()
        config = json.loads(raw)
        hashes[path.name] = hashlib.sha256(raw).hexdigest()
        if tokenizer is None:
            tokenizer = AutoTokenizer.from_pretrained(
                config["model_id"], revision=config["revision"], local_files_only=True
            )
        for task in config["tasks"]:
            try:
                calls = grounded_catalog(task["function"], task["instruction"])
                paths = [
                    encode_call(tokenizer, c, slots=config["slots"], eos=126081)[0] for c in calls
                ]
                row = {
                    "id": task["id"],
                    "status": "represented",
                    "catalog_size": len(calls),
                    "max_ordinary_tokens": max(sum(t != 126081 for t in path) for path in paths),
                    "all_byte_reconstructions_valid": True,
                }
            except ValueError as exc:
                row = {"id": task["id"], "status": "unsupported", "reason": str(exc)}
            rows.append(row)
    result = {
        "model_id": config["model_id"],
        "tokenizer_revision": config["revision"],
        "config_sha256": hashes,
        "tasks": rows,
    }
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        assert args.output.read_text() == text
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(
        json.dumps(
            {"tasks": len(rows), "represented": sum(r["status"] == "represented" for r in rows)}
        )
    )


if __name__ == "__main__":
    main()
