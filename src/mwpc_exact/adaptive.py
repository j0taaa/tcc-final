"""Deterministic adaptive top-K orchestration for exact MWPC steps.

Only a conclusive ``INFEASIBLE_ON_SUPPORT`` result permits a wider retry.
Every represented row is checked to be a superset of the preceding attempt,
and the complete attempt history is attached to the final structured result.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from math import isfinite
from time import monotonic

from mwpc_exact.eos_lattice import EOSPolicy
from mwpc_exact.finite_solver import ExactBackend
from mwpc_exact.profiling import ComponentProfiler
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.solver import solve_exact_commit
from mwpc_exact.support import PerPositionSupport, SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import ExactCommitResult, Proposal, SolveStatus, SupportKind


class SupportGrowthPolicy(StrEnum):
    """Deterministic rules for choosing the next represented top-K width."""

    LINEAR = "linear"
    DOUBLING = "doubling"


def _positive_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


@dataclass(frozen=True, slots=True)
class AdaptiveSupportConfig:
    """Validated schedule and total deadline for adaptive support expansion."""

    initial_k: int
    k_max: int
    growth_policy: SupportGrowthPolicy = SupportGrowthPolicy.DOUBLING
    total_timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        initial_k = _positive_integer(self.initial_k, "initial_k")
        k_max = _positive_integer(self.k_max, "k_max")
        if k_max < initial_k:
            raise ValueError("k_max must be greater than or equal to initial_k")
        if not isinstance(self.growth_policy, SupportGrowthPolicy):
            raise TypeError("growth_policy must be a SupportGrowthPolicy")
        if self.total_timeout_seconds is not None:
            timeout = self.total_timeout_seconds
            if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
                raise TypeError("total_timeout_seconds must be a real number or None")
            timeout = float(timeout)
            if not isfinite(timeout) or timeout < 0.0:
                raise ValueError("total_timeout_seconds must be finite and non-negative")
            object.__setattr__(self, "total_timeout_seconds", timeout)
        object.__setattr__(self, "initial_k", initial_k)
        object.__setattr__(self, "k_max", k_max)

    def attempt_widths(self, available_token_count: int) -> tuple[int, ...]:
        """Return the finite deterministic schedule, capped at full support."""

        available = _positive_integer(available_token_count, "available_token_count")
        if self.initial_k > available:
            raise ValueError("initial_k cannot exceed the permitted token count")
        ceiling = min(self.k_max, available)
        widths = [self.initial_k]
        while widths[-1] < ceiling:
            current = widths[-1]
            proposed = (
                current + 1
                if self.growth_policy is SupportGrowthPolicy.LINEAR
                else current * 2
            )
            widths.append(min(proposed, ceiling))
        return tuple(widths)

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible immutable configuration metadata."""

        return {
            "initial_k": self.initial_k,
            "growth_policy": self.growth_policy.value,
            "k_max": self.k_max,
            "total_timeout_seconds": self.total_timeout_seconds,
        }


@dataclass(frozen=True, slots=True)
class _AttemptRecord:
    attempt_index: int
    requested_k: int
    support: PerPositionSupport
    result: ExactCommitResult
    support_construction_seconds: float
    solve_seconds: float
    cumulative_elapsed_seconds: float
    backend_timeout_seconds: float | None
    superset_of_previous: bool | None

    def to_dict(self) -> dict[str, object]:
        token_diagnostics = _nested_diagnostics(
            self.result.diagnostics,
            "token_lattice_diagnostics",
        )
        byte_diagnostics = _nested_diagnostics(
            self.result.diagnostics,
            "byte_eos_lattice_diagnostics",
        )
        return {
            "attempt_index": self.attempt_index,
            "requested_k": self.requested_k,
            "effective_support_kind": self.support.exactness_scope.kind.value,
            "effective_top_k": self.support.effective_top_k,
            "scope": self.support.exactness_scope.to_dict(),
            "status": self.result.status.value,
            "objective_value": self.result.objective_value,
            "represented_support_sha256": self.support.fingerprint,
            "represented_support_row_sizes": [len(row) for row in self.support.rows],
            "superset_of_previous": self.superset_of_previous,
            "support_construction_seconds": self.support_construction_seconds,
            "solve_seconds": self.solve_seconds,
            "elapsed_seconds": self.support_construction_seconds + self.solve_seconds,
            "cumulative_elapsed_seconds": self.cumulative_elapsed_seconds,
            "backend_timeout_seconds": self.backend_timeout_seconds,
            "graph_sizes": {
                "token_choice_count": token_diagnostics.get("token_choice_count"),
                "original_node_count": byte_diagnostics.get("original_graph_node_count"),
                "original_edge_count": byte_diagnostics.get("original_graph_edge_count"),
                "normalized_edge_count": byte_diagnostics.get("normalized_graph_edge_count"),
            },
        }


