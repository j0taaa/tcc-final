"""Independent validation for public exact-commit certificates.

This module deliberately does not import or call a weighted parser. It
recomputes certificate facts from public inputs and accepts independent
boolean recognizers through small protocols.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from functools import partial
from math import fsum, isclose, isfinite
from types import MappingProxyType
from typing import Protocol

from mwpc_exact.types import (
    ExactCommitResult,
    ExactnessScope,
    Proposal,
    SolveStatus,
    TerminalLabel,
    WeightedTerminalDAG,
)


class GrammarRecognizer(Protocol):
    """Independent boolean recognizer over a completed terminal sequence."""

    def __call__(self, terminal_labels: tuple[TerminalLabel, ...], /) -> bool: ...


class TokenizerWitnessValidator(Protocol):
    """Validate that witness token IDs produce the recorded terminals."""

    def __call__(
        self,
        token_ids: tuple[int, ...],
        terminal_labels: tuple[TerminalLabel, ...],
        /,
    ) -> bool: ...


class EOSWitnessValidator(Protocol):
    """Validate finite-slot EOS/PAD behavior for witness token IDs."""

    def __call__(self, token_ids: tuple[int, ...], /) -> bool: ...


class ValidationCode(StrEnum):
    """Stable categories for independently detected certificate failures."""

    RESULT_NOT_OPTIMAL = "result_not_optimal"
    SCOPE_MISMATCH = "scope_mismatch"
    SLOT_COUNT_MISMATCH = "slot_count_mismatch"
    FIXED_POSITION_MISMATCH = "fixed_position_mismatch"
    DUPLICATE_PROPOSAL_ID = "duplicate_proposal_id"
    PROPOSAL_POSITION_OUT_OF_RANGE = "proposal_position_out_of_range"
    SELECTED_PROPOSALS_MISMATCH = "selected_proposals_mismatch"
    OBJECTIVE_MISMATCH = "objective_mismatch"
    UNKNOWN_GRAPH_EDGE = "unknown_graph_edge"
    EDGE_CONTINUITY = "edge_continuity"
    TERMINAL_LABEL_MISMATCH = "terminal_label_mismatch"
    PATH_FINAL_STATE = "path_final_state"
    GRAMMAR_REJECTED = "grammar_rejected"
    TOKENIZER_REJECTED = "tokenizer_rejected"
    EOS_REJECTED = "eos_rejected"
    INJECTED_VALIDATOR_ERROR = "injected_validator_error"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One serializable certificate failure with local context."""

    code: ValidationCode
    message: str
    context: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.message:
            raise ValueError("validation issue message must be non-empty")
        if not isinstance(self.context, Mapping):
            raise TypeError("validation issue context must be a mapping")
        if not all(isinstance(key, str) for key in self.context):
            raise TypeError("validation issue context keys must be strings")
        object.__setattr__(self, "context", MappingProxyType(dict(self.context)))

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "message": self.message,
            "context": dict(self.context),
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Structured result of independent certificate validation."""

    issues: tuple[ValidationIssue, ...]
    skipped_checks: tuple[str, ...]
    recomputed_objective: float | None
    recomputed_selected_proposal_ids: tuple[int, ...]

    @property
    def is_valid(self) -> bool:
        """True only when every required injected check ran and no issue exists."""
        return not self.issues and not self.skipped_checks

    def to_dict(self) -> dict[str, object]:
        return {
            "is_valid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
            "skipped_checks": list(self.skipped_checks),
            "recomputed_objective": self.recomputed_objective,
            "recomputed_selected_proposal_ids": list(
                self.recomputed_selected_proposal_ids
            ),
        }


def _validate_canvas(canvas: Sequence[int | None]) -> tuple[int | None, ...]:
    if isinstance(canvas, (str, bytes)) or not isinstance(canvas, Sequence):
        raise TypeError("canvas must be a finite sequence of token IDs or None")
    normalized: list[int | None] = []
    for position, token_id in enumerate(canvas):
        if token_id is None:
            normalized.append(None)
            continue
        if isinstance(token_id, bool) or not isinstance(token_id, int):
            raise TypeError(f"canvas token at position {position} must be an integer or None")
        if token_id < 0:
            raise ValueError(f"canvas token at position {position} must be non-negative")
        normalized.append(token_id)
    return tuple(normalized)


def _issue(
    issues: list[ValidationIssue],
    code: ValidationCode,
    message: str,
    **context: object,
) -> None:
    issues.append(ValidationIssue(code=code, message=message, context=context))


def _run_injected_check(
    *,
    name: str,
    call: Callable[[], object] | None,
    rejected_code: ValidationCode,
    issues: list[ValidationIssue],
    skipped: list[str],
) -> None:
    if call is None:
        skipped.append(name)
        return
    try:
        outcome = call()
    except Exception as exc:  # injected boundary must become structured evidence
        _issue(
            issues,
            ValidationCode.INJECTED_VALIDATOR_ERROR,
            f"{name} validator raised an exception",
            validator=name,
            exception_type=type(exc).__name__,
            exception_message=str(exc),
        )
        return
    if not isinstance(outcome, bool):
        _issue(
            issues,
            ValidationCode.INJECTED_VALIDATOR_ERROR,
            f"{name} validator did not return bool",
            validator=name,
            returned_type=type(outcome).__name__,
        )
    elif not outcome:
        _issue(issues, rejected_code, f"{name} validator rejected the witness")


def validate_exact_commit_certificate(
    result: ExactCommitResult,
    *,
    expected_scope: ExactnessScope,
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    graph: WeightedTerminalDAG,
    grammar_recognizer: GrammarRecognizer | None = None,
    tokenizer_validator: TokenizerWitnessValidator | None = None,
    eos_validator: EOSWitnessValidator | None = None,
    objective_tolerance: float = 1e-12,
) -> ValidationReport:
    """Validate one certificate without trusting weighted-parser internals."""
    if not isinstance(result, ExactCommitResult):
        raise TypeError("result must be an ExactCommitResult")
    if not isinstance(expected_scope, ExactnessScope):
        raise TypeError("expected_scope must be an ExactnessScope")
    if not isinstance(graph, WeightedTerminalDAG):
        raise TypeError("graph must be a WeightedTerminalDAG")
    if (
        isinstance(objective_tolerance, bool)
        or not isinstance(objective_tolerance, (int, float))
        or not isfinite(objective_tolerance)
        or objective_tolerance < 0
    ):
        raise ValueError("objective_tolerance must be finite and non-negative")

    canvas_tokens = _validate_canvas(canvas)
    proposal_items = tuple(proposals)
    if not all(isinstance(proposal, Proposal) for proposal in proposal_items):
        raise TypeError("proposals must contain only Proposal instances")

    issues: list[ValidationIssue] = []
    skipped: list[str] = []
    if result.exactness_scope != expected_scope:
        _issue(
            issues,
            ValidationCode.SCOPE_MISMATCH,
            "result exactness scope does not match the validated input scope",
            expected=expected_scope.to_dict(),
            actual=result.exactness_scope.to_dict(),
        )

    if result.status is not SolveStatus.OPTIMAL:
        _issue(
            issues,
            ValidationCode.RESULT_NOT_OPTIMAL,
            "only OPTIMAL results carry a certificate to validate",
            status=result.status.value,
        )
        skipped.extend(("grammar", "tokenizer", "eos"))
        return ValidationReport(tuple(issues), tuple(skipped), None, ())

    witness = result.witness_token_ids
    if len(witness) != len(canvas_tokens):
        _issue(
            issues,
            ValidationCode.SLOT_COUNT_MISMATCH,
            "witness must consume exactly the physical canvas slots",
            expected_slots=len(canvas_tokens),
            actual_slots=len(witness),
        )
    for position, fixed_token_id in enumerate(canvas_tokens):
        if fixed_token_id is None or position >= len(witness):
            continue
        if witness[position] != fixed_token_id:
            _issue(
                issues,
                ValidationCode.FIXED_POSITION_MISMATCH,
                "witness changed an already committed canvas position",
                position=position,
                expected_token_id=fixed_token_id,
                actual_token_id=witness[position],
            )

    proposal_by_id: dict[int, Proposal] = {}
    for proposal in proposal_items:
        if proposal.proposal_id in proposal_by_id:
            _issue(
                issues,
                ValidationCode.DUPLICATE_PROPOSAL_ID,
                "proposal collection contains a duplicate stable ID",
                proposal_id=proposal.proposal_id,
            )
        else:
            proposal_by_id[proposal.proposal_id] = proposal
        if not 0 <= proposal.position < len(canvas_tokens):
            _issue(
                issues,
                ValidationCode.PROPOSAL_POSITION_OUT_OF_RANGE,
                "proposal position is outside the finite canvas",
                proposal_id=proposal.proposal_id,
                position=proposal.position,
                slot_count=len(canvas_tokens),
            )

    matched = tuple(
        proposal
        for proposal in proposal_items
        if proposal.weight > 0
        and 0 <= proposal.position < len(witness)
        and witness[proposal.position] == proposal.token_id
    )
    recomputed_ids = tuple(proposal.proposal_id for proposal in matched)
    recomputed_objective = fsum(proposal.weight for proposal in matched)
    if set(result.selected_proposal_ids) != set(recomputed_ids):
        _issue(
            issues,
            ValidationCode.SELECTED_PROPOSALS_MISMATCH,
            "selected proposal IDs are not exactly the positive-weight witness matches",
            expected_ids=list(recomputed_ids),
            actual_ids=list(result.selected_proposal_ids),
        )
    assert result.objective_value is not None
    if not isclose(
        result.objective_value,
        recomputed_objective,
        rel_tol=float(objective_tolerance),
        abs_tol=float(objective_tolerance),
    ):
        _issue(
            issues,
            ValidationCode.OBJECTIVE_MISMATCH,
            "objective does not equal the independently recomputed proposal sum",
            expected_objective=recomputed_objective,
            actual_objective=result.objective_value,
            tolerance=float(objective_tolerance),
        )

    edge_by_id = {edge.edge_id: edge for edge in graph.edges}
    current_state = graph.start_node_id
    path_complete = True
    for index, (edge_id, terminal_label) in enumerate(
        zip(
            result.witness_graph_edge_ids,
            result.witness_terminal_labels,
            strict=True,
        )
    ):
        edge = edge_by_id.get(edge_id)
        if edge is None:
            _issue(
                issues,
                ValidationCode.UNKNOWN_GRAPH_EDGE,
                "witness references an edge absent from the terminal graph",
                path_index=index,
                edge_id=edge_id,
            )
            path_complete = False
            continue
        if edge.source_state != current_state:
            _issue(
                issues,
                ValidationCode.EDGE_CONTINUITY,
                "witness graph edges do not form a continuous path",
                path_index=index,
                edge_id=edge_id,
                expected_source_state=current_state,
                actual_source_state=edge.source_state,
            )
            path_complete = False
        current_state = edge.target_state
        if edge.terminal_label != terminal_label:
            _issue(
                issues,
                ValidationCode.TERMINAL_LABEL_MISMATCH,
                "witness terminal label does not match its graph edge",
                path_index=index,
                edge_id=edge_id,
                expected_label=edge.terminal_label,
                actual_label=terminal_label,
            )
    if path_complete and current_state not in graph.final_node_ids:
        _issue(
            issues,
            ValidationCode.PATH_FINAL_STATE,
            "witness graph path does not end at a final state",
            actual_state=current_state,
            final_states=list(graph.final_node_ids),
        )

    _run_injected_check(
        name="grammar",
        call=(
            None
            if grammar_recognizer is None
            else partial(grammar_recognizer, result.witness_terminal_labels)
        ),
        rejected_code=ValidationCode.GRAMMAR_REJECTED,
        issues=issues,
        skipped=skipped,
    )
    _run_injected_check(
        name="tokenizer",
        call=(
            None
            if tokenizer_validator is None
            else partial(
                tokenizer_validator,
                result.witness_token_ids,
                result.witness_terminal_labels,
            )
        ),
        rejected_code=ValidationCode.TOKENIZER_REJECTED,
        issues=issues,
        skipped=skipped,
    )
    _run_injected_check(
        name="eos",
        call=(
            None
            if eos_validator is None
            else partial(eos_validator, result.witness_token_ids)
        ),
        rejected_code=ValidationCode.EOS_REJECTED,
        issues=issues,
        skipped=skipped,
    )

    return ValidationReport(
        issues=tuple(issues),
        skipped_checks=tuple(skipped),
        recomputed_objective=recomputed_objective,
        recomputed_selected_proposal_ids=recomputed_ids,
    )
