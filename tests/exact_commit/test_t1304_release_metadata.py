from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAG = "v0.1.0"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_release_reference_is_consistent_across_repository_and_paper() -> None:
    project = tomllib.loads(_read("pyproject.toml"))

    assert project["project"]["version"] == TAG.removeprefix("v")
    for relative in (
        "README.md",
        "REPRODUCING.md",
        "docs/releases/v0.1.0.md",
        "paper/main.tex",
    ):
        assert TAG in _read(relative), relative
    assert "git clone --branch v0.1.0 --recurse-submodules" in _read(
        "REPRODUCING.md"
    ).replace("\\\n  ", "")


def test_release_archive_covers_required_versioned_evidence_layers() -> None:
    release = _read("docs/releases/v0.1.0.md")

    for required_path in (
        "REPRODUCING.md",
        "UPSTREAM.md",
        "LICENSES.md",
        "configs",
        "docs/artifacts",
        "docs/evidence",
        "paper",
    ):
        assert required_path in release
        assert (ROOT / required_path).exists()
    assert "mwpc-exact-v0.1.0-paper.pdf" in release
    assert "mwpc-exact-v0.1.0-evidence.tar.gz" in release
    assert "SHA256SUMS" in release
    assert "evidence-only archive" in release
    assert "not a standalone source checkout" in release


def test_release_records_scientific_and_external_boundaries() -> None:
    release = _read("docs/releases/v0.1.0.md")
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
        "parent research-code license remains an author decision",
    ):
        assert boundary in normalized


def test_paper_has_no_unresolved_implementation_or_result_placeholder() -> None:
    article = _read("paper/main.tex")
    placeholders = set(re.findall(r"\\ph\{([^}]+)\}", article))

    assert placeholders == {
        "Advisor name",
        "Campus and institutional address",
        "email addresses",
    }
    for forbidden in ("[TO BE MEASURED]", "[MODEL_ID]", "[paper section]"):
        assert forbidden not in article
    assert "Reproduction commands and final repository tag" in _read(
        "paper/FIELDS_TO_FILL.md"
    )
    assert "- [x] Reproduction commands and final repository tag" in _read(
        "paper/FIELDS_TO_FILL.md"
    )
