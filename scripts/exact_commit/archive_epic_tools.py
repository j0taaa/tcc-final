#!/usr/bin/env python3
"""Archive an M23 cohort losslessly with deterministic gzip and checksums."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--recovery", action="store_true")
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=False)
    names = ["config.json", "metadata.json"]
    if (args.source / "resume_segments.jsonl").exists():
        names.append("resume_segments.jsonl")
    if not args.recovery:
        names += ["support.json", "token_emissions.json"]
    for name in names:
        (args.destination / name).write_bytes((args.source / name).read_bytes())
    raw = (args.source / "results.jsonl").read_bytes()
    (args.destination / "results.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
    names.append("results.jsonl.gz")
    manifest = {
        "source_experiment": json.loads((args.source / "config.json").read_text())["experiment_id"],
        "records": len(raw.splitlines()),
        "uncompressed_results_sha256": hashlib.sha256(raw).hexdigest(),
        "sha256": {
            name: hashlib.sha256((args.destination / name).read_bytes()).hexdigest()
            for name in names
        },
    }
    (args.destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(args.destination)


if __name__ == "__main__":
    main()
