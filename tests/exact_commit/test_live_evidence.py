"""Saved model evidence must not acquire answers or hide failed attempts."""

from mwpc_research.live_evidence import (
    live_jobs,
    snapshot_instance,
    study_tasks,
    summarize_live_rows,
)


def test_confirmation_is_disjoint_and_every_strategy_uses_identical_tasks_and_seeds():
    pilot = study_tasks("pilot")
    confirmation = study_tasks("confirmation")
    assert len(pilot) == len(confirmation) == 12
    assert not {t.prompt for t in pilot} & {t.prompt for t in confirmation}
    jobs = live_jobs("pilot", (71,), 2)
    for task in pilot:
        selected = [job for job in jobs if job["task"]["task_id"] == task.task_id]
        assert len(selected) == 9
        assert {job["seed"] for job in selected} == {71}
        assert len([job for job in selected if job["strategy"] == "capture"]) == 1
        for strategy in ("unconstrained", "serial", "epic", "exact"):
            assert len([job for job in selected if job["strategy"] == strategy]) == 2


def test_saved_support_is_nested_preserves_fixed_positions_and_never_injects_a_target():
    snapshot = {
        "snapshot_id": "test",
        "seed": 71,
        "task_id": "test-task",
        "forward_index": 0,
        "model_revision": "fake-model",
        "tokenizer_revision": "fake-tokenizer",
        "family": "brackets",
        "canvas": [None, 11, None],
        "rankings": [[10, 11], [10, 11], [11, 10]],
        "proposals": [{"proposal_id": 0, "position": 0, "token_id": 12, "weight": 0.7}],
        "termination_token_ids": [20],
        "pad_token_id": 20,
        "emissions": {"10": "28", "11": "29", "12": "5b", "20": None},
    }
    narrow, wide = (snapshot_instance(snapshot, width) for width in (1, 2))
    assert narrow.metadata["target_injected"] is False
    assert narrow.metadata["source_seed"] == 71
    assert narrow.metadata["source_task_id"] == "test-task"
    assert set(wide.metadata["model_token_ids"]) == {10, 11, 12, 20}
    assert narrow.selection_input.proposals == wide.selection_input.proposals
    assert narrow.selection_input.canvas == wide.selection_input.canvas
    assert narrow.selection_input.support.to_dict() != wide.selection_input.support.to_dict()


def test_runtime_summary_keeps_timeout_and_incomplete_attempts_in_denominator():
    common = {"strategy": "exact", "task": {"family": "brackets", "task_id": "one"}}
    rows = [
        {
            **common,
            "execution_status": "complete",
            "runtime_seconds": 2.0,
            "syntactic_valid": True,
            "functional_success": False,
        },
        {**common, "execution_status": "timeout", "runtime_seconds": None},
        {**common, "execution_status": "incomplete", "runtime_seconds": 1.0},
    ]
    group = summarize_live_rows(rows)["groups"][0]
    assert group["attempts"] == 3
    assert group["unique_tasks"] == 1
    assert group["functional_success"] == 0
    assert group["statuses"] == {"complete": 1, "timeout": 1, "incomplete": 1}
    assert group["complete_runtime_median_seconds"] == 2
    assert group["complete_runtime_sample_count"] == 1
