"""Pinned external corpus selection, independent copied function from21."""

import hashlib
import json
import zipfile
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def select_documents(folder, tokenizer, protocol):
    found = {}
    low, high = protocol["external"]["eligible_tokens"]
    for path in sorted((folder / "tests/draft2020-12").glob("*.json")):
        for group in json.loads(path.read_text()):
            for test in group["tests"]:
                if not isinstance(test["data"], (dict, list)):
                    continue
                text = json.dumps(
                    test["data"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
                )
                tokens = tokenizer.encode(text, add_special_tokens=False)
                if low <= len(tokens) <= high:
                    key = digest(f"{protocol['seed']}/{text}".encode())
                    found.setdefault(
                        key,
                        dict(
                            key=key,
                            text=text,
                            tokens=tokens,
                            file=path.name,
                            description=test["description"],
                        ),
                    )
    ordered = [found[k] for k in sorted(found)]
    if len(ordered) < 24:
        raise ValueError("fewer than predeclared external documents")
    return ordered[:6], ordered[6:18], ordered[18:24]


def select_independent(archive, tokenizer, protocol):
    """Every eligible positive external document; keep its original bytes."""
    corpus = protocol["independent_corpus"]
    found = {}
    with zipfile.ZipFile(archive) as source:
        for name in sorted(source.namelist()):
            if f"JSONTestSuite-{corpus['revision']}/test_parsing/y_" not in name:
                continue
            raw = source.read(name)
            try:
                text = raw.decode("utf8")
                value = json.loads(
                    text, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x))
                )
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(value, (dict, list)):
                continue
            tokens = tokenizer.encode(text, add_special_tokens=False)
            low, high = protocol["external"]["eligible_tokens"]
            if low <= len(tokens) <= high:
                # IDs were pinned under the corpus identity seed before A24
                # chose its independent sampler seed. Do not silently change
                # documents/IDs when rotating sampler randomness.
                key = digest(f"{corpus.get('identity_seed', protocol['seed'])}/{text}".encode())
                found.setdefault(
                    key,
                    dict(
                        key=key,
                        text=text,
                        tokens=tokens,
                        file=Path(name).name,
                        source_sha256=digest(raw),
                    ),
                )
    if len(found) != corpus["eligible_count"]:
        raise ValueError("independent external corpus eligibility changed")
    expected = {r["key"]: (r["file"], r["source_sha256"]) for r in corpus["cases"]}
    if {key: (r["file"], r["source_sha256"]) for key, r in found.items()} != expected:
        raise ValueError("independent predeclared documents changed")
    return [found[key] for key in sorted(found)]
