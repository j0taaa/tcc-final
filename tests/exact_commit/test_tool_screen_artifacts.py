import gzip
import json
import shutil
from pathlib import Path

import pytest
from scripts.exact_commit.summarize_tool_screen import summarize

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "docs/artifacts/raw/m22_dllm_discovery_v1"


def test_archived_production_certificates_and_frozen_confirmation():
    result = summarize(ARCHIVE / "confirmation")
    assert result["unique_tasks"] == 100
    assert result["records"] == 200
    assert [(c["method"], c["correct"]) for c in result["cells"]] == [
        ("exact", 65),
        ("greedy", 63),
    ]


def test_archive_hash_gate_detects_changed_support(tmp_path):
    target = tmp_path / "archive"
    shutil.copytree(ARCHIVE / "screen_v1", target)
    with (target / "support.json").open("a") as stream:
        stream.write(" ")
    with pytest.raises(AssertionError):
        summarize(target)


@pytest.mark.parametrize("corruption", ["wrong_success", "missing_pair", "changed_token"])
def test_semantic_gate_detects_corruption_even_without_manifest(tmp_path, corruption):
    target = tmp_path / "archive"
    shutil.copytree(ARCHIVE / "confirmation", target)
    (target / "manifest.json").unlink()
    path = target / "results.jsonl.gz"
    records = [
        json.loads(line) for line in gzip.decompress(path.read_bytes()).decode().splitlines()
    ]
    if corruption == "wrong_success":
        records[0]["correct"] = not records[0]["correct"]
    elif corruption == "missing_pair":
        records.pop()
    else:
        records[0]["trace"][0]["witness_token_ids"][0] = 999999
    path.write_bytes(
        gzip.compress(("\n".join(json.dumps(r) for r in records) + "\n").encode(), mtime=0)
    )
    with pytest.raises(AssertionError):
        summarize(target)
