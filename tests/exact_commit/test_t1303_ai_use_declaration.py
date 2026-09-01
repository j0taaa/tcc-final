from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "paper" / "main.tex"


def _declaration() -> str:
    article = ARTICLE.read_text(encoding="utf-8")
    return article.split(r"\section*{AI-Use Declaration}", maxsplit=1)[1].split(
        r"\bibliographystyle", maxsplit=1
    )[0]


def test_t1303_names_the_verified_tool_provider_and_available_versions() -> None:
    declaration = _declaration()

    assert "OpenAI Codex (OpenAI)" in declaration
    assert "Codex CLI 0.151.0" in declaration
    assert "GPT-5-based" in declaration
    assert "no immutable model-build identifier" in declaration


def test_t1303_discloses_purposes_and_affected_components() -> None:
    declaration = _declaration()

    for purpose in (
        "planning",
        "drafting and review",
        "coding",
        "test generation",
        "debugging",
        "reproducibility review",
    ):
        assert purpose in declaration

    for component in (
        "manuscript's method, results, limitations",
        "Python and Rust code",
        "tests",
        "experiment and artifact scripts",
        "task records",
        "documentation",
    ):
        assert component in declaration


def test_t1303_keeps_human_review_and_integrity_explicit() -> None:
    declaration = _declaration()

    for reviewed_item in (
        "proof",
        "code change",
        "reference",
        "configuration",
        "result",
        "table",
        "claim",
    ):
        assert reviewed_item in declaration
    assert "remains solely responsible for correctness and originality" in declaration
    assert "No AI-proposed measurement" in declaration
    assert "fabricated datum" in declaration
    assert "AI-generated figure" in declaration
    assert "unattributed third-party text" in declaration
    assert r"\ph{" not in declaration