def _nested_diagnostics(
    diagnostics: Mapping[str, object],
    key: str,
) -> Mapping[str, object]:
    value = diagnostics.get(key)
    return value if isinstance(value, Mapping) else {}


def _special_token_ids(policy: EOSPolicy) -> tuple[int, ...]:
    token_ids = set(policy.termination_token_ids)
    if policy.pad_token_id is not None:
        token_ids.add(policy.pad_token_id)
    return tuple(sorted(token_ids))


def _support_policy_for_attempt(
    *,
    width: int,
    attempt_index: int,
    widths: tuple[int, ...],
    permitted_token_count: int,
    vocabulary_size: int,
    permitted_token_ids: tuple[int, ...],
    special_token_ids: tuple[int, ...],
    include_proposal_tokens: bool,
    pruning_description: str | None,
) -> SupportPolicy:
    if width == permitted_token_count:
        return SupportPolicy(
            kind=SupportKind.FULL,
            vocabulary_size=vocabulary_size,
            required_special_token_ids=special_token_ids,
            include_proposal_tokens=include_proposal_tokens,
            permitted_token_ids=permitted_token_ids,
            pruning_description=pruning_description,
        )
    return SupportPolicy(
        kind=SupportKind.TOP_K,
        vocabulary_size=vocabulary_size,
        top_k=widths[0],
        adaptive_expansions=widths[1 : attempt_index + 1],
        required_special_token_ids=special_token_ids,
        include_proposal_tokens=include_proposal_tokens,
        permitted_token_ids=permitted_token_ids,
        pruning_description=pruning_description,
    )


def _validate_support_superset(
    previous: PerPositionSupport,
    current: PerPositionSupport,
) -> None:
    if previous.canvas != current.canvas:
        raise RuntimeError("adaptive support expansion changed the frozen canvas")
    if previous.permitted_token_ids != current.permitted_token_ids:
        raise RuntimeError("adaptive support expansion changed the permitted token universe")
    for position, (old_row, new_row) in enumerate(
        zip(previous.rows, current.rows, strict=True)
    ):
        if not set(old_row) <= set(new_row):
            raise RuntimeError(
                f"adaptive support row {position} is not a superset of its predecessor"
            )


def _copy_result_with_diagnostics(
    result: ExactCommitResult,
    diagnostics: Mapping[str, object],
) -> ExactCommitResult:
    return ExactCommitResult(
        status=result.status,
        exactness_scope=result.exactness_scope,
        objective_value=result.objective_value,
        selected_proposal_ids=result.selected_proposal_ids,
        witness_token_ids=result.witness_token_ids,
        witness_terminal_labels=result.witness_terminal_labels,
        witness_graph_edge_ids=result.witness_graph_edge_ids,
        witness_eos_position=result.witness_eos_position,
        witness_content_endpoint_slot=result.witness_content_endpoint_slot,
        diagnostics=diagnostics,
    )


