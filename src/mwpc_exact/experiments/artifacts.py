"""Deterministic separation and generation of research artifacts."""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from mwpc_exact.experiments.metadata import canonical_json_sha256

ARTIFACT_BUILD_SCHEMA_VERSION = 1
ARTIFACT_MANIFEST_KIND = "mwpc_publication_artifact_manifest"
ARTIFACT_MANIFEST_FILENAME = "artifact-manifest.json"
ARTIFACT_TABLE_FILENAME = "artifact-inventory.tex"
ARTIFACT_FIGURE_FILENAME = "artifact-row-counts.svg"

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


@dataclass(frozen=True, slots=True)
class RawArtifactInput:
    """One immutable JSONL input declared by an artifact-build config."""

    input_id: str
    raw_jsonl: Path
    expected_sha256: str

    def __post_init__(self) -> None:
        _safe_id(self.input_id, "inputs[].input_id")
        _relative_path(self.raw_jsonl.as_posix(), "inputs[].raw_jsonl")
        _digest(self.expected_sha256, "inputs[].expected_sha256")

    @property
    def csv_filename(self) -> str:
        return f"{self.input_id}.csv"


@dataclass(frozen=True, slots=True)
class ArtifactBuildConfig:
    """Strict immutable raw-to-publication artifact build configuration."""

    schema_version: int
    artifact_id: str
    processed_directory: Path
    paper_directory: Path
    inputs: tuple[RawArtifactInput, ...]
    config_sha256: str
    config_file_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != ARTIFACT_BUILD_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {ARTIFACT_BUILD_SCHEMA_VERSION}"
            )
        _safe_id(self.artifact_id, "artifact_id")
        _relative_path(self.processed_directory.as_posix(), "processed_directory")
        _relative_path(self.paper_directory.as_posix(), "paper_directory")
        if self.processed_directory == self.paper_directory:
            raise ValueError("processed and paper directories must be distinct")
        if not self.inputs:
            raise ValueError("inputs must be non-empty")
        if len({item.input_id for item in self.inputs}) != len(self.inputs):
            raise ValueError("input_id values must be unique")
        if len({item.raw_jsonl for item in self.inputs}) != len(self.inputs):
            raise ValueError("raw_jsonl paths must be unique")
        _digest(self.config_sha256, "config_sha256")
        _digest(self.config_file_sha256, "config_file_sha256")


def load_artifact_build_config(path: str | Path) -> ArtifactBuildConfig:
    """Load and strictly validate one versioned artifact-build TOML file."""

    config_path = Path(path)
    payload = config_path.read_bytes()
    try:
        raw = tomllib.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"invalid artifact-build TOML: {config_path}") from error
    root = _mapping(raw, "artifact config")
    _exact_fields(
        root,
        {
            "schema_version",
            "artifact_id",
            "processed_directory",
            "paper_directory",
            "inputs",
        },
        "artifact config",
    )
    raw_inputs = root["inputs"]
    if isinstance(raw_inputs, (str, bytes)) or not isinstance(raw_inputs, Sequence):
        raise TypeError("inputs must be an array of tables")
    inputs: list[RawArtifactInput] = []
    for index, raw_input in enumerate(raw_inputs):
        item = _mapping(raw_input, f"inputs[{index}]")
        _exact_fields(
            item,
            {"input_id", "raw_jsonl", "expected_sha256"},
            f"inputs[{index}]",
        )
        inputs.append(
            RawArtifactInput(
                input_id=_safe_id(item["input_id"], f"inputs[{index}].input_id"),
                raw_jsonl=_relative_path(
                    item["raw_jsonl"], f"inputs[{index}].raw_jsonl"
                ),
                expected_sha256=_digest(
                    item["expected_sha256"], f"inputs[{index}].expected_sha256"
                ),
            )
        )
    schema = root["schema_version"]
    if isinstance(schema, bool) or not isinstance(schema, int):
        raise TypeError("schema_version must be an integer")
    return ArtifactBuildConfig(
        schema_version=schema,
        artifact_id=_safe_id(root["artifact_id"], "artifact_id"),
        processed_directory=_relative_path(
            root["processed_directory"], "processed_directory"
        ),
        paper_directory=_relative_path(root["paper_directory"], "paper_directory"),
        inputs=tuple(inputs),
        config_sha256=canonical_json_sha256(raw),
        config_file_sha256=_sha256_bytes(payload),
    )


def _resolved_within(repository_root: Path, relative: Path, field_name: str) -> Path:
    root = repository_root.resolve()
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{field_name} resolves outside the repository")
    return resolved


def prepare_artifact_directories(
    raw_directory: str | Path,
    processed_directory: str | Path,
) -> tuple[Path, Path]:
    """Create distinct non-nested raw and processed output directories."""

    raw = Path(raw_directory).resolve()
    processed = Path(processed_directory).resolve()
    if raw == processed or raw.is_relative_to(processed) or processed.is_relative_to(raw):
        raise ValueError("raw and processed directories must be distinct and non-nested")
    raw.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    return raw, processed


