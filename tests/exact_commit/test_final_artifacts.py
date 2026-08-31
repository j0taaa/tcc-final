from __future__ import annotations

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree

import pytest

from mwpc_research.final_artifacts import (
    CORRECTNESS_TABLE_FILENAME,
    END_TO_END_TABLE_FILENAME,
    FINAL_MANIFEST_FILENAME,
    FINAL_RESULTS_FILENAME,
    HEURISTIC_GAP_FIGURE_FILENAME,
    SCALING_FIGURE_FILENAME,
    build_final_artifacts,
)


def _metadata(role: str, *, benchmark_claim: bool | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "git_commit": "b" * 40,
        "git_dirty": False,
        "config_sha256": "c" * 64,
        "run_id": role,
        "exactness_scope": "exact_on_support",
        "exactness_guarantee": "per_step",
    }
    if benchmark_claim is not None:
        result["benchmark_claim"] = benchmark_claim
    return result


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> str:
    payload = b"".join(
        (json.dumps(row, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n").encode(
            "utf-8"
        )
        for row in rows
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _fixture_repository(
    root: Path,
    *,
    q1_agreement: bool = True,
    q2_stored_gap: float = 1.0,
    exact_certificate_valid: bool = True,
) -> Path:
    inputs: dict[str, tuple[str, list[dict[str, object]]]] = {
        "q1_correctness": (
            "mwpc_q1_correctness_case",
            [
                {
                    "artifact_kind": "mwpc_q1_correctness_case",
                    "schema_version": 1,
                    "run_metadata": _metadata("q1"),
                    "family": "canonical",
                    "agreement": q1_agreement,
                    "solver_statuses": {
                        "exhaustive_oracle": "optimal",
                        "python_reference": "optimal",
                        "rust_production": "optimal",
                    },
                }
            ],
        ),
        "q2_heuristic_gap": (
            "mwpc_q2_heuristic_gap_row",
            [
                {
                    "artifact_kind": "mwpc_q2_heuristic_gap_row",
                    "schema_version": 1,
                    "run_metadata": _metadata("q2"),
                    "success": True,
                    "weight_mode": "unit",
                    "selector_results": {
                        "exact_mwpc": {"runtime_seconds": 0.3},
                        "greedy_exact_feasibility": {"runtime_seconds": 0.2},
                        "epic_regular_cover": {"runtime_seconds": 0.1},
                    },
                    "comparisons": {
                        "greedy_exact_feasibility": {
                            "exact_score": 2.0,
                            "heuristic_score": 1.0,
                            "absolute_gap": q2_stored_gap,
                        },
                        "epic_regular_cover": {
                            "exact_score": 2.0,
                            "heuristic_score": 0.0,
                            "absolute_gap": 2.0,
                        },
                    },
                }
            ],
        ),
        "q3_finite_slots": (
            "mwpc_q3_finite_slot_row",
            [
                {
                    "artifact_kind": "mwpc_q3_finite_slot_row",
                    "schema_version": 1,
                    "run_metadata": _metadata("q3"),
                    "success": True,
                    "case_id": "counterexample",
                    "title": "Required EOS does not fit",
                    "abstract_decision": {
                        "status": "accepted",
                        "objective_value": 2.0,
                    },
                    "finite_decision": {
                        "status": "infeasible_on_support",
                        "objective_value": None,
                        "reason_code": "finite_canvas_too_short",
                        "exactness_scope": {"claim": "exact_on_support"},
                    },
                    "slot_accounting": {
                        "available_physical_slots": 1,
                        "minimum_required_physical_tokens": 2,
                        "slot_shortfall": 1,
                    },
                    "comparison": {
                        "abstract_witness_fits_finite_canvas": False,
                        "claim_supported": True,
                    },
                }
            ],
        ),
        "q4_scaling": (
            "mwpc_q4_scaling_row",
            [
                {
                    "artifact_kind": "mwpc_q4_scaling_row",
                    "schema_version": 1,
                    "run_metadata": _metadata("q4"),
                    "backend": backend,
                    "axis": "slot_count",
                    "axis_value": 1,
                    "status": "optimal",
                    "censored": False,
                    "certificate_valid": True,
                    "successful_runtime_seconds": runtime,
                    "observed_profile": {
                        "timings_seconds": {
                            "components": {"parser": runtime / 2.0},
                            "unattributed_measurement_overhead": runtime / 4.0,
                            "wall_span": runtime,
                        }
                    },
                }
                for backend, runtime in (("python", 0.004), ("rust", 0.002))
            ],
        ),
        "q5_end_to_end": (
            "mwpc_q5_end_to_end_row",
            [
                {
                    "artifact_kind": "mwpc_q5_end_to_end_row",
                    "schema_version": 1,
                    "run_metadata": _metadata("q5", benchmark_claim=False),
                    "comparison_fingerprint": "d" * 64,
                    "strategy": strategy,
                    "execution_status": "complete",
                    "syntactic_valid": True,
                    "functional_success": True,
                    "resources": {"elapsed_seconds": runtime},
                    "generation": {
                        "average_commit_batch_size": batch,
                        "fallback_count": int(strategy == "epic"),
                        "support_expansion_count": 0 if strategy == "exact" else None,
                    },
                    "exact_solver": {
                        "status": "optimal" if strategy == "exact" else None,
                        "certificate_valid": (
                            exact_certificate_valid if strategy == "exact" else None
                        ),
                    },
                }
                for strategy, runtime, batch in (
                    ("unconstrained", 1.0, 1.0),
                    ("serial", 2.0, 1.0),
                    ("epic", 1.5, 1.0),
                    ("exact", 3.0, 2.0),
                )
            ],
        ),
    }
    declarations: list[tuple[str, Path, str]] = []
    for role, (_, rows) in inputs.items():
        relative = Path(f"raw/{role}.jsonl")
        digest = _write_jsonl(root / relative, rows)
        declarations.append((role, relative, digest))
    config_path = root / "configs/final.toml"
    config_path.parent.mkdir(parents=True)
    lines = [
        "schema_version = 1",
        'artifact_id = "test_final_v1"',
        'processed_directory = "processed/test_final_v1"',
        'paper_directory = "paper/generated/test_final_v1"',
        "confidence_level = 0.95",
    ]
    for role, relative, digest in declarations:
        lines.extend(
            (
                "",
                "[[inputs]]",
                f'role = "{role}"',
                f'raw_jsonl = "{relative.as_posix()}"',
                f'expected_sha256 = "{digest}"',
            )
        )
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def test_final_bundle_is_generated_directly_from_pinned_rows(tmp_path: Path) -> None:
    config = _fixture_repository(tmp_path)

    result = build_final_artifacts(config, repository_root=tmp_path)

    processed = tmp_path / "processed/test_final_v1"
    paper = tmp_path / "paper/generated/test_final_v1"
    summary = json.loads((processed / FINAL_RESULTS_FILENAME).read_text())
    assert summary["correctness"]["case_count"] == 1
    assert summary["correctness"]["failed_case_count"] == 0
    assert summary["heuristic_gap"]["gap_rows"][0]["statistics"]["absolute_gap"]["median"] == 1.0
    assert summary["finite_slots"]["counterexample_count"] == 1
    assert summary["runtime_breakdown"]["status_counts"] == {"optimal": 2}
    assert summary["end_to_end"]["benchmark_claim"] is False
    assert summary["end_to_end"]["step_level_rates"] is None
    assert (
        summary["end_to_end"]["exact_runtime_comparisons"]["serial"]["median_runtime_ratio"] == 1.5
    )
    assert "100.0" in (paper / CORRECTNESS_TABLE_FILENAME).read_text()
    assert "0/0/0" in (paper / END_TO_END_TABLE_FILENAME).read_text()
    ElementTree.parse(paper / HEURISTIC_GAP_FIGURE_FILENAME)
    ElementTree.parse(paper / SCALING_FIGURE_FILENAME)
    manifest = json.loads((processed / FINAL_MANIFEST_FILENAME).read_text())
    assert len(manifest["sources"]) == 5
    assert len(manifest["generated_artifacts"]) == 8
    assert len(result.source_sha256) == 5

    verified = build_final_artifacts(
        config,
        repository_root=tmp_path,
        verify_existing=True,
    )
    assert verified.verified_existing is True
    assert verified.output_sha256 == result.output_sha256


def test_final_bundle_rejects_hand_edited_output(tmp_path: Path) -> None:
    config = _fixture_repository(tmp_path)
    build_final_artifacts(config, repository_root=tmp_path)
    table = tmp_path / "paper/generated/test_final_v1" / CORRECTNESS_TABLE_FILENAME
    table.write_text("hand edited\n", encoding="utf-8")

    with pytest.raises(ValueError, match="differs from raw inputs"):
        build_final_artifacts(config, repository_root=tmp_path, verify_existing=True)


def test_final_bundle_rejects_raw_hash_change(tmp_path: Path) -> None:
    config = _fixture_repository(tmp_path)
    raw = tmp_path / "raw/q1_correctness.jsonl"
    raw.write_bytes(raw.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="raw hash mismatch"):
        build_final_artifacts(config, repository_root=tmp_path)


def test_q1_disagreement_blocks_final_artifact_generation(tmp_path: Path) -> None:
    config = _fixture_repository(tmp_path, q1_agreement=False)

    with pytest.raises(ValueError, match="Q1 correctness disagreement"):
        build_final_artifacts(config, repository_root=tmp_path)


def test_q2_gap_and_q5_certificate_are_independently_checked(tmp_path: Path) -> None:
    bad_gap_root = tmp_path / "bad-gap"
    bad_gap = _fixture_repository(bad_gap_root, q2_stored_gap=0.5)
    with pytest.raises(ValueError, match="stored gap mismatch"):
        build_final_artifacts(bad_gap, repository_root=bad_gap_root)

    bad_certificate_root = tmp_path / "bad-certificate"
    bad_certificate = _fixture_repository(
        bad_certificate_root,
        exact_certificate_valid=False,
    )
    with pytest.raises(ValueError, match="independently valid certificate"):
        build_final_artifacts(
            bad_certificate,
            repository_root=bad_certificate_root,
        )
