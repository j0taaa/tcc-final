from __future__ import annotations

import runpy
import tarfile
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_source_distribution_excludes_nested_build_outputs() -> None:
    from hatchling.builders.sdist import SdistBuilder

    files = tuple(SdistBuilder(str(ROOT)).recurse_included_files())
    assert files
    assert not any("target" in Path(item.relative_path).parts for item in files)
    assert sum(Path(item.path).stat().st_size for item in files) < 50_000_000


def test_archive_inspection_rejects_a_nested_vendor_target(tmp_path: Path) -> None:
    archive = tmp_path / "bad.tar.gz"
    with tarfile.open(archive, "w:gz") as output:
        output.addfile(
            tarfile.TarInfo("mwpc/vendor/EPIC-Decoding/rustformlang/target/debug/binary")
        )
    inspect = runpy.run_path(str(ROOT / "scripts/rehearse_release_wheel.py"))["_inspect_sdist"]
    with pytest.raises(RuntimeError, match="generated/local"):
        inspect(archive)


def test_reproducibility_entrypoints_use_exact_constraints() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert all(
        "==" in dependency for dependency in config["project"]["optional-dependencies"]["dev"]
    )
    toolchain = tomllib.loads((ROOT / "rust-toolchain.toml").read_text())
    assert toolchain["toolchain"]["channel"] == "1.98.0"
    constraints = (ROOT / "requirements/constraints-py311-linux.txt").read_text()
    assert all(
        "==" in line for line in constraints.splitlines() if line and not line.startswith("#")
    )
    assert "constraints-py311-linux.txt" in (ROOT / "Makefile").read_text()
    assert "constraints-py311-linux.txt" in (ROOT / ".github/workflows/ci.yml").read_text()
