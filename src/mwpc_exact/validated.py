"""Typed boundary between independently validated solves and physical commits."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from math import isclose

from mwpc_exact.types import ExactCommitResult, SolveStatus
from mwpc_exact.validator import ValidationReport


@dataclass(frozen=True, slots=True)
class ValidatedExactCommit:
    """An optimal result paired with its typed independent validation report."""

    result: ExactCommitResult
    validation_report: ValidationReport

    def __post_init__(self) -> None:
        if not isinstance(self.result, ExactCommitResult):
            raise TypeError("result must be an ExactCommitResult")
        if not isinstance(self.validation_report, ValidationReport):
            raise TypeError("validation_report must be a ValidationReport")
        if self.result.status is not SolveStatus.OPTIMAL:
            raise ValueError("ValidatedExactCommit requires an OPTIMAL result")
        if not self.validation_report.is_valid:
            raise ValueError("ValidatedExactCommit requires a fully valid report")
        if Counter(self.result.selected_proposal_ids) != Counter(
            self.validation_report.recomputed_selected_proposal_ids
        ):
            raise ValueError("validation report proposal IDs disagree with the result")
        recomputed = self.validation_report.recomputed_objective
        if recomputed is None or self.result.objective_value is None or not isclose(
            self.result.objective_value, recomputed, rel_tol=1e-12, abs_tol=1e-12
        ):
            raise ValueError("validation report objective disagrees with the result")

    @property
    def status(self) -> SolveStatus:
        return self.result.status

    @property
    def exactness_scope(self):  # type: ignore[no-untyped-def]
        return self.result.exactness_scope

    @property
    def objective_value(self) -> float:
        assert self.result.objective_value is not None
        return self.result.objective_value

    @property
    def selected_proposal_ids(self) -> tuple[int, ...]:
        return self.result.selected_proposal_ids

    @property
    def witness_token_ids(self) -> tuple[int, ...]:
        return self.result.witness_token_ids

    @property
    def witness_terminal_labels(self):  # type: ignore[no-untyped-def]
        return self.result.witness_terminal_labels

    @property
    def witness_graph_edge_ids(self) -> tuple[int, ...]:
        return self.result.witness_graph_edge_ids

    @property
    def witness_eos_position(self) -> int | None:
        return self.result.witness_eos_position

    @property
    def witness_content_endpoint_slot(self) -> int | None:
        return self.result.witness_content_endpoint_slot

    @property
    def diagnostics(self) -> Mapping[str, object]:
        return self.result.diagnostics

    def to_dict(self) -> dict[str, object]:
        return self.result.to_dict()


def validated_exact_commit(result: ExactCommitResult) -> ValidatedExactCommit:
    """Create the typed commit boundary from the orchestrator's recorded report."""

    if not isinstance(result, ExactCommitResult):
        raise TypeError("result must be an ExactCommitResult")
    raw_report = result.diagnostics.get("certificate_validation")
    if not isinstance(raw_report, Mapping):
        raise ValueError("optimal result omitted typed certificate-validation evidence")
    return ValidatedExactCommit(
        result=result,
        validation_report=ValidationReport.from_dict(raw_report),
    )


__all__ = ["ValidatedExactCommit", "validated_exact_commit"]
