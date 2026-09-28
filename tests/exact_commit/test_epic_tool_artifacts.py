"""Archived EPIC outputs must be complete, reconstructible and honestly scored."""

import gzip
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "docs/artifacts/raw/m23_epic_tools_v1/confirmation"


def reader():
    spec = importlib.util.spec_from_file_location(
        "summarize_epic_tools", ROOT / "scripts/exact_commit/summarize_epic_tools.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.read_cohort


def test_archived_epic_and_exact_outputs_are_rechecked():
    config, metadata, rows = reader()(ARCHIVE)
    assert len(rows) == 700
    assert len(config["tasks"]) == 100
    assert metadata["upstream_epic_commit"] == "5b1b31098f34ed3691d2a9f4aae14fdf5839d072"
    assert all(
        any(r["epic_counters"]["batch_selected"] >= 2 for (_, m), r in rows.items() if m == method)
        for method in ("epic_native_1", "epic_native_4", "epic_domains_1", "epic_domains_4")
    )


@pytest.mark.parametrize("mutation", ["false_success", "different_tokens", "missing_pair", "hash"])
def test_epic_archive_rejects_corruption(tmp_path, mutation):
    target = tmp_path / "cohort"
    shutil.copytree(ARCHIVE, target)
    if mutation == "hash":
        with (target / "support.json").open("a") as stream:
            stream.write(" ")
    else:
        # Bypass only the manifest deliberately, to exercise semantic checks.
        (target / "manifest.json").unlink()
        rows = [
            json.loads(line)
            for line in gzip.decompress((target / "results.jsonl.gz").read_bytes()).splitlines()
        ]
        epic = next(
            row for row in rows if row["method"] == "epic_native_1" and row["status"] == "complete"
        )
        if mutation == "false_success":
            epic["correct"] = not epic["correct"]
        elif mutation == "different_tokens":
            epic["token_ids"][0] = 126336
        else:
            rows.pop()
        (target / "results.jsonl").write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    with pytest.raises(AssertionError):
        reader()(target)
