from __future__ import annotations

import json
from pathlib import Path

from mwpc_exact.experiments import RUN_METADATA_SCHEMA_VERSION, load_experiment_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q1_correctness_v1.toml"
EVIDENCE_PATH = REPOSITORY_ROOT / "docs/evidence/t1200-run-metadata-sample.json"
T1200_IMPLEMENTATION_COMMIT = "f62765d69ac8fd30d197077ae189ecd1f5607f02"


def test_t1200_sample_has_complete_reproducibility_metadata() -> None:
    config = load_experiment_config(CONFIG_PATH)
    summary = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    metadata = summary["run_metadata"]

    assert summary["artifact_kind"] == "mwpc_q1_correctness_summary"
    assert summary["failed_cases"] == 0
    assert summary["agreement_rate"] == 1.0
    assert metadata["metadata_schema_version"] == RUN_METADATA_SCHEMA_VERSION
    assert metadata["git_commit"] == T1200_IMPLEMENTATION_COMMIT
    assert metadata["git_dirty"] is False
    assert metadata["config_sha256"] == config.config_sha256
    assert metadata["model"] == {
        "local_files_only": config.local_files_only,
        "model_id": config.model_id,
        "requested_revision": config.model_revision,
    }
    assert metadata["tokenizer"] == {
        "requested_revision": config.tokenizer_revision,
        "tokenizer_id": config.tokenizer_id,
    }
    grammar_hashes = metadata["grammar"]["sha256"]
    assert grammar_hashes
    assert all(len(value) == 64 for value in grammar_hashes)

    software = metadata["software_versions"]
    for field in ("python", "rust", "pytorch", "transformers"):
        assert software[field]
    assert any(
        software[field]
        for field in ("cuda_toolkit", "cuda_driver_supported_runtime", "cuda_runtime")
    )

    hardware = metadata["hardware"]
    assert hardware["cpu"]["model"]
    assert hardware["cpu"]["logical_count"] > 0
    assert hardware["ram"]["total_bytes"] > 0
    assert hardware["gpu"]["name"]
    assert hardware["gpu"]["total_vram_bytes"] > 0
    assert hardware["os"]["platform"]
    assert hardware["threads"]["configured_cpu_threads"] == config.cpu_threads
    assert set(hardware["threads"]["environment"]) == {
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "RAYON_NUM_THREADS",
        "RUST_MIN_STACK",
    }
    assert metadata["solver_status_counts"] == summary["solver_status_counts"]
    assert metadata["metadata_integrity"] == {
        "critical_fields_complete": True,
        "missing_critical_fields": [],
        "publication_blockers": [],
    }
