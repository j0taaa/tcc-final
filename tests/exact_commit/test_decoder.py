from __future__ import annotations

import json

import pytest

from mwpc_exact import (
    CommitGuarantee,
    CommitSource,
    ExactCommitResult,
    ExactnessScope,
    FailureFallbackRequest,
    FailureFallbackStrategy,
    FallbackSelection,
    FallbackToken,
    Proposal,
    SolveStatus,
    SupportKind,
    apply_exact_commit_result,
)

SCOPE = ExactnessScope(
    kind=SupportKind.EXPLICIT,
    vocabulary_size=10,
    pruning_description="T803 offline decoder fixture",
)


def optimal_result(
    witness: tuple[int, ...],
    *,
    selected: tuple[int, ...] = (),
    objective: float = 0.0,
) -> ExactCommitResult:
    return ExactCommitResult(
        status=SolveStatus.OPTIMAL,
        exactness_scope=SCOPE,
        objective_value=objective,
        selected_proposal_ids=selected,
        witness_token_ids=witness,
        witness_terminal_labels=(ord("a"),),
        witness_graph_edge_ids=(100,),
        witness_content_endpoint_slot=len(witness),
        diagnostics={"certificate_validation": {"is_valid": True}},
    )


def failed_result(
    status: SolveStatus,
    *,
    diagnostics: dict[str, object] | None = None,
) -> ExactCommitResult:
    return ExactCommitResult(
        status=status,
        exactness_scope=SCOPE,
        diagnostics={} if diagnostics is None else diagnostics,
    )


def test_optimal_nonempty_selection_commits_exactly_matching_proposals() -> None:
    canvas = (None, None, 9, None)
    proposals = (
        Proposal(10, position=0, token_id=4, weight=2),
        Proposal(11, position=0, token_id=4, weight=3),
        Proposal(12, position=1, token_id=5, weight=1),
        Proposal(13, position=3, token_id=7, weight=4),
    )
    result = optimal_result((4, 5, 9, 6), selected=(10, 11, 12), objective=6)

    step = apply_exact_commit_result(result, canvas=canvas, proposals=proposals)

    assert step.solver_result is result
    assert step.updated_canvas == (4, 5, 9, None)
    assert step.commit_source is CommitSource.EXACT_PROPOSALS
    assert step.commit_guarantee is CommitGuarantee.EXACT_MWPC_SELECTION
    assert tuple((commit.position, commit.token_id) for commit in step.commits) == (
        (0, 4),
        (1, 5),
    )
    assert step.commits[0].selected_proposal_ids == (10, 11)
    assert step.commits[0].matching_proposal_ids == (10, 11)
    assert step.commits[0].matching_proposal_weight == 5.0
    assert step.selected_proposal_ids == (10, 11, 12)
    assert step.diagnostics["committed_position_count"] == 2
    assert step.diagnostics["witness_compatible_after_commit"] is True
    assert step.diagnostics["progress_fallback"] is False
    assert step.diagnostics["failure_fallback_attempted"] is False
    json.dumps(step.to_dict())


def test_optimal_selected_set_is_recomputed_before_any_commit() -> None:
    proposals = (
        Proposal(10, position=0, token_id=4, weight=2),
        Proposal(11, position=0, token_id=4, weight=3),
    )
    corrupted = optimal_result((4,), selected=(10,), objective=2)

    with pytest.raises(ValueError, match="selected proposal IDs disagree"):
        apply_exact_commit_result(corrupted, canvas=(None,), proposals=proposals)


def test_optimal_result_without_independent_validation_is_never_committed() -> None:
    unvalidated = ExactCommitResult(
        status=SolveStatus.OPTIMAL,
        exactness_scope=SCOPE,
        objective_value=1,
        selected_proposal_ids=(10,),
        witness_token_ids=(4,),
        witness_terminal_labels=(ord("a"),),
        witness_graph_edge_ids=(100,),
        witness_content_endpoint_slot=1,
    )

    with pytest.raises(ValueError, match="independent certificate validation"):
        apply_exact_commit_result(
            unvalidated,
            canvas=(None,),
            proposals=(Proposal(10, position=0, token_id=4, weight=1),),
        )


def test_optimal_witness_must_preserve_fixed_canvas_before_commit() -> None:
    result = optimal_result((3, 5), selected=(10,), objective=1)
    proposals = (Proposal(10, position=1, token_id=5, weight=1),)

    with pytest.raises(ValueError, match="does not preserve"):
        apply_exact_commit_result(result, canvas=(4, None), proposals=proposals)


def test_selected_decoder_proposal_cannot_target_an_already_fixed_slot() -> None:
    result = optimal_result((4, 5), selected=(10,), objective=1)
    proposals = (Proposal(10, position=0, token_id=4, weight=1),)

    with pytest.raises(ValueError, match="currently masked positions"):
        apply_exact_commit_result(result, canvas=(4, None), proposals=proposals)


