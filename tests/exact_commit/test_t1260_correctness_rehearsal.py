from __future__ import annotations

import json
from pathlib import Path

import pytest

from mwpc_research.correctness_rehearsal import (
    SemanticMismatchError,
    compare_correctness_semantics,
    main,
)


def _row(*, objective: float = 3.0, timing: float = 0.01) -> dict[str, object]:
    return {
        "agreement": True,
        "artifact_kind": "mwpc_q1_correctness_case",
        "case_id": "case-a",
        "family": "canonical",
        "objective_value": objective,
        "property_checks": {"certificate_validation": 2},
        "solver_statuses": {
            "exhaustive_oracle": "optimal",
            "python_reference": "optimal",
            "rust_production": "optimal",
        },
        "status": "optimal",
        "timings_seconds": {"total": timing},
    }


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_semantic_comparison_ignores_legitimate_timing_changes(tmp_path: Path) -> None:
    reference = tmp_path / "reference.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    _write_rows(reference, [_row(timing=0.01)])
    _write_rows(candidate, [_row(timing=9.99)])

    records = compare_correctness_semantics(reference, candidate)

    assert len(records) == 1
    assert records[0].case_id == "case-a"


def test_semantic_comparison_rejects_objective_change(tmp_path: Path) -> None:
    reference = tmp_path / "reference.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    _write_rows(reference, [_row(objective=3.0, timing=0.01)])
    _write_rows(candidate, [_row(objective=2.0, timing=9.99)])

    with pytest.raises(SemanticMismatchError, match="objective_value"):
        compare_correctness_semantics(reference, candidate)


def test_nonoptimal_rows_have_zero_certificate_validations(tmp_path: Path) -> None:
    reference = tmp_path / "reference.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    row = _row()
    row["status"] = "infeasible_on_support"
    row["objective_value"] = None
    row["property_checks"] = {"nonoptimal_payload": 2}
    row["solver_statuses"] = {
        "exhaustive_oracle": "infeasible_on_support",
        "python_reference": "infeasible_on_support",
        "rust_production": "infeasible_on_support",
    }
    _write_rows(reference, [row])
    _write_rows(candidate, [row])

    records = compare_correctness_semantics(reference, candidate)

    assert records[0].certificate_validation_count == 0


def test_cli_fails_on_certificate_mismatch_even_when_timing_differs(
    tmp_path: Path,
) -> None:
    reference = tmp_path / "reference.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    expected = _row(timing=0.01)
    observed = _row(timing=9.99)
    observed["property_checks"] = {"certificate_validation": 1}
    _write_rows(reference, [expected])
    _write_rows(candidate, [observed])

    exit_code = main(
        [
            "--reference",
            str(reference),
            "--candidate",
            str(candidate),
            "--summary-output",
            str(tmp_path / "summary.json"),
            "--table-output",
            str(tmp_path / "table.tex"),
        ]
    )

    assert exit_code == 1
    assert not (tmp_path / "summary.json").exists()
    assert not (tmp_path / "table.tex").exists()


def test_cli_writes_semantic_summary_and_table(tmp_path: Path) -> None:
    reference = tmp_path / "reference.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    summary = tmp_path / "summary.json"
    table = tmp_path / "table.tex"
    _write_rows(reference, [_row(timing=0.01)])
    _write_rows(candidate, [_row(timing=9.99)])

    exit_code = main(
        [
            "--reference",
            str(reference),
            "--candidate",
            str(candidate),
            "--summary-output",
            str(summary),
            "--table-output",
            str(table),
        ]
    )

    assert exit_code == 0
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["comparison"] == "PASS"
    assert payload["timing_fields_compared"] is False
    assert payload["agreement_count"] == 1
    assert "Certificate checks" in table.read_text(encoding="utf-8")
