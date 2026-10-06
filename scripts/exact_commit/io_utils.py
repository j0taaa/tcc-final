"""Small immutable JSON/gzip and provenance helpers for the current campaign."""

import gzip
import hashlib
import json
from dataclasses import fields


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def system_data(system):
    return {
        field.name: dict(getattr(system, field.name))
        if field.name == "thread_environment"
        else getattr(system, field.name)
        for field in fields(system)
    }
