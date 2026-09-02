from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAG = "v0.1.1"
RELEASE_PATH = "docs/releases/v0.1.1.md"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_release_reference_is_consistent_across_repository_and_paper() -> None:
    project = tomllib.loads(_read("pyproject.toml"))

    assert project["project"]["version"] == TAG.removeprefix("v")
    for relative in (
        "README.md",
        "REPRODUCING.md",
        RELEASE_PATH,
        "paper/main.tex",
    ):
        assert TAG in _read(relative), relative
    assert "git clone --branch v0.1.1 --recurse-submodules" in _read(
        "REPRODUCING.md"
    ).replace("\\\n  ", "")


def test_release_archive_covers_required_versioned_evidence_layers() -> None:
    release = _read(RELEASE_PATH)

    for required_path in (
        "REPRODUCING.md",
        "UPSTREAM.md",
        "LICENSE",
        "LICENSES.md",
        "configs",
        "docs/artifacts",
        "docs/evidence",
        "paper",
    ):
        assert required_path in release
        assert (ROOT / required_path).exists()
    assert "mwpc-exact-v0.1.1-paper.pdf" in release
    assert "mwpc-exact-v0.1.1-evidence.tar.gz" in release
    assert "SHA256SUMS" in release
    assert "evidence-only archive" in release
    assert "not a standalone source checkout" in release


def test_release_records_scientific_and_external_boundaries() -> None:
    release = _read(RELEASE_PATH)
    normalized = " ".join(release.split())

    for boundary in (
        "per-step `exact_on_support`",
        "not full-vocabulary exactness",
        "`TIMEOUT` is not support infeasibility",
        "singleton represented supports",
        "generated compound graph-size settings",
        "two literal structured tasks",
        "GSAI-ML/LLaDA-8B-Instruct",
        "Weights, caches, and credentials are not archived",
        "The MIT parent license does not replace EPIC's license",
    ):
        assert boundary in normalized


def test_paper_has_no_unresolved_placeholder_and_submission_identity_is_complete() -> None:
    article = _read("paper/main.tex")
    placeholders = set(re.findall(r"\\ph\{([^}]+)\}", article))
    checklist = _read("paper/FIELDS_TO_FILL.md")

    assert placeholders == set()
    for identity_value in (
        "Gabriel Jota Lizardo",
        "Gabriel Barbosa da Fonseca",
        "Praça da Liberdade",
        "Av. Brasil, 2023",
        "gabrieljotalizardo@gmail.com",
        "gabriel.jota@sga.pucminas.br",
    ):
        assert identity_value in article
    for completed_field in (
        "Advisor name",
        "Campus and institutional address",
        "Email addresses",
    ):
        assert f"- [x] {completed_field}" in checklist
    for forbidden in ("[TO BE MEASURED]", "[MODEL_ID]", "[paper section]"):
        assert forbidden not in article
    assert "- [x] Reproduction commands and final repository tag" in checklist
