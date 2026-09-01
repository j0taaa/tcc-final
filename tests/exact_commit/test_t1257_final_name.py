from __future__ import annotations

import json
import tomllib
from pathlib import Path

from mwpc_research.final_artifacts import FINAL_NAME_CLARIFICATION

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = REPOSITORY_ROOT / "docs/artifacts/processed/t1203_final_results_v1"
CONFIG_PATH = REPOSITORY_ROOT / "configs/analysis/t1203_final_artifacts_v1.toml"
EXPECTED_RAW_HASHES = {
    "q1_correctness": "62fb83b48c8809a3958df486b387e017ba245e97e4e74e475ca1fb55659ade8a",
    "q2_heuristic_gap": "1af3865368c0cff24bf75fe103354bd51e0bd42bd7a381ba1b3cec3538a0a2e1",
    "q3_finite_slots": "060957e2a68d71a30696b6406e43d737458f0a13ae0ca1abd750885220c3ce20",
    "q4_scaling": "4ece645bc4b9a497623738b378bf58bba05805c6fa03bf49a555973dcf8a0765",
    "q5_end_to_end": "1132d0f29561d7b3eca8a72d382c22422275f2f54eb462da264b4fc1da9508b4",
}


def test_t1257_generated_bundle_carries_the_name_clarification() -> None:
    results = json.loads((PROCESSED / "final-results.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (PROCESSED / "artifact-manifest.json").read_text(encoding="utf-8")
    )

    assert results["artifact_id"] == manifest["artifact_id"] == "t1203_final_results_v1"
    assert results["name_clarification"] == FINAL_NAME_CLARIFICATION
    assert manifest["name_clarification"] == FINAL_NAME_CLARIFICATION


def test_t1257_reader_entry_points_show_the_clarification_before_results() -> None:
    reproducing = (REPOSITORY_ROOT / "REPRODUCING.md").read_text(encoding="utf-8")
    storage = (REPOSITORY_ROOT / "docs/artifacts/README.md").read_text(encoding="utf-8")
    normalized_reproducing = " ".join(reproducing.split())
    normalized_storage = " ".join(storage.split())

    assert "T1203 name clarification" in reproducing
    assert "M13 source note" in storage
    assert "publication-level benchmark status" in normalized_reproducing
    assert "publication-level benchmark status" in normalized_storage
    assert "new bundle ID" in normalized_reproducing
    assert "never overwrite" in normalized_reproducing
    assert "new bundle ID" in normalized_storage
    assert "never overwrite" in normalized_storage
    assert reproducing.index("T1203 name clarification") < reproducing.index(
        "## 1. Prerequisites"
    )
    assert storage.index("M13 source note") < storage.index("## Final T1203")
    assert "m125_publication_results_v1" in storage


def test_t1257_keeps_every_t1203_raw_input_hash_stable() -> None:
    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert config["artifact_id"] == "t1203_final_results_v1"
    assert {item["role"]: item["expected_sha256"] for item in config["inputs"]} == (
        EXPECTED_RAW_HASHES
    )
