"""Opt-in pinned external fetch; select using questions alone, labels ignored."""

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

REVISION = "3101c7d5072418e28b9008a6636bde82a006892c"
BASE = f"https://raw.githubusercontent.com/openai/grade-school-math/{REVISION}"


def manifest():
    result = dict(repository="openai/grade-school-math", revision=REVISION, files={}, selections={})
    for split, count in (("train", 32), ("test", 64)):
        url = f"{BASE}/grade_school_math/data/{split}.jsonl"
        data = urllib.request.urlopen(url, timeout=30).read()
        result["files"][split] = dict(
            url=url, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)
        )
        eligible, refusals = [], []
        for index, line in enumerate(data.splitlines()):
            # Never access answer value: the public files include it by design.
            question = json.loads(line)["question"]
            identity = f"{split}:{index}"
            if not isinstance(question, str) or not question or len(question) > 3000:
                refusals.append(dict(id=identity, reason="input_character_budget_or_type"))
                continue
            rank = hashlib.sha256(
                f"A32-GSM-fixed-v1|{split}|{index}|{question}".encode()
            ).hexdigest()
            eligible.append(dict(id=identity, question=question, selection_sha256=rank))
        eligible.sort(key=lambda row: row["selection_sha256"])
        result["selections"][split] = eligible[:count]
        result["files"][split].update(
            total=len(data.splitlines()), eligible=len(eligible), selected=count, refusals=refusals
        )
        if len(eligible) < count:
            raise ValueError("not enough eligible inputs; do not substitute another protocol")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--license", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.license.exists():
        raise SystemExit("refuse to overwrite inputs/license")
    result = manifest()
    license_data = urllib.request.urlopen(f"{BASE}/LICENSE", timeout=30).read()
    result["license_sha256"] = hashlib.sha256(license_data).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    args.license.write_bytes(license_data)
    print(json.dumps({k: result["files"][k] for k in ("train", "test")}, indent=2))


if __name__ == "__main__":
    main()
