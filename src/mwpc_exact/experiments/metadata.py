"""Validated, shared metadata capture for reproducible experiment artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import MappingProxyType

_THREAD_ENVIRONMENT_VARIABLES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "RAYON_NUM_THREADS",
    "RUST_MIN_STACK",
)


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
