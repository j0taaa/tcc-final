"""Semantic comparison for clean Q1 source-experiment rehearsals."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast


class SemanticMismatchError(RuntimeError):
    """Raised when a source rerun changes correctness semantics."""


@dataclass(frozen=True, slots=True)
class CorrectnessCaseSemantics:
    """Timing-independent Q1 fields that must reproduce exactly."""

    case_id: str
    family: str
    status: str
    objective_value: float | None
    agreement: bool
    certificate_validation_count: int
    solver_statuses: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible representation."""

        return {
            "agreement": self.agreement,
            "case_id": self.case_id,
            "certificate_validation_count": self.certificate_validation_count,
            "family": self.family,
            "objective_value": self.objective_value,
            "solver_statuses": dict(self.solver_statuses),
            "status": self.status,
        }


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{field_name} must be a string-keyed object")
    return cast(Mapping[str, object], value)


def _string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _nonnegative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _objective(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number or null")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _case_semantics(row: Mapping[str, object], *, row_number: int) -> CorrectnessCaseSemantics:
    prefix = f"row {row_number}"
    if row.get("artifact_kind") != "mwpc_q1_correctness_case":
        raise ValueError(f"{prefix}.artifact_kind is not a Q1 correctness case")
    agreement = row.get("agreement")
    if not isinstance(agreement, bool):
        raise ValueError(f"{prefix}.agreement must be boolean")
    property_checks = _mapping(row.get("property_checks"), f"{prefix}.property_checks")
    solver_statuses = _mapping(row.get("solver_statuses"), f"{prefix}.solver_statuses")
    normalized_statuses = tuple(
        sorted(
            (
                _string(solver, f"{prefix}.solver_statuses key"),
                _string(status, f"{prefix}.solver_statuses.{solver}"),
            )
            for solver, status in solver_statuses.items()
        )
    )
    if not normalized_statuses:
        raise ValueError(f"{prefix}.solver_statuses cannot be empty")
    return CorrectnessCaseSemantics(
        case_id=_string(row.get("case_id"), f"{prefix}.case_id"),
        family=_string(row.get("family"), f"{prefix}.family"),
        status=_string(row.get("status"), f"{prefix}.status"),
        objective_value=_objective(row.get("objective_value"), f"{prefix}.objective_value"),
        agreement=agreement,
        certificate_validation_count=_nonnegative_integer(
            property_checks.get("certificate_validation"),
            f"{prefix}.property_checks.certificate_validation",
        ),
        solver_statuses=normalized_statuses,
    )


def load_correctness_semantics(path: str | Path) -> tuple[CorrectnessCaseSemantics, ...]:
    """Load and validate timing-independent semantics from Q1 JSONL rows."""

    source = Path(path)
    records: list[CorrectnessCaseSemantics] = []
    for row_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"{source}: blank JSONL row {row_number}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{source}: invalid JSONL row {row_number}") from error
        records.append(_case_semantics(_mapping(row, f"row {row_number}"), row_number=row_number))
    if not records:
        raise ValueError(f"{source}: no correctness rows")
    case_ids = [record.case_id for record in records]
    duplicates = sorted(case_id for case_id, count in Counter(case_ids).items() if count > 1)
    if duplicates:
        raise ValueError(f"{source}: duplicate case IDs: {', '.join(duplicates)}")
    return tuple(sorted(records, key=lambda record: record.case_id))


def compare_correctness_semantics(
    reference_path: str | Path,
    candidate_path: str | Path,
) -> tuple[CorrectnessCaseSemantics, ...]:
    """Compare required Q1 semantics while deliberately ignoring timing metadata."""

    reference = load_correctness_semantics(reference_path)
    candidate = load_correctness_semantics(candidate_path)
    reference_by_id = {record.case_id: record for record in reference}
    candidate_by_id = {record.case_id: record for record in candidate}
    if reference_by_id.keys() != candidate_by_id.keys():
        missing = sorted(reference_by_id.keys() - candidate_by_id.keys())
        extra = sorted(candidate_by_id.keys() - reference_by_id.keys())
        raise SemanticMismatchError(f"case ID mismatch: missing={missing!r}, extra={extra!r}")
    for case_id in sorted(reference_by_id):
        expected = reference_by_id[case_id]
        observed = candidate_by_id[case_id]
        if expected != observed:
            differing_fields = [
                field
                for field in expected.__dataclass_fields__
                if getattr(expected, field) != getattr(observed, field)
            ]
            raise SemanticMismatchError(
                f"semantic mismatch for {case_id}: {', '.join(differing_fields)}"
            )
    return candidate