def default_processed_directory(
    raw_directory: str | Path,
    repository_root: str | Path,
) -> Path:
    """Map a standard results/raw run to results/processed without ambiguity."""

    raw = Path(raw_directory).resolve()
    root = Path(repository_root).resolve()
    standard_raw = root / "results/raw"
    if raw.is_relative_to(standard_raw):
        return root / "results/processed" / raw.relative_to(standard_raw)
    return raw.parent / f"{raw.name}-processed"


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"raw JSONL contains non-finite constant: {value}")


@dataclass(frozen=True, slots=True)
class _LoadedInput:
    declaration: RawArtifactInput
    rows: tuple[Mapping[str, object], ...]
    artifact_kinds: tuple[str, ...]
    schema_versions: tuple[int, ...]


def _load_input(path: Path, declaration: RawArtifactInput) -> _LoadedInput:
    observed = _sha256_file(path)
    if observed != declaration.expected_sha256:
        raise ValueError(
            f"raw artifact hash mismatch for {declaration.input_id}: "
            f"expected {declaration.expected_sha256}, observed {observed}"
        )
    payload = path.read_bytes()
    if not payload or not payload.endswith(b"\n"):
        raise ValueError("raw JSONL must be non-empty and newline-terminated")
    rows: list[Mapping[str, object]] = []
    kinds: set[str] = set()
    versions: set[int] = set()
    for line_number, raw_line in enumerate(payload.splitlines(), start=1):
        if not raw_line:
            raise ValueError(f"raw JSONL line {line_number} is blank")
        try:
            value = json.loads(
                raw_line,
                parse_constant=_reject_json_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid raw JSONL line {line_number}") from error
        row = _mapping(value, f"raw JSONL line {line_number}")
        kind = row.get("artifact_kind")
        version = row.get("schema_version")
        if not isinstance(kind, str) or not kind:
            raise ValueError(f"raw JSONL line {line_number} lacks artifact_kind")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise ValueError(f"raw JSONL line {line_number} lacks a valid schema_version")
        kinds.add(kind)
        versions.add(version)
        rows.append(row)
    if _sha256_file(path) != observed:
        raise RuntimeError("raw artifact changed while derived outputs were being built")
    return _LoadedInput(
        declaration=declaration,
        rows=tuple(rows),
        artifact_kinds=tuple(sorted(kinds)),
        schema_versions=tuple(sorted(versions)),
    )


def _json_pointer_segment(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _flatten_json(value: object, prefix: str = "") -> dict[str, str]:
    if isinstance(value, Mapping) and value:
        flattened: dict[str, str] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError("raw JSON mappings must use string keys")
            child = f"{prefix}/{_json_pointer_segment(key)}"
            flattened.update(_flatten_json(value[key], child))
        return flattened
    return {prefix or "/": _canonical_json(value)}


def _csv_bytes(rows: Sequence[Mapping[str, object]]) -> bytes:
    flattened = tuple(_flatten_json(row) for row in rows)
    columns = sorted({column for row in flattened for column in row})
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=columns,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(flattened)
    return output.getvalue().encode("utf-8")


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


def _table_bytes(inputs: Sequence[_LoadedInput]) -> bytes:
    lines = [
        "% Generated by scripts/exact_commit/build_publication_artifacts.py.",
        "% Do not edit numeric values manually.",
        r"\begin{tabular}{llrl}",
        r"\toprule",
        r"Input & Artifact kind & Rows & Raw SHA-256 \\",
        r"\midrule",
    ]
    for item in inputs:
        kinds = ", ".join(item.artifact_kinds)
        lines.append(
            f"{_latex_escape(item.declaration.input_id)} & "
            f"{_latex_escape(kinds)} & {len(item.rows)} & "
            f"\\texttt{{{item.declaration.expected_sha256[:12]}}} \\\\"
        )
    lines.extend((r"\bottomrule", r"\end{tabular}", ""))
    return "\n".join(lines).encode("utf-8")


def _figure_bytes(inputs: Sequence[_LoadedInput]) -> bytes:
    width = 900
    top = 70
    row_height = 52
    height = top + row_height * len(inputs) + 30
    maximum = max(len(item.rows) for item in inputs)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="white"/>',
        (
            '<text x="20" y="32" font-family="sans-serif" font-size="20" '
            'font-weight="bold">Raw artifact row inventory</text>'
        ),
    ]
    for index, item in enumerate(inputs):
        y = top + index * row_height
        bar_width = max(1, 600 * len(item.rows) // maximum)
        label = html.escape(item.declaration.input_id, quote=True)
        lines.extend(
            (
                f'<text x="20" y="{y + 20}" font-family="sans-serif" '
                f'font-size="15">{label}</text>',
                f'<rect x="220" y="{y}" width="{bar_width}" height="28" '
                'fill="#2f6f9f"/>',
                f'<text x="{230 + bar_width}" y="{y + 20}" '
                f'font-family="sans-serif" font-size="15">{len(item.rows)}</text>',
            )
        )
    lines.append("</svg>")
    lines.append("")
    return "\n".join(lines).encode("utf-8")


@dataclass(frozen=True, slots=True)
class ArtifactBuildResult:
    """Paths and hashes for one created or verified deterministic build."""

    artifact_id: str
    output_sha256: Mapping[str, str]
    source_sha256: Mapping[str, str]
    verified_existing: bool


def build_publication_artifacts(
    config_path: str | Path,
    *,
    repository_root: str | Path,
    verify_existing: bool = False,
) -> ArtifactBuildResult:
    """Create or byte-verify CSV, manifest, SVG, and LaTeX from raw JSONL."""

    if not isinstance(verify_existing, bool):
        raise TypeError("verify_existing must be a boolean")
    root = Path(repository_root).resolve()
    config_file = Path(config_path).resolve()
    if not config_file.is_relative_to(root):
        raise ValueError("artifact config must be inside the repository")
    config = load_artifact_build_config(config_file)
    processed = _resolved_within(root, config.processed_directory, "processed_directory")
    paper = _resolved_within(root, config.paper_directory, "paper_directory")
    if processed == paper or processed.is_relative_to(paper) or paper.is_relative_to(processed):
        raise ValueError("processed and paper directories must be distinct and non-nested")

    loaded: list[_LoadedInput] = []
    for declaration in config.inputs:
        raw_path = _resolved_within(root, declaration.raw_jsonl, "raw_jsonl")
        if raw_path.is_relative_to(processed) or raw_path.is_relative_to(paper):
            raise ValueError("raw artifacts cannot live inside derived output directories")
        loaded.append(_load_input(raw_path, declaration))

    table_path = paper / ARTIFACT_TABLE_FILENAME
    figure_path = paper / ARTIFACT_FIGURE_FILENAME
    rendered: dict[Path, bytes] = {
        processed / item.declaration.csv_filename: _csv_bytes(item.rows)
        for item in loaded
    }
    rendered[table_path] = _table_bytes(loaded)
    rendered[figure_path] = _figure_bytes(loaded)
    generated_entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256_bytes(payload),
        }
        for path, payload in sorted(rendered.items(), key=lambda pair: pair[0].as_posix())
    ]
    manifest = {
        "artifact_kind": ARTIFACT_MANIFEST_KIND,
        "schema_version": ARTIFACT_BUILD_SCHEMA_VERSION,
        "artifact_id": config.artifact_id,
        "configuration": {
            "path": config_file.relative_to(root).as_posix(),
            "normalized_sha256": config.config_sha256,
            "file_sha256": config.config_file_sha256,
        },
        "sources": [
            {
                "input_id": item.declaration.input_id,
                "path": item.declaration.raw_jsonl.as_posix(),
                "sha256": item.declaration.expected_sha256,
                "row_count": len(item.rows),
                "artifact_kinds": list(item.artifact_kinds),
                "schema_versions": list(item.schema_versions),
            }
            for item in loaded
        ],
        "generated_artifacts": generated_entries,
    }
    manifest_path = processed / ARTIFACT_MANIFEST_FILENAME
    rendered[manifest_path] = (
        json.dumps(manifest, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    if verify_existing:
        for path, expected in rendered.items():
            if not path.is_file():
                raise FileNotFoundError(f"generated artifact is missing: {path}")
            if path.read_bytes() != expected:
                raise ValueError(f"generated artifact differs from raw inputs: {path}")
    else:
        existing = [path for path in rendered if path.exists()]
        if existing:
            raise FileExistsError(
                "refusing to overwrite derived artifacts: "
                + ", ".join(path.as_posix() for path in sorted(existing))
            )
        processed.mkdir(parents=True, exist_ok=True)
        paper.mkdir(parents=True, exist_ok=True)
        for path, payload in sorted(rendered.items(), key=lambda pair: pair[0].as_posix()):
            with path.open("xb") as output:
                output.write(payload)

    return ArtifactBuildResult(
        artifact_id=config.artifact_id,
        output_sha256={
            path.relative_to(root).as_posix(): _sha256_bytes(payload)
            for path, payload in sorted(rendered.items(), key=lambda pair: pair[0].as_posix())
        },
        source_sha256={
            item.declaration.raw_jsonl.as_posix(): item.declaration.expected_sha256
            for item in loaded
        },
        verified_existing=verify_existing,
    )


__all__ = [
    "ARTIFACT_BUILD_SCHEMA_VERSION",
    "ARTIFACT_FIGURE_FILENAME",
    "ARTIFACT_MANIFEST_FILENAME",
    "ARTIFACT_MANIFEST_KIND",
    "ARTIFACT_TABLE_FILENAME",
    "ArtifactBuildConfig",
    "ArtifactBuildResult",
    "RawArtifactInput",
    "build_publication_artifacts",
    "default_processed_directory",
    "load_artifact_build_config",
    "prepare_artifact_directories",
]
