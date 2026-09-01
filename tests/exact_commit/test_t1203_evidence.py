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
        "532c433de1e0654fcde7781b51e9b0b14fd9a05b7782e8adfa7a8bbdd7600af2"
    ),
    "docs/artifacts/processed/t1203_final_results_v1/final-results.json": (
        "b72d6fd08429e3eb3c18fca4e5788a4fe3617a62a1972deedd6801cd176884d0"
    ),
    "paper/generated/t1203_final_results_v1/correctness-oracle-table.tex": (
        "119fd38aeec70ef870941fe13a528a62170bb8e20bebf5f0b0842033e2fdad7b"
    ),
    "paper/generated/t1203_final_results_v1/end-to-end-comparison-table.tex": (
        "a294899f8615f49081bc73ad157099d2f6a99f6daca4775d94aa45fad36463aa"
    ),
    "paper/generated/t1203_final_results_v1/finite-slot-counterexample-table.tex": (
        "105796e828459894a3983d195adc7a895240af17ed3ce99348beae3b1e409014"
    ),
    "paper/generated/t1203_final_results_v1/heuristic-gap-distribution.svg": (
        "fd93746d680d128816ea4b9908e320da06b49eda2662be3e6a9fc4a7b1bb5507"
    ),
    "paper/generated/t1203_final_results_v1/heuristic-gap-table.tex": (
        "a16be730136d8f4d63e661ab4b321c77e8ec13426b0883180009d6e4c4b3d484"
    ),
    "paper/generated/t1203_final_results_v1/runtime-breakdown-table.tex": (
        "08130e62ec8bd0de4f7d6882e221da223a7c8043bf9c6dfe2721b9ec9b2ba772"
    ),
    "paper/generated/t1203_final_results_v1/runtime-scaling.svg": (
        "872ee33930d052a6bdb0eb1b4bbbf46ac5fac9fba22c60dfd11887c9a5029a2f"
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
    assert len(manifest["generated_artifacts"]) == 8

    correctness = results["correctness"]
    assert correctness["case_count"] == 249
    assert correctness["failed_case_count"] == 0
    overall = correctness["families"][-1]
    assert overall["family"] == "overall"
    assert overall["agreement"]["event_count"] == 249
    assert "confidence_interval_method" not in overall["agreement"]
    assert overall["agreement"]["uncertainty_method"] == "not_applicable_complete_configured_set"
    assert overall["oracle_status_counts"] == {
        "infeasible_on_support": 82,
        "optimal": 167,
    }
    families = {row["family"]: row for row in correctness["families"]}
    for family in ("canonical", "exhaustive", "overall"):
        assert "confidence_interval_lower" not in families[family]["agreement"]
        assert "confidence_interval_upper" not in families[family]["agreement"]
    assert families["randomized"]["agreement"]["confidence_interval_method"] == "wilson_score"
    assert correctness["randomized_sampling"] == {
        "generator": "mwpc_research.q1_correctness.generate_random_finite_lattice_instance",
        "maximum_seed": 1200,
        "minimum_seed": 1101,
        "seed_count": 100,
        "seed_selection": "consecutive_integer_seeds",
        "seeds_are_consecutive": True,
        "unique_seed_count": 100,
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
    assert len(runtime["scaling_series"]) == 12
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

    source_contexts = {
        key: results[key]["source_context"]
        for key in (
            "correctness",
            "heuristic_gap",
            "finite_slots",
            "runtime_breakdown",
            "end_to_end",
        )
    }
    assert {key: value["run_id"] for key, value in source_contexts.items()} == {
        "correctness": "bd6b445",
        "heuristic_gap": "a8b4e7c",
        "finite_slots": "ac447a8",
        "runtime_breakdown": "66b8b5d",
        "end_to_end": "83ba41d",
    }
    assert all(
        context["exactness_scope"] == "exact_on_support" for context in source_contexts.values()
    )
    assert source_contexts["end_to_end"]["model_id"] == "GSAI-ML/LLaDA-8B-Instruct"
    assert source_contexts["end_to_end"]["task_configuration"] == "t904_literal_zero"

    generated_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(PAPER.glob("*.tex"))
    )
    for placeholder in ("[TO BE MEASURED]", "[MODEL_ID]", "estimated"):
        assert placeholder not in generated_text
    assert "not a publication benchmark" in generated_text
    assert generated_text.count(r"\texttt{exact\_on\_support}") == 5
    for run_id in ("bd6b445", "a8b4e7c", "ac447a8", "66b8b5d", "83ba41d"):
        assert f"run \\texttt{{{run_id}}}" in generated_text
    assert r"GSAI-ML/LLaDA-8B-Instruct@08b83a6feb34" in generated_text
    assert r"t904\_literal\_zero" in generated_text
    ElementTree.parse(PAPER / "heuristic-gap-distribution.svg")
    ElementTree.parse(PAPER / "runtime-scaling.svg")

    verified = build_final_artifacts(
        CONFIG_PATH,
        repository_root=REPOSITORY_ROOT,
        verify_existing=True,
    )
    assert verified.verified_existing is True
    assert verified.source_sha256 == {
        relative: digest for relative, digest in EXPECTED_HASHES.items() if "/raw/" in relative
    }
