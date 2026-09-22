from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from mwpc_research.campaign_output import prepare_output_directory, write_summary

ROOT = Path(__file__).resolve().parents[2]


def test_campaign_output_protects_preexisting_files_and_races(tmp_path: Path) -> None:
    directory = prepare_output_directory(tmp_path, ("summary.json",))
    write_summary(directory, "summary.json", {"original": True})
    original = (directory / "summary.json").read_bytes()
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        prepare_output_directory(directory, ("summary.json",))
    with pytest.raises(FileExistsError):
        write_summary(directory, "summary.json", {"original": False})
    assert (directory / "summary.json").read_bytes() == original


@pytest.mark.parametrize(
    "script,summary",
    [
        ("run_m5_rust_differential.py", "m5-rust-differential-normal-summary.json"),
        (
            "run_m6_finite_lattice_differential.py",
            "m6-finite-lattice-differential-normal-summary.json",
        ),
        (
            "run_m7_eos_finite_slot_differential.py",
            "m7-eos-finite-slot-differential-normal-summary.json",
        ),
    ],
)
def test_campaign_cli_refuses_to_overwrite_existing_evidence(
    script: str, summary: str, tmp_path: Path
) -> None:
    destination = tmp_path / summary
    destination.write_text("protected historical evidence")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/exact_commit" / script),
            "--campaign",
            "normal",
            "--output-directory",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "refusing to overwrite" in result.stderr
    assert destination.read_text() == "protected historical evidence"
