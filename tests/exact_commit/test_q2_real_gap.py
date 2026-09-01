from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from mwpc_exact import CompositionalByteLevelAdapter
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_research.q2_real_gap import (
    build_real_snapshot_instance,
    replay_real_snapshot,
    summarize_real_rows,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _literal_ab_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(
            Nonterminal(0, "S"),
            Nonterminal(1, "A"),
            Nonterminal(2, "B"),
        ),
        terminals=(Terminal(0, ord("a")), Terminal(1, ord("b"))),
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 1, 0),
            TerminalProduction(1, 2, 1),
        ),
        binary_productions=(BinaryProduction(2, 0, 1, 2),),
    )


def _instance():
    words = ("a", "b", "x")
    return build_real_snapshot_instance(
        instance_id="real-ab-state0",
        grammar=_literal_ab_grammar(),
        target_token_ids=(0, 1),
        canvas_token_ids=(None, None),
        predicted_token_ids=(0, 2),
        confidence_values=(0.9, 0.8),
        source_adapter=CompositionalByteLevelAdapter((b"a", b"b", b"x")),
        decode_actual_token=lambda token_id: words[token_id],
        metadata={"task_id": "ab", "seed": 7, "selected_state_rank": 0},
    )


def test_real_snapshot_compacts_actual_tokens_without_changing_common_support() -> None:
    instance = _instance()

    assert instance.selection_input.support.rows == ((0,), (1, 2))
    assert [proposal.position for proposal in instance.selection_input.proposals] == [0, 1]
    assert instance.metadata["support_interpretation"] == (
        "explicit_primary_proposal_plus_target_witness"
    )
    assert instance.metadata["snapshot_payload_sha256"]
    assert type(instance).from_dict(instance.to_dict()).fingerprint == instance.fingerprint


def test_real_snapshot_replays_three_selectors_and_validates_exact_certificate() -> None:
    row = replay_real_snapshot(_instance(), timeout_seconds=5.0, maximum_support_combinations=16)

    assert set(row["selector_results"]) == {
        "greedy_exact_feasibility",
        "epic_regular_cover",
        "exact_mwpc",
    }
    assert row["selector_results"]["exact_mwpc"]["status"] == "optimal"
    assert row["independent_exact_validation"] == {
        "certificate_valid": True,
        "grammar_witness_valid": True,
        "objective_value": 0.9,
        "recomputed_objective_value": 0.9,
        "selected_proposal_ids": [0],
        "recomputed_selected_proposal_ids": [0],
    }
    assert all(
        row["selector_results"][name]["selected_subset_feasible"] is True
        for name in ("greedy_exact_feasibility", "epic_regular_cover")
    )
    assert json.loads(json.dumps(row, allow_nan=False))["snapshot_id"] == "real-ab-state0"


def test_all_valid_support_gets_out_of_support_negative_alignment_sentinel() -> None:
    instance = build_real_snapshot_instance(
        instance_id="real-ab-all-valid",
        grammar=_literal_ab_grammar(),
        target_token_ids=(0, 1),
        canvas_token_ids=(None, None),
        predicted_token_ids=(0, 1),
        confidence_values=(0.9, 0.8),
        source_adapter=CompositionalByteLevelAdapter((b"a", b"b")),
        decode_actual_token=lambda token_id: ("a", "b")[token_id],
        metadata={"task_id": "ab", "seed": 7, "selected_state_rank": 0},
    )

    cases = instance.to_dict()["expected_metadata"]["semantic_alignment"]["cases"]
    assert cases == [
        {"token_ids": [0, 1], "expected_accepts": True},
        {"token_ids": [], "expected_accepts": False},
    ]
    assert instance.metadata["alignment_negative_sentinel_added"] is True
    row = replay_real_snapshot(
        instance, timeout_seconds=5.0, maximum_support_combinations=16
    )
    assert row["selector_results"]["exact_mwpc"]["status"] == "optimal"


def test_fixed_position_infinite_confidence_is_not_serialized_as_a_weight() -> None:
    instance = build_real_snapshot_instance(
        instance_id="real-ab-fixed-confidence",
        grammar=_literal_ab_grammar(),
        target_token_ids=(0, 1),
        canvas_token_ids=(0, None),
        predicted_token_ids=(0, 1),
        confidence_values=(float("inf"), 0.8),
        source_adapter=CompositionalByteLevelAdapter((b"a", b"b")),
        decode_actual_token=lambda token_id: ("a", "b")[token_id],
        metadata={"task_id": "ab", "seed": 7, "selected_state_rank": 0},
    )

    assert instance.metadata["snapshot_payload"]["confidence_values"] == (None, 0.8)
    assert "Infinity" not in instance.to_json(indent=None)


def test_real_summary_keeps_real_snapshot_denominators_and_zero_optima() -> None:
    row = replay_real_snapshot(_instance(), timeout_seconds=5.0, maximum_support_combinations=16)
    summary = summarize_real_rows((row,))

    assert summary["snapshot_count"] == 1
    assert summary["support_combination_counts"] == {"2": 1}
    assert summary["non_singleton_support_count"] == 1
    assert summary["empirical_interpretation"] == "bounded_real_state_gap_sample"
    assert summary["task_counts"] == {"ab": 1}
    assert summary["seed_counts"] == {"7": 1}
    assert summary["zero_optimum_count"] == 0
    assert summary["timeout_count"] == 0
    assert summary["all_snapshots_common_across_selectors"] is True


def test_real_replay_enforces_independent_validation_limit() -> None:
    with pytest.raises(ValueError, match="independent-validation limit"):
        replay_real_snapshot(_instance(), timeout_seconds=5.0, maximum_support_combinations=1)


def test_snapshot_collector_is_directly_executable() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts/exact_commit/collect_q2_real_snapshots.py"),
            "--help",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Capture compact real LLaDA selector states" in completed.stdout
