from __future__ import annotations

import json
from collections.abc import Mapping
from importlib import import_module

import pytest

import mwpc_exact.adaptive as adaptive
from mwpc_exact import (
    AdaptiveSupportConfig,
    ComponentProfiler,
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    ExactCommitResult,
    Proposal,
    SolveStatus,
    SupportGrowthPolicy,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
    solve_exact_commit,
    solve_exact_commit_adaptive,
)
from mwpc_exact.reference.grammar import (
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.support import PerPositionSupport

REQUIRED_ADAPTER = CompositionalByteLevelAdapter((b"a", b"b", None, None, None))
REQUIRED_EOS = EOSPolicy(
    EOSMode.REQUIRED,
    termination_token_ids=(2, 3),
    pad_token_id=2,
)


def rust_binding_available() -> bool:
    try:
        import_module("mwpc_parser_py")
    except ImportError:
        return False
    return True


requires_rust = pytest.mark.skipif(
    not rust_binding_available(),
    reason="build the production binding with `make bootstrap-rust-parser`",
)


def one_byte_grammar(*labels: int) -> CnfGrammar:
    terminals = tuple(Terminal(index, label) for index, label in enumerate(labels))
    return CnfGrammar(
        nonterminals=(Nonterminal(0, "S"),),
        terminals=terminals,
        start_nonterminal_id=0,
        terminal_productions=tuple(
            TerminalProduction(index, 0, index) for index in range(len(terminals))
        ),
    )


def adaptive_diagnostics(result: ExactCommitResult) -> Mapping[str, object]:
    diagnostics = result.diagnostics["adaptive_support"]
    assert isinstance(diagnostics, Mapping)
    return diagnostics


def test_growth_schedules_are_deterministic_and_cap_at_available_support() -> None:
    doubling = AdaptiveSupportConfig(
        initial_k=3,
        k_max=10,
        growth_policy=SupportGrowthPolicy.DOUBLING,
    )
    linear = AdaptiveSupportConfig(
        initial_k=3,
        k_max=6,
        growth_policy=SupportGrowthPolicy.LINEAR,
    )

    assert doubling.attempt_widths(20) == (3, 6, 10)
    assert doubling.attempt_widths(7) == (3, 6, 7)
    assert linear.attempt_widths(20) == (3, 4, 5, 6)
    assert AdaptiveSupportConfig(initial_k=4, k_max=4).attempt_widths(9) == (4,)


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"initial_k": 0, "k_max": 2}, ValueError, "initial_k must be positive"),
        ({"initial_k": True, "k_max": 2}, TypeError, "initial_k must be an integer"),
        ({"initial_k": 3, "k_max": 2}, ValueError, "greater than or equal"),
        (
            {"initial_k": 1, "k_max": 2, "growth_policy": "doubling"},
            TypeError,
            "SupportGrowthPolicy",
        ),
        (
            {"initial_k": 1, "k_max": 2, "total_timeout_seconds": float("inf")},
            ValueError,
            "finite and non-negative",
        ),
    ],
)
def test_adaptive_config_rejects_malformed_values(
    kwargs: dict[str, object],
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error, match=message):
        AdaptiveSupportConfig(**kwargs)  # type: ignore[arg-type]


