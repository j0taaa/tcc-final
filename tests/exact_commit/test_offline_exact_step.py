"""Complete exact-step integration regressions over fixed CPU-side inputs.

These tests intentionally use only immutable Python sequences, the reference
backend, and a tiny byte vocabulary. They require no network, model weights,
GPU, tensor framework, or production binding.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

import pytest

from mwpc_exact import (
    AdaptiveSupportConfig,
    CommitGuarantee,
    CommitSource,
    ComponentProfiler,
    CompositionalByteLevelAdapter,
    DecoderStepResult,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    ExactCommitResult,
    FailureFallbackCallable,
    FailureFallbackRequest,
    FailureFallbackStrategy,
    FallbackSelection,
    FallbackToken,
    ProfilingComponent,
    ProfilingEvent,
    ProposalWeightMode,
    ScheduleProposalBatch,
    SolveStatus,
    SupportKind,
    apply_exact_commit_result,
    build_schedule_proposals,
    solve_exact_commit_adaptive,
)
from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)

ADAPTER = CompositionalByteLevelAdapter((b"a", b"b", b"c", None, None))
EOS_POLICY = EOSPolicy(
    EOSMode.REQUIRED,
    termination_token_ids=(3,),
    pad_token_id=4,
)


@dataclass(frozen=True, slots=True)
class _OfflineStepRun:
    proposal_batch: ScheduleProposalBatch
    solver_result: ExactCommitResult
    decoder_step: DecoderStepResult
    profile_event: ProfilingEvent

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_batch": self.proposal_batch.to_dict(),
            "solver_result": self.solver_result.to_dict(),
            "decoder_step": self.decoder_step.to_dict(),
            "profile_event": self.profile_event.to_dict(),
        }


def _exact_word_grammar(word: bytes) -> CnfGrammar:
    if len(word) == 1:
        return CnfGrammar(
            nonterminals=(Nonterminal(0, "S"),),
            terminals=(Terminal(0, word[0]),),
            start_nonterminal_id=0,
            terminal_productions=(TerminalProduction(0, 0, 0),),
        )
    if len(word) != 2:
        raise ValueError("offline fixture helper supports one- or two-byte words")
    terminals = tuple(
        Terminal(symbol_id, label) for symbol_id, label in enumerate(sorted(set(word)))
    )
    terminal_id = {terminal.label: terminal.symbol_id for terminal in terminals}
    return CnfGrammar(
        nonterminals=(
            Nonterminal(0, "S"),
            Nonterminal(1, "LEFT"),
            Nonterminal(2, "RIGHT"),
        ),
        terminals=terminals,
        start_nonterminal_id=0,
        terminal_productions=(
            TerminalProduction(0, 1, terminal_id[word[0]]),
            TerminalProduction(1, 2, terminal_id[word[1]]),
        ),
        binary_productions=(BinaryProduction(2, 0, 1, 2),),
    )


def _run_offline_step(
    grammar: CnfGrammar,
    *,
    canvas: tuple[int | None, ...],
    logits: tuple[tuple[float, ...], ...],
    predicted_token_ids: tuple[int, ...],
    confidence_values: tuple[float, ...],
    schedule_mask: tuple[bool, ...],
    schedule_budget: int,
    support_config: AdaptiveSupportConfig,
    witness_token_probabilities: tuple[float, ...] | None = None,
    failure_fallback_strategy: FailureFallbackStrategy | None = None,
    failure_fallback: FailureFallbackCallable | None = None,
) -> _OfflineStepRun:
    profiler = ComponentProfiler(enabled=True)
    proposal_batch = build_schedule_proposals(
        predicted_token_ids=predicted_token_ids,
        confidence_values=confidence_values,
        schedule_mask=schedule_mask,
        k_s=schedule_budget,
        weight_mode=ProposalWeightMode.CONFIDENCE,
        profiler=profiler,
    )
    solver_result = solve_exact_commit_adaptive(
        grammar,
        canvas=canvas,
        logits=logits,
        proposals=proposal_batch.proposals,
        tokenizer_adapter=ADAPTER,
        eos_policy=EOS_POLICY,
        config=support_config,
        backend=ExactBackend.PYTHON,
        pruning_description="T805 fixed offline CPU integration fixture",
        profiler=profiler,
    )
    decoder_step = apply_exact_commit_result(
        solver_result,
        canvas=canvas,
        proposals=proposal_batch.proposals,
        witness_token_probabilities=witness_token_probabilities,
        failure_fallback_strategy=failure_fallback_strategy,
        failure_fallback=failure_fallback,
        profiler=profiler,
    )
    profile_event = profiler.snapshot()
    if profile_event is None:
        raise AssertionError("enabled offline profiler omitted its event")
    return _OfflineStepRun(
        proposal_batch=proposal_batch,
        solver_result=solver_result,
        decoder_step=decoder_step,
        profile_event=profile_event,
    )


def _adaptive_diagnostics(result: ExactCommitResult) -> Mapping[str, object]:
    value = result.diagnostics.get("adaptive_support")
    if not isinstance(value, Mapping):
        raise AssertionError("adaptive exact result omitted its diagnostics")
    return value


def _assert_certified_optimum(run: _OfflineStepRun) -> None:
    result = run.solver_result
    assert result.status is SolveStatus.OPTIMAL
    assert result.exactness_scope.kind is SupportKind.TOP_K
    validation = result.diagnostics.get("certificate_validation")
    assert isinstance(validation, Mapping)
    assert validation["is_valid"] is True
    assert len(result.witness_token_ids) == len(run.decoder_step.input_canvas)
    assert result.witness_graph_edge_ids
    assert run.profile_event.accounted_total_seconds == pytest.approx(
        run.profile_event.wall_span_seconds
    )


def test_fully_compatible_batch_completes_fixed_canvas_with_required_eos_pad() -> None:
    run = _run_offline_step(
        _exact_word_grammar(b"ab"),
        canvas=(0, None, None, None),
        logits=(
            (10.0, 0.0, -1.0, -2.0, -3.0),
            (0.0, 10.0, -1.0, -2.0, -3.0),
            (0.0, -1.0, -2.0, 10.0, 9.0),
            (0.0, -1.0, -2.0, 9.0, 10.0),
        ),
        predicted_token_ids=(0, 1, 3, 4),
        confidence_values=(0.0, 0.9, 0.8, 0.7),
        schedule_mask=(False, True, True, True),
        schedule_budget=3,
        support_config=AdaptiveSupportConfig(initial_k=1, k_max=1),
    )

    _assert_certified_optimum(run)
    assert run.solver_result.objective_value == pytest.approx(2.4)
    assert run.solver_result.selected_proposal_ids == (0, 1, 2)
    assert run.solver_result.witness_token_ids == (0, 1, 3, 4)
    assert run.solver_result.witness_terminal_labels == (ord("a"), ord("b"))
    assert run.solver_result.witness_eos_position == 2
    assert run.solver_result.witness_content_endpoint_slot == 2
    assert run.decoder_step.updated_canvas == (0, 1, 3, 4)
    assert run.decoder_step.input_canvas[0] == run.decoder_step.updated_canvas[0] == 0
    assert run.decoder_step.commit_source is CommitSource.EXACT_PROPOSALS
    assert run.decoder_step.commit_guarantee is CommitGuarantee.EXACT_MWPC_SELECTION
    assert tuple(commit.position for commit in run.decoder_step.commits) == (1, 2, 3)
    assert run.profile_event.counters["commit_count"] == 3
    assert all(
        run.profile_event.component_invocations[component.value] >= 1
        for component in ProfilingComponent
    )
    json.dumps(run.to_dict())


def test_grammar_selects_a_strict_optimal_subset_of_the_frozen_batch() -> None:
    run = _run_offline_step(
        _exact_word_grammar(b"ab"),
        canvas=(None, None, None, None),
        logits=(
            (10.0, 9.0, 0.0, -1.0, -2.0),
            (0.0, 9.0, 10.0, -1.0, -2.0),
            (0.0, -1.0, -2.0, 10.0, 9.0),
            (0.0, -1.0, -2.0, 9.0, 10.0),
        ),
        predicted_token_ids=(0, 2, 3, 4),
        confidence_values=(1.0, 0.9, 0.8, 0.7),
        schedule_mask=(True, True, True, True),
        schedule_budget=4,
        support_config=AdaptiveSupportConfig(initial_k=2, k_max=2),
    )

    _assert_certified_optimum(run)
    assert run.solver_result.witness_token_ids == (0, 1, 3, 4)
    assert run.solver_result.selected_proposal_ids == (0, 2, 3)
    assert run.solver_result.objective_value == pytest.approx(2.5)
    assert set(run.solver_result.selected_proposal_ids) < {
        proposal.proposal_id for proposal in run.proposal_batch.proposals
    }
    assert run.decoder_step.updated_canvas == (0, None, 3, 4)
    assert tuple(commit.position for commit in run.decoder_step.commits) == (0, 2, 3)
    assert run.decoder_step.diagnostics["witness_compatible_after_commit"] is True


def test_empty_matched_set_commits_one_unmatched_witness_token_for_progress() -> None:
    run = _run_offline_step(
        _exact_word_grammar(b"ab"),
        canvas=(0, None, None, None),
        logits=(
            (10.0, 0.0, -1.0, -2.0, -3.0),
            (0.0, 9.0, 10.0, -1.0, -2.0),
            (0.0, -1.0, -2.0, 10.0, 9.0),
            (0.0, -1.0, -2.0, 9.0, 10.0),
        ),
        predicted_token_ids=(0, 2, 3, 4),
        confidence_values=(0.0, 0.9, 0.0, 0.0),
        schedule_mask=(False, True, False, False),
        schedule_budget=1,
        support_config=AdaptiveSupportConfig(initial_k=2, k_max=2),
        witness_token_probabilities=(0.1, 0.9, 0.2, 0.3),
    )

    _assert_certified_optimum(run)
    assert run.solver_result.objective_value == 0.0
    assert run.solver_result.selected_proposal_ids == ()
    assert run.solver_result.witness_token_ids == (0, 1, 3, 4)
    assert run.decoder_step.updated_canvas == (0, 1, None, None)
    assert run.decoder_step.commit_source is CommitSource.WITNESS_PROGRESS
    assert run.decoder_step.commit_guarantee is CommitGuarantee.EXACT_WITNESS_PROGRESS
    assert len(run.decoder_step.commits) == 1
    commit = run.decoder_step.commits[0]
    assert (commit.position, commit.token_id) == (1, 1)
    assert commit.selected_proposal_ids == commit.matching_proposal_ids == ()
    assert run.decoder_step.diagnostics["fallback_class"] == "witness_progress"
    assert run.decoder_step.diagnostics["original_solver_status"] == "optimal"


def test_infeasible_top_one_expands_once_then_returns_a_certified_optimum() -> None:
    run = _run_offline_step(
        _exact_word_grammar(b"b"),
        canvas=(None, None, None),
        logits=(
            (10.0, 9.0, 0.0, -1.0, -2.0),
            (0.0, -1.0, -2.0, 10.0, 9.0),
            (0.0, -1.0, -2.0, 9.0, 10.0),
        ),
        predicted_token_ids=(0, 3, 4),
        confidence_values=(0.9, 0.8, 0.7),
        schedule_mask=(True, True, True),
        schedule_budget=3,
        support_config=AdaptiveSupportConfig(initial_k=1, k_max=2),
    )

    _assert_certified_optimum(run)
    assert run.solver_result.witness_token_ids == (1, 3, 4)
    assert run.solver_result.selected_proposal_ids == (1, 2)
    assert run.solver_result.objective_value == pytest.approx(1.5)
    assert run.solver_result.exactness_scope.adaptive_expansions == (2,)
    adaptive = _adaptive_diagnostics(run.solver_result)
    assert adaptive["attempted_k"] == (1, 2)
    assert adaptive["support_superset_verified"] is True
    assert run.profile_event.counters["support_attempt_count"] == 2
    assert run.profile_event.counters["support_expansion_count"] == 1
    assert run.decoder_step.diagnostics["support_expansion_attempted_k"] == (1, 2)


def test_total_timeout_preserves_status_and_uses_explicit_serial_fallback() -> None:
    requests: list[FailureFallbackRequest] = []

    def serial_fallback(request: FailureFallbackRequest) -> FallbackSelection:
        requests.append(request)
        assert request.strategy is FailureFallbackStrategy.SERIAL
        assert request.solver_result.status is SolveStatus.TIMEOUT
        return FallbackSelection(
            tokens=(FallbackToken(position=0, token_id=1),),
            diagnostics={"fixture": "offline_serial_progress"},
        )

    run = _run_offline_step(
        _exact_word_grammar(b"b"),
        canvas=(None, None, None),
        logits=(
            (10.0, 9.0, 0.0, -1.0, -2.0),
            (0.0, -1.0, -2.0, 10.0, 9.0),
            (0.0, -1.0, -2.0, 9.0, 10.0),
        ),
        predicted_token_ids=(0, 3, 4),
        confidence_values=(0.9, 0.8, 0.7),
        schedule_mask=(True, True, True),
        schedule_budget=3,
        support_config=AdaptiveSupportConfig(
            initial_k=1,
            k_max=2,
            total_timeout_seconds=0.0,
        ),
        failure_fallback_strategy=FailureFallbackStrategy.SERIAL,
        failure_fallback=serial_fallback,
    )

    assert len(requests) == 1
    assert run.solver_result.status is SolveStatus.TIMEOUT
    assert run.solver_result.objective_value is None
    assert run.solver_result.selected_proposal_ids == ()
    assert run.solver_result.witness_token_ids == ()
    adaptive = _adaptive_diagnostics(run.solver_result)
    assert adaptive["attempted_k"] == (1,)
    assert adaptive["resource_limit_prevented_expansion"] is True
    assert adaptive["stopped_reason"] == "total_timeout_before_next_expansion"
    assert run.decoder_step.solver_result.status is SolveStatus.TIMEOUT
    assert run.decoder_step.updated_canvas == (1, None, None)
    assert run.decoder_step.commit_source is CommitSource.SERIAL_FALLBACK
    assert run.decoder_step.commit_guarantee is (
        CommitGuarantee.BASELINE_FALLBACK_NO_EXACT_GUARANTEE
    )
    assert run.decoder_step.fallback_strategy is FailureFallbackStrategy.SERIAL
    assert run.decoder_step.selected_proposal_ids == ()
    assert run.decoder_step.matching_proposal_ids == ()
    assert run.decoder_step.diagnostics["failure_fallback_attempted"] is True
    assert run.decoder_step.diagnostics["failure_fallback_succeeded"] is True
    assert run.profile_event.counters["support_expansion_count"] == 0
    assert run.profile_event.counters["commit_count"] == 1
    json.dumps(run.to_dict())
