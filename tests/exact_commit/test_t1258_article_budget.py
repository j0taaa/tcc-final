from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs" / "article" / "M13_RESULTS_AND_PAGE_BUDGET.md"


def test_article_plan_selects_exactly_three_replacement_elements() -> None:
    text = PLAN.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    selected = re.findall(r"^### (R\d+) —", text, flags=re.MULTILINE)

    assert selected == ["R1", "R2", "R3"]
    assert "No fourth result table or figure is authorized" in text
    assert "labelled `tab:resultados`" in text
    assert "labelled `tab:cronograma`" in text
    assert "rather than append every generated artifact" in normalized


def test_article_plan_tracks_omitted_artifacts_in_reproduction_guide() -> None:
    plan = PLAN.read_text(encoding="utf-8")
    reproducing = (ROOT / "REPRODUCING.md").read_text(encoding="utf-8")
    artifact_names = (
        "correctness-oracle-table.tex",
        "finite-slot-counterexample-table.tex",
        "heuristic-gap-table.tex",
        "heuristic-gap-distribution.svg",
        "runtime-breakdown-table.tex",
        "runtime-scaling.svg",
        "end-to-end-comparison-table.tex",
    )

    for artifact_name in artifact_names:
        assert artifact_name in plan
        assert artifact_name in reproducing


def test_article_plan_preserves_page_limit_and_required_content() -> None:
    text = PLAN.read_text(encoding="utf-8")

    assert "10--16 page limit" in text
    assert "**14.25**" in text
    assert "**1.75**" in text
    assert "not a measured final page count" in text
    assert "preserve the template font, margins, required summaries" in text
    assert "silently shrinking required content" in text
    assert "measure the produced PDF" in text


def test_t1301_explicitly_depends_on_t1258() -> None:
    tasks = (ROOT / "TASKS.md").read_text(encoding="utf-8")
    t1301 = tasks.split("## T1301", maxsplit=1)[1].split("## T1302", maxsplit=1)[0]
    normalized = " ".join(t1301.split())

    assert "**Depends on:** M12.5 gate, T1258" in t1301
    assert "does not append all generated artifacts" in normalized


def test_replacement_targets_exist_in_current_manuscript() -> None:
    manuscript = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")

    assert r"\label{tab:resultados}" in manuscript
    assert r"\label{tab:cronograma}" in manuscript
