from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from mwpc_exact.experiments import (
    ARTIFACT_FIGURE_FILENAME,
    ARTIFACT_MANIFEST_FILENAME,
    ARTIFACT_TABLE_FILENAME,
    build_publication_artifacts,
    default_processed_directory,
    load_artifact_build_config,
    prepare_artifact_directories,
)


def _write_fixture_repository(root: Path) -> tuple[Path, Path, bytes]:
    raw_relative = Path("raw/example/run-1/rows.jsonl")
    raw_path = root / raw_relative
    raw_path.parent.mkdir(parents=True)
    rows = (
        {
            "artifact_kind": "mwpc_test_row",
            "schema_version": 1,
            "example_id": "optimal",
            "solver_status": "optimal",
            "objective_value": 3.0,
            "nested": {"a/b": [1, 2], "empty": {}},
        },
        {
            "artifact_kind": "mwpc_test_row",
            "schema_version": 1,
            "example_id": "timeout",
            "solver_status": "timeout",
            "objective_value": None,
            "nested": {"a/b": [], "empty": {}},
        },
    )
    payload = b"".join(
        (
            json.dumps(row, allow_nan=False, separators=(",", ":"), sort_keys=True)
            + "\n"
        ).encode("utf-8")
        for row in rows
    )
    raw_path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    config_path = root / "configs/artifacts.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "\n".join(
            (
                "schema_version = 1",
                'artifact_id = "test_artifacts_v1"',
                'processed_directory = "processed/test_artifacts_v1"',
                'paper_directory = "paper/generated/test_artifacts_v1"',
                "",
                "[[inputs]]",
                'input_id = "test_rows"',
                f'raw_jsonl = "{raw_relative.as_posix()}"',
                f'expected_sha256 = "{digest}"',
                "",
            )
        ),
        encoding="utf-8",
    )
    return config_path, raw_path, payload


def test_deleting_derived_outputs_and_rebuilding_from_raw_is_byte_identical(
    tmp_path: Path,
) -> None:
    config_path, raw_path, raw_payload = _write_fixture_repository(tmp_path)

    first = build_publication_artifacts(config_path, repository_root=tmp_path)
    first_bytes = {
        relative: (tmp_path / relative).read_bytes()
        for relative in first.output_sha256
    }
    assert raw_path.read_bytes() == raw_payload
    assert first.verified_existing is False

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        build_publication_artifacts(config_path, repository_root=tmp_path)

    shutil.rmtree(tmp_path / "processed")
    shutil.rmtree(tmp_path / "paper/generated")
    assert raw_path.read_bytes() == raw_payload

    second = build_publication_artifacts(config_path, repository_root=tmp_path)
    second_bytes = {
        relative: (tmp_path / relative).read_bytes()
        for relative in second.output_sha256
    }
    assert second.output_sha256 == first.output_sha256
    assert second_bytes == first_bytes
    assert raw_path.read_bytes() == raw_payload

    verified = build_publication_artifacts(
        config_path,
        repository_root=tmp_path,
        verify_existing=True,
    )
    assert verified.verified_existing is True
    assert verified.output_sha256 == first.output_sha256


def test_generated_csv_manifest_table_and_figure_are_source_derived(tmp_path: Path) -> None:
    config_path, _, _ = _write_fixture_repository(tmp_path)

    result = build_publication_artifacts(config_path, repository_root=tmp_path)

    csv_path = tmp_path / "processed/test_artifacts_v1/test_rows.csv"
    with csv_path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 2
    assert rows[0]["/solver_status"] == '"optimal"'
    assert rows[1]["/objective_value"] == "null"
    assert "/nested/a~1b" in rows[0]

    manifest = json.loads(
        (tmp_path / "processed/test_artifacts_v1" / ARTIFACT_MANIFEST_FILENAME).read_text()
    )
    assert manifest["sources"][0]["row_count"] == 2
    assert manifest["sources"][0]["sha256"] == next(iter(result.source_sha256.values()))
    assert len(manifest["generated_artifacts"]) == 3
    table = (
        tmp_path / "paper/generated/test_artifacts_v1" / ARTIFACT_TABLE_FILENAME
    ).read_text()
    figure = (
        tmp_path / "paper/generated/test_artifacts_v1" / ARTIFACT_FIGURE_FILENAME
    ).read_text()
    assert "% Do not edit numeric values manually." in table
    assert r"test\_rows & mwpc\_test\_row & 2" in table
    assert "Raw artifact row inventory" in figure
    assert ">2</text>" in figure


def test_verify_detects_hand_edited_derived_artifact(tmp_path: Path) -> None:
    config_path, _, _ = _write_fixture_repository(tmp_path)
    build_publication_artifacts(config_path, repository_root=tmp_path)
    table_path = tmp_path / "paper/generated/test_artifacts_v1" / ARTIFACT_TABLE_FILENAME
    table_path.write_text("manually edited\n", encoding="utf-8")

    with pytest.raises(ValueError, match="differs from raw inputs"):
        build_publication_artifacts(
            config_path,
            repository_root=tmp_path,
            verify_existing=True,
        )


def test_config_and_raw_hash_validation_fail_closed(tmp_path: Path) -> None:
    config_path, raw_path, _ = _write_fixture_repository(tmp_path)
    config = load_artifact_build_config(config_path)
    assert config.artifact_id == "test_artifacts_v1"
    raw_path.write_text('{"artifact_kind":"changed","schema_version":1}\n')

    with pytest.raises(ValueError, match="raw artifact hash mismatch"):
        build_publication_artifacts(config_path, repository_root=tmp_path)


def test_raw_and_processed_directories_must_be_separate_and_non_nested(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="distinct and non-nested"):
        prepare_artifact_directories(tmp_path / "run", tmp_path / "run/processed")

    raw, processed = prepare_artifact_directories(
        tmp_path / "raw/run",
        tmp_path / "processed/run",
    )
    assert raw.is_dir()
    assert processed.is_dir()
    assert default_processed_directory(
        tmp_path / "repository/results/raw/q1/run",
        tmp_path / "repository",
    ) == (tmp_path / "repository/results/processed/q1/run")
