#!/usr/bin/env python3
"""Archive one finished review run, without rewriting measurements."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def archive(source: Path, destination: Path) -> None:
    if not (source / "summary.json").is_file() or not (source / "rows.jsonl").is_file():
        raise ValueError("only finished runs with rows and summary can be archived")
    destination.mkdir(parents=True, exist_ok=False)
    paths = [
        source / name
        for name in (
            "metadata.json",
            "initial-metadata.json",
            "summary.json",
            "config.toml",
            "resolved-config.json",
            "input-hashes.json",
            "worker.log",
        )
        if (source / name).is_file()
    ]
    paths.extend(sorted((source / "snapshots").glob("*.json")))
    for path in paths:
        target = destination / path.relative_to(source)
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(path.read_bytes())
    raw = (source / "rows.jsonl").read_bytes()
    (destination / "rows.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
    manifest = {
        "raw_rows_sha256": hashlib.sha256(raw).hexdigest(),
        "row_count": len(raw.splitlines()),
        "files": {
            path.relative_to(destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(destination.rglob("*"))
            if path.is_file()
        },
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    archive(args.source, args.destination)
