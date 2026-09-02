from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIT_COPYRIGHT = "Copyright (c) 2026 Gabriel Jota Lizardo"


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
