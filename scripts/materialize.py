#!/usr/bin/env python3
"""Download and safely expand the immutable, SHA-256-verified source snapshot."""
from __future__ import annotations

import base64
import hashlib
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / ".bootstrap"
HASH_FILE = BOOTSTRAP / "source-template.sha256"
SOURCE_COMMIT = "2ae9fe6a888d0e97f5921810c8effa4c7024ca30"
SOURCE_BASE = (
    "https://raw.githubusercontent.com/j0taaa/tcc/"
    f"{SOURCE_COMMIT}/.bootstrap"
)
CHUNK_COUNT = 6


def download(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "tcc-final-bootstrap/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"failed to download {url}: {exc}") from exc


def patch_repository_references() -> None:
    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        text = text.replace(
            "git clone --branch exact-cfg-dllm --recurse-submodules \\\n  https://github.com/j0taaa/tcc.git exact-cfg-dllm\ncd exact-cfg-dllm",
            "git clone --recurse-submodules https://github.com/j0taaa/tcc-final.git\ncd tcc-final",
        )
        text = text.replace("j0taaa/tcc.git", "j0taaa/tcc-final.git")
        readme.write_text(text, encoding="utf-8")

    ci = ROOT / ".github" / "workflows" / "ci.yml"
    if ci.exists():
        text = ci.read_text(encoding="utf-8")
        text = text.replace('branches: ["exact-cfg-dllm"]', 'branches: ["main"]')
        ci.write_text(text, encoding="utf-8")

    status = ROOT / "BOOTSTRAP_STATUS.md"
    if status.exists():
        text = status.read_text(encoding="utf-8")
        text = text.replace("Target branch: `exact-cfg-dllm`", "Definitive repository: `j0taaa/tcc-final` on `main`")
        text = text.replace("Existing unrelated `main`: intentionally unchanged", "The `main` branch is the definitive TCC workspace")
        status.write_text(text, encoding="utf-8")


def main() -> int:
    expected = HASH_FILE.read_text(encoding="utf-8").strip()
    try:
        encoded = b"".join(
            download(f"{SOURCE_BASE}/chunk-{index:02d}.b64")
            for index in range(CHUNK_COUNT)
        )
        archive_bytes = base64.b64decode(encoded, validate=True)
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    actual = hashlib.sha256(archive_bytes).hexdigest()
    if actual != expected:
        print(f"bootstrap archive hash mismatch: {actual} != {expected}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="mwpc-bootstrap-") as temp_dir:
        temp = Path(temp_dir)
        archive_path = temp / "template.zip"
        archive_path.write_bytes(archive_bytes)
        expanded_root = (temp / "expanded").resolve()
        expanded_root.mkdir()

        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                target = (expanded_root / member.filename).resolve()
                if expanded_root not in target.parents and target != expanded_root:
                    print(f"unsafe archive member: {member.filename}", file=sys.stderr)
                    return 1
            archive.extractall(expanded_root)

        copied = 0
        for source in sorted(expanded_root.rglob("*")):
            relative = source.relative_to(expanded_root)
            rel_text = relative.as_posix()
            if (
                rel_text == ".git"
                or rel_text.startswith(".git/")
                or rel_text.startswith(".bootstrap/")
                or rel_text == "scripts/materialize.py"
                or rel_text.startswith("vendor/EPIC-Decoding/")
            ):
                continue
            destination = ROOT / relative
            if source.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied += 1

    patch_repository_references()
    for path in (
        ROOT / "scripts" / "bootstrap.sh",
        ROOT / "scripts" / "verify_upstream.sh",
        ROOT / "scripts" / "materialize.py",
    ):
        if path.exists():
            os.chmod(path, path.stat().st_mode | 0o111)

    (ROOT / "PROJECT_MATERIALIZED").write_text(
        "Workspace materialized from immutable snapshot " + SOURCE_COMMIT + "\n",
        encoding="utf-8",
    )
    print(f"materialized {copied} files from immutable source {SOURCE_COMMIT}")
    print("next: git submodule update --init --recursive && make bootstrap && make check")
    print("then review git status, commit the expanded tree and begin TASKS.md at T000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
