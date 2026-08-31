from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GUIDE = REPOSITORY_ROOT / "REPRODUCING.md"
MANIFEST = (
    REPOSITORY_ROOT / "docs/artifacts/processed/t1203_final_results_v1/artifact-manifest.json"
)
REHEARSAL = REPOSITORY_ROOT / "scripts/rehearse_cpu_correctness.sh"
MAKEFILE = REPOSITORY_ROOT / "Makefile"


def test_reproduction_guide_names_every_generated_table_and_figure() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paper_artifacts = [
        artifact["path"]
        for artifact in manifest["generated_artifacts"]
        if artifact["path"].endswith((".tex", ".svg"))
    ]

    assert len(paper_artifacts) == 7
    assert all(artifact["path"] in guide for artifact in manifest["generated_artifacts"])
    assert "docs/artifacts/processed/t1203_final_results_v1/artifact-manifest.json" in guide
    assert "make final-artifacts-check" in guide
    assert "make rehearse-cpu-correctness" in guide


def test_reproduction_guide_separates_cpu_and_gpu_requirements() -> None:
    guide = GUIDE.read_text(encoding="utf-8")

    assert "CPU-only artifact reproduction" in guide
    assert "Optional CUDA end-to-end reproduction" in guide
    assert "local_files_only=true" in guide
    assert "publication_mode=false" in guide
    assert "benchmark_claim=false" in guide
    assert "never write a token into this repository" in guide
    assert "exact_on_support" in guide
    assert "TIMEOUT" in guide
    assert "INFEASIBLE_ON_SUPPORT" in guide
    assert "HF_TOKEN=" not in guide
    assert "[TO BE MEASURED]" not in guide
    assert "[MODEL_ID]" not in guide


def test_cpu_rehearsal_script_is_valid_and_non_destructive() -> None:
    script = REHEARSAL.read_text(encoding="utf-8")
    makefile = MAKEFILE.read_text(encoding="utf-8")

    subprocess.run(["bash", "-n", REHEARSAL], check=True)
    assert "mktemp -d" in script
    assert "git clone" in script
    assert 'make -C "$checkout" bootstrap' in script
    assert 'make -C "$checkout" final-artifacts' in script
    assert 'make -C "$checkout" final-artifacts-check' in script
    assert "correctness-oracle-table.tex" in script
    assert "rm -rf" not in script
    assert "rehearse-cpu-correctness:\n\t./scripts/rehearse_cpu_correctness.sh" in makefile
