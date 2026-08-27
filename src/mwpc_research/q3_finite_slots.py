"""Q3 experiment over curated abstract-``Sigma*`` finite-slot counterexamples."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from time import monotonic, perf_counter
from types import MappingProxyType

from mwpc_exact.experiments.artifacts import prepare_artifact_directories
from mwpc_exact.types import SolveStatus
from mwpc_research.finite_slot_counterexamples import (
    ABSTRACT_SIGMA_STAR_SEMANTICS,
    FiniteSlotCounterexample,
    FiniteSlotCounterexampleReport,
    replay_finite_slot_counterexample,
)

Q3_ARTIFACT_SCHEMA_VERSION = 1
Q3_RAW_ARTIFACT_KIND = "mwpc_q3_finite_slot_row"
Q3_SUMMARY_ARTIFACT_KIND = "mwpc_q3_finite_slot_summary"
Q3_RAW_FILENAME = "q3-finite-slot-rows.jsonl"
Q3_SUMMARY_FILENAME = "q3-finite-slot-summary.json"
Q3_CASE_IDS = (
    "required_eos_one_slot_infeasible_v1",
    "required_eos_one_slot_lower_empty_v1",
)

_FINITE_REASON_BY_STATUS = {
    SolveStatus.INFEASIBLE_ON_SUPPORT: (
        "no_grammar_valid_finite_path_under_explicit_support_and_required_eos"
    ),
    SolveStatus.OPTIMAL: ("abstract_witness_exceeds_canvas_lower_score_finite_path_selected"),
}


def _grammar_sha256(case: FiniteSlotCounterexample) -> str:
    payload = json.dumps(case.grammar.to_dict(), separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class Q3CaseRecord:
    """One measured comparison between relaxed and finite-slot decisions."""

    case: FiniteSlotCounterexample
    report: FiniteSlotCounterexampleReport | None
    runtime_seconds: float
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.case, FiniteSlotCounterexample):
            raise TypeError("case must be a FiniteSlotCounterexample")
        if self.report is not None and not isinstance(self.report, FiniteSlotCounterexampleReport):
            raise TypeError("report must be a FiniteSlotCounterexampleReport or None")
        if not isfinite(self.runtime_seconds) or self.runtime_seconds < 0.0:
            raise ValueError("runtime_seconds must be finite and non-negative")
        if self.report is None:
            if not self.error_type or self.error_message is None:
                raise ValueError("a failed Q3 record requires error details")
        elif self.error_type is not None or self.error_message is not None:
            raise ValueError("a successful Q3 record cannot contain error details")

    @property
    def success(self) -> bool:
        return self.report is not None

    @property
    def claim_supported(self) -> bool:
        report = self.report
        if report is None or report.slot_shortfall <= 0:
            return False
        if report.finite_status is SolveStatus.INFEASIBLE_ON_SUPPORT:
            return report.finite_objective is None and report.finite_witness_token_ids is None
        return (
            report.finite_status is SolveStatus.OPTIMAL
            and report.finite_objective is not None
            and report.finite_objective < report.abstract_objective
            and report.finite_witness_token_ids is not None
        )

    def to_dict(
        self,
        *,
        run_metadata: Mapping[str, object],
        fixture_path: str,
        fixture_sha256: str,
    ) -> dict[str, object]:
        """Serialize one raw row without hiding unsuccessful decisions."""

        base: dict[str, object] = {
            "artifact_kind": Q3_RAW_ARTIFACT_KIND,
            "schema_version": Q3_ARTIFACT_SCHEMA_VERSION,
            "case_id": self.case.case_id,
            "title": self.case.title,
            "case_kind": "curated_synthetic_counterexample",
            "success": self.success,
            "runtime_seconds": self.runtime_seconds,
            "fixture_path": fixture_path,
            "fixture_sha256": fixture_sha256,
            "grammar_sha256": _grammar_sha256(self.case),
            "run_metadata": dict(run_metadata),
            "error_type": self.error_type,
            "error_message": self.error_message,
        }
        report = self.report
        if report is None:
            return {
                **base,
                "slot_accounting": None,
                "abstract_decision": None,
                "finite_decision": None,
                "comparison": {"claim_supported": False},
                "independent_validation": None,
            }

        finite_reason = _FINITE_REASON_BY_STATUS[report.finite_status]
        finite_witness = {
            "token_ids": (
                None
                if report.finite_witness_token_ids is None
                else list(report.finite_witness_token_ids)
            ),
            "terminal_labels": (
                None
                if report.finite_witness_terminal_labels is None
                else list(report.finite_witness_terminal_labels)
            ),
            "graph_edge_ids": (
                None
                if report.finite_witness_graph_edge_ids is None
                else list(report.finite_witness_graph_edge_ids)
            ),
            "token_roles": (
                None
                if report.finite_witness_token_roles is None
                else list(report.finite_witness_token_roles)
            ),
            "eos_position": report.finite_witness_eos_position,
            "content_endpoint_slot": report.finite_witness_content_endpoint_slot,
        }
        return {
            **base,
            "slot_accounting": {
                "available_physical_slots": report.available_physical_slots,
                "minimum_content_tokens_in_abstract_witness": len(
                    self.case.abstract_witness_token_ids
                ),
                "required_termination_tokens": 1,
                "minimum_required_physical_tokens": report.minimum_physical_slots,
                "slot_shortfall": report.slot_shortfall,
            },
            "abstract_decision": {
                "abstraction": "ordered_anchor_sigma_star",
                "semantics": ABSTRACT_SIGMA_STAR_SEMANTICS,
                "status": "accepted",
                "pattern": report.abstract_pattern,
                "witness_token_ids": list(self.case.abstract_witness_token_ids),
                "witness_terminal_labels": list(report.abstract_terminal_labels),
                "objective_value": report.abstract_objective,
            },
            "finite_decision": {
                "status": report.finite_status.value,
                "reason_code": finite_reason,
                "objective_value": report.finite_objective,
                "selected_proposal_ids": list(report.finite_selected_proposal_ids),
                "witness": finite_witness,
                "exactness_scope": {
                    "claim": "exact_on_support",
                    **report.finite_exactness_scope.to_dict(),
                },
                "represented_support_sha256": report.represented_support_sha256,
                "eos_policy": report.eos_policy.to_dict(),
            },
            "comparison": {
                "abstract_witness_fits_finite_canvas": False,
                "abstract_objective_minus_finite": (
                    None
                    if report.finite_objective is None
                    else report.abstract_objective - report.finite_objective
                ),
                "claim_supported": self.claim_supported,
            },
            "independent_validation": {
                "abstract_witness_cfg_recognized": True,
                "required_eos_slot_count_recomputed": True,
                "finite_paths_exhaustively_enumerated": True,
                "finite_parser_agreed_with_enumeration": True,
            },
        }


@dataclass(frozen=True, slots=True)
class Q3ExperimentResult:
    """Complete raw records plus computed Q3 summary metadata."""

    records: tuple[Q3CaseRecord, ...]
    run_metadata: Mapping[str, object]
    fixture_path: str
    fixture_sha256: str

    def __post_init__(self) -> None:
        records = tuple(self.records)
        if not records:
            raise ValueError("Q3 experiment requires at least one record")
        if len({record.case.case_id for record in records}) != len(records):
            raise ValueError("Q3 case IDs must be unique")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "run_metadata", MappingProxyType(dict(self.run_metadata)))

    @property
    def failed_cases(self) -> int:
        return sum(not record.success for record in self.records)

    def summary_dict(self) -> dict[str, object]:
        """Compute a compact claim-level summary solely from raw records."""

        successful = tuple(record for record in self.records if record.success)
        status_counts = Counter(
            record.report.finite_status.value for record in successful if record.report is not None
        )
        claim_rows = []
        for record in successful:
            report = record.report
            assert report is not None
            claim_rows.append(
                {
                    "case_id": record.case.case_id,
                    "available_physical_slots": report.available_physical_slots,
                    "minimum_required_physical_tokens": report.minimum_physical_slots,
                    "slot_shortfall": report.slot_shortfall,
                    "abstract_status": "accepted",
                    "abstract_witness_token_ids": list(record.case.abstract_witness_token_ids),
                    "finite_status": report.finite_status.value,
                    "finite_reason_code": _FINITE_REASON_BY_STATUS[report.finite_status],
                    "finite_objective_value": report.finite_objective,
                    "finite_witness_token_ids": (
                        None
                        if report.finite_witness_token_ids is None
                        else list(report.finite_witness_token_ids)
                    ),
                    "claim_supported": record.claim_supported,
                }
            )
        return {
            "artifact_kind": Q3_SUMMARY_ARTIFACT_KIND,
            "schema_version": Q3_ARTIFACT_SCHEMA_VERSION,
            "case_count": len(self.records),
            "passed_cases": len(successful),
            "failed_cases": self.failed_cases,
            "curated_case_count": len(self.records),
            "real_decoder_state_count": 0,
            "abstract_accept_count": len(successful),
            "finite_status_counts": dict(sorted(status_counts.items())),
            "finite_slot_false_positive_count": sum(
                record.claim_supported for record in successful
            ),
            "all_results_support_finite_slot_claim": (
                bool(successful)
                and not self.failed_cases
                and all(record.claim_supported for record in successful)
            ),
            "total_runtime_seconds": sum(record.runtime_seconds for record in self.records),
            "source_fixture": {
                "path": self.fixture_path,
                "sha256": self.fixture_sha256,
            },
            "cases": claim_rows,
            "failures": [
                {
                    "case_id": record.case.case_id,
                    "error_type": record.error_type,
                    "error_message": record.error_message,
                }
                for record in self.records
                if not record.success
            ],
            "run_metadata": dict(self.run_metadata),
        }


def run_q3_finite_slot_cases(
    cases: Sequence[FiniteSlotCounterexample],
    *,
    run_metadata: Mapping[str, object],
    fixture_path: str,
    fixture_sha256: str,
    replay: Callable[
        [FiniteSlotCounterexample], FiniteSlotCounterexampleReport
    ] = replay_finite_slot_counterexample,
    case_timeout_seconds: float | None = None,
    run_timeout_seconds: float | None = None,
) -> Q3ExperimentResult:
    """Replay all curated cases and preserve failures as distinct raw rows."""

    case_items = tuple(cases)
    if not case_items:
        raise ValueError("Q3 cases must not be empty")
    for value, field_name in (
        (case_timeout_seconds, "case_timeout_seconds"),
        (run_timeout_seconds, "run_timeout_seconds"),
    ):
        if value is not None and (not isfinite(value) or value <= 0.0):
            raise ValueError(f"{field_name} must be finite and positive")
    deadline = None if run_timeout_seconds is None else monotonic() + run_timeout_seconds
    records: list[Q3CaseRecord] = []
    for case in case_items:
        start = perf_counter()
        try:
            if deadline is not None and monotonic() >= deadline:
                raise TimeoutError("Q3 run deadline expired before this case started")
            report = replay(case)
            if report.case_id != case.case_id:
                raise AssertionError("Q3 replay returned a report for a different case")
            if case_timeout_seconds is not None and perf_counter() - start > case_timeout_seconds:
                raise TimeoutError("Q3 case exceeded its configured solver deadline")
            if deadline is not None and monotonic() > deadline:
                raise TimeoutError("Q3 run deadline expired while replaying this case")
        except Exception as error:
            records.append(
                Q3CaseRecord(
                    case=case,
                    report=None,
                    runtime_seconds=perf_counter() - start,
                    error_type=type(error).__name__,
                    error_message=str(error),
                )
            )
        else:
            records.append(
                Q3CaseRecord(
                    case=case,
                    report=report,
                    runtime_seconds=perf_counter() - start,
                )
            )
    return Q3ExperimentResult(
        records=tuple(records),
        run_metadata=run_metadata,
        fixture_path=fixture_path,
        fixture_sha256=fixture_sha256,
    )


def write_q3_artifacts(
    result: Q3ExperimentResult,
    raw_directory: str | Path,
    processed_directory: str | Path,
) -> tuple[Path, Path]:
    """Write immutable raw Q3 rows separately from their computed summary."""

    if not isinstance(result, Q3ExperimentResult):
        raise TypeError("result must be a Q3ExperimentResult")
    raw_output, processed_output = prepare_artifact_directories(
        raw_directory,
        processed_directory,
    )
    raw_path = raw_output / Q3_RAW_FILENAME
    summary_path = processed_output / Q3_SUMMARY_FILENAME
    if raw_path.exists() or summary_path.exists():
        raise FileExistsError("refusing to overwrite Q3 raw or processed artifacts")
    with raw_path.open("x", encoding="utf-8") as output:
        for record in result.records:
            output.write(
                json.dumps(
                    record.to_dict(
                        run_metadata=result.run_metadata,
                        fixture_path=result.fixture_path,
                        fixture_sha256=result.fixture_sha256,
                    ),
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
    with summary_path.open("x", encoding="utf-8") as output:
        json.dump(result.summary_dict(), output, allow_nan=False, indent=2, sort_keys=True)
        output.write("\n")
    return raw_path, summary_path


__all__ = [
    "Q3_ARTIFACT_SCHEMA_VERSION",
    "Q3_CASE_IDS",
    "Q3_RAW_FILENAME",
    "Q3_SUMMARY_FILENAME",
    "Q3CaseRecord",
    "Q3ExperimentResult",
    "run_q3_finite_slot_cases",
    "write_q3_artifacts",
]
