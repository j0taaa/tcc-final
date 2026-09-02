from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIBLIOGRAPHY = ROOT / "paper" / "referencias.bib"
ARTICLE = ROOT / "paper" / "main.tex"
EVIDENCE = ROOT / "docs" / "evidence" / "submission-bibliography-verification.md"
CHECKLIST = ROOT / "paper" / "FIELDS_TO_FILL.md"

EXPECTED_KEYS = {
    "aho2006",
    "amarilli2026probabilistic",
    "austin2021d3pm",
    "barhillel1961",
    "dang2026automata",
    "earley1970",
    "goodman1999semiring",
    "hopcroft2006",
    "jin2026epic",
    "kasami1965",
    "kudo2018sentencepiece",
    "mohri2002",
    "mundler2025cfg",
    "nie2025llada",
    "sahoo2024mdlm",
    "sennrich2016bpe",
    "stolcke1995",
    "suresh2025dingo",
    "younger1967",
}
UNCITED_KEYS = {"stolcke1995", "younger1967"}


def _entries() -> dict[str, tuple[str, str]]:
    bibliography = BIBLIOGRAPHY.read_text(encoding="utf-8")
    matches = list(re.finditer(r"@(?P<type>[a-z]+)\{(?P<key>[^,]+),", bibliography))
    entries: dict[str, tuple[str, str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(bibliography)
        entries[match.group("key")] = (match.group("type"), bibliography[match.start() : end])
    return entries


def _citation_keys() -> set[str]:
    article = ARTICLE.read_text(encoding="utf-8")
    citations = re.findall(r"\\cite[a-zA-Z]*\{([^}]+)\}", article)
    return {key.strip() for group in citations for key in group.split(",")}


def test_every_bibliography_record_has_a_stable_verification_source() -> None:
    entries = _entries()
    assert set(entries) == EXPECTED_KEYS
    for key, (_, entry) in entries.items():
        assert "  url" in entry.lower(), key


def test_citation_inventory_and_per_record_audit_are_complete() -> None:
    assert _citation_keys() == EXPECTED_KEYS - UNCITED_KEYS

    evidence = EVIDENCE.read_text(encoding="utf-8")
    assert "Verification date: 2026-09-01" in evidence
    assert "all 19 BibTeX records" in evidence
    for key in EXPECTED_KEYS:
        assert evidence.count(f"| `{key}` |") == 1, key
    for key in UNCITED_KEYS:
        assert f"| `{key}` | Uncited |" in evidence


def test_corrected_publication_metadata_is_preserved() -> None:
    entries = _entries()

    for key in ("austin2021d3pm", "sahoo2024mdlm", "nie2025llada"):
        assert entries[key][0] == "inproceedings"

    mdlm = entries["sahoo2024mdlm"][1]
    assert "volume    = {37}" in mdlm
    assert "pages     = {130136--130184}" in mdlm
    assert "doi       = {10.52202/079017-4135}" in mdlm

    llada = entries["nie2025llada"][1]
    assert "booktitle = {Advances in Neural Information Processing Systems}" in llada
    assert "volume    = {38}" in llada
    assert "pages     = {50608--50646}" in llada
    assert "doi       = {10.52202/085713-1689}" in llada
    assert "arXiv preprint" not in llada

    dingo = entries["suresh2025dingo"][1]
    assert "pages     = {160518--160551}" in dingo
    assert "doi       = {10.52202/085713-5362}" in dingo

    assert "doi     = {10.25596/JALC-2002-321}" in entries["mohri2002"][1]
    assert "doi     = {10.1016/S0019-9958(67)80007-X}" in entries["younger1967"][1]


def test_submission_checklist_records_completed_verification() -> None:
    checklist = CHECKLIST.read_text(encoding="utf-8")
    assert "- [x] Verify every bibliographic reference" in checklist
    assert "- [ ] Submit the manuscript for advisor review" in checklist
