"""Lexical MWPC rewards for a finite token-aligned canvas."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import inf, isfinite
from types import MappingProxyType

from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.types import Proposal, aggregate_proposals

NEGATIVE_INFINITY = -inf


def _token_id(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


@dataclass(frozen=True, slots=True)
class LexicalReward:
    """One terminal choice's score and positive-weight proposal provenance."""

    score: float
    matched_proposal_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise TypeError("lexical score must be a real number")
        normalized = float(self.score)
        if normalized != NEGATIVE_INFINITY and (not isfinite(normalized) or normalized < 0):
            raise ValueError("lexical score must be non-negative finite or negative infinity")
        proposal_ids = tuple(self.matched_proposal_ids)
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in proposal_ids
        ):
            raise ValueError("matched proposal IDs must be non-negative integers")
        if len(set(proposal_ids)) != len(proposal_ids):
            raise ValueError("matched proposal IDs must not contain duplicates")
        if normalized == NEGATIVE_INFINITY and proposal_ids:
            raise ValueError("a conflicting lexical choice cannot match proposals")
        object.__setattr__(self, "score", normalized)
        object.__setattr__(self, "matched_proposal_ids", proposal_ids)


@dataclass(frozen=True, slots=True)
class LexicalRewardTable:
    """Immutable dense position-by-terminal max-plus initialization table."""

    rows: tuple[Mapping[int, LexicalReward], ...]
    terminal_token_ids: Mapping[int, int]

    def __post_init__(self) -> None:
        rows = tuple(self.rows)
        terminal_token_ids = dict(self.terminal_token_ids)
        normalized_mapping: dict[int, int] = {}
        for terminal_id, token_id in terminal_token_ids.items():
            normalized_mapping[_token_id(terminal_id, "terminal symbol ID")] = _token_id(
                token_id, "terminal token ID"
            )
        if len(set(normalized_mapping.values())) != len(normalized_mapping):
            raise ValueError("token-aligned terminal token IDs must be unique")
        expected_ids = set(normalized_mapping)
        frozen_rows: list[Mapping[int, LexicalReward]] = []
        for position, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise TypeError(f"lexical row {position} must be a mapping")
            normalized_row = dict(row)
            if set(normalized_row) != expected_ids:
                raise ValueError(f"lexical row {position} must contain exactly every terminal ID")
            if not all(isinstance(cell, LexicalReward) for cell in normalized_row.values()):
                raise TypeError("lexical rows must contain only LexicalReward values")
            frozen_rows.append(MappingProxyType(normalized_row))
        object.__setattr__(self, "rows", tuple(frozen_rows))
        object.__setattr__(self, "terminal_token_ids", MappingProxyType(normalized_mapping))

    @property
    def slot_count(self) -> int:
        return len(self.rows)

    def reward(self, position: int, terminal_id: int) -> LexicalReward:
        """Return one checked lexical cell."""
        if isinstance(position, bool) or not isinstance(position, int):
            raise TypeError("position must be an integer")
        if not 0 <= position < self.slot_count:
            raise IndexError("position is outside the lexical table")
        try:
            return self.rows[position][terminal_id]
        except KeyError as exc:
            raise KeyError(f"unknown terminal ID: {terminal_id}") from exc


def build_lexical_rewards(
    *,
    grammar: CnfGrammar,
    canvas: Sequence[int | None],
    proposals: Iterable[Proposal],
    terminal_token_ids: Mapping[int, int] | None = None,
) -> LexicalRewardTable:
    """Construct the exact token-aligned lexical objective.

    When ``terminal_token_ids`` is omitted, every grammar terminal label must
    already be an integer token ID. A supplied map must cover exactly the
    grammar's terminal symbol IDs.
    """
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    canvas_tokens = _canvas(canvas)
    proposal_items = tuple(proposals)
    if not all(isinstance(item, Proposal) for item in proposal_items):
        raise TypeError("proposals must contain only Proposal instances")
    for proposal in proposal_items:
        if proposal.position >= len(canvas_tokens):
            raise ValueError(
                f"proposal {proposal.proposal_id} position is outside the finite canvas"
            )

    mapping = _terminal_token_mapping(grammar, terminal_token_ids)
    aggregated = aggregate_proposals(proposal_items)
    reward_by_choice = {(item.position, item.token_id): item.weight for item in aggregated}
    positive_ids_by_choice: dict[tuple[int, int], list[int]] = {}
    for proposal in proposal_items:
        if proposal.weight > 0:
            positive_ids_by_choice.setdefault((proposal.position, proposal.token_id), []).append(
                proposal.proposal_id
            )

    rows: list[Mapping[int, LexicalReward]] = []
    for position, fixed_token_id in enumerate(canvas_tokens):
        row: dict[int, LexicalReward] = {}
        for terminal in grammar.terminals:
            token_id = mapping[terminal.symbol_id]
            if fixed_token_id is not None and token_id != fixed_token_id:
                row[terminal.symbol_id] = LexicalReward(NEGATIVE_INFINITY)
                continue
            choice = (position, token_id)
            row[terminal.symbol_id] = LexicalReward(
                score=reward_by_choice.get(choice, 0.0),
                matched_proposal_ids=tuple(positive_ids_by_choice.get(choice, ())),
            )
        rows.append(row)
    return LexicalRewardTable(tuple(rows), mapping)


def _canvas(value: object) -> tuple[int | None, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("canvas must be a finite sequence of token IDs or None")
    result: list[int | None] = []
    for position, item in enumerate(value):
        if item is None:
            result.append(None)
        else:
            result.append(_token_id(item, f"canvas token at position {position}"))
    return tuple(result)


def _terminal_token_mapping(
    grammar: CnfGrammar, supplied: Mapping[int, int] | None
) -> dict[int, int]:
    terminal_ids = {item.symbol_id for item in grammar.terminals}
    if supplied is None:
        result: dict[int, int] = {}
        for terminal in grammar.terminals:
            if isinstance(terminal.label, bool) or not isinstance(terminal.label, int):
                raise ValueError(
                    "terminal_token_ids is required when terminal labels are not token IDs"
                )
            result[terminal.symbol_id] = _token_id(terminal.label, "integer terminal label")
    else:
        if not isinstance(supplied, Mapping):
            raise TypeError("terminal_token_ids must be a mapping")
        result = {
            _token_id(key, "terminal symbol ID"): _token_id(token_id, "terminal token ID")
            for key, token_id in supplied.items()
        }
    if set(result) != terminal_ids:
        missing = terminal_ids - set(result)
        extra = set(result) - terminal_ids
        raise ValueError(
            "terminal_token_ids must cover exactly the grammar terminals "
            f"(missing={sorted(missing)}, extra={sorted(extra)})"
        )
    if len(set(result.values())) != len(result):
        raise ValueError("token-aligned terminal token IDs must be unique")
    return result
