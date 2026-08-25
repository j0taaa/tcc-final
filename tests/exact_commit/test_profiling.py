from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from mwpc_exact import (
    ComponentProfiler,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    ProfilingComponent,
    ProposalWeightMode,
    SolveStatus,
    SupportKind,
    SupportPolicy,
    apply_exact_commit_result,
    build_per_position_support,
    build_schedule_proposals,
    solve_exact_commit,
)
from mwpc_exact.reference.grammar import (
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)


def _clock(values: tuple[float, ...]) -> Callable[[], float]:
    items = iter(values)
    return lambda: next(items)


def _one_byte_grammar(label: int) -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=(Terminal(0, label),),
        start_nonterminal_id=0,
        terminal_productions=(TerminalProduction(0, 0, 0),),
    )


def test_deterministic_breakdown_accounts_for_unmeasured_wall_overhead() -> None:
    profiler = ComponentProfiler(enabled=True, clock=_clock((0.0, 1.0, 1.5, 3.5)))

    with profiler.measure(ProfilingComponent.PROPOSAL_POLICY):
        pass
    with profiler.measure(ProfilingComponent.SUPPORT_CONSTRUCTION):
        pass
    profiler.set_counter("proposal_count", 3)
    profiler.set_support_row_sizes((2, 4))
    profiler.set_counter("support_slot_count", 2)
    profiler.set_counter("support_alternative_count", 6)
    profiler.set_counter("support_max_row_size", 4)
    profiler.set_counter("support_attempt_count", 1)

    event = profiler.snapshot()

    assert event is not None
    assert event.component_seconds["proposal_policy"] == 1.0
    assert event.component_seconds["support_construction"] == 2.0
    assert event.measured_component_seconds == 3.0
    assert event.unattributed_overhead_seconds == 0.5
    assert event.accounted_total_seconds == event.wall_span_seconds == 3.5
    assert event.component_invocations["proposal_policy"] == 1
    assert event.counters["proposal_count"] == 3
    assert event.support_row_sizes == (2, 4)
    json.dumps(event.to_dict())
    evidence = json.loads(
        (Path(__file__).parents[2] / "docs/evidence/t804-component-profile-sample.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["event"] == event.to_dict()


def test_disabled_profiler_never_reads_clock_and_emits_no_event() -> None:
    def forbidden_clock() -> float:
        raise AssertionError("disabled profiling read its clock")

    profiler = ComponentProfiler(clock=forbidden_clock)

    with profiler.measure(ProfilingComponent.PARSER):
        pass
    with profiler.observe_wall_span():
        pass
    profiler.add_duration(ProfilingComponent.BACKTRACKING, 1.0)
    profiler.set_counter("chart_entries", 10)
    profiler.set_support_row_sizes((1, 2))

    assert profiler.snapshot() is None


def test_profiled_python_step_is_observational_and_records_every_component() -> None:
    adapter = CompositionalByteLevelAdapter((b"a", None, None))
    eos_policy = EOSPolicy(
        EOSMode.REQUIRED,
        termination_token_ids=(1,),
        pad_token_id=2,
    )
    profiler = ComponentProfiler(enabled=True)
    proposal_batch = build_schedule_proposals(
        predicted_token_ids=(0, 1),
        confidence_values=(0.9, 0.8),
        schedule_mask=(True, True),
        k_s=2,
        weight_mode=ProposalWeightMode.CONFIDENCE,
        profiler=profiler,
    )
    support = build_per_position_support(
        canvas=(None, None),
        policy=SupportPolicy(
            kind=SupportKind.TOP_K,
            vocabulary_size=adapter.vocabulary_size,
            top_k=1,
            required_special_token_ids=(1, 2),
        ),
        logits=((9.0, 1.0, 0.0), (0.0, 9.0, 1.0)),
        proposals=proposal_batch.proposals,
        profiler=profiler,
    )
    result = solve_exact_commit(
        _one_byte_grammar(ord("a")),
        canvas=(None, None),
        support=support,
        proposals=proposal_batch.proposals,
        tokenizer_adapter=adapter,
        eos_policy=eos_policy,
        backend=ExactBackend.PYTHON,
        profiler=profiler,
    )
    step = apply_exact_commit_result(
        result,
        canvas=(None, None),
        proposals=proposal_batch.proposals,
        profiler=profiler,
    )
    event = profiler.snapshot()

    assert result.status is SolveStatus.OPTIMAL
    assert step.updated_canvas == result.witness_token_ids == (0, 1)
    assert event is not None
    assert all(
        event.component_invocations[component.value] >= 1 for component in ProfilingComponent
    )
    assert event.counters["proposal_count"] == 2
    assert event.counters["support_slot_count"] == 2
    assert event.counters["support_alternative_count"] == 5
    assert event.counters["support_max_row_size"] == 3
    assert event.support_row_sizes == (3, 2)
    assert event.counters["token_lattice_node_count"] == 3
    assert event.counters["token_lattice_edge_count"] == 5
    assert event.counters["terminal_graph_node_count"] > 0
    assert event.counters["terminal_graph_edge_count"] > 0
    assert event.counters["normalized_graph_edge_count"] > 0
    assert event.counters["chart_entries"] > 0
    assert event.counters["commit_count"] == 2
    assert event.accounted_total_seconds == pytest.approx(event.wall_span_seconds)
    json.dumps(event.to_dict())

    unprofiled_result = solve_exact_commit(
        _one_byte_grammar(ord("a")),
        canvas=(None, None),
        support=support,
        proposals=proposal_batch.proposals,
        tokenizer_adapter=adapter,
        eos_policy=eos_policy,
        backend=ExactBackend.PYTHON,
    )
    unprofiled_step = apply_exact_commit_result(
        unprofiled_result,
        canvas=(None, None),
        proposals=proposal_batch.proposals,
    )
    assert result.to_dict() == unprofiled_result.to_dict()
    assert step.to_dict() == unprofiled_step.to_dict()


@pytest.mark.integration
def test_rust_profile_uses_separate_internal_parser_and_backtracking_timers() -> None:
    pytest.importorskip("mwpc_parser_py")
    adapter = CompositionalByteLevelAdapter((b"a",))
    support = build_per_position_support(
        canvas=(None,),
        policy=SupportPolicy(kind=SupportKind.FULL, vocabulary_size=1),
        logits=((1.0,),),
    )
    profiler = ComponentProfiler(enabled=True)

    result = solve_exact_commit(
        _one_byte_grammar(ord("a")),
        canvas=(None,),
        support=support,
        proposals=(),
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        backend=ExactBackend.RUST,
        profiler=profiler,
    )
    event = profiler.snapshot()

    assert result.status is SolveStatus.OPTIMAL
    assert event is not None
    assert event.component_invocations["parser"] == 1
    assert event.component_invocations["backtracking"] >= 2
    assert event.component_seconds["parser"] >= 0.0
    assert event.component_seconds["backtracking"] >= 0.0
