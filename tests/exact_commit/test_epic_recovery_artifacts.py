import gzip
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "docs/artifacts/raw/m23_epic_tools_v1/recovery"


def summarizer(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts/exact_commit"))
    spec = importlib.util.spec_from_file_location(
        "summarize_epic_recovery", ROOT / "scripts/exact_commit/summarize_epic_recovery.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.summarize


def test_official_recovery_archive_is_independently_rechecked(monkeypatch):
    result, _ = summarizer(monkeypatch)(ARCHIVE)
    assert result["records"] == 2000
    assert len(result["cells"]) == 12
    assert result["metadata"]["model_forwards"] == 0


def test_recovery_rejects_a_false_success_even_without_manifest(tmp_path, monkeypatch):
    target = tmp_path / "recovery"
    shutil.copytree(ARCHIVE, target)
    (target / "manifest.json").unlink()
    rows = [
        json.loads(line)
        for line in gzip.decompress((target / "results.jsonl.gz").read_bytes()).splitlines()
    ]
    rows[0]["correct"] = not rows[0]["correct"]
    (target / "results.jsonl").write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    with pytest.raises(AssertionError):
        summarizer(monkeypatch)(target)
