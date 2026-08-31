from __future__ import annotations

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree

from mwpc_research.final_artifacts import (
    FINAL_MANIFEST_KIND,
    FINAL_RESULTS_KIND,
    build_final_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/analysis/t1203_final_artifacts_v1.toml"
PROCESSED = REPOSITORY_ROOT / "docs/artifacts/processed/t1203_final_results_v1"
PAPER = REPOSITORY_ROOT / "paper/generated/t1203_final_results_v1"

EXPECTED_HASHES = {
    "docs/artifacts/raw/t1203_final_results_v1/q1-correctness-cases.jsonl": (
        "62fb83b48c8809a3958df486b387e017ba245e97e4e74e475ca1fb55659ade8a"
    ),
    "docs/artifacts/raw/t1203_final_results_v1/q2-heuristic-gap-rows.jsonl": (
        "1af3865368c0cff24bf75fe103354bd51e0bd42bd7a381ba1b3cec3538a0a2e1"
    ),
    "docs/artifacts/raw/t1203_final_results_v1/q3-finite-slot-rows.jsonl": (
        "060957e2a68d71a30696b6406e43d737458f0a13ae0ca1abd750885220c3ce20"
    ),
    "docs/artifacts/raw/t1203_final_results_v1/q4-scaling-rows.jsonl": (
        "4ece645bc4b9a497623738b378bf58bba05805c6fa03bf49a555973dcf8a0765"
    ),
    "docs/artifacts/raw/t1203_final_results_v1/q5-end-to-end-rows.jsonl": (
        "1132d0f29561d7b3eca8a72d382c22422275f2f54eb462da264b4fc1da9508b4"
    ),
    "docs/artifacts/processed/t1203_final_results_v1/artifact-manifest.json": (
        "a45b8aededf49b509ad1f63ace81f86feebd3ad1332d0068c176469d07ba336b"
    ),
    "docs/artifacts/processed/t1203_final_results_v1/final-results.json": (
        "716ad951d1760d7817c3d6a466af5b45cd999445f3aeb1f56009b8419a78c31e"
    ),
    "paper/generated/t1203_final_results_v1/correctness-oracle-table.tex": (
        "a4ac0e3695ddba0c9101a215afbbbeb7e443c96bc2f244d9346aa1f396e1bfe8"
    ),
    "paper/generated/t1203_final_results_v1/end-to-end-comparison-table.tex": (
        "824c4743da410ab2874a54c1dcbbb4a0e4177b1a809070fede4c84b517afbdc5"
    ),
    "paper/generated/t1203_final_results_v1/finite-slot-counterexample-table.tex": (
        "af4f2ac71ad418a6bc2942c8b73e48f00b5d4a6a6d11d22d2705a49d71581c2c"
    ),
    "paper/generated/t1203_final_results_v1/heuristic-gap-distribution.svg": (
        "e3900d3f65ff5b89adc4457318bd6b661a38bb37d321c7876f6e134ac6dc6180"
    ),
    "paper/generated/t1203_final_results_v1/heuristic-gap-table.tex": (
        "6aae1f29308316b862ed7db12682f277fe7200950c3adc7cea0f5e1d6c530b5f"
    ),
    "paper/generated/t1203_final_results_v1/runtime-breakdown-table.tex": (
        "9cddef0c071c8249e846346f08e9d7776bc9c3d0c9436ed82873dba6016cb1de"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_t1203_tables_and_figure_are_pinned_to_raw_rows() -> None:
    for relative, expected in EXPECTED_HASHES.items():
        assert _sha256(REPOSITORY_ROOT / relative) == expected

    results = json.loads((PROCESSED / "final-results.json").read_text())
    manifest = json.loads((PROCESSED / "artifact-manifest.json").read_text())
    assert results["artifact_kind"] == FINAL_RESULTS_KIND
    assert manifest["artifact_kind"] == FINAL_MANIFEST_KIND
    assert len(results["sources"]) == 5
    assert [source["row_count"] for source in results["sources"]] == [249, 6, 2, 84, 32]
    assert all(source["exactness_scope"] == "exact_on_support" for source in results["sources"])
    assert len(manifest["generated_artifacts"]) == 7

    correctness = results["correctness"]
    assert correctness["case_count"] == 249
    assert correctness["failed_case_count"] == 0
    overall = correctness["families"][-1]
    assert overall["family"] == "overall"
    assert overall["agreement"]["event_count"] == 249
    assert overall["agreement"]["confidence_interval_method"] == "wilson_score"
    assert overall["oracle_status_counts"] == {
        "infeasible_on_support": 82,
        "optimal": 167,
    }

    gap = results["heuristic_gap"]
    assert gap["case_count"] == 6
    assert len(gap["gap_rows"]) == 4
    assert all(row["statistics"]["comparison_count"] == 3 for row in gap["gap_rows"])
    assert "not_model_benchmark" in gap["interpretation"]

    finite_slots = results["finite_slots"]
    assert finite_slots["counterexample_count"] == 2
    assert all(case["claim_supported"] for case in finite_slots["cases"])
    assert {case["finite_status"] for case in finite_slots["cases"]} == {
        "infeasible_on_support",
        "optimal",
    }

    runtime = results["runtime_breakdown"]
    assert runtime["measurement_count"] == 84
    assert runtime["censored_count"] == 0
    assert runtime["status_counts"] == {"optimal": 84}
    assert all(row["runtime_seconds"]["count"] == 42 for row in runtime["component_breakdown"])
    assert "not_publication_benchmark" in runtime["interpretation"]

    end_to_end = results["end_to_end"]
    assert end_to_end["benchmark_claim"] is False
    assert end_to_end["all_required_methods_passed"] is True
    assert end_to_end["analysis_unit"] == "generation"
    assert end_to_end["step_level_rates"] is None
    assert [method["strategy"] for method in end_to_end["methods"]] == [
        "unconstrained",
        "serial",
        "epic",
        "exact",
    ]
    exact = end_to_end["methods"][-1]
    assert exact["exact_solver_status_counts"] == {"optimal": 8}
    assert exact["support_expansion_rate_per_generation"]["event_count"] == 0

    generated_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(PAPER.glob("*.tex"))
    )
    for placeholder in ("[TO BE MEASURED]", "[MODEL_ID]", "estimated"):
        assert placeholder not in generated_text
    assert "not a publication benchmark" in generated_text
    ElementTree.parse(PAPER / "heuristic-gap-distribution.svg")

    verified = build_final_artifacts(
        CONFIG_PATH,
        repository_root=REPOSITORY_ROOT,
        verify_existing=True,
    )
    assert verified.verified_existing is True
    assert verified.source_sha256 == {
        relative: digest for relative, digest in EXPECTED_HASHES.items() if "/raw/" in relative
    }