def test_infeasible_attempt_expands_to_optimal_saved_logits_support() -> None:
    canvas = (None, None)
    logits = (
        (10.0, 9.0, 0.0, -1.0, -2.0),
        (0.0, -1.0, 9.0, 10.0, -2.0),
    )
    proposals = (
        Proposal(0, position=0, token_id=1, weight=5),
        Proposal(1, position=1, token_id=3, weight=2),
    )
    profiler = ComponentProfiler(enabled=True)

    result = solve_exact_commit_adaptive(
        one_byte_grammar(ord("b")),
        canvas=canvas,
        logits=logits,
        proposals=proposals,
        tokenizer_adapter=REQUIRED_ADAPTER,
        eos_policy=REQUIRED_EOS,
        config=AdaptiveSupportConfig(initial_k=1, k_max=4),
        backend=ExactBackend.PYTHON,
        profiler=profiler,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 7.0
    assert result.selected_proposal_ids == (0, 1)
    assert result.witness_token_ids == (1, 3)
    assert result.exactness_scope.kind is SupportKind.TOP_K
    assert result.exactness_scope.top_k == 1
    assert result.exactness_scope.adaptive_expansions == (2,)

    diagnostics = adaptive_diagnostics(result)
    assert diagnostics["configured_widths"] == (1, 2, 4)
    assert diagnostics["attempted_k"] == (1, 2)
    assert diagnostics["stopped_reason"] == "terminal_status_optimal"
    assert diagnostics["support_superset_verified"] is True
    assert diagnostics["optimal_objective_non_decreasing"] is True
    attempts = diagnostics["attempts"]
    assert isinstance(attempts, tuple)
    assert tuple(attempt["status"] for attempt in attempts) == (
        SolveStatus.INFEASIBLE_ON_SUPPORT.value,
        SolveStatus.OPTIMAL.value,
    )
    assert attempts[0]["superset_of_previous"] is None
    assert attempts[1]["superset_of_previous"] is True
    assert attempts[0]["represented_support_sha256"] != attempts[1][
        "represented_support_sha256"
    ]
    for attempt in attempts:
        graph_sizes = attempt["graph_sizes"]
        assert graph_sizes["token_choice_count"] > 0
        assert graph_sizes["original_node_count"] > 0
        assert graph_sizes["original_edge_count"] > 0
        assert graph_sizes["normalized_edge_count"] > 0
        assert attempt["support_construction_seconds"] >= 0.0
        assert attempt["solve_seconds"] >= 0.0
    profile_event = profiler.snapshot()
    assert profile_event is not None
    assert profile_event.counters["support_attempt_count"] == 2
    assert profile_event.counters["support_expansion_count"] == 1
    assert profile_event.component_invocations["support_construction"] == 2
    assert profile_event.component_invocations["parser"] == 2
    json.dumps(result.to_dict())


@requires_rust
def test_rust_and_python_adaptive_expansion_agree() -> None:
    kwargs = {
        "canvas": (None, None),
        "logits": (
            (10.0, 9.0, 0.0, -1.0, -2.0),
            (0.0, -1.0, 9.0, 10.0, -2.0),
        ),
        "proposals": (
            Proposal(0, position=0, token_id=1, weight=5),
            Proposal(1, position=1, token_id=3, weight=2),
        ),
        "tokenizer_adapter": REQUIRED_ADAPTER,
        "eos_policy": REQUIRED_EOS,
        "config": AdaptiveSupportConfig(initial_k=1, k_max=4),
    }

    python_result = solve_exact_commit_adaptive(
        one_byte_grammar(ord("b")),
        backend=ExactBackend.PYTHON,
        **kwargs,  # type: ignore[arg-type]
    )
    rust_result = solve_exact_commit_adaptive(
        one_byte_grammar(ord("b")),
        backend=ExactBackend.RUST,
        **kwargs,  # type: ignore[arg-type]
    )

    assert python_result.status is rust_result.status is SolveStatus.OPTIMAL
    assert python_result.objective_value == rust_result.objective_value == 7.0
    assert python_result.exactness_scope == rust_result.exactness_scope
    assert adaptive_diagnostics(python_result)["attempted_k"] == (1, 2)
    assert adaptive_diagnostics(rust_result)["attempted_k"] == (1, 2)


def test_reaching_every_permitted_token_uses_validated_full_scope() -> None:
    adapter = CompositionalByteLevelAdapter((b"a", b"b"))
    result = solve_exact_commit_adaptive(
        one_byte_grammar(ord("b")),
        canvas=(None,),
        logits=((2.0, 1.0),),
        proposals=(Proposal(0, position=0, token_id=1, weight=4),),
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        config=AdaptiveSupportConfig(initial_k=1, k_max=2),
        backend=ExactBackend.PYTHON,
    )

    assert result.status is SolveStatus.OPTIMAL
    assert result.exactness_scope.kind is SupportKind.FULL
    assert result.objective_value == 4.0
    diagnostics = adaptive_diagnostics(result)
    assert diagnostics["attempted_k"] == (1, 2)
    attempts = diagnostics["attempts"]
    assert isinstance(attempts, tuple)
    assert tuple(attempt["effective_support_kind"] for attempt in attempts) == (
        SupportKind.TOP_K.value,
        SupportKind.FULL.value,
    )
    assert result.diagnostics["exactness_name"] == (
        "exact_declared_full_finite_slot_instance"
    )


def test_linear_growth_stops_deterministically_at_k_max_when_still_infeasible() -> None:
    adapter = CompositionalByteLevelAdapter((b"a", b"b", b"c", b"d"))
    result = solve_exact_commit_adaptive(
        one_byte_grammar(ord("z")),
        canvas=(None,),
        logits=((4.0, 3.0, 2.0, 1.0),),
        proposals=(),
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        config=AdaptiveSupportConfig(
            initial_k=1,
            k_max=3,
            growth_policy=SupportGrowthPolicy.LINEAR,
        ),
        backend=ExactBackend.PYTHON,
    )

    assert result.status is SolveStatus.INFEASIBLE_ON_SUPPORT
    assert result.exactness_scope.adaptive_expansions == (2, 3)
    diagnostics = adaptive_diagnostics(result)
    assert diagnostics["configured_widths"] == (1, 2, 3)
    assert diagnostics["attempted_k"] == (1, 2, 3)
    assert diagnostics["stopped_reason"] == "k_max_reached"
    attempts = diagnostics["attempts"]
    assert isinstance(attempts, tuple)
    assert all(
        attempt["status"] == SolveStatus.INFEASIBLE_ON_SUPPORT.value
        for attempt in attempts
    )


@pytest.mark.parametrize(
    "status",
    [SolveStatus.TIMEOUT, SolveStatus.UNSUPPORTED, SolveStatus.ERROR],
)
def test_timeout_unsupported_and_error_never_trigger_expansion(
    monkeypatch: pytest.MonkeyPatch,
    status: SolveStatus,
) -> None:
    calls: list[int] = []

    def terminal_result(*_args: object, **kwargs: object) -> ExactCommitResult:
        support = kwargs["support"]
        assert isinstance(support, PerPositionSupport)
        assert support.effective_top_k is not None
        calls.append(support.effective_top_k)
        return ExactCommitResult(status=status, exactness_scope=support.exactness_scope)

    monkeypatch.setattr(adaptive, "solve_exact_commit", terminal_result)
    result = solve_exact_commit_adaptive(
        one_byte_grammar(ord("a")),
        canvas=(None,),
        logits=((4.0, 3.0, 2.0, 1.0),),
        proposals=(),
        tokenizer_adapter=CompositionalByteLevelAdapter((b"a", b"b", b"c", b"d")),
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        config=AdaptiveSupportConfig(initial_k=1, k_max=4),
        backend=ExactBackend.PYTHON,
    )

    assert result.status is status
    assert calls == [1]
    diagnostics = adaptive_diagnostics(result)
    assert diagnostics["attempted_k"] == (1,)
    assert diagnostics["stopped_reason"] == f"terminal_status_{status.value}"


def test_total_timeout_between_infeasible_attempts_is_not_infeasibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    times = iter((0.0, 0.1, 1.1))
    calls = 0

    def clock() -> float:
        return next(times)

    def infeasible(*_args: object, **kwargs: object) -> ExactCommitResult:
        nonlocal calls
        calls += 1
        support = kwargs["support"]
        assert isinstance(support, PerPositionSupport)
        return ExactCommitResult(
            status=SolveStatus.INFEASIBLE_ON_SUPPORT,
            exactness_scope=support.exactness_scope,
        )

    monkeypatch.setattr(adaptive, "monotonic", clock)
    monkeypatch.setattr(adaptive, "solve_exact_commit", infeasible)
    result = solve_exact_commit_adaptive(
        one_byte_grammar(ord("a")),
        canvas=(None,),
        logits=((4.0, 3.0, 2.0, 1.0),),
        proposals=(),
        tokenizer_adapter=CompositionalByteLevelAdapter((b"a", b"b", b"c", b"d")),
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        config=AdaptiveSupportConfig(
            initial_k=1,
            k_max=4,
            total_timeout_seconds=1.0,
        ),
        backend=ExactBackend.PYTHON,
    )

    assert calls == 1
    assert result.status is SolveStatus.TIMEOUT
    assert result.objective_value is None
    diagnostics = adaptive_diagnostics(result)
    assert diagnostics["attempted_k"] == (1,)
    assert diagnostics["resource_limit_prevented_expansion"] is True
    assert diagnostics["stopped_reason"] == "total_timeout_before_next_expansion"
    assert diagnostics["deadline_enforcement"] == "checked_between_reference_parser_attempts"


def test_rust_attempt_receives_only_remaining_total_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    times = iter((10.0, 10.25, 10.5))
    received_timeout: float | None = None

    def clock() -> float:
        return next(times)

    def terminal_error(*_args: object, **kwargs: object) -> ExactCommitResult:
        nonlocal received_timeout
        raw_timeout = kwargs["timeout_seconds"]
        assert isinstance(raw_timeout, float)
        received_timeout = raw_timeout
        support = kwargs["support"]
        assert isinstance(support, PerPositionSupport)
        return ExactCommitResult(
            status=SolveStatus.ERROR,
            exactness_scope=support.exactness_scope,
        )

    monkeypatch.setattr(adaptive, "monotonic", clock)
    monkeypatch.setattr(adaptive, "solve_exact_commit", terminal_error)
    result = solve_exact_commit_adaptive(
        one_byte_grammar(ord("a")),
        canvas=(None,),
        logits=((4.0, 3.0, 2.0, 1.0),),
        proposals=(),
        tokenizer_adapter=CompositionalByteLevelAdapter((b"a", b"b", b"c", b"d")),
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        config=AdaptiveSupportConfig(
            initial_k=1,
            k_max=4,
            total_timeout_seconds=2.0,
        ),
        backend=ExactBackend.RUST,
    )

    assert result.status is SolveStatus.ERROR
    assert received_timeout == pytest.approx(1.75)
    diagnostics = adaptive_diagnostics(result)
    assert diagnostics["deadline_enforcement"] == (
        "remaining_total_time_passed_to_each_parser_attempt"
    )


def test_non_superset_expansion_is_rejected_before_the_second_solve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = CompositionalByteLevelAdapter((b"a", b"b", b"c", b"d"))
    first = build_per_position_support(
        canvas=(None,),
        policy=SupportPolicy(kind=SupportKind.TOP_K, vocabulary_size=4, top_k=1),
        logits=((4.0, 3.0, 2.0, 1.0),),
    )
    second = build_per_position_support(
        canvas=(None,),
        policy=SupportPolicy(
            kind=SupportKind.TOP_K,
            vocabulary_size=4,
            top_k=1,
            adaptive_expansions=(2,),
        ),
        logits=((1.0, 4.0, 3.0, 2.0),),
    )
    supports = iter((first, second))
    solves = 0

    def broken_builder(**_kwargs: object) -> PerPositionSupport:
        return next(supports)

    def infeasible(*_args: object, **kwargs: object) -> ExactCommitResult:
        nonlocal solves
        solves += 1
        support = kwargs["support"]
        assert isinstance(support, PerPositionSupport)
        return ExactCommitResult(
            status=SolveStatus.INFEASIBLE_ON_SUPPORT,
            exactness_scope=support.exactness_scope,
        )

    monkeypatch.setattr(adaptive, "build_per_position_support", broken_builder)
    monkeypatch.setattr(adaptive, "solve_exact_commit", infeasible)
    with pytest.raises(RuntimeError, match="not a superset"):
        solve_exact_commit_adaptive(
            one_byte_grammar(ord("z")),
            canvas=(None,),
            logits=((4.0, 3.0, 2.0, 1.0),),
            proposals=(),
            tokenizer_adapter=adapter,
            eos_policy=EOSPolicy(EOSMode.ABSENT),
            config=AdaptiveSupportConfig(initial_k=1, k_max=2),
            backend=ExactBackend.PYTHON,
        )
    assert solves == 1


def test_verified_support_growth_cannot_decrease_the_exact_optimum() -> None:
    adapter = CompositionalByteLevelAdapter((b"a", b"b"))
    canvas = (None,)
    logits = ((2.0, 1.0),)
    proposals = (
        Proposal(0, position=0, token_id=0, weight=1),
        Proposal(1, position=0, token_id=1, weight=4),
    )
    narrow = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.TOP_K, vocabulary_size=2, top_k=1),
        logits=logits,
        proposals=proposals,
    )
    full = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.FULL, vocabulary_size=2),
        logits=logits,
        proposals=proposals,
    )

    narrow_result = solve_exact_commit(
        one_byte_grammar(ord("a"), ord("b")),
        canvas=canvas,
        support=narrow,
        proposals=proposals,
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        backend=ExactBackend.PYTHON,
    )
    full_result = solve_exact_commit(
        one_byte_grammar(ord("a"), ord("b")),
        canvas=canvas,
        support=full,
        proposals=proposals,
        tokenizer_adapter=adapter,
        eos_policy=EOSPolicy(EOSMode.ABSENT),
        backend=ExactBackend.PYTHON,
    )

    assert set(narrow.rows[0]) <= set(full.rows[0])
    assert narrow_result.status is full_result.status is SolveStatus.OPTIMAL
    assert narrow_result.objective_value == 1.0
    assert full_result.objective_value == 4.0
    assert narrow_result.objective_value <= full_result.objective_value
