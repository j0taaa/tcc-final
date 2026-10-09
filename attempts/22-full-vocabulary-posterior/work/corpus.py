"""Pinned external corpus selection, independent copied function from21."""

import hashlib
import json


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
