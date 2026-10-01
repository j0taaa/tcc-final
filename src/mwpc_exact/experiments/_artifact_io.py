"""Shared artifact I/O validation; no solvers, statistics or oracles."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path
from typing import cast

_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exact_fields(
    value: Mapping[str, object],
    required: set[str],
    field_name: str,
) -> None:
    missing = required - set(value)
    if missing:
        raise ValueError(f"missing {field_name} fields: {', '.join(sorted(missing))}")
    unknown = set(value) - required
    if unknown:
        raise ValueError(f"unknown {field_name} fields: {', '.join(sorted(unknown))}")


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} must be a string-keyed mapping")
    return cast(Mapping[str, object], value)


def _safe_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a safe lowercase identifier")
    return value


def _relative_path(value: object, field_name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError(f"{field_name} must stay inside the repository")
    return path


def _digest(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _resolved_within(repository_root: Path, relative: Path, field_name: str) -> Path:
    root = repository_root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{field_name} resolves outside the repository")
    return resolved


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"raw JSONL contains non-finite constant: {value}")


def _latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def _boolean(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean")
    return value
