"""Common offline selection contracts for fair frozen-instance comparisons.

The serial baseline consumes proposals in their saved order and retains a
proposal choice only when the remaining finite support still has a
grammar-valid completion.  It is a feasibility-preserving greedy baseline,
not an MWPC optimizer.  The exact adapter accepts the same immutable input and
keeps its stronger ``OPTIMAL`` status separate.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from math import fsum, isclose, isfinite
from time import perf_counter
from types import MappingProxyType

from mwpc_exact.backend import ExactBackend
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.solver import solve_exact_commit
from mwpc_exact.support import PerPositionSupport
from mwpc_exact.token_lattice import build_token_lattice
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import (
    ExactCommitResult,
    ExactnessScope,
    Proposal,
    SolveStatus,
    TerminalLabel,
    aggregate_proposals,
)


class SelectorKind(StrEnum):
    """Stable serialized selector IDs with precise evaluation-facing names."""

    GREEDY_EXACT_FEASIBILITY = "serial"
    EPIC_REGULAR_COVER = "epic"
    EXACT_MWPC = "exact"
    BRUTE_FORCE = "brute_force"
    UNCONSTRAINED = "unconstrained"

    # Compatibility aliases for version-1 benchmark artifacts.
    SERIAL = GREEDY_EXACT_FEASIBILITY
    EPIC = EPIC_REGULAR_COVER
    EXACT = EXACT_MWPC


class SelectionStatus(StrEnum):
    """Mutually exclusive selector outcomes without overstating baselines."""

    OPTIMAL = "optimal"
    FEASIBLE_ON_SUPPORT = "feasible_on_support"
    HEURISTIC = "heuristic"
    INFEASIBLE_ON_SUPPORT = "infeasible_on_support"
    TIMEOUT = "timeout"
    SIZE_LIMIT_EXCEEDED = "size_limit_exceeded"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


def _non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _finite_non_negative(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number")
    try:
        normalized = float(value)
    except OverflowError as error:
        raise ValueError(f"{field_name} must be finite and non-negative") from error
    if not isfinite(normalized) or normalized < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return normalized


def _id_tuple(value: object, field_name: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of IDs")
    ids = tuple(_non_negative_integer(item, f"{field_name} item") for item in value)
    if len(set(ids)) != len(ids):
        raise ValueError(f"{field_name} must not contain duplicates")
    return ids


def _non_negative_integer_tuple(value: object, field_name: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be an iterable of integers")
    return tuple(_non_negative_integer(item, f"{field_name} item") for item in value)


def _normalize_canvas(value: object) -> tuple[int | None, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("canvas must be a finite sequence of token IDs or None")
    canvas: list[int | None] = []
    for position, token_id in enumerate(value):
        if token_id is None:
            canvas.append(None)
        else:
            canvas.append(_non_negative_integer(token_id, f"canvas token at {position}"))
    if not canvas:
        raise ValueError("canvas must contain at least one physical slot")
    return tuple(canvas)


def _terminal_tuple(value: object) -> tuple[TerminalLabel, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError("witness_terminal_labels must be an iterable")
    labels: list[TerminalLabel] = []
    for label in value:
        if isinstance(label, bool) or not isinstance(label, (int, str)):
            raise TypeError("witness terminal labels must be byte integers or strings")
        if isinstance(label, int) and not 0 <= label <= 255:
            raise ValueError("integer witness terminal labels must be bytes in [0, 255]")
        if isinstance(label, str) and not label:
            raise ValueError("string witness terminal labels must be non-empty")
        labels.append(label)
    return tuple(labels)


def _freeze_json(value: object, field_name: str) -> object:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"{field_name} must not contain NaN or infinity")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{field_name} keys must be strings")
            frozen[key] = _freeze_json(item, f"{field_name}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, field_name) for item in value)
    raise TypeError(f"{field_name} must contain only JSON-compatible values")


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class SelectionInput:
    """One frozen canvas/proposal/support instance shared by all selectors."""

    grammar: CnfGrammar
    canvas: tuple[int | None, ...]
    proposals: tuple[Proposal, ...]
    support: PerPositionSupport
    tokenizer_adapter: CompositionalByteLevelAdapter
    eos_policy: EOSPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        canvas = _normalize_canvas(self.canvas)
        proposals = tuple(self.proposals)
        aggregate_proposals(proposals)
        if not isinstance(self.support, PerPositionSupport):
            raise TypeError("support must be a PerPositionSupport")
        if not isinstance(self.tokenizer_adapter, CompositionalByteLevelAdapter):
            raise TypeError("tokenizer_adapter must be a CompositionalByteLevelAdapter")
        if not isinstance(self.eos_policy, EOSPolicy):
            raise TypeError("eos_policy must be an EOSPolicy")
        if canvas != self.support.canvas:
            raise ValueError("canvas must exactly match the saved support canvas")
        if self.tokenizer_adapter.vocabulary_size != self.support.exactness_scope.vocabulary_size:
            raise ValueError("tokenizer adapter and support must have equal vocabularies")

        configured_specials = set(self.eos_policy.termination_token_ids)
        if self.eos_policy.pad_token_id is not None:
            configured_specials.add(self.eos_policy.pad_token_id)
        missing_specials = sorted(
            configured_specials - set(self.support.exactness_scope.included_special_tokens)
        )
        if missing_specials:
            raise ValueError(
                "EOS/PAD token IDs must be listed in the support exactness scope: "
                f"{missing_specials}"
            )
        if self.eos_policy.mode is EOSMode.ABSENT and configured_specials:
            raise AssertionError("validated ABSENT EOS policy unexpectedly has special IDs")

        # Reuse the public finite-support boundary to validate proposal IDs,
        # positions, token IDs, fixed positions, and represented/unrepresented
        # proposal accounting without executing either selector.
        build_token_lattice(support=self.support, proposals=proposals)
        object.__setattr__(self, "canvas", canvas)
        object.__setattr__(self, "proposals", proposals)


def validate_ordinary_primary_proposal_comparison(selection_input: SelectionInput) -> None:
    """Enforce the shared ordinary-candidate universe used by Q2 comparisons."""

    if not isinstance(selection_input, SelectionInput):
        raise TypeError("selection_input must be a SelectionInput")
    positions = tuple(proposal.position for proposal in selection_input.proposals)
    if len(set(positions)) != len(positions):
        raise ValueError("common comparison requires at most one primary proposal per position")
    special_ids = set(selection_input.eos_policy.termination_token_ids)
    if selection_input.eos_policy.pad_token_id is not None:
        special_ids.add(selection_input.eos_policy.pad_token_id)
    for proposal in selection_input.proposals:
        if selection_input.canvas[proposal.position] is not None:
            raise ValueError("common comparison proposals must target masked positions")
        if proposal.token_id not in selection_input.support.rows[proposal.position]:
            raise ValueError("common comparison proposals must be represented in support")
        if proposal.token_id in special_ids:
            raise ValueError("ordinary proposal comparison excludes EOS/PAD side effects")
        if proposal.model_confidence is None:
            raise ValueError("common comparison proposals must retain model_confidence")


@dataclass(frozen=True, slots=True)
class SelectionResult:
    """Comparable output shared by exact and non-optimal baseline selectors."""

    selector: SelectorKind
    status: SelectionStatus
    exactness_scope: ExactnessScope
    runtime_seconds: float
    selected_proposal_ids: tuple[int, ...] = ()
    score: float | None = None
    witness_token_ids: tuple[int, ...] = ()
    witness_terminal_labels: tuple[TerminalLabel, ...] = ()
    witness_graph_edge_ids: tuple[int, ...] = ()
    witness_eos_position: int | None = None
    witness_content_endpoint_slot: int | None = None
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.selector, SelectorKind):
            raise TypeError("selector must be a SelectorKind")
        if not isinstance(self.status, SelectionStatus):
            raise TypeError("status must be a SelectionStatus")
        if not isinstance(self.exactness_scope, ExactnessScope):
            raise TypeError("exactness_scope must be an ExactnessScope")
        object.__setattr__(
            self,
            "runtime_seconds",
            _finite_non_negative(self.runtime_seconds, "runtime_seconds"),
        )

        selected_ids = _id_tuple(self.selected_proposal_ids, "selected_proposal_ids")
        token_ids = _non_negative_integer_tuple(
            self.witness_token_ids,
            "witness_token_ids",
        )
        terminal_labels = _terminal_tuple(self.witness_terminal_labels)
        graph_edge_ids = _id_tuple(self.witness_graph_edge_ids, "witness_graph_edge_ids")
        score = None if self.score is None else _finite_non_negative(self.score, "score")
        eos_position = self.witness_eos_position
        if eos_position is not None:
            eos_position = _non_negative_integer(eos_position, "witness_eos_position")
        content_endpoint = self.witness_content_endpoint_slot
        if content_endpoint is not None:
            content_endpoint = _non_negative_integer(
                content_endpoint,
                "witness_content_endpoint_slot",
            )

        frozen = _freeze_json(self.diagnostics, "diagnostics")
        if not isinstance(frozen, Mapping):
            raise TypeError("diagnostics must be a mapping")
        object.__setattr__(self, "selected_proposal_ids", selected_ids)
        object.__setattr__(self, "score", score)
        object.__setattr__(self, "witness_token_ids", token_ids)
        object.__setattr__(self, "witness_terminal_labels", terminal_labels)
        object.__setattr__(self, "witness_graph_edge_ids", graph_edge_ids)
        object.__setattr__(self, "witness_eos_position", eos_position)
        object.__setattr__(self, "witness_content_endpoint_slot", content_endpoint)
        object.__setattr__(self, "diagnostics", frozen)

        has_graph_witness = bool(graph_edge_ids)
        has_token_witness = bool(token_ids)
        has_witness = has_token_witness or has_graph_witness
        has_witness_metadata = any(
            (
                bool(terminal_labels),
                has_graph_witness,
                eos_position is not None,
                content_endpoint is not None,
            )
        )
        if has_witness_metadata and not has_witness:
            raise ValueError("witness metadata requires a token or graph witness")
        if (eos_position is not None or content_endpoint is not None) and not has_token_witness:
            raise ValueError("finite-slot witness metadata requires witness_token_ids")
        if self.status is SelectionStatus.OPTIMAL:
            if score is None or not has_witness:
                raise ValueError("OPTIMAL requires a score and reconstructible witness")
            if self.selector is not SelectorKind.BRUTE_FORCE and not has_token_witness:
                raise ValueError("non-oracle OPTIMAL results require a witness token sequence")
        elif self.status in {
            SelectionStatus.FEASIBLE_ON_SUPPORT,
            SelectionStatus.HEURISTIC,
        }:
            if score is None:
                raise ValueError("successful baseline results require a recomputed score")
        elif any(
            (
                score is not None,
                bool(selected_ids),
                bool(token_ids),
                has_witness_metadata,
            )
        ):
            raise ValueError("inconclusive/non-feasible results cannot expose a score or witness")

    @property
    def witness_available(self) -> bool:
        """Whether this selector returned a token or terminal-graph witness."""

        return self.token_witness_available or self.graph_witness_available

    @property
    def token_witness_available(self) -> bool:
        """Whether a finite physical-token completion is available."""

        return bool(self.witness_token_ids)

    @property
    def graph_witness_available(self) -> bool:
        """Whether a stable terminal-graph edge path is available."""

        return bool(self.witness_graph_edge_ids)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible result for later benchmark schemas."""

        return {
            "selector": self.selector.value,
            "status": self.status.value,
            "selected_proposal_ids": list(self.selected_proposal_ids),
            "score": self.score,
            "runtime_seconds": self.runtime_seconds,
            "witness_available": self.witness_available,
            "token_witness_available": self.token_witness_available,
            "graph_witness_available": self.graph_witness_available,
            "witness_token_ids": list(self.witness_token_ids),
            "witness_terminal_labels": list(self.witness_terminal_labels),
            "witness_graph_edge_ids": list(self.witness_graph_edge_ids),
            "witness_eos_position": self.witness_eos_position,
            "witness_content_endpoint_slot": self.witness_content_endpoint_slot,
            "exactness_scope": self.exactness_scope.to_dict(),
            "diagnostics": _thaw_json(self.diagnostics),
        }


