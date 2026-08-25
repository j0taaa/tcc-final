from __future__ import annotations

from collections.abc import Mapping

import pytest

from mwpc_exact import (
    ExactCommitResult,
    ExactnessScope,
    SolveStatus,
    SupportKind,
    ValidatedExactCommit,
    ValidationReport,
)
from mwpc_exact.validated import _validated_exact_commit

SCOPE = ExactnessScope(
    kind=SupportKind.EXPLICIT,
    vocabulary_size=2,
    pruning_description="typed validation boundary fixture",
)


def result() -> ExactCommitResult:
    return ExactCommitResult(
        status=SolveStatus.OPTIMAL,
        exactness_scope=SCOPE,
        objective_value=1.0,
        selected_proposal_ids=(7,),
        witness_token_ids=(0,),
        witness_terminal_labels=(97,),
        witness_graph_edge_ids=(1,),
        witness_content_endpoint_slot=1,
    )


def test_validated_boundary_requires_a_fully_valid_typed_report() -> None:
    validated = _validated_exact_commit(
        result(),
        ValidationReport(
            issues=(),
            skipped_checks=(),
            recomputed_objective=1.0,
            recomputed_selected_proposal_ids=(7,),
        ),
    )

    assert validated.status is SolveStatus.OPTIMAL
    assert validated.result.objective_value == 1.0


def test_validated_boundary_rejects_mismatched_objective() -> None:
    with pytest.raises(ValueError, match="objective"):
        _validated_exact_commit(
            result(),
            ValidationReport(
                issues=(),
                skipped_checks=(),
                recomputed_objective=0.0,
                recomputed_selected_proposal_ids=(7,),
            ),
        )


def test_public_constructor_cannot_turn_self_reported_diagnostics_into_authority() -> None:
    forged = ExactCommitResult(
        status=SolveStatus.OPTIMAL,
        exactness_scope=SCOPE,
        objective_value=1.0,
        selected_proposal_ids=(7,),
        witness_token_ids=(0,),
        witness_terminal_labels=(255,),
        witness_graph_edge_ids=(999,),
        witness_content_endpoint_slot=1,
        diagnostics={
            "certificate_validation": {
                "is_valid": True,
                "issues": [],
                "skipped_checks": [],
                "recomputed_objective": 1.0,
                "recomputed_selected_proposal_ids": [7],
            }
        },
    )
    raw_report = forged.diagnostics["certificate_validation"]
    assert isinstance(raw_report, Mapping)
    report = ValidationReport.from_dict(raw_report)

    with pytest.raises(TypeError, match="validated solve API"):
        ValidatedExactCommit(forged, report)