def _finalize(
    result: ExactCommitResult,
    *,
    config: AdaptiveSupportConfig,
    configured_widths: tuple[int, ...],
    attempts: Sequence[_AttemptRecord],
    backend: ExactBackend,
    stopped_reason: str,
    resource_limit_prevented_expansion: bool,
    total_elapsed_seconds: float,
) -> ExactCommitResult:
    attempt_dicts = [attempt.to_dict() for attempt in attempts]
    optimal_objectives = [
        float(attempt.result.objective_value)
        for attempt in attempts
        if attempt.result.status is SolveStatus.OPTIMAL
        and attempt.result.objective_value is not None
    ]
    diagnostics = dict(result.diagnostics)
    diagnostics["adaptive_support"] = {
        "orchestrator": "adaptive_support_v1",
        "config": config.to_dict(),
        "configured_widths": list(configured_widths),
        "attempted_k": [attempt.requested_k for attempt in attempts],
        "attempts": attempt_dicts,
        "final_scope": result.exactness_scope.to_dict(),
        "final_status": result.status.value,
        "stopped_reason": stopped_reason,
        "resource_limit_prevented_expansion": resource_limit_prevented_expansion,
        "support_superset_verified": all(
            attempt.superset_of_previous is not False for attempt in attempts
        ),
        "objective_monotonicity_basis": (
            "fixed proposals over row-wise verified support supersets"
        ),
        "optimal_objective_non_decreasing": all(
            earlier <= later for earlier, later in pairwise(optimal_objectives)
        ),
        "optimal_objective_values": optimal_objectives,
        "total_elapsed_seconds": total_elapsed_seconds,
        "deadline_enforcement": (
            "remaining_total_time_passed_to_each_parser_attempt"
            if backend is ExactBackend.RUST
            else "checked_between_reference_parser_attempts"
        ),
    }
    return _copy_result_with_diagnostics(result, diagnostics)


