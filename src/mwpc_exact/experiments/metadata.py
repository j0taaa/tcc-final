"""Validated, shared metadata capture for reproducible experiment artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import MappingProxyType

from mwpc_exact.experiments.config import ExperimentConfig

RUN_METADATA_SCHEMA_VERSION = 1
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_GIT_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40,64}")
_THREAD_ENVIRONMENT_VARIABLES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "RAYON_NUM_THREADS",
    "RUST_MIN_STACK",
)
_RESERVED_FIELDS = {
    "metadata_schema_version",
    "run_id",
    "generated_at_utc",
    "git_commit",
    "git_dirty",
    "config_sha256",
    "config",
    "seeds",
    "repetitions",
    "model",
    "tokenizer",
    "grammar",
    "exactness",
    "support",
    "timeouts",
    "hardware",
    "software_versions",
    "solver_status_counts",
    "metadata_integrity",
}


class MissingCriticalMetadataWarning(UserWarning):
    """A diagnostic run continued with explicitly identified metadata gaps."""


class MissingCriticalMetadataError(RuntimeError):
    """A publication-mode run lacks metadata required for reproducibility."""


def canonical_json_sha256(value: object) -> str:
    """Hash one finite JSON value with the repository's canonical encoding."""

    try:
        payload = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("canonical hash input must be a finite JSON value") from error
    return hashlib.sha256(payload).hexdigest()


def _optional_command(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    allow_empty: bool = False,
) -> str | None:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=10.0,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    output = completed.stdout.strip()
    return output if output or allow_empty else None


def _optional_package_version(distribution: str) -> str | None:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def _cpu_model() -> str | None:
    cpuinfo = Path("/proc/cpuinfo")
    try:
        lines = cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in lines:
        if line.lower().startswith("model name") and ":" in line:
            value = line.split(":", 1)[1].strip()
            return value or None
    return platform.processor().strip() or None


def _total_ram_bytes() -> int | None:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        page_count = os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        return None
    if not isinstance(page_size, int) or not isinstance(page_count, int):
        return None
    total = page_size * page_count
    return total if total > 0 else None


def _affinity_cpu_count() -> int | None:
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return None


@dataclass(frozen=True, slots=True)
class SystemMetadata:
    """Host and toolchain observations, with absence represented by ``None``."""

    git_commit: str | None
    git_dirty: bool | None
    python_version: str | None
    rust_version: str | None
    cuda_toolkit_version: str | None
    cuda_driver_supported_runtime: str | None
    pytorch_version: str | None
    transformers_version: str | None
    mwpc_exact_version: str | None
    mwpc_parser_py_version: str | None
    rustformlang_version: str | None
    machine: str | None
    cpu_model: str | None
    logical_cpu_count: int | None
    affinity_cpu_count: int | None
    total_ram_bytes: int | None
    os_system: str | None
    os_release: str | None
    os_platform: str | None
    gpu_name: str | None
    gpu_total_vram_bytes: int | None
    cuda_driver_version: str | None
    thread_environment: Mapping[str, str | None]

    def __post_init__(self) -> None:
        for field_name in (
            "logical_cpu_count",
            "affinity_cpu_count",
            "total_ram_bytes",
            "gpu_total_vram_bytes",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
            ):
                raise ValueError(f"{field_name} must be a positive integer or None")
        if self.git_dirty is not None and not isinstance(self.git_dirty, bool):
            raise TypeError("git_dirty must be a boolean or None")
        environment = dict(self.thread_environment)
        if set(environment) != set(_THREAD_ENVIRONMENT_VARIABLES):
            raise ValueError("thread_environment does not contain the standard thread settings")
        if not all(value is None or isinstance(value, str) for value in environment.values()):
            raise TypeError("thread environment values must be strings or None")
        object.__setattr__(self, "thread_environment", MappingProxyType(environment))