def recompute_witness_selection(
    selection_input: SelectionInput,
    witness_token_ids: Sequence[int],
) -> tuple[tuple[int, ...], float]:
    """Recompute positive proposal matches and score from a finite witness."""

    if not isinstance(selection_input, SelectionInput):
        raise TypeError("selection_input must be a SelectionInput")
    if isinstance(witness_token_ids, (str, bytes)) or not isinstance(
        witness_token_ids,
        Sequence,
    ):
        raise TypeError("witness_token_ids must be a finite sequence")
    token_ids = tuple(
        _non_negative_integer(token_id, f"witness token at {position}")
        for position, token_id in enumerate(witness_token_ids)
    )
    if len(token_ids) != len(selection_input.canvas):
        raise ValueError("witness and canvas must contain the same number of physical slots")
    for position, (token_id, fixed_token, row) in enumerate(
        zip(
            token_ids,
            selection_input.canvas,
            selection_input.support.rows,
            strict=True,
        )
    ):
        if fixed_token is not None and token_id != fixed_token:
            raise ValueError(f"witness changes fixed canvas position {position}")
        if token_id not in row:
            raise ValueError(f"witness token at position {position} is outside saved support")

    matched = tuple(
        proposal
        for proposal in selection_input.proposals
        if proposal.weight > 0.0 and token_ids[proposal.position] == proposal.token_id
    )
    try:
        score = fsum(proposal.weight for proposal in matched)
    except OverflowError as error:
        raise ValueError("recomputed witness score must be finite") from error
    if not isfinite(score):
        raise ValueError("recomputed witness score must be finite")
    return tuple(proposal.proposal_id for proposal in matched), score


