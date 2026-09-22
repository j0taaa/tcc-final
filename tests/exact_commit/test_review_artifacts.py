"""Data integrity and executed protocol checks, independent of article wording."""

import gzip
import json
from pathlib import Path

import pytest
from scripts.exact_commit.build_review_results import RAW, outputs, verified_rows


def test_review_results_recompute_and_all_measured_sources_are_clean():
    generated = outputs()
    summary = json.loads(generated["summary.json"])
    assert summary["branching"]["failures"] == 0
    assert summary["replay"]["paired_conditions"] == 72
    assert summary["scaling"]["max_nodes"] > 118
    assert set(summary["producing_commits"]) == {
        "branching",
        "pilot-v1",
        "pilot-v2",
        "confirmation",
        "scaling",
        "replay-v1",
        "replay",
    }


@pytest.mark.parametrize("cohort", ["pilot-v2", "confirmation"])
def test_executed_live_protocol_keeps_matched_schedules_and_every_outcome(cohort):
    rows = verified_rows(RAW / cohort)
    generations = [r for r in rows if r["strategy"] != "capture"]
    assert len(generations) == (48 if cohort == "pilot-v2" else 96)
    by_task = {}
    for row in generations:
        by_task.setdefault(row["task"]["task_id"], []).append(row)
        assert row["schedule"]["proposal_budgets"] == [2] * 16
        assert row["execution_status"] in {"complete", "incomplete", "timeout", "error"}
        if row["strategy"] == "exact" and "payload" in row:
            assert row["payload"]["proposal_schedule"] == [2] * 16
            assert row["payload"]["diagnostics"]["all_optimal_certificates_independently_valid"]
    assert len(by_task) == 12
    for attempts in by_task.values():
        assert {row["strategy"] for row in attempts} == {"serial", "epic", "exact", "unconstrained"}


def test_archive_verifier_rejects_changed_raw_data(tmp_path: Path):
    source = RAW / "scaling"
    manifest = json.loads((source / "manifest.json").read_text())
    for name in manifest["files"]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / name).read_bytes())
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "rows.jsonl.gz").write_bytes(gzip.compress(b"{}\n", mtime=0))
    with pytest.raises(ValueError, match="archive hash mismatch"):
        verified_rows(tmp_path)
