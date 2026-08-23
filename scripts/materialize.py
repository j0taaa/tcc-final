#!/usr/bin/env python3
"""Safely expand the checked-in, SHA-256-verified source snapshot."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import os
import shutil
import sys
import tempfile
import zipfile
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / ".bootstrap"
HASH_FILE = BOOTSTRAP / "source-template.sha256"
SOURCE_ID = "local-content-addressed-snapshot"


def load_archive() -> tuple[bytes, int]:
    """Decode and verify the locally versioned source archive."""
    chunks = sorted(BOOTSTRAP.glob("chunk-*.b64"))
    if not chunks:
        raise RuntimeError("no local bootstrap chunks found")

    encoded = b"".join(path.read_bytes() for path in chunks)
    try:
        archive_bytes = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise RuntimeError(f"invalid bootstrap base64: {exc}") from exc

    expected = HASH_FILE.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(archive_bytes).hexdigest()
    if actual != expected:
        raise RuntimeError(f"bootstrap archive hash mismatch: {actual} != {expected}")
    return archive_bytes, len(chunks)


def verify_archive(archive_bytes: bytes) -> int:
    """Validate ZIP integrity and reject members that could escape extraction."""
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise RuntimeError(f"corrupt bootstrap archive member: {corrupt_member}")
        members = archive.infolist()
        for member in members:
            path = Path(member.filename)
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeError(f"unsafe archive member: {member.filename}")
    return len(members)


def patch_repository_references() -> None:
    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        text = text.replace(
            "git clone --branch exact-cfg-dllm --recurse-submodules \\\n"
            "  https://github.com/j0taaa/tcc.git exact-cfg-dllm\n"
            "cd exact-cfg-dllm",
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
        text = text.replace(
            "Target branch: `exact-cfg-dllm`",
            "Definitive repository: `j0taaa/tcc-final` on `main`",
        )
        text = text.replace(
            "Existing unrelated `main`: intentionally unchanged",
            "The `main` branch is the definitive TCC workspace",
        )
        status.write_text(text, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="verify the historical archive without changing the working tree",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite the expanded parent files from the historical archive",
    )
    args = parser.parse_args(argv)

    try:
        archive_bytes, chunk_count = load_archive()
        member_count = verify_archive(archive_bytes)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    if args.verify_only:
        print(
            f"verified {member_count} members from {chunk_count} checked-in chunks; "
            f"sha256={archive_hash}"
        )
        return 0

    marker = ROOT / "PROJECT_MATERIALIZED"
    if marker.exists() and not args.force:
        print(
            "workspace is already materialized; archive verified without overwriting files "
            "(pass --force to restore the historical snapshot)"
        )
        return 0

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

    marker.write_text(
        f"Workspace materialized from {SOURCE_ID}; "
        f"sha256={archive_hash}\n",
        encoding="utf-8",
    )
    print(
        f"materialized {copied} files from {chunk_count} checked-in chunks; "
        f"sha256={archive_hash}"
    )
    print("next: git submodule update --init --recursive && make bootstrap && make check")
    print("then review git status, commit the expanded tree and begin TASKS.md at T000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
