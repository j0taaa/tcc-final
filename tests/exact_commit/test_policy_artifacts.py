import gzip
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location(
        "policy_summary", ROOT / "scripts/exact_commit/summarize_policy_screen.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_smoke_has_every_policy_and_valid_certificates():
    config, rows = load().read(ROOT / "docs/artifacts/raw/m24_policy_v1/smoke")
    assert len(rows) == 40 and len(config["policies"]) == 20
    assert any(row["method"] == "exact_review" and "draft" in row for row in rows)
    assert any(row["method"].startswith("margin") for row in rows)


@pytest.mark.parametrize("mutation", ["success", "fixed", "score", "forced", "missing"])
def test_semantic_corruption_is_rejected(tmp_path, mutation):
    shutil.copytree(ROOT / "docs/artifacts/raw/m24_policy_v1/smoke", tmp_path / "data")
    directory = tmp_path / "data"
    (directory / "manifest.json").unlink()
    path = directory / "results.jsonl.gz"
    rows = [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
    if mutation == "success":
        rows[0]["correct"] = not rows[0]["correct"]
    elif mutation == "fixed":
        row = next(r for r in rows if r["method"] == "exact_b24")
        row["trace"][1]["canvas_before"][0] = -1
    elif mutation == "score":
        row = next(r for r in rows if r["method"] == "exact_b24")
        row["trace"][0]["production_result"]["score"] += 1
    elif mutation == "forced":
        row = next(r for r in rows if r["method"] == "margin_0")
        query = row["trace"][0]["gate"]["queries"][0]
        query["forced"] = not query["forced"]
    else:
        rows.pop()
    path.write_bytes(gzip.compress("\n".join(json.dumps(r) for r in rows).encode()))
    with pytest.raises((AssertionError, ValueError)):
        load().read(directory)
