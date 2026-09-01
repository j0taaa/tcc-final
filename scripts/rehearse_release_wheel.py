#!/usr/bin/env python3
"""Build and exercise the release wheel without editable-source leakage."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
Q3_CONFIG = REPOSITORY_ROOT / "configs/experiments/q3_finite_slots_v1.toml"
STATISTICS_CONFIG_RELATIVE = Path("configs/analysis/t1202_statistics_v1.toml")
STATISTICS_RAW_RELATIVE = Path(
    "docs/artifacts/raw/t1202_statistics_v1/statistical-observations.jsonl"
)


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _isolated_python(environment: Path) -> Path:
    if sys.platform == "win32":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def _inspect_wheel(wheel: Path) -> dict[str, int]:
    with zipfile.ZipFile(wheel) as archive:
        names = tuple(archive.namelist())
    counts = {
        package: sum(name.startswith(f"{package}/") and name.endswith(".py") for name in names)
        for package in ("mwpc_exact", "mwpc_research")
    }
    missing = [package for package, count in counts.items() if count == 0]
    if missing:
        raise RuntimeError(f"release wheel omits package trees: {', '.join(missing)}")
    return counts


def _copy_statistical_fixture(smoke_root: Path) -> Path:
    config = smoke_root / STATISTICS_CONFIG_RELATIVE
    raw = smoke_root / STATISTICS_RAW_RELATIVE
    config.parent.mkdir(parents=True)
    raw.parent.mkdir(parents=True)
    shutil.copy2(REPOSITORY_ROOT / STATISTICS_CONFIG_RELATIVE, config)
    shutil.copy2(REPOSITORY_ROOT / STATISTICS_RAW_RELATIVE, raw)
    return config


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="mwpc-release-wheel-") as temporary:
        root = Path(temporary).resolve()
        dist = root / "dist"
        _run(
            [
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--outdir",
                str(dist),
                str(REPOSITORY_ROOT),
            ],
            cwd=root,
        )
        wheels = sorted(dist.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"expected one built wheel, found {len(wheels)}")
        wheel = wheels[0]
        package_file_counts = _inspect_wheel(wheel)

        environment = root / "wheel-environment"
        venv.EnvBuilder(with_pip=True, clear=False).create(environment)
        python = _isolated_python(environment)
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                str(wheel),
            ],
            cwd=root,
        )

        work = root / "outside-checkout"
        work.mkdir()
        import_check = (
            "import json; from pathlib import Path; "
            "import mwpc_exact, mwpc_research; "
            f"repo=Path({str(REPOSITORY_ROOT)!r}).resolve(); "
            "paths={m.__name__: str(Path(m.__file__).resolve()) "
            "for m in (mwpc_exact, mwpc_research)}; "
            "assert all(not Path(p).is_relative_to(repo) for p in paths.values()); "
            "print(json.dumps(paths, sort_keys=True))"
        )
        _run([str(python), "-I", "-c", import_check], cwd=work)

        q3_raw = root / "q3-smoke" / "raw"
        q3_processed = root / "q3-smoke" / "processed"
        _run(
            [
                str(python),
                "-I",
                str(REPOSITORY_ROOT / "scripts/exact_commit/run_q3_finite_slots.py"),
                "--config",
                str(Q3_CONFIG),
                "--run-directory",
                str(q3_raw),
                "--processed-directory",
                str(q3_processed),
            ],
            cwd=work,
        )
        if not (q3_raw / "q3-finite-slot-rows.jsonl").is_file():
            raise RuntimeError("wheel-installed Q3 smoke did not create raw rows")
        if not (q3_processed / "q3-finite-slot-summary.json").is_file():
            raise RuntimeError("wheel-installed Q3 smoke did not create its summary")

        artifact_root = root / "artifact-smoke"
        artifact_config = _copy_statistical_fixture(artifact_root)
        artifact_check = (
            "import json, sys; from pathlib import Path; "
            "from mwpc_research.statistical_artifacts import build_statistical_artifact; "
            "result=build_statistical_artifact(sys.argv[1], repository_root=sys.argv[2]); "
            "assert result.output_path.is_file(); "
            "print(json.dumps({'output': str(result.output_path), "
            "'sha256': result.output_sha256}, sort_keys=True))"
        )
        _run(
            [
                str(python),
                "-I",
                "-c",
                artifact_check,
                str(artifact_config),
                str(artifact_root),
            ],
            cwd=work,
        )

        print(
            json.dumps(
                {
                    "artifact_generator": "PASS",
                    "experiment": "PASS",
                    "package_python_files": package_file_counts,
                    "source_tree_leakage": False,
                    "wheel": wheel.name,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
