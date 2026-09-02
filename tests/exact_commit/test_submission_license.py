from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIT_COPYRIGHT = "Copyright (c) 2026 Gabriel Jota Lizardo"
EVIDENCE = "docs/evidence/submission-license-release.md"


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_parent_mit_license_is_canonical_and_attributed() -> None:
    license_text = _read("LICENSE")

    assert license_text.startswith("MIT License\n")
    assert MIT_COPYRIGHT in license_text
    assert "Permission is hereby granted, free of charge" in license_text
    assert 'THE SOFTWARE IS PROVIDED "AS IS"' in license_text


def test_license_scopes_preserve_manuscript_and_third_party_boundaries() -> None:
    scopes = _read("LICENSES.md")

    assert "[LICENSE TO BE CHOSEN]" not in scopes
    assert "licensed under the MIT License" in scopes
    assert "manuscript" in scopes
    assert "all rights reserved" in scopes
    assert "vendor/EPIC-Decoding" in scopes
    assert "remains governed by its own `LICENSE`" in scopes
    assert "external model weights" in scopes


def test_python_and_rust_package_metadata_declare_mit() -> None:
    project = tomllib.loads(_read("pyproject.toml"))["project"]
    binding = tomllib.loads(_read("crates/mwpc_parser_py/pyproject.toml"))["project"]

    assert project["version"] == "0.1.1"
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert binding["license"] == "MIT"
    for manifest in (
        "crates/mwpc_parser/Cargo.toml",
        "crates/mwpc_parser_py/Cargo.toml",
    ):
        assert 'license = "MIT"' in _read(manifest)


def test_submission_checklist_and_article_record_the_resolved_license() -> None:
    checklist = _read("paper/FIELDS_TO_FILL.md")
    article = _read("paper/main.tex")

    assert "- [x] Parent repository release license" in checklist
    assert "Parent software and research artifacts use MIT" in article
    assert "Parent release license is pending" not in article
    assert "j0taaa/tcc-final@v0.1.1" in article


def test_licensed_release_evidence_is_versioned_and_current() -> None:
    evidence = _read(EVIDENCE)
    tasks = _read("TASKS.md")

    for value in (
        "3db85bb0ec7e4416352b74832e8a6750af8bcaf2",
        "33584766533",
        "26195f5129bcfb9a09f4c8f892aa4c1708f3f405c78a7d9e3a57858f76ecd1be",
        "f1bb235b40f17ad5f3fd2840fd6511f6fe4ba819fa43c5c1f9d5d90594d86037",
        "249/249 agreement",
        "334 certificate validations",
    ):
        assert value in evidence
    assert "v0.1.1" in tasks
    assert EVIDENCE in tasks
