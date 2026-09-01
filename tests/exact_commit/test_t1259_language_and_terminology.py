from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _article_without_resumo() -> tuple[str, str]:
    article = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    match = re.search(
        r"\\begin\{otherlanguage\}\{brazilian\}.*?"
        r"\\begin\{resumo\}(.*?)\\end\{resumo\}.*?"
        r"\\end\{otherlanguage\}",
        article,
        flags=re.DOTALL,
    )
    assert match is not None
    return article[: match.start()] + article[match.end() :], match.group(1)


def test_article_body_is_english_and_resumo_remains_portuguese() -> None:
    body, resumo = _article_without_resumo()

    assert "Modelos de linguagem por difusão" in resumo
    assert r"\section{Introduction}" in body
    assert r"\section{Conclusion and Future Work}" in body
    assert r"\newtheorem{theorem}{Theorem}" in body
    assert r"\floatname{algorithm}{Algorithm}" in body
    assert r"\caption{Max-plus parsing over a finite lattice}" in body

    portuguese_fragments = (
        "\\section{Introdução}",
        "\\section{Conclusões",
        "\\caption{Resultados",
        "\\caption{Cronograma",
        "\\textsc{Inviável}",
        "\\text{ compatível}",
        " propostas ",
        " testemunha ",
        " conclusão ",
    )
    for fragment in portuguese_fragments:
        assert fragment not in body


def test_language_decision_defines_the_scientific_vocabulary() -> None:
    decision = (
        ROOT / "docs" / "decisions" / "0022-article-language-and-terminology.md"
    ).read_text(encoding="utf-8")

    for term in (
        "`exact_on_support`",
        "`OPTIMAL`",
        "`INFEASIBLE_ON_SUPPORT`",
        "`TIMEOUT`",
        "`UNSUPPORTED`",
        "`ERROR`",
        "finite slots",
        "proposal",
        "witness",
        "progress fallback",
        "serial baseline",
        "EPIC baseline",
        "exact strategy",
    ):
        assert term in decision
    assert "never evidence of infeasibility" in decision
    assert "not counted as a matched model proposal unless" in decision


def test_legacy_plan_is_archived_and_superseded() -> None:
    notice = (ROOT / "IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8")
    archive = (
        ROOT / "docs" / "history" / "IMPLEMENTATION_PLAN-legacy-pt.md"
    ).read_text(encoding="utf-8")

    assert notice.startswith("# Superseded implementation plan")
    assert "fefe0b6f250e75c887455fcf3fe3459fa5d1be3fc92a385aef42dc0428c07f33" in notice
    assert archive.startswith("# Plano completo de implementação")
    assert len(archive.splitlines()) == 1030
    assert "never to override an accepted ADR or the current task" in notice


def test_active_paper_documentation_is_english() -> None:
    readme = (ROOT / "paper" / "README.md").read_text(encoding="utf-8")
    checklist_path = ROOT / "paper" / "FIELDS_TO_FILL.md"
    checklist = checklist_path.read_text(encoding="utf-8")

    assert not (ROOT / "paper" / "CAMPOS_A_PREENCHER.md").exists()
    assert checklist_path.is_file()
    assert "# TCC in LaTeX" in readme
    assert "## Building locally" in readme
    assert "`exact_on_support`" in readme
    assert "# Fields to fill before submission" in checklist
    assert "## Academic integrity" in checklist
    for portuguese_fragment in (
        "## Arquivos",
        "## Compilação",
        "## Campos pendentes",
        "## Observações importantes",
        "# Campos a preencher",
        "## Identificação",
        "## Resultados",
        "## Integridade acadêmica",
    ):
        assert portuguese_fragment not in readme
        assert portuguese_fragment not in checklist
