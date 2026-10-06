"""Strict JSON/gzip and file hashing for offline artifact verification."""

import gzip
import hashlib
import json


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_json_constant(value):
    raise ValueError(f"raw JSONL contains non-finite constant: {value}")


def read(path):
    raw = path.read_bytes()
    return json.loads(
        gzip.decompress(raw) if path.suffix == ".gz" else raw,
        parse_constant=_reject_json_constant,
    )
