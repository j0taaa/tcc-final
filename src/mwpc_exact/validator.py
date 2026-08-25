"""Independent validation for public exact-commit certificates.

This module deliberately does not import or call a weighted parser. It
recomputes certificate facts from public inputs and accepts independent
boolean recognizers through small protocols.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from functools import partial
from math import fsum, isclose, isfinite
from types import MappingProxyType
from typing import Protocol

from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import (
    ExactCommitResult,
    ExactnessScope,
    Proposal,
    SolveStatus,
    TerminalEdge,
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


class SupportWitnessValidator(Protocol):
    """Validate membership in the represented finite token support."""

    def __call__(self, token_ids: tuple[int, ...], /) -> bool: ...


class EOSWitnessValidator(Protocol):
    """Legacy boolean EOS hook used when no structured EOS policy is supplied."""

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
    SUPPORT_REJECTED = "support_rejected"
    EOS_REJECTED = "eos_rejected"
    EOS_TOKEN_ID_OUT_OF_RANGE = "eos_token_id_out_of_range"
    EOS_PAD_BEFORE_TERMINATION = "eos_pad_before_termination"
    EOS_UNSUPPORTED_CONTROL = "eos_unsupported_control"
    EOS_TOKEN_AFTER_TERMINATION = "eos_token_after_termination"
    EOS_REQUIRED_MISSING = "eos_required_missing"
    EOS_POSITION_MISMATCH = "eos_position_mismatch"
    CONTENT_ENDPOINT_MISMATCH = "content_endpoint_mismatch"
    EFFECTIVE_TERMINAL_SEQUENCE_MISMATCH = "effective_terminal_sequence_mismatch"
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


    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ValidationReport:
        """Reconstruct a typed report from its JSON-compatible representation."""

        if not isinstance(data, Mapping):
            raise TypeError("validation report data must be a mapping")
        raw_issues = data.get("issues", ())
        if isinstance(raw_issues, (str, bytes)) or not isinstance(raw_issues, Sequence):
            raise TypeError("validation report issues must be a finite sequence")
        issues: list[ValidationIssue] = []
        for index, raw_issue in enumerate(raw_issues):
            if not isinstance(raw_issue, Mapping):
                raise TypeError(f"validation issue {index} must be a mapping")
            raw_code = raw_issue.get("code")
            raw_message = raw_issue.get("message")
            raw_context = raw_issue.get("context", {})
            if not isinstance(raw_code, str):
                raise TypeError(f"validation issue {index} code must be a string")
            if not isinstance(raw_message, str):
                raise TypeError(f"validation issue {index} message must be a string")
            if not isinstance(raw_context, Mapping):
                raise TypeError(f"validation issue {index} context must be a mapping")
            try:
                code = ValidationCode(raw_code)
            except ValueError as exc:
                raise ValueError(f"unknown validation issue code: {raw_code!r}") from exc
            issues.append(ValidationIssue(code=code, message=raw_message, context=raw_context))

        raw_skipped = data.get("skipped_checks", ())
        if isinstance(raw_skipped, (str, bytes)) or not isinstance(raw_skipped, Sequence):
            raise TypeError("skipped_checks must be a finite sequence")
        skipped = tuple(raw_skipped)
        if not all(isinstance(item, str) and item for item in skipped):
            raise TypeError("skipped_checks must contain non-empty strings")

        raw_objective = data.get("recomputed_objective")
        if raw_objective is None:
            objective = None
        elif isinstance(raw_objective, bool) or not isinstance(raw_objective, (int, float)):
            raise TypeError("recomputed_objective must be a real number or None")
        else:
            objective = float(raw_objective)
            if not isfinite(objective):
                raise ValueError("recomputed_objective must be finite")

        raw_ids = data.get("recomputed_selected_proposal_ids", ())
        if isinstance(raw_ids, (str, bytes)) or not isinstance(raw_ids, Sequence):
            raise TypeError("recomputed_selected_proposal_ids must be a finite sequence")
        recomputed_ids: list[int] = []
        for item in raw_ids:
            if isinstance(item, bool) or not isinstance(item, int) or item < 0:
                raise ValueError("recomputed selected proposal IDs must be non-negative integers")
            recomputed_ids.append(item)

        report = cls(
            issues=tuple(issues),
            skipped_checks=skipped,
            recomputed_objective=objective,
            recomputed_selected_proposal_ids=tuple(recomputed_ids),
        )
        declared_valid = data.get("is_valid")
        if declared_valid is not None:
            if not isinstance(declared_valid, bool):
                raise TypeError("is_valid must be a boolean when provided")
            if declared_valid is not report.is_valid:
                raise ValueError("serialized is_valid disagrees with reconstructed report")
        return report


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


def _validate_eos_policy_configuration(
    *,
    expected_scope: ExactnessScope,
    eos_policy: EOSPolicy | None,
    eos_adapter: CompositionalByteLevelAdapter | None,
    eos_validator: EOSWitnessValidator | None,
) -> None:
    if eos_policy is not None and not isinstance(eos_policy, EOSPolicy):
        raise TypeError("eos_policy must be an EOSPolicy or None")
    if eos_adapter is not None and not isinstance(
        eos_adapter,
        CompositionalByteLevelAdapter,
    ):
        raise TypeError("eos_adapter must be a CompositionalByteLevelAdapter or None")
    if (eos_policy is None) != (eos_adapter is None):
        raise ValueError("eos_policy and eos_adapter must be supplied together")
    if eos_policy is not None and eos_validator is not None:
        raise ValueError("structured eos_policy and legacy eos_validator are mutually exclusive")
    if eos_adapter is None or eos_policy is None:
        return
    if eos_adapter.vocabulary_size != expected_scope.vocabulary_size:
        raise ValueError("EOS tokenizer adapter and exactness scope must have equal vocabularies")
    special_ids = (*eos_policy.termination_token_ids, eos_policy.pad_token_id)
    if any(
        token_id is not None and token_id >= eos_adapter.vocabulary_size
        for token_id in special_ids
    ):
        raise ValueError("EOS policy token IDs must belong to the tokenizer vocabulary")


def _validate_finite_eos_policy(
    *,
    result: ExactCommitResult,
    canvas_tokens: tuple[int | None, ...],
    policy: EOSPolicy,
    adapter: CompositionalByteLevelAdapter,
    issues: list[ValidationIssue],
) -> None:
    """Recompute finite-slot EOS roles and effective bytes without lattice state."""

    after_eos = False
    eos_position: int | None = None
    effective_bytes = bytearray()
    special_mode = policy.mode is not EOSMode.ABSENT

    for position, token_id in enumerate(result.witness_token_ids):
        if token_id >= adapter.vocabulary_size:
            _issue(
                issues,
                ValidationCode.EOS_TOKEN_ID_OUT_OF_RANGE,
                "witness token is outside the EOS policy tokenizer vocabulary",
                position=position,
                token_id=token_id,
                vocabulary_size=adapter.vocabulary_size,
            )
            continue

        if after_eos:
            if token_id != policy.pad_token_id:
                _issue(
                    issues,
                    ValidationCode.EOS_TOKEN_AFTER_TERMINATION,
                    "only the canonical PAD token is legal after EOS",
                    position=position,
                    eos_position=eos_position,
                    expected_pad_token_id=policy.pad_token_id,
                    actual_token_id=token_id,
                )
            continue

        if special_mode and token_id in policy.termination_token_ids:
            eos_position = position
            after_eos = True
            continue

        if special_mode and token_id == policy.pad_token_id:
            _issue(
                issues,
                ValidationCode.EOS_PAD_BEFORE_TERMINATION,
                "canonical PAD is illegal before the first termination token",
                position=position,
                pad_token_id=policy.pad_token_id,
            )
            continue

        emission = adapter.emissions[token_id]
        if emission is None:
            _issue(
                issues,
                ValidationCode.EOS_UNSUPPORTED_CONTROL,
                "unsupported control token is neither ordinary content nor legal EOS/PAD",
                position=position,
                token_id=token_id,
                eos_mode=policy.mode.value,
            )
            continue
        effective_bytes.extend(emission)

    if policy.mode is EOSMode.REQUIRED and eos_position is None:
        _issue(
            issues,
            ValidationCode.EOS_REQUIRED_MISSING,
            "REQUIRED EOS policy needs one termination token within the physical slots",
            termination_token_ids=list(policy.termination_token_ids),
            physical_slot_count=len(canvas_tokens),
        )

    content_endpoint = len(canvas_tokens) if eos_position is None else eos_position
    if result.witness_eos_position != eos_position:
        _issue(
            issues,
            ValidationCode.EOS_POSITION_MISMATCH,
            "reported EOS position does not equal the first termination token position",
            expected_eos_position=eos_position,
            actual_eos_position=result.witness_eos_position,
        )
    if result.witness_content_endpoint_slot != content_endpoint:
        _issue(
            issues,
            ValidationCode.CONTENT_ENDPOINT_MISMATCH,
            "reported content endpoint does not match the finite-slot EOS policy",
            expected_content_endpoint_slot=content_endpoint,
            actual_content_endpoint_slot=result.witness_content_endpoint_slot,
        )

    expected_labels = tuple(effective_bytes)
    if result.witness_terminal_labels != expected_labels:
        _issue(
            issues,
            ValidationCode.EFFECTIVE_TERMINAL_SEQUENCE_MISMATCH,
            "witness terminal sequence is not the ordinary-token bytes before EOS",
            expected_terminal_labels=list(expected_labels),
            actual_terminal_labels=list(result.witness_terminal_labels),
            content_endpoint_slot=content_endpoint,
        )


def validate_exact_commit_certificate(
    result: ExactCommitResult,
    *,
    expected_scope: ExactnessScope,
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    graph: WeightedTerminalDAG,
    grammar_recognizer: GrammarRecognizer | None = None,
    tokenizer_validator: TokenizerWitnessValidator | None = None,
    support_validator: SupportWitnessValidator | None = None,
    eos_validator: EOSWitnessValidator | None = None,
    eos_policy: EOSPolicy | None = None,
    eos_adapter: CompositionalByteLevelAdapter | None = None,
    objective_tolerance: float = 1e-12,
) -> ValidationReport:
    """Validate one certificate without trusting weighted-parser internals."""
    if not isinstance(result, ExactCommitResult):
        raise TypeError("result must be an ExactCommitResult")
    if not isinstance(expected_scope, ExactnessScope):
        raise TypeError("expected_scope must be an ExactnessScope")
    if not isinstance(graph, WeightedTerminalDAG):
        raise TypeError("graph must be a WeightedTerminalDAG")
    _validate_eos_policy_configuration(
        expected_scope=expected_scope,
        eos_policy=eos_policy,
        eos_adapter=eos_adapter,
        eos_validator=eos_validator,
    )
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
    if Counter(result.selected_proposal_ids) != Counter(recomputed_ids):
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
    terminal_index = 0
    for path_index, edge_id in enumerate(result.witness_graph_edge_ids):
        edge = edge_by_id.get(edge_id)
        if edge is None:
            _issue(
                issues,
                ValidationCode.UNKNOWN_GRAPH_EDGE,
                "witness references an edge absent from the terminal graph",
                path_index=path_index,
                edge_id=edge_id,
            )
            path_complete = False
            continue
        if edge.source_state != current_state:
            _issue(
                issues,
                ValidationCode.EDGE_CONTINUITY,
                "witness graph edges do not form a continuous path",
                path_index=path_index,
                edge_id=edge_id,
                expected_source_state=current_state,
                actual_source_state=edge.source_state,
            )
            path_complete = False
        current_state = edge.target_state
        if not isinstance(edge, TerminalEdge):
            continue
        if terminal_index >= len(result.witness_terminal_labels):
            _issue(
                issues,
                ValidationCode.TERMINAL_LABEL_MISMATCH,
                "terminal graph edge has no corresponding witness terminal label",
                path_index=path_index,
                terminal_index=terminal_index,
                edge_id=edge_id,
                expected_label=edge.terminal_label,
            )
            path_complete = False
        else:
            terminal_label = result.witness_terminal_labels[terminal_index]
            if edge.terminal_label != terminal_label:
                _issue(
                    issues,
                    ValidationCode.TERMINAL_LABEL_MISMATCH,
                    "witness terminal label does not match its terminal graph edge",
                    path_index=path_index,
                    terminal_index=terminal_index,
                    edge_id=edge_id,
                    expected_label=edge.terminal_label,
                    actual_label=terminal_label,
                )
        terminal_index += 1
    if terminal_index < len(result.witness_terminal_labels):
        _issue(
            issues,
            ValidationCode.TERMINAL_LABEL_MISMATCH,
            "witness contains terminal labels without corresponding terminal graph edges",
            expected_terminal_count=terminal_index,
            actual_terminal_count=len(result.witness_terminal_labels),
            extra_terminal_labels=list(result.witness_terminal_labels[terminal_index:]),
        )
        path_complete = False
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
    if tokenizer_validator is not None:
        _run_injected_check(
            name="tokenizer",
            call=partial(
                tokenizer_validator,
                result.witness_token_ids,
                result.witness_terminal_labels,
            ),
            rejected_code=ValidationCode.TOKENIZER_REJECTED,
            issues=issues,
            skipped=skipped,
        )
    elif eos_policy is None:
        skipped.append("tokenizer")
    if support_validator is not None:
        _run_injected_check(
            name="support",
            call=partial(support_validator, result.witness_token_ids),
            rejected_code=ValidationCode.SUPPORT_REJECTED,
            issues=issues,
            skipped=skipped,
        )
    if eos_policy is not None and eos_adapter is not None:
        _validate_finite_eos_policy(
            result=result,
            canvas_tokens=canvas_tokens,
            policy=eos_policy,
            adapter=eos_adapter,
            issues=issues,
        )
    else:
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
