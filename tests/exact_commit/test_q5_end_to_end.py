from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from mwpc_exact.experiments import ExperimentKind, load_experiment_config
from mwpc_exact.types import SolveStatus
from mwpc_research.q5_end_to_end import (
    Q5_STRATEGIES,
    Q5ExecutionStatus,
    Q5ExperimentResult,
    Q5MethodRecord,
    upstream_selection_batch_size,
    write_q5_artifacts,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPOSITORY_ROOT / "configs/experiments/q5_end_to_end_v1.toml"


def _record(
    strategy: str,
    *,
    fingerprint: str = "paired-input",
    elapsed_seconds: float = 1.0,
) -> Q5MethodRecord:
    exact = strategy == "exact"
    return Q5MethodRecord(
        strategy=strategy,
        execution_status=Q5ExecutionStatus.COMPLETE,
        comparison_fingerprint=fingerprint,
        seed=904,
        repetition=0,
        generated_token_ids=(15, 126348, 126081, 126081),
        decoded_with_specials="0<|eot_id|><|endoftext|><|endoftext|>",
        syntactic_valid=True,
        functional_success=True,
        checker={
            "independent_grammar_valid": True,
            "exact_target_match": True,
            "content_bytes_hex": "30",
        },
        configured_diffusion_steps=1,
        model_forward_count=1,
        commit_batch_sizes=(4,) if exact else (1, 1, 1),
        physical_update_batch_sizes=(4,) if exact else (1, 1, 2),
        fallback_count=0,
        support_expansion_count=0 if exact else None,
        empty_optimal_batch_count=0 if exact else None,
        solver_backend="rust" if exact else None,
        solver_status=SolveStatus.OPTIMAL if exact else None,
        exactness_scope={"claim": "exact_on_support", "kind": "top_k", "top_k": 1}
        if exact
        else None,
        objective_value=3.0 if exact else None,
        certificate_valid=True if exact else None,
        certificate={
            "witness_token_ids": [15, 126348, 126081, 126081],
            "witness_terminal_labels": [48],
            "witness_graph_edge_ids": [0, 1, 2, 3],
            "selected_proposal_ids": [0, 1, 2, 3],
            "objective_value": 3.0,
        }
        if exact
        else None,
        elapsed_seconds=elapsed_seconds,
        process_rss_before_bytes=100,
        process_rss_after_bytes=110,
        process_high_water_rss_bytes=120,
        cuda_peak_allocated_bytes=200,
        cuda_peak_reserved_bytes=250,
        diagnostics={"implementation": strategy},
    )


def _result(
    *,
    times: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
) -> Q5ExperimentResult:
    return Q5ExperimentResult(
        tuple(
            _record(strategy, elapsed_seconds=elapsed)
            for strategy, elapsed in zip(Q5_STRATEGIES, times, strict=True)
        ),
        {"run_id": "test", "benchmark_claim": False},
    )


def test_q5_config_freezes_live_task_model_prompt_schedule_and_seed() -> None:
    config = load_experiment_config(CONFIG_PATH)
    source_path = REPOSITORY_ROOT / config.grammar_source

    assert config.question is ExperimentKind.END_TO_END
    assert config.publication_mode is False
    assert config.seeds == (904,)
    assert config.repetitions == 1
    assert config.model_id == "GSAI-ML/LLaDA-8B-Instruct"
    assert config.model_revision == "08b83a6feb34df1a6011b80c3c00c7563e963b07"
    assert config.tokenizer_revision == config.model_revision
    assert config.parameters["strategies"] == Q5_STRATEGIES
    assert config.parameters["task_ids"] == ("t904_literal_zero",)
    assert config.parameters["prompt_instruction"] == (
        "Reply with exactly the single digit 0 and nothing else."
    )
    assert config.parameters["generation_length"] == 4
    assert config.parameters["block_length"] == 4
    assert config.parameters["steps"] == 1
    assert config.parameters["exact_backend"] == "rust"
    assert config.parameters["warmup_runs"] == 0
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == (
        config.parameters["live_profile_source_sha256"]
    )


def test_all_four_methods_must_share_one_comparison_fingerprint() -> None:
    records = [_record(strategy) for strategy in Q5_STRATEGIES]
    records[-1] = _record("exact", fingerprint="different-input")

    with pytest.raises(ValueError, match="one frozen comparison input"):
        Q5ExperimentResult(tuple(records), {})


def test_optimal_exact_row_requires_a_reconstructible_validated_certificate() -> None:
    exact = _record("exact")

    with pytest.raises(ValueError, match="validated certificate"):
        replace(exact, certificate_valid=False)
    with pytest.raises(ValueError, match="reconstructible"):
        replace(exact, certificate={"witness_token_ids": [15]})


def test_summary_computes_batch_mean_and_diagnostic_overhead_without_dividing_by_zero() -> None:
    result = _result(times=(2.0, 4.0, 0.0, 8.0))
    summary = result.summary_dict()

    assert summary["paired_input_verified"] is True
    assert summary["benchmark_claim"] is False
    assert summary["all_required_methods_passed"] is True
    assert summary["required_contract_failure_count"] == 0
    assert summary["diagnostic_exact_runtime_ratio"] == {
        "unconstrained": 4.0,
        "serial": 2.0,
        "epic": None,
    }
    methods = summary["methods"]
    assert isinstance(methods, dict)
    assert methods["serial"]["average_commit_batch_size"] == 1.0
    assert methods["exact"]["average_commit_batch_size"] == 4.0


def test_upstream_eos_suffix_fill_is_not_counted_as_a_selected_batch() -> None:
    assert (
        upstream_selection_batch_size(physical_update_count=3, regular_cover_selected_count=0)
        == 1
    )
    assert (
        upstream_selection_batch_size(physical_update_count=3, regular_cover_selected_count=3)
        == 3
    )
    with pytest.raises(ValueError, match="cannot exceed"):
        upstream_selection_batch_size(physical_update_count=2, regular_cover_selected_count=3)


def test_timeout_remains_distinct_from_infeasible_on_support() -> None:
    records = [_record(strategy) for strategy in Q5_STRATEGIES]
    records[-1] = Q5MethodRecord(
        strategy="exact",
        execution_status=Q5ExecutionStatus.TIMEOUT,
        comparison_fingerprint="paired-input",
        seed=904,
        repetition=0,
        generated_token_ids=(),
        decoded_with_specials="",
        syntactic_valid=None,
        functional_success=None,
        checker={"error_type": "TimeoutError"},
        configured_diffusion_steps=1,
        model_forward_count=1,
        commit_batch_sizes=(),
        physical_update_batch_sizes=(),
        fallback_count=0,
        support_expansion_count=None,
        empty_optimal_batch_count=None,
        solver_backend="rust",
        solver_status=SolveStatus.TIMEOUT,
        exactness_scope=None,
        objective_value=None,
        certificate_valid=None,
        certificate=None,
        elapsed_seconds=30.0,
        process_rss_before_bytes=100,
        process_rss_after_bytes=100,
        process_high_water_rss_bytes=120,
        cuda_peak_allocated_bytes=200,
        cuda_peak_reserved_bytes=250,
    )
    summary = Q5ExperimentResult(tuple(records), {}).summary_dict()

    assert summary["execution_status_counts"]["timeout"] == 1
    assert summary["exact_solver_status_counts"] == {"timeout": 1}
    assert "infeasible_on_support" not in summary["exact_solver_status_counts"]


def test_raw_rows_save_generated_outputs_checkers_and_exact_certificate(tmp_path: Path) -> None:
    raw_path, summary_path = write_q5_artifacts(_result(), tmp_path)
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]

    assert len(rows) == 4
    assert rows[0]["generated_output"]["token_ids"]
    assert rows[0]["checker"]["independent_grammar_valid"] is True
    assert rows[-1]["exact_solver"]["status"] == "optimal"
    assert rows[-1]["exact_solver"]["certificate_valid"] is True
    assert json.loads(summary_path.read_text(encoding="utf-8"))["measurement_count"] == 4
    with pytest.raises(FileExistsError):
        write_q5_artifacts(_result(), tmp_path)