def semantic_summary(records: Sequence[CorrectnessCaseSemantics]) -> dict[str, object]:
    """Summarize the compared case IDs, statuses, agreement, and certificates."""

    family_counts: Counter[str] = Counter()
    family_agreement: Counter[str] = Counter()
    family_certificates: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    solver_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        family_counts[record.family] += 1
        family_agreement[record.family] += int(record.agreement)
        family_certificates[record.family] += record.certificate_validation_count
        status_counts[record.status] += 1
        for solver, status in record.solver_statuses:
            solver_status_counts[solver][status] += 1
    families = {
        family: {
            "agreement_count": family_agreement[family],
            "case_count": family_counts[family],
            "certificate_validation_count": family_certificates[family],
        }
        for family in sorted(family_counts)
    }
    return {
        "agreement_count": sum(record.agreement for record in records),
        "artifact_kind": "mwpc_q1_source_rehearsal_summary",
        "case_count": len(records),
        "case_ids": [record.case_id for record in records],
        "certificate_validation_count": sum(
            record.certificate_validation_count for record in records
        ),
        "compared_fields": [
            "case_id",
            "family",
            "status",
            "objective_value",
            "agreement",
            "certificate_validation_count",
            "solver_statuses",
        ],
        "families": families,
        "schema_version": 1,
        "solver_status_counts": {
            solver: dict(sorted(counts.items()))
            for solver, counts in sorted(solver_status_counts.items())
        },
        "status_counts": dict(sorted(status_counts.items())),
        "timing_fields_compared": False,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _latex_escape(value: str) -> str:
    return value.replace("\\", r"\textbackslash{}").replace("_", r"\_")


def render_rehearsal_table(summary: Mapping[str, object]) -> bytes:
    """Render a compact, non-publication LaTeX table from a semantic summary."""

    families = _mapping(summary.get("families"), "summary.families")
    lines = [
        "% Generated by mwpc_research.correctness_rehearsal.",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Family & Cases & Agreements & Certificate checks \\",
        r"\midrule",
    ]
    for family, values in sorted(families.items()):
        row = _mapping(values, f"summary.families.{family}")
        lines.append(
            f"{_latex_escape(family)} & {row['case_count']} & "
            f"{row['agreement_count']} & {row['certificate_validation_count']} \\\\"
        )
    lines.extend(
        [
            r"\midrule",
            f"Overall & {summary['case_count']} & {summary['agreement_count']} & "
            f"{summary['certificate_validation_count']} \\\\",
            r"\bottomrule",
            r"\end{tabular}",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(payload)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    parser.add_argument("--table-output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    try:
        records = compare_correctness_semantics(arguments.reference, arguments.candidate)
    except (OSError, ValueError, SemanticMismatchError) as error:
        print(f"SOURCE_EXPERIMENT_RERUN=FAIL: {error}", file=sys.stderr)
        return 1
    summary = semantic_summary(records)
    summary.update(
        {
            "candidate_sha256": _sha256_file(arguments.candidate),
            "comparison": "PASS",
            "reference_sha256": _sha256_file(arguments.reference),
        }
    )
    _write_new(
        arguments.summary_output,
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    _write_new(arguments.table_output, render_rehearsal_table(summary))
    print(
        json.dumps(
            {
                "agreement_count": summary["agreement_count"],
                "case_count": summary["case_count"],
                "certificate_validation_count": summary[
                    "certificate_validation_count"
                ],
                "comparison": summary["comparison"],
                "timing_fields_compared": summary["timing_fields_compared"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
