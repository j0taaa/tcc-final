"""Independent exhaustive oracles for tiny finite MWPC instances."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from math import fsum, prod

from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_exact.types import Proposal, SolveStatus, TerminalLabel


class SearchSpaceLimitExceeded(ValueError):
    """An exhaustive oracle was asked to exceed its explicit finite guard."""

    def __init__(self, *, search_space_size: int, maximum: int) -> None:
        self.search_space_size = search_space_size
        self.maximum = maximum
        super().__init__(f"exhaustive search space {search_space_size} exceeds maximum {maximum}")


@dataclass(frozen=True, slots=True)
class CompletionOptimum:
    """One grammar-valid optimum discovered by direct enumeration."""

    objective_value: float
    selected_proposal_ids: tuple[int, ...]
    witness_token_ids: tuple[int, ...]
    witness_terminal_labels: tuple[TerminalLabel, ...]


@dataclass(frozen=True, slots=True)
class CompletionOracleResult:
    """Structured exhaustive-completion outcome and enumeration accounting."""

    status: SolveStatus
    objective_value: float | None
    optima: tuple[CompletionOptimum, ...]
    search_space_size: int
    enumerated_completions: int
    fixed_compatible_completions: int
    grammar_valid_completions: int

    def __post_init__(self) -> None:
        if self.status not in {
            SolveStatus.OPTIMAL,
            SolveStatus.INFEASIBLE_ON_SUPPORT,
        }:
            raise ValueError("completion oracle status must be OPTIMAL or INFEASIBLE_ON_SUPPORT")
        if self.status is SolveStatus.OPTIMAL:
            if self.objective_value is None or not self.optima:
                raise ValueError("OPTIMAL completion oracle result requires optima")
            if any(item.objective_value != self.objective_value for item in self.optima):
                raise ValueError("all returned completion optima must have the best objective")
        elif self.objective_value is not None or self.optima:
            raise ValueError("infeasible completion result cannot expose optima")
        counts = (
            self.search_space_size,
            self.enumerated_completions,
            self.fixed_compatible_completions,
            self.grammar_valid_completions,
        )
        if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in counts):
            raise ValueError("completion enumeration counts must be non-negative integers")
        if not (
            self.grammar_valid_completions
            <= self.fixed_compatible_completions
            <= self.enumerated_completions
            <= self.search_space_size
        ):
            raise ValueError("completion enumeration counts are inconsistent")


@dataclass(frozen=True, slots=True)
class SubsetOracleResult:
    """Best compatible proposal subset and one existence witness."""

    status: SolveStatus
    objective_value: float | None
    selected_proposal_ids: tuple[int, ...]
    witness_token_ids: tuple[int, ...]
    witness_terminal_labels: tuple[TerminalLabel, ...]
    subset_search_space_size: int
    enumerated_subsets: int
    grammar_valid_completions: int

    def __post_init__(self) -> None:
        if self.status not in {
            SolveStatus.OPTIMAL,
            SolveStatus.INFEASIBLE_ON_SUPPORT,
        }:
            raise ValueError("subset oracle status must be OPTIMAL or INFEASIBLE_ON_SUPPORT")
        if self.status is SolveStatus.OPTIMAL:
            if self.objective_value is None:
                raise ValueError("OPTIMAL subset result requires an objective")
            if len(self.witness_token_ids) != len(self.witness_terminal_labels):
                raise ValueError("subset witness token and terminal lengths must match")
        elif any(
            (
                self.objective_value is not None,
                bool(self.selected_proposal_ids),
                bool(self.witness_token_ids),
                bool(self.witness_terminal_labels),
            )
        ):
            raise ValueError("infeasible subset result cannot expose an optimum witness")
        counts = (
            self.subset_search_space_size,
            self.enumerated_subsets,
            self.grammar_valid_completions,
        )
        if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in counts):
            raise ValueError("subset oracle counts must be non-negative integers")
        if self.enumerated_subsets > self.subset_search_space_size:
            raise ValueError("enumerated subset count exceeds the search space")


def exhaustive_completion_oracle(
    *,
    grammar: CnfGrammar,
    per_position_support: Sequence[Sequence[int]],
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    terminal_labels_by_token_id: Mapping[int, TerminalLabel],
    return_all_optima: bool = False,
    max_completions: int = 1_000_000,
) -> CompletionOracleResult:
    """Enumerate and directly score every represented token completion."""
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    supports = _supports(per_position_support)
    canvas_tokens = _canvas(canvas)
    if len(supports) != len(canvas_tokens):
        raise ValueError("canvas and per-position support must have equal length")
    if not isinstance(return_all_optima, bool):
        raise TypeError("return_all_optima must be a bool")
    maximum = _positive_int(max_completions, "max_completions")
    labels_by_token = _terminal_mapping(grammar, terminal_labels_by_token_id, supports)
    proposal_items = _proposals(proposals, len(supports))

    search_space_size = prod(len(support) for support in supports)
    if search_space_size > maximum:
        raise SearchSpaceLimitExceeded(
            search_space_size=search_space_size,
            maximum=maximum,
        )

    enumerated = 0
    fixed_compatible = 0
    grammar_valid = 0
    best_score: float | None = None
    best: list[CompletionOptimum] = []
    for completion in product(*supports):
        enumerated += 1
        if any(
            fixed_token_id is not None and completion[position] != fixed_token_id
            for position, fixed_token_id in enumerate(canvas_tokens)
        ):
            continue
        fixed_compatible += 1
        terminal_labels = tuple(labels_by_token[token_id] for token_id in completion)
        if not recognizes_cnf(grammar, terminal_labels):
            continue
        grammar_valid += 1
        matched = tuple(
            proposal
            for proposal in proposal_items
            if proposal.weight > 0 and completion[proposal.position] == proposal.token_id
        )
        try:
            score = fsum(proposal.weight for proposal in matched)
        except OverflowError as exc:
            raise ValueError("completion objective overflowed finite float range") from exc
        optimum = CompletionOptimum(
            objective_value=score,
            selected_proposal_ids=tuple(proposal.proposal_id for proposal in matched),
            witness_token_ids=completion,
            witness_terminal_labels=terminal_labels,
        )
        if best_score is None or score > best_score:
            best_score = score
            best = [optimum]
        elif score == best_score and return_all_optima:
            best.append(optimum)

    if best_score is None:
        return CompletionOracleResult(
            status=SolveStatus.INFEASIBLE_ON_SUPPORT,
            objective_value=None,
            optima=(),
            search_space_size=search_space_size,
            enumerated_completions=enumerated,
            fixed_compatible_completions=fixed_compatible,
            grammar_valid_completions=grammar_valid,
        )
    return CompletionOracleResult(
        status=SolveStatus.OPTIMAL,
        objective_value=best_score,
        optima=tuple(best),
        search_space_size=search_space_size,
        enumerated_completions=enumerated,
        fixed_compatible_completions=fixed_compatible,
        grammar_valid_completions=grammar_valid,
    )


def exhaustive_subset_oracle(
    *,
    grammar: CnfGrammar,
    per_position_support: Sequence[Sequence[int]],
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    terminal_labels_by_token_id: Mapping[int, TerminalLabel],
    max_subsets: int = 1_048_576,
    max_completions: int = 1_000_000,
) -> SubsetOracleResult:
    """Enumerate proposal subsets and test each by completion existence.

    This does not call :func:`exhaustive_completion_oracle`; proposal-subset
    scoring and compatibility search are separate loops so their agreement is
    a meaningful correctness check.
    """
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    supports = _supports(per_position_support)
    canvas_tokens = _canvas(canvas)
    if len(supports) != len(canvas_tokens):
        raise ValueError("canvas and per-position support must have equal length")
    labels_by_token = _terminal_mapping(grammar, terminal_labels_by_token_id, supports)
    proposal_items = _proposals(proposals, len(supports))
    subset_maximum = _positive_int(max_subsets, "max_subsets")
    completion_maximum = _positive_int(max_completions, "max_completions")

    subset_search_space_size = 1 << len(proposal_items)
    if subset_search_space_size > subset_maximum:
        raise SearchSpaceLimitExceeded(
            search_space_size=subset_search_space_size,
            maximum=subset_maximum,
        )
    completion_search_space_size = prod(len(support) for support in supports)
    if completion_search_space_size > completion_maximum:
        raise SearchSpaceLimitExceeded(
            search_space_size=completion_search_space_size,
            maximum=completion_maximum,
        )

    valid_completions: list[tuple[tuple[int, ...], tuple[TerminalLabel, ...]]] = []
    for completion in product(*supports):
        if any(
            fixed_token_id is not None and completion[position] != fixed_token_id
            for position, fixed_token_id in enumerate(canvas_tokens)
        ):
            continue
        terminal_labels = tuple(labels_by_token[token_id] for token_id in completion)
        if recognizes_cnf(grammar, terminal_labels):
            valid_completions.append((completion, terminal_labels))

    if not valid_completions:
        return SubsetOracleResult(
            status=SolveStatus.INFEASIBLE_ON_SUPPORT,
            objective_value=None,
            selected_proposal_ids=(),
            witness_token_ids=(),
            witness_terminal_labels=(),
            subset_search_space_size=subset_search_space_size,
            enumerated_subsets=0,
            grammar_valid_completions=0,
        )

    best_score: float | None = None
    best_subset: tuple[Proposal, ...] = ()
    best_witness: tuple[int, ...] = ()
    best_labels: tuple[TerminalLabel, ...] = ()
    enumerated_subsets = 0
    for mask in range(subset_search_space_size):
        enumerated_subsets += 1
        subset = tuple(
            proposal for index, proposal in enumerate(proposal_items) if mask & (1 << index)
        )
        witness = next(
            (
                (completion, terminal_labels)
                for completion, terminal_labels in valid_completions
                if all(completion[proposal.position] == proposal.token_id for proposal in subset)
            ),
            None,
        )
        if witness is None:
            continue
        try:
            score = fsum(proposal.weight for proposal in subset)
        except OverflowError as exc:
            raise ValueError("subset objective overflowed finite float range") from exc
        if best_score is None or score > best_score:
            best_score = score
            best_subset = subset
            best_witness, best_labels = witness

    if best_score is None:
        raise AssertionError("empty proposal subset must match every valid completion")
    positive_subset = tuple(proposal for proposal in best_subset if proposal.weight > 0)
    matched_positive = tuple(
        proposal
        for proposal in proposal_items
        if proposal.weight > 0 and best_witness[proposal.position] == proposal.token_id
    )
    matched_score = fsum(proposal.weight for proposal in matched_positive)
    if matched_score != best_score or {item.proposal_id for item in matched_positive} != {
        item.proposal_id for item in positive_subset
    }:
        raise AssertionError(
            "best subset is not closed under positive proposals matched by its witness"
        )
    return SubsetOracleResult(
        status=SolveStatus.OPTIMAL,
        objective_value=best_score,
        selected_proposal_ids=tuple(item.proposal_id for item in positive_subset),
        witness_token_ids=best_witness,
        witness_terminal_labels=best_labels,
        subset_search_space_size=subset_search_space_size,
        enumerated_subsets=enumerated_subsets,
        grammar_valid_completions=len(valid_completions),
    )


def _supports(value: object) -> tuple[tuple[int, ...], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("per_position_support must be a finite sequence")
    result: list[tuple[int, ...]] = []
    for position, raw_support in enumerate(value):
        if isinstance(raw_support, (str, bytes)) or not isinstance(raw_support, Sequence):
            raise TypeError(f"support at position {position} must be a finite sequence")
        support = tuple(
            _token_id(token_id, f"support token at position {position}") for token_id in raw_support
        )
        if len(set(support)) != len(support):
            raise ValueError(f"support at position {position} contains duplicate token IDs")
        result.append(support)
    return tuple(result)


def _canvas(value: object) -> tuple[int | None, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("canvas must be a finite sequence")
    return tuple(
        None if item is None else _token_id(item, f"canvas token at position {position}")
        for position, item in enumerate(value)
    )


def _terminal_mapping(
    grammar: CnfGrammar,
    value: object,
    supports: tuple[tuple[int, ...], ...],
) -> dict[int, TerminalLabel]:
    if not isinstance(value, Mapping):
        raise TypeError("terminal_labels_by_token_id must be a mapping")
    result: dict[int, TerminalLabel] = {}
    grammar_labels = set(grammar.terminal_labels.values())
    for raw_token_id, label in value.items():
        token_id = _token_id(raw_token_id, "terminal mapping token ID")
        if isinstance(label, bool) or not isinstance(label, (int, str)):
            raise TypeError("mapped terminal labels must be byte integers or strings")
        if isinstance(label, int) and not 0 <= label <= 255:
            raise ValueError("integer terminal labels must be bytes in [0, 255]")
        if isinstance(label, str) and not label:
            raise ValueError("string terminal labels must be non-empty")
        if label not in grammar_labels:
            raise ValueError(f"mapped terminal label {label!r} is absent from the grammar")
        result[token_id] = label
    if len(set(result.values())) != len(result):
        raise ValueError("token-aligned terminal labels must be unique")
    support_tokens = {token_id for support in supports for token_id in support}
    missing = support_tokens - set(result)
    if missing:
        raise ValueError(f"terminal mapping is missing support token IDs: {sorted(missing)}")
    return result


def _proposals(value: Iterable[Proposal], slot_count: int) -> tuple[Proposal, ...]:
    result = tuple(value)
    if not all(isinstance(item, Proposal) for item in result):
        raise TypeError("proposals must contain only Proposal instances")
    seen_ids: set[int] = set()
    for proposal in result:
        if proposal.proposal_id in seen_ids:
            raise ValueError(f"duplicate proposal_id: {proposal.proposal_id}")
        seen_ids.add(proposal.proposal_id)
        if proposal.position >= slot_count:
            raise ValueError(
                f"proposal {proposal.proposal_id} position is outside the finite support"
            )
    return result


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _token_id(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value
