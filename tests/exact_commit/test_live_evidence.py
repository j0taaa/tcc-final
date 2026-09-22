"""Saved model evidence must not acquire answers or hide failed attempts."""

import gzip
import json
import subprocess
import sys
from pathlib import Path

import pytest

from mwpc_research.live_evidence import (
    snapshot_instance,
    summarize_live_rows,
)


def test_confirmation_is_disjoint_and_every_strategy_uses_identical_tasks_and_seeds():
    root = Path(__file__).resolve().parents[2] / "docs/artifacts/raw/m17_review_v1"
    prompts = []
    for cohort, seed, repetitions in (("pilot-v2", 170301, 1), ("confirmation", 170302, 2)):
        with gzip.open(root / cohort / "rows.jsonl.gz", "rt") as source:
            rows = [json.loads(line) for line in source]
        tasks = {row["task"]["task_id"]: row["task"] for row in rows}
        assert len(tasks) == 12
        prompts.append({task["prompt"] for task in tasks.values()})
        for task_id, task in tasks.items():
            selected = [row for row in rows if row["task"]["task_id"] == task_id]
            assert len(selected) == 4 * repetitions + 1
            assert all(row["task"] == task and row["seed"] == seed for row in selected)
            assert sum(row["strategy"] == "capture" for row in selected) == 1
            for strategy in ("unconstrained", "serial", "epic", "exact"):
                assert sum(row["strategy"] == strategy for row in selected) == repetitions
    assert not prompts[0] & prompts[1]


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


def test_batch_replay_uses_saved_probabilities_and_validates_both_methods(tmp_path):
    from mwpc_exact.evaluation.selection import recompute_witness_selection

    root = Path(__file__).resolve().parents[2]
    path = next(
        (root / "docs/artifacts/raw/m17_review_v1/confirmation/snapshots").glob(
            "confirm-brackets-*-forward0.json"
        )
    )
    snapshot = json.loads(path.read_text())
    original = json.dumps(snapshot, sort_keys=True)
    instances = [snapshot_instance(snapshot, 8, budget) for budget in (2, 8, 32)]
    assert [len(i.selection_input.proposals) for i in instances] == [2, 8, 32]
    assert len({i.selection_input.support.fingerprint for i in instances}) == 1
    for instance in instances:
        for p in instance.selection_input.proposals:
            assert p.weight == snapshot["ranked_probabilities"][p.position][0]
            assert (
                instance.metadata["model_token_ids"][p.token_id]
                == snapshot["rankings"][p.position][0]
            )
    assert json.dumps(snapshot, sort_keys=True) == original
    for invalid in (True, 0, -1, 1.5):
        with pytest.raises((TypeError, ValueError)):
            snapshot_instance(snapshot, 8, invalid)
    # A small feasible fixture exercises both certificate checks even when
    # a real model snapshot happens to have no grammar-valid completion.
    snapshot.update(
        canvas=[None] * 4,
        rankings=[[10, 11], [11, 10], [20, 10], [20, 10]],
        ranked_probabilities=[[0.8, 0.2]] * 4,
        proposals=[],
        termination_token_ids=[20],
        pad_token_id=20,
        emissions={"10": "28", "11": "29", "20": None},
    )
    instance = snapshot_instance(snapshot, 2, 4)
    for method in ("rust_exact", "greedy_exact_feasibility"):
        job = tmp_path / f"{method}.json"
        result_path = tmp_path / f"{method}-result.json"
        job.write_text(json.dumps({"instance": instance.to_dict(), "method": method}))
        subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.exact_commit.run_review_offline",
                "--child-job",
                str(job),
                "--child-result",
                str(result_path),
            ],
            check=True,
            cwd=root,
            timeout=15,
        )
        result = json.loads(result_path.read_text())
        assert result["independent_syntax"] is True
        ids, score = recompute_witness_selection(
            instance.selection_input, result["result"]["witness_token_ids"]
        )
        assert set(ids) == set(result["result"]["selected_proposal_ids"])
        assert score == result["score"]


def test_real_batch_optimum_agrees_with_independent_python_reference():
    from mwpc_exact import ExactBackend
    from mwpc_exact.evaluation.selection import select_exact_mwpc

    root = Path(__file__).resolve().parents[2] / "docs/artifacts/raw/m17_review_v1"
    snapshot = json.loads(
        (
            root / "confirmation/snapshots" / "confirm-brackets-3-170302-capture-forward0.json"
        ).read_text()
    )
    state = snapshot_instance(snapshot, 4, 32).selection_input
    results = [
        select_exact_mwpc(state, backend=backend)
        for backend in (ExactBackend.PYTHON, ExactBackend.RUST)
    ]
    assert all(result.score == 14.318663361719748 for result in results)
    assert all(len(result.selected_proposal_ids) == 31 for result in results)