def collect_system_metadata(repository_root: str | Path) -> SystemMetadata:
    """Collect toolchain and host identity without importing optional ML stacks."""

    root = Path(repository_root)
    commit = _optional_command(("git", "rev-parse", "HEAD"), cwd=root)
    status = _optional_command(
        ("git", "status", "--porcelain"),
        cwd=root,
        allow_empty=True,
    )
    rust = _optional_command(("rustc", "--version"), cwd=root)
    nvcc = _optional_command(("nvcc", "--version"), cwd=root)
    nvidia_header = _optional_command(("nvidia-smi",), cwd=root)
    cuda_supported: str | None = None
    if nvidia_header is not None:
        match = re.search(r"CUDA Version:\s*([0-9.]+)", nvidia_header)
        cuda_supported = None if match is None else match.group(1)
    gpu_query = _optional_command(
        (
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ),
        cwd=root,
    )
    gpu_name: str | None = None
    gpu_vram: int | None = None
    driver: str | None = None
    if gpu_query is not None:
        fields = tuple(part.strip() for part in gpu_query.splitlines()[0].rsplit(",", 2))
        if len(fields) == 3:
            gpu_name, raw_mib, driver = fields
            try:
                gpu_vram = int(float(raw_mib) * 1024 * 1024)
            except ValueError:
                gpu_vram = None
    return SystemMetadata(
        git_commit=commit,
        git_dirty=None if status is None else bool(status),
        python_version=platform.python_version() or None,
        rust_version=rust,
        cuda_toolkit_version=nvcc,
        cuda_driver_supported_runtime=cuda_supported,
        pytorch_version=_optional_package_version("torch"),
        transformers_version=_optional_package_version("transformers"),
        mwpc_exact_version=_optional_package_version("mwpc-exact"),
        mwpc_parser_py_version=_optional_package_version("mwpc-parser-py"),
        rustformlang_version=_optional_package_version("rustformlang"),
        machine=platform.machine() or None,
        cpu_model=_cpu_model(),
        logical_cpu_count=os.cpu_count(),
        affinity_cpu_count=_affinity_cpu_count(),
        total_ram_bytes=_total_ram_bytes(),
        os_system=platform.system() or None,
        os_release=platform.release() or None,
        os_platform=platform.platform() or None,
        gpu_name=gpu_name,
        gpu_total_vram_bytes=gpu_vram,
        cuda_driver_version=driver,
        thread_environment={name: os.environ.get(name) for name in _THREAD_ENVIRONMENT_VARIABLES},
    )


