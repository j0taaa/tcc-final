from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

from scripts.install_epic_checkout import EPIC_CHECKOUT, install_path_file

ROOT = Path(__file__).resolve().parents[2]


def load_materialize_module():
    path = ROOT / "scripts" / "materialize.py"
    spec = importlib.util.spec_from_file_location("materialize", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checked_in_bootstrap_archive_is_valid(tmp_path: Path) -> None:
    materialize = load_materialize_module()
    archive_bytes, chunk_count = materialize.load_archive()
    archive_path = tmp_path / "source.zip"
    archive_path.write_bytes(archive_bytes)

    assert chunk_count == 6
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
    assert {"TASKS.md", "src/mwpc_exact/types.py", ".github/workflows/ci.yml"} <= names


def test_materializer_defaults_to_non_destructive_verification(capsys) -> None:
    materialize = load_materialize_module()

    assert materialize.main([]) == 0
    assert "already materialized" in capsys.readouterr().out


def test_materializer_verify_only(capsys) -> None:
    materialize = load_materialize_module()

    assert materialize.main(["--verify-only"]) == 0
    assert "verified 40 members from 6 checked-in chunks" in capsys.readouterr().out


def test_epic_checkout_path_file_is_environment_local(tmp_path: Path) -> None:
    path_file = install_path_file(tmp_path, EPIC_CHECKOUT)

    assert path_file.parent == tmp_path
    assert path_file.read_text(encoding="utf-8") == f"{EPIC_CHECKOUT.resolve()}\n"