def _selection_status(status: SolveStatus) -> SelectionStatus:
    return SelectionStatus(status.value)


def _failure_result(
    *,
    selector: SelectorKind,
    result: ExactCommitResult,
    runtime_seconds: float,
    diagnostics: Mapping[str, object],
) -> SelectionResult:
    if result.status is SolveStatus.OPTIMAL:
        raise ValueError("failure conversion requires a non-optimal exact result")
    return SelectionResult(
        selector=selector,
        status=_selection_status(result.status),
        exactness_scope=result.exactness_scope,
        runtime_seconds=runtime_seconds,
        diagnostics=diagnostics,
    )


def select_exact_mwpc(
    selection_input: SelectionInput,
    *,
    backend: ExactBackend = ExactBackend.RUST,
    timeout_seconds: float | None = None,
    deadline_check_interval: int = 1_024,
    deterministic_work_limit: int | None = None,
) -> SelectionResult:
    """Run MWPC optimization through the common frozen-instance interface."""

    if not isinstance(selection_input, SelectionInput):
        raise TypeError("selection_input must be a SelectionInput")
    started = perf_counter()
    result = solve_exact_commit(
        selection_input.grammar,
        canvas=selection_input.canvas,
        support=selection_input.support,
        proposals=selection_input.proposals,
        tokenizer_adapter=selection_input.tokenizer_adapter,
        eos_policy=selection_input.eos_policy,
        backend=backend,
        timeout_seconds=timeout_seconds,
        deadline_check_interval=deadline_check_interval,
        deterministic_work_limit=deterministic_work_limit,
    )
    if result.status is not SolveStatus.OPTIMAL:
        return _failure_result(
            selector=SelectorKind.EXACT_MWPC,
            result=result,
            runtime_seconds=perf_counter() - started,
            diagnostics={"solver_diagnostics": result.diagnostics},
        )

    selected_ids, score = recompute_witness_selection(
        selection_input,
        result.witness_token_ids,
    )
    if set(selected_ids) != set(result.selected_proposal_ids) or not isclose(
        score,
        result.objective_value if result.objective_value is not None else -1.0,
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        return SelectionResult(
            selector=SelectorKind.EXACT_MWPC,
            status=SelectionStatus.ERROR,
            exactness_scope=result.exactness_scope,
            runtime_seconds=perf_counter() - started,
            diagnostics={
                "error_stage": "common_result_validation",
                "error_message": "exact result disagrees with independent witness scoring",
                "reported_selected_proposal_ids": list(result.selected_proposal_ids),
                "recomputed_selected_proposal_ids": list(selected_ids),
                "reported_score": result.objective_value,
                "recomputed_score": score,
            },
        )

    return SelectionResult(
        selector=SelectorKind.EXACT_MWPC,
        status=SelectionStatus.OPTIMAL,
        exactness_scope=result.exactness_scope,
        runtime_seconds=perf_counter() - started,
        selected_proposal_ids=selected_ids,
        score=score,
        witness_token_ids=result.witness_token_ids,
        witness_terminal_labels=result.witness_terminal_labels,
        witness_graph_edge_ids=result.witness_graph_edge_ids,
        witness_eos_position=result.witness_eos_position,
        witness_content_endpoint_slot=result.witness_content_endpoint_slot,
        diagnostics={
            "optimization_guarantee": "exact_on_support",
            "score_recomputed_from_witness": True,
            "solver_diagnostics": result.diagnostics,
        },
    )


def _restrict_support(
    support: PerPositionSupport,
    canvas: tuple[int | None, ...],
) -> PerPositionSupport:
    rows = tuple(
        original_row if token_id is None else (token_id,)
        for token_id, original_row in zip(canvas, support.rows, strict=True)
    )
    top_k_rows = tuple(
        original_row if token_id is None else ()
        for token_id, original_row in zip(
            canvas,
            support.top_k_token_ids_by_position,
            strict=True,
        )
    )
    proposal_rows = tuple(
        original_row
        if token_id is None
        else tuple(proposal_token for proposal_token in original_row if proposal_token == token_id)
        for token_id, original_row in zip(
            canvas,
            support.proposal_token_ids_by_position,
            strict=True,
        )
    )
    return replace(
        support,
        canvas=canvas,
        rows=rows,
        top_k_token_ids_by_position=top_k_rows,
        proposal_token_ids_by_position=proposal_rows,
    )


def _solve_feasibility(
    selection_input: SelectionInput,
    *,
    canvas: tuple[int | None, ...],
    backend: ExactBackend,
    timeout_seconds: float | None,
    deadline_check_interval: int,
    deterministic_work_limit: int | None,
) -> tuple[ExactCommitResult, PerPositionSupport]:
    support = _restrict_support(selection_input.support, canvas)
    result = solve_exact_commit(
        selection_input.grammar,
        canvas=canvas,
        support=support,
        proposals=(),
        tokenizer_adapter=selection_input.tokenizer_adapter,
        eos_policy=selection_input.eos_policy,
        backend=backend,
        timeout_seconds=timeout_seconds,
        deadline_check_interval=deadline_check_interval,
        deterministic_work_limit=deterministic_work_limit,
    )
    return result, support


def select_greedy_exact_feasibility(
    selection_input: SelectionInput,
    *,
    backend: ExactBackend = ExactBackend.RUST,
    total_timeout_seconds: float | None = None,
    timeout_seconds: float | None = None,
    deadline_check_interval: int = 1_024,
    deterministic_work_limit: int | None = None,
    clock: Callable[[], float] | None = None,
) -> SelectionResult:
    """Order-greedy proposal retention with a single total exact-feasibility budget."""

    if not isinstance(selection_input, SelectionInput):
        raise TypeError("selection_input must be a SelectionInput")
    if clock is None:
        clock = perf_counter
    elif not callable(clock):
        raise TypeError("clock must be callable or None")
    if timeout_seconds is not None:
        if total_timeout_seconds is not None:
            raise ValueError("use only total_timeout_seconds, not both timeout names")
        total_timeout_seconds = timeout_seconds
    if total_timeout_seconds is not None:
        if isinstance(total_timeout_seconds, bool) or not isinstance(
            total_timeout_seconds, (int, float)
        ):
            raise TypeError("total_timeout_seconds must be a real number or None")
        total_timeout_seconds = float(total_timeout_seconds)
        if not isfinite(total_timeout_seconds) or total_timeout_seconds < 0.0:
            raise ValueError("total_timeout_seconds must be finite and non-negative")

    started = clock()
    committed = list(selection_input.canvas)
    decisions: list[dict[str, object]] = []
    accepted_ids: list[int] = []
    feasibility_calls = 0

    def solve_current(
        canvas: tuple[int | None, ...],
    ) -> tuple[ExactCommitResult, PerPositionSupport]:
        nonlocal feasibility_calls
        support = _restrict_support(selection_input.support, canvas)
        remaining: float | None = None
        if total_timeout_seconds is not None:
            remaining = max(0.0, total_timeout_seconds - (clock() - started))
            if remaining <= 0.0:
                return (
                    ExactCommitResult(
                        status=SolveStatus.TIMEOUT,
                        exactness_scope=support.exactness_scope,
                        diagnostics={"timeout_stage": "before_feasibility_call"},
                    ),
                    support,
                )
        feasibility_calls += 1
        result, support = _solve_feasibility(
            selection_input,
            canvas=canvas,
            backend=backend,
            timeout_seconds=(remaining if backend is ExactBackend.RUST else None),
            deadline_check_interval=deadline_check_interval,
            deterministic_work_limit=deterministic_work_limit,
        )
        if (
            total_timeout_seconds is not None
            and clock() - started >= total_timeout_seconds
            and result.status is not SolveStatus.TIMEOUT
        ):
            result = ExactCommitResult(
                status=SolveStatus.TIMEOUT,
                exactness_scope=result.exactness_scope,
                diagnostics={
                    "timeout_stage": "after_feasibility_call",
                    "late_result_status": result.status.value,
                },
            )
        return result, support

    result, witness_support = solve_current(tuple(committed))
    if result.status is not SolveStatus.OPTIMAL:
        return _failure_result(
            selector=SelectorKind.GREEDY_EXACT_FEASIBILITY,
            result=result,
            runtime_seconds=max(0.0, clock() - started),
            diagnostics={
                "implementation": "greedy_exact_feasibility_v2",
                "optimization_guarantee": "none_order_greedy",
                "proposal_order": [proposal.proposal_id for proposal in selection_input.proposals],
                "feasibility_call_count": feasibility_calls,
                "total_timeout_seconds": total_timeout_seconds,
                "initial_feasibility_diagnostics": result.diagnostics,
            },
        )

    for proposal in selection_input.proposals:
        decision: dict[str, object] = {
            "proposal_id": proposal.proposal_id,
            "position": proposal.position,
            "token_id": proposal.token_id,
        }
        if proposal.token_id not in selection_input.support.rows[proposal.position]:
            decision.update(outcome="rejected", reason="unrepresented_on_support")
            decisions.append(decision)
            continue
        fixed_token = committed[proposal.position]
        if fixed_token is not None:
            if fixed_token == proposal.token_id:
                accepted_ids.append(proposal.proposal_id)
                decision.update(outcome="accepted", reason="already_fixed_match")
            else:
                decision.update(outcome="rejected", reason="conflicts_with_prior_commitment")
            decisions.append(decision)
            continue
        tentative = list(committed)
        tentative[proposal.position] = proposal.token_id
        tentative_result, tentative_support = solve_current(tuple(tentative))
        decision["feasibility_status"] = tentative_result.status.value
        if tentative_result.status is SolveStatus.OPTIMAL:
            committed = tentative
            result = tentative_result
            witness_support = tentative_support
            accepted_ids.append(proposal.proposal_id)
            decision.update(outcome="accepted", reason="feasible_with_prior_commitments")
            decisions.append(decision)
            continue
        if tentative_result.status is SolveStatus.INFEASIBLE_ON_SUPPORT:
            decision.update(outcome="rejected", reason="infeasible_with_prior_commitments")
            decisions.append(decision)
            continue
        decision.update(outcome="stopped", reason="inconclusive_feasibility_status")
        decisions.append(decision)
        return _failure_result(
            selector=SelectorKind.GREEDY_EXACT_FEASIBILITY,
            result=tentative_result,
            runtime_seconds=max(0.0, clock() - started),
            diagnostics={
                "implementation": "greedy_exact_feasibility_v2",
                "optimization_guarantee": "none_order_greedy",
                "proposal_order": [item.proposal_id for item in selection_input.proposals],
                "accepted_proposal_ids_before_stop": accepted_ids,
                "decisions": decisions,
                "feasibility_call_count": feasibility_calls,
                "total_timeout_seconds": total_timeout_seconds,
                "last_feasibility_diagnostics": tentative_result.diagnostics,
            },
        )

    selected_ids, score = recompute_witness_selection(selection_input, result.witness_token_ids)
    if not set(selected_ids) <= set(accepted_ids):
        return SelectionResult(
            selector=SelectorKind.GREEDY_EXACT_FEASIBILITY,
            status=SelectionStatus.ERROR,
            exactness_scope=selection_input.support.exactness_scope,
            runtime_seconds=max(0.0, clock() - started),
            diagnostics={
                "error_stage": "common_result_validation",
                "error_message": "greedy witness matches a rejected proposal",
                "accepted_proposal_ids": accepted_ids,
                "recomputed_selected_proposal_ids": list(selected_ids),
            },
        )
    return SelectionResult(
        selector=SelectorKind.GREEDY_EXACT_FEASIBILITY,
        status=SelectionStatus.FEASIBLE_ON_SUPPORT,
        exactness_scope=selection_input.support.exactness_scope,
        runtime_seconds=max(0.0, clock() - started),
        selected_proposal_ids=selected_ids,
        score=score,
        witness_token_ids=result.witness_token_ids,
        witness_terminal_labels=result.witness_terminal_labels,
        witness_graph_edge_ids=result.witness_graph_edge_ids,
        witness_eos_position=result.witness_eos_position,
        witness_content_endpoint_slot=result.witness_content_endpoint_slot,
        diagnostics={
            "implementation": "greedy_exact_feasibility_v2",
            "optimization_guarantee": "none_order_greedy",
            "feasibility_guarantee": "feasible_on_represented_support",
            "proposal_order": [proposal.proposal_id for proposal in selection_input.proposals],
            "accepted_proposal_ids": accepted_ids,
            "decisions": decisions,
            "feasibility_call_count": feasibility_calls,
            "total_timeout_seconds": total_timeout_seconds,
            "score_recomputed_from_witness": True,
            "input_support_sha256": selection_input.support.fingerprint,
            "witness_support_rows": [list(row) for row in witness_support.rows],
            "witness_support_sha256": witness_support.fingerprint,
            "final_feasibility_diagnostics": result.diagnostics,
        },
    )


# Compatibility aliases retained for version-1 callers and artifacts.
select_exact = select_exact_mwpc
select_serial = select_greedy_exact_feasibility


__all__ = [
    "SelectionInput",
    "SelectionResult",
    "SelectionStatus",
    "SelectorKind",
    "recompute_witness_selection",
    "select_exact",
    "select_exact_mwpc",
    "select_greedy_exact_feasibility",
    "select_serial",
    "validate_ordinary_primary_proposal_comparison",
]