def test_zero_score_optimum_uses_probability_then_position_tie_break() -> None:
    canvas = (None, None, 7, None)
    result = optimal_result((1, 2, 7, 3))
    proposals = (Proposal(20, position=1, token_id=2, weight=0),)

    step = apply_exact_commit_result(
        result,
        canvas=canvas,
        proposals=proposals,
        witness_token_probabilities=(0.5, 0.8, 0.99, 0.8),
    )

    assert step.updated_canvas == (None, 2, 7, None)
    assert step.commit_source is CommitSource.WITNESS_PROGRESS
    assert step.commit_guarantee is CommitGuarantee.EXACT_WITNESS_PROGRESS
    assert len(step.commits) == 1
    assert step.commits[0].position == 1
    assert step.commits[0].selected_proposal_ids == ()
    assert step.commits[0].matching_proposal_ids == (20,)
    assert step.commits[0].matching_proposal_weight == 0.0
    assert step.selected_proposal_ids == ()
    assert step.solver_result.selected_proposal_ids == ()
    assert step.fallback_reason == "optimal_zero_selected_proposals"
    assert step.diagnostics["fallback_class"] == "witness_progress"
    assert step.diagnostics["progress_fallback"] is True
    assert step.diagnostics["progress_fallback_rule"] == (
        "witness_probability_descending_then_absolute_position_ascending"
    )
    assert step.diagnostics["failure_fallback_attempted"] is False
    assert step.diagnostics["witness_compatible_after_commit"] is True


def test_zero_selected_progress_requires_explicit_witness_probabilities() -> None:
    with pytest.raises(ValueError, match="required for deterministic witness progress"):
        apply_exact_commit_result(
            optimal_result((1, 2)),
            canvas=(None, None),
            proposals=(),
        )