def solve_exact_commit_adaptive(
    grammar: CnfGrammar,
    *,
    canvas: Sequence[int | None],
    logits: Sequence[Sequence[float]],
    proposals: Iterable[Proposal],
    tokenizer_adapter: CompositionalByteLevelAdapter,
    eos_policy: EOSPolicy,
    config: AdaptiveSupportConfig,
    backend: ExactBackend = ExactBackend.RUST,
    permitted_token_ids: Sequence[int] | None = None,
    include_proposal_tokens: bool = False,
    pruning_description: str | None = None,
    deadline_check_interval: int = 1_024,
    deterministic_work_limit: int | None = None,
    profiler: ComponentProfiler | None = None,
) -> ExactCommitResult:
    """Solve with successively wider deterministic top-K support.

    The model-independent caller supplies saved logits. A wider solve is
    started only after ``INFEASIBLE_ON_SUPPORT``. Rust attempts receive the
    remaining total deadline; the Python reference backend checks that total
    deadline between complete attempts because it has no interruptible parser.
    """

    if not isinstance(config, AdaptiveSupportConfig):
        raise TypeError("config must be an AdaptiveSupportConfig")
    if profiler is not None and not isinstance(profiler, ComponentProfiler):
        raise TypeError("profiler must be a ComponentProfiler or None")
    if not isinstance(tokenizer_adapter, CompositionalByteLevelAdapter):
        raise TypeError("tokenizer_adapter must be a CompositionalByteLevelAdapter")
    if not isinstance(eos_policy, EOSPolicy):
        raise TypeError("eos_policy must be an EOSPolicy")
    if not isinstance(backend, ExactBackend):
        raise TypeError("backend must be an ExactBackend")
    if not isinstance(include_proposal_tokens, bool):
        raise TypeError("include_proposal_tokens must be a boolean")
    if config.k_max > tokenizer_adapter.vocabulary_size:
        raise ValueError("k_max cannot exceed the tokenizer vocabulary size")

    canvas_items = tuple(canvas)
    proposal_items = tuple(proposals)
    special_token_ids = _special_token_ids(eos_policy)
    base_policy = SupportPolicy(
        kind=SupportKind.FULL,
        vocabulary_size=tokenizer_adapter.vocabulary_size,
        required_special_token_ids=special_token_ids,
        include_proposal_tokens=include_proposal_tokens,
        permitted_token_ids=(
            None if permitted_token_ids is None else tuple(permitted_token_ids)
        ),
        pruning_description=pruning_description,
    )
    normalized_permitted = base_policy.permitted_token_ids
    if normalized_permitted is None:
        raise AssertionError("SupportPolicy did not normalize permitted_token_ids")
    widths = config.attempt_widths(len(normalized_permitted))

    started_at = monotonic()
    latest_time = started_at
    attempts: list[_AttemptRecord] = []
    previous_support: PerPositionSupport | None = None

    for attempt_index, width in enumerate(widths):
        support_started_at = latest_time
        policy = _support_policy_for_attempt(
            width=width,
            attempt_index=attempt_index,
            widths=widths,
            permitted_token_count=len(normalized_permitted),
            vocabulary_size=tokenizer_adapter.vocabulary_size,
            permitted_token_ids=normalized_permitted,
            special_token_ids=special_token_ids,
            include_proposal_tokens=include_proposal_tokens,
            pruning_description=pruning_description,
        )
        support = build_per_position_support(
            canvas=canvas_items,
            policy=policy,
            logits=logits,
            proposals=proposal_items,
            profiler=profiler,
        )
        support_finished_at = monotonic()
        if previous_support is not None:
            _validate_support_superset(previous_support, support)

        remaining_timeout: float | None = None
        if config.total_timeout_seconds is not None:
            remaining_timeout = max(
                0.0,
                config.total_timeout_seconds - (support_finished_at - started_at),
            )
        backend_timeout = remaining_timeout if backend is ExactBackend.RUST else None
        result = solve_exact_commit(
            grammar,
            canvas=canvas_items,
            support=support,
            proposals=proposal_items,
            tokenizer_adapter=tokenizer_adapter,
            eos_policy=eos_policy,
            backend=backend,
            timeout_seconds=backend_timeout,
            deadline_check_interval=deadline_check_interval,
            deterministic_work_limit=deterministic_work_limit,
            profiler=profiler,
        )
        latest_time = monotonic()
        attempt = _AttemptRecord(
            attempt_index=attempt_index,
            requested_k=width,
            support=support,
            result=result,
            support_construction_seconds=max(0.0, support_finished_at - support_started_at),
            solve_seconds=max(0.0, latest_time - support_finished_at),
            cumulative_elapsed_seconds=max(0.0, latest_time - started_at),
            backend_timeout_seconds=backend_timeout,
            superset_of_previous=None if previous_support is None else True,
        )
        attempts.append(attempt)
        if profiler is not None and profiler.enabled:
            profiler.set_counter("support_attempt_count", len(attempts))
            profiler.set_counter("support_expansion_count", max(0, len(attempts) - 1))

        if result.status is not SolveStatus.INFEASIBLE_ON_SUPPORT:
            return _finalize(
                result,
                config=config,
                configured_widths=widths,
                attempts=attempts,
                backend=backend,
                stopped_reason=f"terminal_status_{result.status.value}",
                resource_limit_prevented_expansion=False,
                total_elapsed_seconds=max(0.0, latest_time - started_at),
            )
        if attempt_index + 1 == len(widths):
            stopped_reason = (
                "full_permitted_support_reached"
                if support.exactness_scope.kind is SupportKind.FULL
                else "k_max_reached"
            )
            return _finalize(
                result,
                config=config,
                configured_widths=widths,
                attempts=attempts,
                backend=backend,
                stopped_reason=stopped_reason,
                resource_limit_prevented_expansion=False,
                total_elapsed_seconds=max(0.0, latest_time - started_at),
            )
        if (
            config.total_timeout_seconds is not None
            and latest_time - started_at >= config.total_timeout_seconds
        ):
            timeout_result = ExactCommitResult(
                status=SolveStatus.TIMEOUT,
                exactness_scope=result.exactness_scope,
                diagnostics=result.diagnostics,
            )
            return _finalize(
                timeout_result,
                config=config,
                configured_widths=widths,
                attempts=attempts,
                backend=backend,
                stopped_reason="total_timeout_before_next_expansion",
                resource_limit_prevented_expansion=True,
                total_elapsed_seconds=max(0.0, latest_time - started_at),
            )
        previous_support = support

    raise AssertionError("validated adaptive schedule unexpectedly contained no attempts")


__all__ = [
    "AdaptiveSupportConfig",
    "SupportGrowthPolicy",
    "solve_exact_commit_adaptive",
]
