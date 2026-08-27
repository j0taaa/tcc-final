from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from mwpc_exact.experiments import (
    MissingCriticalMetadataError,
    MissingCriticalMetadataWarning,
    SystemMetadata,
    capture_run_metadata,
    collect_system_metadata,
    finalize_run_metadata,
    load_experiment_config,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
Q1_CONFIG = REPOSITORY_ROOT / "configs/experiments/q1_correctness_v1.toml"
Q5_CONFIG = REPOSITORY_ROOT / "configs/experiments/q5_timing_v1.toml"
GRAMMAR_HASH = "b" * 64


def _system(**changes: object) -> SystemMetadata:
    values: dict[str, object] = {
        "git_commit": "a" * 40,
        "git_dirty": False,
        "python_version": "3.11.16",
        "rust_version": "rustc 1.98.0",
        "cuda_toolkit_version": "Cuda compilation tools, release 12.8",
        "cuda_driver_supported_runtime": "13.1",
        "pytorch_version": "2.8.0",
        "transformers_version": "4.57.1",
        "mwpc_exact_version": "0.1.0",
        "mwpc_parser_py_version": "0.1.0",
        "rustformlang_version": "0.1.0",
        "machine": "x86_64",
        "cpu_model": "Test CPU",
        "logical_cpu_count": 16,
        "affinity_cpu_count": 8,
        "total_ram_bytes": 16 * 1024**3,
        "os_system": "Linux",
        "os_release": "test",
        "os_platform": "Linux-test-x86_64",
        "gpu_name": "Test GPU",
        "gpu_total_vram_bytes": 12 * 1024**3,
        "cuda_driver_version": "595.84",
        "thread_environment": {
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": None,
            "OPENBLAS_NUM_THREADS": None,
            "NUMEXPR_NUM_THREADS": None,
            "RAYON_NUM_THREADS": None,
            "RUST_MIN_STACK": None,
        },
    }
    values.update(changes)
    return SystemMetadata(**values)  # type: ignore[arg-type]


def test_common_metadata_captures_every_required_identity_and_nested_status() -> None:
    config = load_experiment_config(Q1_CONFIG)
    metadata = capture_run_metadata(
        config,
        run_id="test-run",
        repository_root=REPOSITORY_ROOT,
        grammar_sha256=(GRAMMAR_HASH,),
        require_rust=True,
        system=_system(),
        additional={"dataset": "synthetic-test"},
    )
    finalized = finalize_run_metadata(
        metadata,
        solver_status_counts={
            "python_reference": {"optimal": 2, "infeasible_on_support": 1},
            "rust_production": {"optimal": 2, "infeasible_on_support": 1},
        },
        publication_mode=False,
    )

    assert finalized["git_commit"] == "a" * 40
    assert finalized["git_dirty"] is False
    assert finalized["config_sha256"] == config.config_sha256
    assert finalized["model"]["requested_revision"] == config.model_revision
    assert finalized["tokenizer"]["requested_revision"] == config.tokenizer_revision
    assert finalized["grammar"]["sha256"] == [GRAMMAR_HASH]
    assert finalized["hardware"]["cpu"]["model"] == "Test CPU"
    assert finalized["hardware"]["ram"]["total_bytes"] == 16 * 1024**3
    assert finalized["hardware"]["gpu"]["total_vram_bytes"] == 12 * 1024**3
    assert finalized["hardware"]["threads"]["configured_cpu_threads"] == 1
    assert finalized["software_versions"]["rust"] == "rustc 1.98.0"
    assert finalized["solver_status_counts"]["rust_production"] == {
        "optimal": 2,
        "infeasible_on_support": 1,
    }
    assert finalized["metadata_integrity"] == {
        "critical_fields_complete": True,
        "missing_critical_fields": [],
        "publication_blockers": [],
    }


def test_cuda_run_requires_ml_cuda_gpu_and_vram_metadata() -> None:
    config = load_experiment_config(Q5_CONFIG)
    metadata = capture_run_metadata(
        config,
        run_id="cuda-test",
        repository_root=REPOSITORY_ROOT,
        grammar_sha256=(GRAMMAR_HASH,),
        require_rust=True,
        require_ml_stack=True,
        system=_system(),
        software_overrides={"cuda_runtime": "12.8"},
    )

    assert metadata["software_versions"]["pytorch"] == "2.8.0"
    assert metadata["software_versions"]["transformers"] == "4.57.1"
    assert metadata["software_versions"]["cuda_runtime"] == "12.8"
    assert metadata["hardware"]["gpu"]["name"] == "Test GPU"
    assert metadata["metadata_integrity"]["critical_fields_complete"] is True


def test_missing_critical_metadata_warns_for_diagnostics_and_fails_publication() -> None:
    diagnostic = load_experiment_config(Q1_CONFIG)
    incomplete = _system(total_ram_bytes=None)

    with pytest.warns(MissingCriticalMetadataWarning, match="hardware.ram.total_bytes"):
        metadata = capture_run_metadata(
            diagnostic,
            run_id="diagnostic",
            repository_root=REPOSITORY_ROOT,
            grammar_sha256=(GRAMMAR_HASH,),
            require_rust=True,
            system=incomplete,
        )
    assert metadata["metadata_integrity"]["missing_critical_fields"] == ["hardware.ram.total_bytes"]

    publication = replace(diagnostic, publication_mode=True)
    with pytest.raises(MissingCriticalMetadataError, match=r"hardware\.ram\.total_bytes"):
        capture_run_metadata(
            publication,
            run_id="publication",
            repository_root=REPOSITORY_ROOT,
            grammar_sha256=(GRAMMAR_HASH,),
            require_rust=True,
            system=incomplete,
        )


def test_dirty_worktree_is_explicit_and_blocks_publication_mode() -> None:
    diagnostic = load_experiment_config(Q1_CONFIG)
    with pytest.warns(MissingCriticalMetadataWarning, match="git.dirty_worktree"):
        metadata = capture_run_metadata(
            diagnostic,
            run_id="dirty",
            repository_root=REPOSITORY_ROOT,
            grammar_sha256=(GRAMMAR_HASH,),
            require_rust=True,
            system=_system(git_dirty=True),
        )
    assert metadata["git_dirty"] is True

    with pytest.raises(MissingCriticalMetadataError, match=r"git\.dirty_worktree"):
        capture_run_metadata(
            replace(diagnostic, publication_mode=True),
            run_id="dirty-publication",
            repository_root=REPOSITORY_ROOT,
            grammar_sha256=(GRAMMAR_HASH,),
            require_rust=True,
            system=_system(git_dirty=True),
        )


def test_system_capture_distinguishes_clean_from_dirty_git_worktree(tmp_path: Path) -> None:
    subprocess.run(("git", "init", "-q"), cwd=tmp_path, check=True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("original\n", encoding="utf-8")
    subprocess.run(("git", "add", "tracked.txt"), cwd=tmp_path, check=True)
    subprocess.run(
        (
            "git",
            "-c",
            "user.name=Metadata Test",
            "-c",
            "user.email=metadata@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ),
        cwd=tmp_path,
        check=True,
    )

    assert collect_system_metadata(tmp_path).git_dirty is False
    tracked.write_text("changed\n", encoding="utf-8")
    assert collect_system_metadata(tmp_path).git_dirty is True


def test_status_counts_must_be_nonempty_nonnegative_and_observed() -> None:
    config = load_experiment_config(Q1_CONFIG)
    metadata = capture_run_metadata(
        config,
        run_id="status-test",
        repository_root=REPOSITORY_ROOT,
        grammar_sha256=(GRAMMAR_HASH,),
        require_rust=True,
        system=_system(),
    )

    with pytest.raises(ValueError, match="non-empty"):
        finalize_run_metadata(metadata, solver_status_counts={}, publication_mode=False)
    with pytest.raises(ValueError, match="non-negative"):
        finalize_run_metadata(
            metadata,
            solver_status_counts={"rust": {"optimal": -1}},
            publication_mode=False,
        )
    with pytest.raises(ValueError, match="at least one"):
        finalize_run_metadata(
            metadata,
            solver_status_counts={"rust": {"optimal": 0}},
            publication_mode=False,
        )


def test_additional_metadata_cannot_replace_validated_common_fields() -> None:
    config = load_experiment_config(Q1_CONFIG)

    with pytest.raises(ValueError, match="reserved"):
        capture_run_metadata(
            config,
            run_id="collision",
            repository_root=REPOSITORY_ROOT,
            grammar_sha256=(GRAMMAR_HASH,),
            require_rust=True,
            system=_system(),
            additional={"git_commit": "invented"},
        )
