"""Freeze independent research snapshots; check preservation, not correctness."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARCHIVES = ROOT / "attempts"
OMITTED = ("attempts/", "docs/artifacts/raw/", "docs/artifacts/processed/")


def tree(commit: str) -> dict[str, tuple[str, str, str]]:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Snapshots require full immutable Git commit hashes")
    output = subprocess.check_output(["git", "ls-tree", "-rz", commit], cwd=ROOT)
    result = {}
    for row in output.split(b"\0"):
        if row:
            metadata, path = row.decode().split("\t", 1)
            result[path] = tuple(metadata.split())
    return result


def selected(
    entries: dict[str, tuple[str, str, str]], kind: str, roots: list[str], attempt_id: str
) -> dict[str, tuple[str, str, str]]:
    return {
        path: entry
        for path, entry in entries.items()
        if entry[1] == "blob"
        and (
            not path.startswith(OMITTED) or path.startswith(f"attempts/{attempt_id}/work/")
            if kind == "source"
            else any(path == root or path.startswith(root + "/") for root in roots)
        )
    }


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def freeze_zip(path: Path, entries: dict[str, tuple[str, str, str]]) -> dict[str, Any]:
    inventory = {}
    with (
        subprocess.Popen(
            ["git", "cat-file", "--batch"], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE
        ) as process,
        zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive,
    ):
        assert process.stdin is not None and process.stdout is not None
        for name, (mode, _, oid) in sorted(entries.items()):
            process.stdin.write((oid + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().decode().split()
            if len(header) != 3 or header[:2] != [oid, "blob"]:
                raise ValueError(f"Missing Git blob: {name}")
            data = process.stdout.read(int(header[2]))
            if len(data) != int(header[2]) or process.stdout.read(1) != b"\n":
                raise ValueError(f"Truncated Git blob: {name}")
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = int(mode, 8) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
            inventory[name] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "git_blob": oid,
                "mode": mode,
                "bytes": len(data),
            }
        process.stdin.close()
        if process.wait() != 0:
            raise ValueError("git cat-file failed")
    return {"sha256": digest(path), "files": inventory}


def freeze(attempt: dict[str, Any], version: dict[str, Any]) -> None:
    folder = ARCHIVES / attempt["id"] / version["id"]
    if folder.exists():
        raise FileExistsError(f"Frozen version already exists; choose a new version: {folder}")
    folder.parent.mkdir(parents=True, exist_ok=True)
    entries = {kind: tree(version[f"{kind}_commit"]) for kind in ("source", "evidence")}
    for root in version["evidence_roots"]:
        if not any(path == root or path.startswith(root + "/") for path in entries["evidence"]):
            raise ValueError(f"Missing evidence root: {root}")
    with tempfile.TemporaryDirectory(prefix=".snapshot-", dir=folder.parent) as temp:
        stage = Path(temp)
        manifest: dict[str, Any] = {
            "schema": 1,
            "attempt_id": attempt["id"],
            "version": version,
            "source_omissions": list(OMITTED),
            "gitlinks": {
                path: entry[2] for path, entry in entries["source"].items() if entry[1] == "commit"
            },
            "archives": {},
        }
        for kind in ("source", "evidence"):
            name = f"{kind}.zip"
            manifest["archives"][name] = freeze_zip(
                stage / name,
                selected(entries[kind], kind, version["evidence_roots"], attempt["id"]),
            )
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        stage.rename(folder)
    print(f"Created {folder.relative_to(ROOT)}")


def check(attempt: dict[str, Any], version: dict[str, Any], check_git: bool) -> tuple[int, int]:
    folder = ARCHIVES / attempt["id"] / version["id"]
    manifest = json.loads((folder / "manifest.json").read_text())
    if (
        manifest["schema"] != 1
        or manifest["attempt_id"] != attempt["id"]
        or manifest["version"] != version
        or set(manifest["archives"]) != {"source.zip", "evidence.zip"}
        or manifest["source_omissions"] != list(OMITTED)
    ):
        raise ValueError(f"Snapshot/catalog mismatch: {folder}")
    count = total = 0
    for name, archived in manifest["archives"].items():
        path = folder / name
        if digest(path) != archived["sha256"]:
            raise ValueError(f"Changed snapshot: {path}")
        with zipfile.ZipFile(path) as archive:
            if sorted(archive.namelist()) != sorted(archived["files"]):
                raise ValueError(f"Changed inventory: {path}")
            for entry, expected in archived["files"].items():
                data = archive.read(entry)
                blob = b"blob " + str(len(data)).encode() + b"\0" + data
                if (
                    hashlib.sha256(data).hexdigest() != expected["sha256"]
                    or hashlib.sha1(blob).hexdigest() != expected["git_blob"]
                    or archive.getinfo(entry).external_attr >> 16 != int(expected["mode"], 8)
                    or len(data) != expected["bytes"]
                ):
                    raise ValueError(f"Changed archived file: {path}:{entry}")
                count += 1
                total += len(data)
        if check_git:
            kind = name.removesuffix(".zip")
            entries = tree(version[f"{kind}_commit"])
            origin = selected(entries, kind, version["evidence_roots"], attempt["id"])
            recorded = {
                path: (file["mode"], "blob", file["git_blob"])
                for path, file in archived["files"].items()
            }
            if origin != recorded:
                raise ValueError(f"Snapshot differs from original Git tree: {path}")
            if kind == "source" and manifest["gitlinks"] != {
                path: entry[2] for path, entry in entries.items() if entry[1] == "commit"
            }:
                raise ValueError("Changed external submodule provenance")
    return count, total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--create", metavar="ATTEMPT", help="Registered ID, or all; never overwrites"
    )
    action.add_argument("--check", action="store_true", help="Offline ZIP/per-file integrity")
    parser.add_argument("--git", action="store_true", help="Also compare with original Git trees")
    parser.add_argument("--version", help="Create only this registered version, e.g. v2")
    args = parser.parse_args()
    if args.version and not args.create:
        parser.error("--version requires --create")
    attempts = json.loads((ARCHIVES / "catalog.json").read_text())["attempts"]
    if args.create:
        attempts = [entry for entry in attempts if args.create in ("all", entry["id"])]
        if not attempts:
            parser.error("Unknown attempt ID")
    count = total = versions = 0
    for attempt in attempts:
        for version in attempt["versions"]:
            if args.version and version["id"] != args.version:
                continue
            if args.create:
                freeze(attempt, version)
            files, size = check(attempt, version, args.git)
            count += files
            total += size
            versions += 1
    if not versions:
        parser.error("No matching version")
    print(
        f"Preserved {len(attempts)} attempts / {versions} versions / {count} files "
        f"({total:,} uncompressed bytes); integrity only, not scientific validation"
    )


if __name__ == "__main__":
    main()
