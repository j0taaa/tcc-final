from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "paper" / "main.tex"
BIBLIOGRAPHY = ROOT / "paper" / "referencias.bib"
EVIDENCE = ROOT / "docs" / "evidence" / "submission-related-work-search.md"

DIRECT_CITATION_KEYS = (
    "suresh2025dingo",
    "mundler2025cfg",
    "jin2026epic",
    "dang2026automata",
)


def test_updated_search_preserves_direct_line_and_records_adjacent_sources() -> None:
    article = ARTICLE.read_text(encoding="utf-8")
    bibliography = BIBLIOGRAPHY.read_text(encoding="utf-8")

    for key in DIRECT_CITATION_KEYS:
        assert key in article
        assert len(re.findall(rf"@[a-z]+\{{{re.escape(key)},", bibliography)) == 1

    evidence = EVIDENCE.read_text(encoding="utf-8")
    for reviewed_source in (
        "arXiv:2602.00286",
        "arXiv:2606.15805",
        "arXiv:2605.29607",
        "XGrammar",
        "Control-DAG",
    ):
        assert reviewed_source in evidence
    assert "one additional reference pushed the paper to 17 pages" in evidence


def test_search_record_is_bounded_reproducible_and_does_not_claim_proof_of_novelty() -> None:
    evidence = EVIDENCE.read_text(encoding="utf-8")
    normalized_evidence = " ".join(evidence.split())
    checklist = (ROOT / "paper" / "FIELDS_TO_FILL.md").read_text(encoding="utf-8")

    assert "Search date: 2026-09-01" in evidence
    assert "Coverage cutoff: primary records discoverable through 2026-08-31" in evidence
    assert "not a claim of a systematic review or proof of novelty" in normalized_evidence
    assert "bounded result of the recorded search" in normalized_evidence
    for key_term in (
        "parallel commitment diffusion language model",
        "non-autoregressive DAG constrained decoding weighted finite state automata",
        "arXiv 2608 diffusion language constrained decoding parallel decoding",
    ):
        assert key_term in evidence
    assert "- [x] Update the related-work search" in checklist


def test_direct_papers_use_verified_conference_records() -> None:
    bibliography = BIBLIOGRAPHY.read_text(encoding="utf-8")

    dingo = bibliography.split("@inproceedings{suresh2025dingo,", maxsplit=1)[1].split(
        "\n}\n", maxsplit=1
    )[0]
    cfg = bibliography.split("@inproceedings{mundler2025cfg,", maxsplit=1)[1].split(
        "\n}\n", maxsplit=1
    )[0]
    assert "Advances in Neural Information Processing Systems" in dingo
    assert "10.52202/085713-5362" in dingo
    assert "International Conference on Learning Representations" in cfg
    assert "https://openreview.net/forum?id=7Sph4KyeYO" in cfg