@pytest.mark.parametrize(
    "probabilities",
    [(0.1,), (0.1, float("nan")), (0.1, 1.1), (0.1, True)],
)
def test_witness_progress_rejects_malformed_probabilities(
    probabilities: tuple[object, ...],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        apply_exact_commit_result(
            optimal_result((1, 2)),
            canvas=(None, None),
            proposals=(),
            witness_token_probabilities=probabilities,  # type: ignore[arg-type]
        )


def test_empty_selected_set_cannot_hide_a_positive_matching_proposal() -> None:
    result = optimal_result((4,), selected=(), objective=0)
    proposals = (Proposal(10, position=0, token_id=4, weight=2),)

    with pytest.raises(ValueError, match="selected proposal IDs disagree"):
        apply_exact_commit_result(
            result,
            canvas=(None,),
            proposals=proposals,
            witness_token_probabilities=(0.8,),
        )


def test_fully_fixed_optimal_witness_is_complete_without_a_fake_commit() -> None:
    result = optimal_result((4, 5))

    step = apply_exact_commit_result(result, canvas=(4, 5), proposals=())

    assert step.commit_source is CommitSource.COMPLETE
    assert step.commit_guarantee is CommitGuarantee.EXACT_WITNESS_PROGRESS
    assert step.updated_canvas == (4, 5)
    assert step.commits == ()
    assert step.diagnostics["committed_position_count"] == 0


@pytest.mark.parametrize(
    ("status", "strategy", "expected_source"),
    [
        (
            SolveStatus.TIMEOUT,
            FailureFallbackStrategy.SERIAL,
            CommitSource.SERIAL_FALLBACK,
        ),
        (SolveStatus.ERROR, FailureFallbackStrategy.EPIC, CommitSource.EPIC_FALLBACK),
        (
            SolveStatus.INFEASIBLE_ON_SUPPORT,
            FailureFallbackStrategy.SERIAL,
            CommitSource.SERIAL_FALLBACK,
        ),
        (
            SolveStatus.UNSUPPORTED,
            FailureFallbackStrategy.EPIC,
            CommitSource.EPIC_FALLBACK,
        ),
    ],
)
def test_nonoptimal_status_invokes_configured_baseline_without_exact_label(
    status: SolveStatus,
    strategy: FailureFallbackStrategy,
    expected_source: CommitSource,
) -> None:
    diagnostics: dict[str, object] = {
        "adaptive_support": {
            "attempted_k": [2, 4],
            "stopped_reason": "terminal_status_timeout",
        }
    }
    if status is SolveStatus.ERROR:
        diagnostics.update(
            {
                "error_stage": "backend_solve",
                "error_type": "RuntimeError",
                "error_message": "fixture failure",
            }
        )
    result = failed_result(status, diagnostics=diagnostics)
    proposal = Proposal(30, position=1, token_id=6, weight=3)
    requests: list[FailureFallbackRequest] = []

    def fallback(request: FailureFallbackRequest) -> FallbackSelection:
        requests.append(request)
        return FallbackSelection(
            tokens=(FallbackToken(position=1, token_id=6),),
            diagnostics={"baseline": strategy.value, "accepted": True},
        )

    step = apply_exact_commit_result(
        result,
        canvas=(8, None),
        proposals=(proposal,),
        failure_fallback_strategy=strategy,
        failure_fallback=fallback,
    )

    assert len(requests) == 1
    assert requests[0].solver_result.status is status
    assert requests[0].strategy is strategy
    assert step.solver_result.status is status
    assert step.solver_result.status is not SolveStatus.OPTIMAL
    assert step.updated_canvas == (8, 6)
    assert step.commit_source is expected_source
    assert (
        step.commit_guarantee
        is CommitGuarantee.BASELINE_FALLBACK_NO_EXACT_GUARANTEE
    )
    assert step.fallback_strategy is strategy
    assert step.selected_proposal_ids == ()
    assert step.matching_proposal_ids == (30,)
    assert step.commits[0].matching_proposal_weight == 3.0
    assert f"solver_status={status.value}" in (step.fallback_reason or "")
    assert step.diagnostics["fallback_class"] == "solver_failure"
    assert step.diagnostics["progress_fallback"] is False
    assert step.diagnostics["failure_fallback_attempted"] is True
    assert step.diagnostics["failure_fallback_succeeded"] is True
    assert step.diagnostics["support_expansion_attempted_k"] == (2, 4)
    assert step.diagnostics["fallback_handler_diagnostics"]["accepted"] is True  # type: ignore[index]
    json.dumps(step.to_dict())


def test_fallback_can_commit_multiple_distinct_masked_positions_without_remasking() -> None:
    result = failed_result(SolveStatus.TIMEOUT)

    def serial(_request: FailureFallbackRequest) -> FallbackSelection:
        return FallbackSelection(
            tokens=(FallbackToken(0, 2), FallbackToken(2, 4)),
        )

    step = apply_exact_commit_result(
        result,
        canvas=(None, 9, None),
        proposals=(),
        failure_fallback_strategy=FailureFallbackStrategy.SERIAL,
        failure_fallback=serial,
    )

    assert step.updated_canvas == (2, 9, 4)
    assert tuple(commit.position for commit in step.commits) == (0, 2)
    assert step.diagnostics["no_remasking_verified"] is True


def test_fallback_handler_exception_is_recorded_without_partial_commit() -> None:
    result = failed_result(SolveStatus.ERROR)

    def broken(_request: FailureFallbackRequest) -> FallbackSelection:
        raise RuntimeError("injected serial failure")

    step = apply_exact_commit_result(
        result,
        canvas=(None,),
        proposals=(),
        failure_fallback_strategy=FailureFallbackStrategy.SERIAL,
        failure_fallback=broken,
    )

    assert step.solver_result.status is SolveStatus.ERROR
    assert step.commit_source is CommitSource.FALLBACK_FAILED
    assert step.commit_guarantee is CommitGuarantee.NONE
    assert step.updated_canvas == (None,)
    assert step.commits == ()
    assert step.diagnostics["failure_fallback_attempted"] is True
    assert step.diagnostics["failure_fallback_succeeded"] is False
    assert step.diagnostics["fallback_error_type"] == "RuntimeError"
    assert step.diagnostics["fallback_error_message"] == "injected serial failure"


def test_fallback_cannot_overwrite_a_fixed_slot() -> None:
    result = failed_result(SolveStatus.TIMEOUT)

    def invalid(_request: FailureFallbackRequest) -> FallbackSelection:
        return FallbackSelection(tokens=(FallbackToken(0, 3),))

    step = apply_exact_commit_result(
        result,
        canvas=(8, None),
        proposals=(),
        failure_fallback_strategy=FailureFallbackStrategy.EPIC,
        failure_fallback=invalid,
    )

    assert step.commit_source is CommitSource.FALLBACK_FAILED
    assert step.updated_canvas == (8, None)
    assert step.diagnostics["fallback_error_type"] == "ValueError"
    assert "already fixed" in step.diagnostics["fallback_error_message"]


def test_nonoptimal_result_without_configured_fallback_is_explicit_no_commit() -> None:
    result = failed_result(SolveStatus.TIMEOUT)

    step = apply_exact_commit_result(result, canvas=(None,), proposals=())

    assert step.commit_source is CommitSource.NO_COMMIT
    assert step.commit_guarantee is CommitGuarantee.NONE
    assert step.updated_canvas == (None,)
    assert step.diagnostics["failure_fallback_attempted"] is False
    assert "no_failure_fallback_configured" in (step.fallback_reason or "")


def test_fallback_strategy_and_callable_must_be_configured_together() -> None:
    result = failed_result(SolveStatus.TIMEOUT)

    with pytest.raises(ValueError, match="must be supplied together"):
        apply_exact_commit_result(
            result,
            canvas=(None,),
            proposals=(),
            failure_fallback_strategy=FailureFallbackStrategy.SERIAL,
        )

    def fallback(_request: FailureFallbackRequest) -> FallbackSelection:
        return FallbackSelection(tokens=(FallbackToken(0, 1),))

    with pytest.raises(ValueError, match="must be supplied together"):
        apply_exact_commit_result(
            result,
            canvas=(None,),
            proposals=(),
            failure_fallback=fallback,
        )


def test_fallback_selection_rejects_empty_or_duplicate_updates() -> None:
    with pytest.raises(ValueError, match="at least one"):
        FallbackSelection(tokens=())
    with pytest.raises(ValueError, match="more than once"):
        FallbackSelection(tokens=(FallbackToken(0, 1), FallbackToken(0, 2)))
