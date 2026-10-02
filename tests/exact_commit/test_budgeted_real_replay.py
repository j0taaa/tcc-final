"""Authentic-source reconstruction and scientific replay boundaries, offline."""

from __future__ import annotations

import json
import subprocess
from fractions import Fraction

import pytest
from scripts.exact_commit import run_budgeted_real_replay as replay

from mwpc_exact import ComponentProfiler
from mwpc_exact.budget_proof import read_budget_proof
from mwpc_exact.budgeted_commit import budgeted_commit_frontier


def test_frozen_real_cohort_is_complete_and_profiles_preserve_support():
    config = replay.read_json(replay.DEFAULT_CONFIG)
    cases = list(replay.cases(config))
    assert len(cases) == 72
    assert len({case.metadata["source_task_id"] for case in cases}) == 13
    for all_primary, ordinary in zip(cases[::2], cases[1::2], strict=True):
        full, visible = all_primary.selection_input, ordinary.selection_input
        assert full.canvas == visible.canvas
        assert full.support == visible.support
        assert full.grammar == visible.grammar
        assert full.eos_policy == visible.eos_policy
        assert full.tokenizer_adapter == visible.tokenizer_adapter
        assert len(full.proposals) == sum(t is None for t in full.canvas)
        specials = {*full.eos_policy.termination_token_ids, full.eos_policy.pad_token_id}
        assert visible.proposals == tuple(p for p in full.proposals if p.token_id not in specials)
        assert set(ordinary.metadata["excluded_special_proposal_ids"]) == {
            p.proposal_id for p in full.proposals if p.token_id in specials
        }


def test_recursive_replay_preserves_saved_primary_probabilities_without_preselection():
    config = replay.read_json(replay.DEFAULT_CONFIG)
    case = next(replay.cases(config))
    source = replay.read_json(replay.ROOT / case.metadata["source_path"])
    model_ids = case.metadata["model_token_ids"]
    for p in case.selection_input.proposals:
        assert p.weight == source["ranked_probabilities"][p.position][0]
        assert model_ids[p.token_id] == source["rankings"][p.position][0]
    assert len(case.selection_input.proposals) > len(source["proposals"])


def test_query_compaction_retains_original_tokens_weights_and_every_physical_slot():
    record = replay.read_json(replay.ROOT / replay.read_json(replay.DEFAULT_CONFIG)["query_record"])
    for step in record["generation"]["trace"]:
        instance = replay.query_instance(record, step)
        state, ids = instance.selection_input, instance.metadata["model_token_ids"]
        assert [None if t is None else ids[t] for t in state.canvas] == step["canvas_before"]
        assert [(p.position, ids[p.token_id], p.weight) for p in state.proposals] == [
            tuple(p) for p in step["proposals"]
        ]
        assert len(state.canvas) == 64
        for position, row in enumerate(state.support.rows):
            expected = {path[position] for path in record["support"]["paths"]}
            # The original production_input adds required EOS to every free row.
            # Replay invokes that same support contract before lossless ID mapping.
            expected.add(126081)
            if step["canvas_before"][position] is not None:
                expected = {step["canvas_before"][position]}
            assert {ids[t] for t in row} == expected


def test_changed_source_is_rejected_before_replay(tmp_path):
    (tmp_path / "capture.json").write_text("modified")
    with pytest.raises(ValueError, match="Source hash mismatch"):
        replay.validate_sources({"input_sha256": {"capture.json": "0" * 64}}, tmp_path)


def test_budgeted_profiling_preserves_the_entire_mathematical_result():
    state, _ = read_budget_proof(
        replay.read_json(replay.ROOT / "docs/artifacts/math/m27-budget-proof.json")
    )
    original = budgeted_commit_frontier(state, 2)
    profiler = ComponentProfiler(enabled=True)
    measured = budgeted_commit_frontier(state, 2, profiler=profiler)
    assert original == measured
    event = profiler.snapshot()
    assert event is not None
    assert event.component_seconds["parser"] > 0
    assert event.component_seconds["backtracking"] > 0
    assert event.component_seconds["validation"] > 0
    assert event.measured_component_seconds <= event.wall_span_seconds


def test_real_replay_baselines_recover_expected_budget_separation():
    state, _ = read_budget_proof(
        replay.read_json(replay.ROOT / "docs/artifacts/math/m27-budget-proof.json")
    )
    config = {"max_budget": 2, "finite_validation_timeout_seconds": 10}
    filtered = replay.baseline(state, "unbudgeted_then_cap", config)["frontier"]
    preselected = replay.baseline(state, "confidence_preselection", config)["frontier"]
    assert Fraction(*filtered[0]["objective_value"]) == Fraction(1, 2)
    assert Fraction(*preselected[0]["objective_value"]) == Fraction(7, 8)
    rows = [
        {
            "instance_id": "a",
            "family": "example",
            "reward_profile": "all_primary",
            "method": "budgeted_rational",
            "status": "complete",
            "worker_seconds": 0.1,
            "frontier": [{"budget": 1, "status": "optimal", "objective_value": [7, 8]}],
        },
        {
            "instance_id": "a",
            "family": "example",
            "reward_profile": "all_primary",
            "method": "unbudgeted_then_cap",
            "status": "complete",
            "worker_seconds": 0.1,
            "frontier": [filtered[0]],
        },
    ]
    group = next(g for g in replay.summary(rows)["groups"] if g["method"] == "unbudgeted_then_cap")
    assert group["strict_gaps"] == 1 and group["max_gap"] == [3, 8]


def test_timeout_is_not_a_zero_score_or_infeasibility(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("worker", 1)

    monkeypatch.setattr(replay.subprocess, "run", timeout)
    result = replay.bounded_job({}, 1)
    assert result["status"] == "timeout"
    assert result["frontier"] == []
    assert "objective_value" not in result
    assert json.dumps(result)


def test_summary_counts_unresolved_jobs_without_pairing_them():
    rows = [
        {
            "instance_id": "a",
            "family": "test",
            "reward_profile": "ordinary_primary",
            "method": "budgeted_rational",
            "status": "timeout",
            "frontier": [],
        },
        {
            "instance_id": "a",
            "family": "test",
            "reward_profile": "ordinary_primary",
            "method": "epic_regular_cover_then_cap",
            "status": "complete",
            "worker_seconds": 1,
            "frontier": [
                {"budget": 1, "status": "infeasible_batch_on_support", "objective_value": None}
            ],
        },
    ]
    groups = replay.summary(rows)["groups"]
    assert all(g["certified_paired_budget_cases"] == 0 for g in groups)
    assert any(g["execution_statuses"] == {"timeout": 1} for g in groups)
