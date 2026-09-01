from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = REPOSITORY_ROOT / "docs/evidence/t1253-q5-publication-summary.json"
RAW_PATH = (
    REPOSITORY_ROOT
    / "docs/artifacts/raw/m125_publication_results_v1/q5-end-to-end-rows.jsonl"
)
TABLE_PATH = (
    REPOSITORY_ROOT
    / "paper/generated/t1203_final_results_v1/end-to-end-comparison-table.tex"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_t1253_summary_pins_complete_parallel_epic_campaign() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert (
        _sha256(SUMMARY_PATH)
        == "700aa99e870c06704bbd98a4bd481bb2ee1c73c3dbff7843f3cca16a2b7f5ec1"
    )
    assert summary["artifact_kind"] == "mwpc_q5_publication_campaign_summary"
    assert summary["producing_commit"] == "b4a8ffde4cc2aabc61844a955ce98933ef03dfb9"
    assert summary["tasks"] == ["json_x_zero", "fenced_add_dsl"]
    assert summary["seeds"] == [125301, 125302, 125303]
    assert summary["measured_row_count"] == 240
    assert summary["exact_optimizer_step_count"] == 60
    assert summary["contract_failure_count"] == 0
    assert summary["all_constrained_outputs_independently_valid"] is True
    assert summary["all_exact_optimizer_certificates_independently_valid"] is True
    assert summary["epic_parallel_commit_observed_in_every_task_seed"] is True
    assert len(summary["runs"]) == 6
    assert all(run["epic_regular_cover_selector_calls"] > 0 for run in summary["runs"])
    assert all(run["epic_max_batch_size"] == 2 for run in summary["runs"])
    assert all(
        set(run["fallback_count_by_strategy"])
        == {"unconstrained", "serial", "epic", "exact"}
        for run in summary["runs"]
    )
    assert all(run["fallback_count_by_strategy"]["epic"] > 0 for run in summary["runs"])
    assert all(run["fallback_count_by_strategy"]["exact"] == 0 for run in summary["runs"])
    assert summary["pinned_raw_sha256"] == _sha256(RAW_PATH)


def test_t1253_pinned_rows_preserve_strategies_outputs_and_exact_certificates() -> None:
    rows = [json.loads(line) for line in RAW_PATH.read_text(encoding="utf-8").splitlines()]

    assert len(rows) == 240
    assert Counter(row["strategy"] for row in rows) == {
        "unconstrained": 60,
        "serial": 60,
        "epic": 60,
        "exact": 60,
    }
    assert all(row["execution_status"] == "complete" for row in rows)
    constrained = [row for row in rows if row["strategy"] != "unconstrained"]
    assert all(row["syntactic_valid"] is True for row in constrained)
    assert all(row["functional_success"] is True for row in constrained)

    epic = [row for row in rows if row["strategy"] == "epic"]
    assert all(row["diagnostics"]["regular_cover_selector_calls"] > 0 for row in epic)
    assert all(max(row["diagnostics"]["regular_cover_batch_sizes"]) == 2 for row in epic)

    exact = [row for row in rows if row["strategy"] == "exact"]
    assert all(row["exact_solver"]["status"] == "optimal" for row in exact)
    assert all(row["exact_solver"]["certificate_valid"] is True for row in exact)
    assert all(
        row["exact_solver"]["exactness_scope"]["claim"] == "exact_on_support"
        for row in exact
    )
    for row in exact:
        for outcome in row["diagnostics"]["optimizer_outcomes"]:
            solver = outcome["decoder_step"]["solver_result"]
            validation = solver["diagnostics"]["certificate_validation"]
            assert validation["is_valid"] is True
            assert solver["objective_value"] == validation["recomputed_objective"]
            assert sorted(solver["selected_proposal_ids"]) == sorted(
                validation["recomputed_selected_proposal_ids"]
            )


def test_t1253_keeps_the_old_single_token_epic_row_explicitly_diagnostic() -> None:
    table = TABLE_PATH.read_text(encoding="utf-8")

    assert "EPIC-enabled (serial fallback)" in table
    assert "EPIC-enabled decoder with serial fallback" in table
