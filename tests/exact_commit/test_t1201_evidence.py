from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from mwpc_exact.experiments import build_publication_artifacts

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/analysis/t1201_q3_artifacts_v1.toml"
RAW_DIRECTORY = REPOSITORY_ROOT / "docs/artifacts/raw/t1201_q3_finite_slots_v1"
PROCESSED_DIRECTORY = REPOSITORY_ROOT / "docs/artifacts/processed/t1201_q3_finite_slots_v1"
PAPER_DIRECTORY = REPOSITORY_ROOT / "paper/generated/t1201_q3_finite_slots_v1"
T1201_IMPLEMENTATION_COMMIT = "b463ca37a3225d5ca0eb688e0864fa7e66c1ce0b"
RAW_SHA256 = "454b2ec1efd6cff32913d501179050b0008eb974bc5ef4563bd6d62f0e2cd997"
EXPECTED_OUTPUT_SHA256 = {
    "docs/artifacts/processed/t1201_q3_finite_slots_v1/artifact-manifest.json": (
        "2f46fcddbe21eab7eaf88f093ee652e8aae32b684fdf0df960ffa427de12af42"
    ),
    "docs/artifacts/processed/t1201_q3_finite_slots_v1/q3_finite_slot_rows.csv": (
        "0b073202534bea277301ebbb28431440c43191fed35932a5b9bdb5c4f72d23c3"
    ),
    "paper/generated/t1201_q3_finite_slots_v1/artifact-inventory.tex": (
        "040ebe421c236da01db741e834155c8f383df8471dde263abea7240151b133ec"
    ),
    "paper/generated/t1201_q3_finite_slots_v1/artifact-row-counts.svg": (
        "be08804a25f320d1e6dffa3fc288d28969569a7c97d030e22c56e7630a53eb54"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_t1201_versioned_artifacts_are_clean_source_derived_and_reproducible() -> None:
    raw_path = RAW_DIRECTORY / "q3-finite-slot-rows.jsonl"
    raw_rows = [json.loads(line) for line in raw_path.read_text().splitlines()]
    assert _sha256(raw_path) == RAW_SHA256
    assert {path.name for path in RAW_DIRECTORY.iterdir()} == {
        "q3-finite-slot-rows.jsonl",
        "resolved-config.json",
    }
    assert len(raw_rows) == 2
    assert all(row["success"] is True for row in raw_rows)
    assert all(row["run_metadata"]["git_commit"] == T1201_IMPLEMENTATION_COMMIT for row in raw_rows)
    assert all(row["run_metadata"]["git_dirty"] is False for row in raw_rows)
    assert all(
        row["run_metadata"]["metadata_integrity"]
        == {
            "critical_fields_complete": True,
            "missing_critical_fields": [],
            "publication_blockers": [],
        }
        for row in raw_rows
    )

    assert {path.name for path in PROCESSED_DIRECTORY.iterdir()} == {
        "artifact-manifest.json",
        "q3_finite_slot_rows.csv",
    }
    assert {path.name for path in PAPER_DIRECTORY.iterdir()} == {
        "artifact-inventory.tex",
        "artifact-row-counts.svg",
    }
    with (PROCESSED_DIRECTORY / "q3_finite_slot_rows.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        assert len(list(csv.DictReader(source))) == len(raw_rows)

    verified = build_publication_artifacts(
        CONFIG_PATH,
        repository_root=REPOSITORY_ROOT,
        verify_existing=True,
    )
    assert verified.source_sha256 == {
        "docs/artifacts/raw/t1201_q3_finite_slots_v1/q3-finite-slot-rows.jsonl": (RAW_SHA256)
    }
    assert verified.output_sha256 == EXPECTED_OUTPUT_SHA256
    for relative_path, expected_sha256 in EXPECTED_OUTPUT_SHA256.items():
        assert _sha256(REPOSITORY_ROOT / relative_path) == expected_sha256
