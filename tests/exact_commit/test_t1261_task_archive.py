from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTIVE = ROOT / "TASKS.md"
ARCHIVE = ROOT / "docs" / "history" / "TASKS-through-M12.md"


def test_m11_m12_task_detail_is_complete_only_in_archive() -> None:
    active = ACTIVE.read_text(encoding="utf-8")
    archive = ARCHIVE.read_text(encoding="utf-8")
    archived_ids = re.findall(r"^## (T(?:11|12)\d+) —", archive, flags=re.MULTILINE)

    assert archived_ids == [
        "T1100",
        "T1101",
        "T1102",
        "T1103",
        "T1104",
        "T1105",
        "T1106",
        "T1200",
        "T1201",
        "T1202",
        "T1203",
        "T1204",
    ]
    assert "# M12.5" not in archive
    assert "## T1100 —" not in active
    assert "## T1204 —" not in active
    assert "T1100--T1106" in active
    assert "T1200--T1204" in active


def test_archive_preserves_prior_history_chain_and_evidence() -> None:
    archive = ARCHIVE.read_text(encoding="utf-8")

    for relative in (
        "docs/history/TASKS-through-M10.md",
        "docs/history/TASKS-through-M8.md",
        "docs/history/TASKS-through-M3.md",
    ):
        assert (ROOT / relative).is_file()
        assert Path(relative).name in archive
    for task_id in (
        "T1100",
        "T1101",
        "T1102",
        "T1103",
        "T1104",
        "T1105",
        "T1106",
        "T1200",
        "T1201",
        "T1202",
        "T1203",
        "T1204",
    ):
        section = archive.split(f"## {task_id}", maxsplit=1)[1]
        assert "**Evidence:**" in section.split("\n## ", maxsplit=1)[0]


def test_active_file_keeps_m125_and_m13_full_and_names_next_work() -> None:
    active = ACTIVE.read_text(encoding="utf-8")

    assert len(active.splitlines()) < 900
    assert "**M12.5 gate audit.**" in active
    assert "The first remaining required task is T1300" in active
    assert "# M12.5 — Review fixes before article writing" in active
    assert "## T1250 —" in active
    assert "## T1261 —" in active
    assert "# M13 — Synchronize implementation with the TCC" in active
    assert "## T1300 —" in active
    assert "**Depends on:** M12.5 gate" in active


def test_active_evidence_links_resolve() -> None:
    active = ACTIVE.read_text(encoding="utf-8")
    relative_links = re.findall(r"\[[^]]+\]\(([^):#]+)\)", active)

    assert relative_links
    for relative in relative_links:
        assert (ROOT / relative).exists(), relative