def _normalized_hashes(values: Sequence[str]) -> list[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("grammar_sha256 must be a finite sequence")
    if not all(isinstance(value, str) for value in values):
        raise TypeError("grammar_sha256 values must be strings")
    hashes = sorted(set(values))
    if not all(_SHA256_PATTERN.fullmatch(value) for value in hashes):
        raise ValueError("grammar_sha256 values must be lowercase SHA-256 digests")
    return hashes


def _missing_base_fields(
    config: ExperimentConfig,
    system: SystemMetadata,
    grammar_hashes: Sequence[str],
    *,
    require_rust: bool,
    require_ml_stack: bool,
    software_versions: Mapping[str, object],
) -> list[str]:
    missing: list[str] = []
    if system.git_commit is None or _GIT_COMMIT_PATTERN.fullmatch(system.git_commit) is None:
        missing.append("git.commit_sha")
    if system.git_dirty is None:
        missing.append("git.dirty")
    if not grammar_hashes:
        missing.append("grammar.sha256")
    for name, value in (
        ("software_versions.python", system.python_version),
        ("hardware.cpu.model", system.cpu_model),
        ("hardware.cpu.logical_count", system.logical_cpu_count),
        ("hardware.ram.total_bytes", system.total_ram_bytes),
        ("hardware.os.platform", system.os_platform),
    ):
        if value is None:
            missing.append(name)
    if require_rust and system.rust_version is None:
        missing.append("software_versions.rust")
    needs_ml_stack = require_ml_stack or config.device.startswith("cuda")
    if needs_ml_stack:
        for ml_name, ml_value in (
            ("software_versions.pytorch", software_versions.get("pytorch")),
            ("software_versions.transformers", software_versions.get("transformers")),
            ("software_versions.cuda_runtime", software_versions.get("cuda_runtime")),
            ("hardware.gpu.name", system.gpu_name),
            ("hardware.gpu.total_vram_bytes", system.gpu_total_vram_bytes),
            ("hardware.gpu.driver_version", system.cuda_driver_version),
        ):
            if ml_value is None:
                missing.append(ml_name)
    return missing


def _integrity_payload(missing: Sequence[str], *, dirty: bool | None) -> dict[str, object]:
    blockers = list(missing)
    if dirty is True:
        blockers.append("git.dirty_worktree")
    return {
        "critical_fields_complete": not blockers,
        "missing_critical_fields": list(missing),
        "publication_blockers": blockers,
    }


def _enforce_integrity(
    integrity: Mapping[str, object],
    *,
    publication_mode: bool,
    warn_nonpublication: bool = True,
) -> None:
    blockers = integrity["publication_blockers"]
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        raise TypeError("metadata publication blockers must be a string list")
    if not blockers:
        return
    message = "critical run metadata is incomplete: " + ", ".join(blockers)
    if publication_mode:
        raise MissingCriticalMetadataError(message)
    if warn_nonpublication:
        warnings.warn(message, MissingCriticalMetadataWarning, stacklevel=3)


def capture_run_metadata(
    config: ExperimentConfig,
    *,
    run_id: str,
    repository_root: str | Path,
    grammar_sha256: Sequence[str],
    require_rust: bool,
    require_ml_stack: bool = False,
    additional: Mapping[str, object] | None = None,
    system: SystemMetadata | None = None,
    software_overrides: Mapping[str, str | None] | None = None,
) -> dict[str, object]:
    """Capture the common metadata contract before artifact serialization."""

    if not isinstance(config, ExperimentConfig):
        raise TypeError("config must be an ExperimentConfig")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run_id must be a non-empty string")
    if not isinstance(require_rust, bool) or not isinstance(require_ml_stack, bool):
        raise TypeError("software requirements must be booleans")
    hashes = _normalized_hashes(grammar_sha256)
    observed = collect_system_metadata(repository_root) if system is None else system
    software_versions: dict[str, str | None] = {
        "python": observed.python_version,
        "rust": observed.rust_version,
        "cuda_toolkit": observed.cuda_toolkit_version,
        "cuda_driver_supported_runtime": observed.cuda_driver_supported_runtime,
        "cuda_runtime": None,
        "pytorch": observed.pytorch_version,
        "transformers": observed.transformers_version,
        "mwpc_exact": observed.mwpc_exact_version,
        "mwpc_parser_py": observed.mwpc_parser_py_version,
        "rustformlang": observed.rustformlang_version,
    }
    if software_overrides is not None:
        unknown = set(software_overrides) - set(software_versions)
        if unknown:
            raise ValueError("unknown software override fields: " + ", ".join(sorted(unknown)))
        software_versions.update(software_overrides)
    missing = _missing_base_fields(
        config,
        observed,
        hashes,
        require_rust=require_rust,
        require_ml_stack=require_ml_stack,
        software_versions=software_versions,
    )
    integrity = _integrity_payload(missing, dirty=observed.git_dirty)
    _enforce_integrity(integrity, publication_mode=config.publication_mode)
    metadata: dict[str, object] = {
        "metadata_schema_version": RUN_METADATA_SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_commit": observed.git_commit,
        "git_dirty": observed.git_dirty,
        "config_sha256": config.config_sha256,
        "config": {
            "experiment_id": config.experiment_id,
            "question": config.question.value,
            "publication_mode": config.publication_mode,
            "sha256": config.config_sha256,
        },
        "seeds": list(config.seeds),
        "repetitions": config.repetitions,
        "model": {
            "model_id": config.model_id,
            "requested_revision": config.model_revision,
            "local_files_only": config.local_files_only,
        },
        "tokenizer": {
            "tokenizer_id": config.tokenizer_id,
            "requested_revision": config.tokenizer_revision,
        },
        "grammar": {
            "grammar_id": config.grammar_id,
            "source": config.grammar_source,
            "revision": config.grammar_revision,
            "hash_policy": config.grammar_hash_policy,
            "sha256": hashes,
        },
        "exactness": {
            "scope": config.exactness_scope,
            "guarantee": config.exactness_guarantee,
            "independent_certificate_required": config.require_independent_certificate,
        },
        "support": {
            "policy": config.support_policy,
            "top_k": config.support_top_k,
            "k_max": config.support_k_max,
            "finite_slots": config.finite_slots,
        },
        "timeouts": {
            "solver_seconds": config.solver_timeout_seconds,
            "run_seconds": config.run_timeout_seconds,
        },
        "hardware": {
            "accelerator_config": {
                "device": config.device,
                "dtype": config.dtype,
                "cuda_device": config.cuda_device,
                "synchronize_cuda": config.synchronize_cuda,
            },
            "cpu": {
                "machine": observed.machine,
                "model": observed.cpu_model,
                "logical_count": observed.logical_cpu_count,
                "affinity_count": observed.affinity_cpu_count,
            },
            "ram": {"total_bytes": observed.total_ram_bytes},
            "gpu": {
                "available": observed.gpu_name is not None,
                "name": observed.gpu_name,
                "total_vram_bytes": observed.gpu_total_vram_bytes,
                "driver_version": observed.cuda_driver_version,
            },
            "os": {
                "system": observed.os_system,
                "release": observed.os_release,
                "platform": observed.os_platform,
            },
            "threads": {
                "configured_cpu_threads": config.cpu_threads,
                "environment": dict(observed.thread_environment),
            },
        },
        "software_versions": software_versions,
        "solver_status_counts": {},
        "metadata_integrity": integrity,
    }
    if additional is not None:
        if not isinstance(additional, Mapping) or not all(
            isinstance(key, str) for key in additional
        ):
            raise TypeError("additional metadata must be a string-keyed mapping")
        conflicts = set(additional) & _RESERVED_FIELDS
        if conflicts:
            raise ValueError("additional metadata uses reserved fields: " + ", ".join(conflicts))
        metadata.update(additional)
    try:
        json.dumps(metadata, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("run metadata must contain finite JSON values") from error
    return metadata


def _normalize_status_counts(
    value: Mapping[str, object], path: str
) -> tuple[dict[str, object], int]:
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"{path} must be a non-empty mapping")
    normalized: dict[str, object] = {}
    leaf_total = 0
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise TypeError(f"{path} keys must be non-empty strings")
        if isinstance(item, Mapping):
            child, child_total = _normalize_status_counts(item, f"{path}.{key}")
            normalized[key] = child
            leaf_total += child_total
        else:
            if isinstance(item, bool) or not isinstance(item, int) or item < 0:
                raise ValueError(f"{path}.{key} must be a non-negative integer")
            normalized[key] = item
            leaf_total += item
    return normalized, leaf_total


def finalize_run_metadata(
    metadata: Mapping[str, object],
    *,
    solver_status_counts: Mapping[str, object],
    publication_mode: bool,
) -> dict[str, object]:
    """Attach all observed status counts and enforce publication completeness."""

    if not isinstance(publication_mode, bool):
        raise TypeError("publication_mode must be a boolean")
    normalized_counts, total = _normalize_status_counts(
        solver_status_counts,
        "solver_status_counts",
    )
    if total == 0:
        raise ValueError("solver_status_counts must contain at least one observed result")
    result = dict(metadata)
    integrity_value = result.get("metadata_integrity")
    if not isinstance(integrity_value, Mapping):
        raise TypeError("metadata_integrity must be present before finalization")
    missing_value = integrity_value.get("missing_critical_fields")
    if not isinstance(missing_value, list) or not all(
        isinstance(item, str) for item in missing_value
    ):
        raise TypeError("missing_critical_fields must be a string list")
    raw_dirty = result.get("git_dirty")
    dirty = raw_dirty if isinstance(raw_dirty, bool) else None
    integrity = _integrity_payload(missing_value, dirty=dirty)
    _enforce_integrity(
        integrity,
        publication_mode=publication_mode,
        warn_nonpublication=False,
    )
    result["solver_status_counts"] = normalized_counts
    result["metadata_integrity"] = integrity
    return result


__all__ = [
    "RUN_METADATA_SCHEMA_VERSION",
    "MissingCriticalMetadataError",
    "MissingCriticalMetadataWarning",
    "SystemMetadata",
    "canonical_json_sha256",
    "capture_run_metadata",
    "collect_system_metadata",
    "finalize_run_metadata",
]
