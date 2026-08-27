from __future__ import annotations

import json
from pathlib import Path

import pytest

from mwpc_exact import (
    BenchmarkInstance,
    ExactBackend,
    ProposalWeightMode,
    SelectionResult,
    SelectionStatus,
    SelectorKind,
    select_brute_force,
    select_exact_mwpc,
    select_greedy_exact_feasibility,
)
from mwpc_exact.experiments import ExperimentKind, load_experiment_config
from mwpc_research.q2_gap import (
    Q2_CASE_IDS,
    Q2_COMPONENT_SELECTORS,
    configured_q2_instances,
    run_q2_gap_instances,
    write_q2_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q2_heuristic_gap_v1.toml"
WEIGHT_MODES = (ProposalWeightMode.UNIT, ProposalWeightMode.CONFIDENCE)


def _fake_replay(instance: BenchmarkInstance):
    selection_input = instance.selection_input
    serial = select_greedy_exact_feasibility(selection_input, backend=ExactBackend.PYTHON)
    exact = select_exact_mwpc(selection_input, backend=ExactBackend.PYTHON)
    brute_force = select_brute_force(selection_input, max_completions=64)
    epic = SelectionResult(
        selector=SelectorKind.EPIC_REGULAR_COVER,
        status=SelectionStatus.HEURISTIC,
        exactness_scope=selection_input.support.exactness_scope,
        runtime_seconds=0.0,
        score=0.0,
        diagnostics={"implementation": "test_empty_epic_selection"},
    )
    return {
        SelectorKind.GREEDY_EXACT_FEASIBILITY: serial,
        SelectorKind.EPIC_REGULAR_COVER: epic,
        SelectorKind.EXACT_MWPC: exact,
        SelectorKind.BRUTE_FORCE: brute_force,
    }


def test_q2_config_freezes_cases_component_selectors_and_weight_modes() -> None:
    config = load_experiment_config(CONFIG_PATH)

    assert config.question is ExperimentKind.HEURISTIC_GAP
    assert config.publication_mode is False
    assert config.exactness_scope == "exact_on_support"
    assert config.parameters["case_ids"] == Q2_CASE_IDS
    assert config.parameters["selectors"] == Q2_COMPONENT_SELECTORS
    assert config.parameters["weight_modes"] == ("unit", "confidence")
    assert config.parameters["exact_backend"] == "rust"
    assert config.parameters["epic_exact_shrink"] is True


def test_weight_modes_share_state_support_candidates_and_confidences() -> None:
    instances = configured_q2_instances(seed_start=1102, weight_modes=WEIGHT_MODES)

    assert len(instances) == 6
    assert {item.common_instance_id for item in instances} == set(Q2_CASE_IDS)
    for common_id in Q2_CASE_IDS:
        unit, confidence = tuple(item for item in instances if item.common_instance_id == common_id)
        assert unit.weight_mode is ProposalWeightMode.UNIT
        assert confidence.weight_mode is ProposalWeightMode.CONFIDENCE
        assert unit.common_state_sha256 == confidence.common_state_sha256
        assert (
            unit.benchmark_instance.selection_input.support.fingerprint
            == confidence.benchmark_instance.selection_input.support.fingerprint
        )
        unit_proposals = unit.benchmark_instance.selection_input.proposals
        confidence_proposals = confidence.benchmark_instance.selection_input.proposals
        assert [(item.position, item.token_id) for item in unit_proposals] == [
            (item.position, item.token_id) for item in confidence_proposals
        ]
        assert [item.model_confidence for item in unit_proposals] == [
            item.model_confidence for item in confidence_proposals
        ]
        assert {item.weight for item in unit_proposals} == {1.0}
        assert [item.weight for item in confidence_proposals] == [
            item.model_confidence for item in confidence_proposals
        ]


def test_gap_rows_and_equality_rates_are_computed_from_selector_results() -> None:
    instances = configured_q2_instances(seed_start=1102, weight_modes=WEIGHT_MODES)
    result = run_q2_gap_instances(
        instances,
        replay=_fake_replay,
        run_metadata={"test": "computed-gaps"},
    )

    assert result.failed_cases == 0
    records = {(item.common_instance_id, item.weight_mode.value): item for item in result.records}
    divergence = records[("adversarial-weight-mode-divergence", "confidence")]
    assert divergence.selector_results["exact_mwpc"]["score"] == 0.9
    assert divergence.selector_results["greedy_exact_feasibility"]["score"] == 0.9
    assert divergence.comparisons["greedy_exact_feasibility"]["score_equal"] is True
    assert divergence.comparisons["epic_regular_cover"]["absolute_gap"] == 0.9

    summary = result.summary_dict()
    unit_serial = summary["weight_modes"]["unit"]["selectors"]["greedy_exact_feasibility"]
    confidence_serial = summary["weight_modes"]["confidence"]["selectors"][
        "greedy_exact_feasibility"
    ]
    assert unit_serial["equality_count"] == 1
    assert unit_serial["equality_rate"] == pytest.approx(1 / 3)
    assert confidence_serial["equality_count"] == 2
    assert confidence_serial["equality_rate"] == pytest.approx(2 / 3)


def test_raw_rows_reference_common_instance_and_support_scope(tmp_path: Path) -> None:
    instances = configured_q2_instances(seed_start=1102, weight_modes=WEIGHT_MODES)[:2]
    result = run_q2_gap_instances(
        instances,
        replay=_fake_replay,
        run_metadata={"config_sha256": "test-hash"},
    )

    raw_directory = tmp_path / "raw"
    processed_directory = tmp_path / "processed"
    raw_path, summary_path = write_q2_artifacts(
        result,
        raw_directory,
        processed_directory,
    )
    assert raw_path.parent == raw_directory
    assert summary_path.parent == processed_directory
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert len(rows) == summary["case_count"] == 2
    for row in rows:
        assert row["common_instance_id"]
        assert len(row["common_state_sha256"]) == 64
        assert len(row["weighted_instance_sha256"]) == 64
        assert row["support_specification"]["kind"] == "explicit"
        assert set(row["selector_results"]) == set(Q2_COMPONENT_SELECTORS)
        assert set(row["comparisons"]) == {
            "greedy_exact_feasibility",
            "epic_regular_cover",
        }
        assert row["selector_results"]["greedy_exact_feasibility"]["selected_subset_feasible"]
        assert row["selector_results"]["epic_regular_cover"]["selected_subset_feasible"]
    with pytest.raises(FileExistsError):
        write_q2_artifacts(result, raw_directory, processed_directory)


def test_replay_failure_emits_deterministic_benchmark_fixture(tmp_path: Path) -> None:
    instance = configured_q2_instances(
        seed_start=1102,
        weight_modes=(ProposalWeightMode.UNIT,),
    )[0]

    def failing_replay(_: BenchmarkInstance):
        raise AssertionError("injected Q2 selector failure")

    result = run_q2_gap_instances(
        (instance,),
        replay=failing_replay,
        run_metadata={"test": "failure"},
        failure_directory=tmp_path,
    )

    assert result.failed_cases == 1
    record = result.records[0]
    assert record.error_type == "AssertionError"
    assert record.fixture_file == "all-compatible-unit.json"
    fixture = BenchmarkInstance.read_json(tmp_path / record.fixture_file)
    assert fixture.fingerprint == instance.benchmark_instance.fingerprint
    assert (tmp_path / "all-compatible-unit.failure.json").is_file()


def test_exact_oracle_disagreement_fails_closed() -> None:
    instance = configured_q2_instances(
        seed_start=1102,
        weight_modes=(ProposalWeightMode.UNIT,),
    )[0]

    def mismatched_replay(benchmark: BenchmarkInstance):
        results = dict(_fake_replay(benchmark))
        oracle = results[SelectorKind.BRUTE_FORCE]
        results[SelectorKind.BRUTE_FORCE] = SelectionResult(
            selector=SelectorKind.BRUTE_FORCE,
            status=SelectionStatus.OPTIMAL,
            exactness_scope=oracle.exactness_scope,
            runtime_seconds=oracle.runtime_seconds,
            selected_proposal_ids=(0,),
            score=1.0,
            witness_token_ids=oracle.witness_token_ids,
        )
        return results

    result = run_q2_gap_instances(
        (instance,),
        replay=mismatched_replay,
        run_metadata={"test": "oracle-disagreement"},
    )

    assert result.failed_cases == 1
    assert "disagrees with brute force" in (result.records[0].error_message or "")


def test_infeasible_heuristic_selection_fails_closed() -> None:
    instance = configured_q2_instances(
        seed_start=1102,
        weight_modes=(ProposalWeightMode.UNIT,),
    )[1]

    def invalid_epic_replay(benchmark: BenchmarkInstance):
        results = dict(_fake_replay(benchmark))
        scope = benchmark.selection_input.support.exactness_scope
        results[SelectorKind.EPIC_REGULAR_COVER] = SelectionResult(
            selector=SelectorKind.EPIC_REGULAR_COVER,
            status=SelectionStatus.HEURISTIC,
            exactness_scope=scope,
            runtime_seconds=0.0,
            selected_proposal_ids=(0, 1, 2),
            score=3.0,
        )
        return results

    result = run_q2_gap_instances(
        (instance,),
        replay=invalid_epic_replay,
        run_metadata={"test": "infeasible-heuristic"},
    )

    assert result.failed_cases == 1
    assert "no valid completion" in (result.records[0].error_message or "")
