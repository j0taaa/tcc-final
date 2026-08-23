"""Token-aligned max-plus CKY reference implementation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import TypeAlias

from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.lexical import NEGATIVE_INFINITY, LexicalRewardTable
from mwpc_exact.types import SolveStatus


@dataclass(frozen=True, slots=True)
class EmptyBackpointer:
    """The explicit empty witness accepted by a zero-slot grammar."""


@dataclass(frozen=True, slots=True)
class TerminalBackpointer:
    """A terminal production selected for a unit-width span."""

    production_id: int
    terminal_id: int


@dataclass(frozen=True, slots=True)
class BinaryBackpointer:
    """A binary production and split selected for a wider span."""

    production_id: int
    split: int
    left_nonterminal_id: int
    right_nonterminal_id: int


CkyBackpointer: TypeAlias = EmptyBackpointer | TerminalBackpointer | BinaryBackpointer
ChartKey: TypeAlias = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class ChartEntry:
    """Best known max-plus value and its reconstructible decision."""

    score: float
    backpointer: CkyBackpointer

    def __post_init__(self) -> None:
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise TypeError("chart score must be a real number")
        normalized = float(self.score)
        if not isfinite(normalized) or normalized < 0:
            raise ValueError("stored chart scores must be finite and non-negative")
        if not isinstance(
            self.backpointer,
            (EmptyBackpointer, TerminalBackpointer, BinaryBackpointer),
        ):
            raise TypeError("invalid CKY backpointer type")
        object.__setattr__(self, "score", normalized)


@dataclass(frozen=True, slots=True)
class CkyChart:
    """Immutable sparse chart for one grammar and lexical table."""

    grammar: CnfGrammar
    lexical_rewards: LexicalRewardTable
    entries: Mapping[ChartKey, ChartEntry]

    def __post_init__(self) -> None:
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        if not isinstance(self.lexical_rewards, LexicalRewardTable):
            raise TypeError("lexical_rewards must be a LexicalRewardTable")
        entries = dict(self.entries)
        nonterminal_ids = {item.symbol_id for item in self.grammar.nonterminals}
        slot_count = self.lexical_rewards.slot_count
        for key, entry in entries.items():
            if (
                not isinstance(key, tuple)
                or len(key) != 3
                or any(isinstance(item, bool) or not isinstance(item, int) for item in key)
            ):
                raise TypeError("chart keys must be (nonterminal_id, start, end) integers")
            nonterminal_id, start, end = key
            if nonterminal_id not in nonterminal_ids:
                raise ValueError("chart key references an unknown nonterminal")
            if not 0 <= start <= end <= slot_count:
                raise ValueError("chart key span is outside the finite canvas")
            if not isinstance(entry, ChartEntry):
                raise TypeError("chart values must be ChartEntry instances")
        object.__setattr__(self, "entries", MappingProxyType(entries))

    @property
    def root_key(self) -> ChartKey:
        return (
            self.grammar.start_nonterminal_id,
            0,
            self.lexical_rewards.slot_count,
        )

    @property
    def root_entry(self) -> ChartEntry | None:
        return self.entries.get(self.root_key)

    def entry(self, nonterminal_id: int, start: int, end: int) -> ChartEntry | None:
        """Look up one sparse chart entry."""
        return self.entries.get((nonterminal_id, start, end))


@dataclass(frozen=True, slots=True)
class CkySolve:
    """Internal CKY outcome before public certificate reconstruction."""

    status: SolveStatus
    chart: CkyChart

    def __post_init__(self) -> None:
        if self.status not in {
            SolveStatus.OPTIMAL,
            SolveStatus.INFEASIBLE_ON_SUPPORT,
        }:
            raise ValueError("CKY outcome must be OPTIMAL or INFEASIBLE_ON_SUPPORT")
        if not isinstance(self.chart, CkyChart):
            raise TypeError("chart must be a CkyChart")
        if (self.chart.root_entry is not None) != (self.status is SolveStatus.OPTIMAL):
            raise ValueError("CKY status must agree with start-symbol chart reachability")


def run_cky(grammar: CnfGrammar, lexical_rewards: LexicalRewardTable) -> CkySolve:
    """Run deterministic max-plus CKY over exactly the finite lexical rows."""
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    if not isinstance(lexical_rewards, LexicalRewardTable):
        raise TypeError("lexical_rewards must be a LexicalRewardTable")
    grammar_terminal_ids = {item.symbol_id for item in grammar.terminals}
    if set(lexical_rewards.terminal_token_ids) != grammar_terminal_ids:
        raise ValueError("lexical terminal IDs do not match the grammar")

    entries: dict[ChartKey, ChartEntry] = {}
    slot_count = lexical_rewards.slot_count
    terminal_productions = sorted(grammar.terminal_productions, key=lambda item: item.production_id)
    binary_productions = sorted(grammar.binary_productions, key=lambda item: item.production_id)

    for position in range(slot_count):
        for terminal_production in terminal_productions:
            lexical = lexical_rewards.reward(position, terminal_production.terminal_id)
            if lexical.score == NEGATIVE_INFINITY:
                continue
            _stable_update(
                entries,
                (terminal_production.head_id, position, position + 1),
                lexical.score,
                TerminalBackpointer(
                    terminal_production.production_id,
                    terminal_production.terminal_id,
                ),
            )

    for span_width in range(2, slot_count + 1):
        for start in range(0, slot_count - span_width + 1):
            end = start + span_width
            for binary_production in binary_productions:
                for split in range(start + 1, end):
                    left = entries.get((binary_production.left_id, start, split))
                    if left is None:
                        continue
                    right = entries.get((binary_production.right_id, split, end))
                    if right is None:
                        continue
                    candidate = left.score + right.score
                    if not isfinite(candidate):
                        raise ValueError("CKY objective overflowed finite float range")
                    _stable_update(
                        entries,
                        (binary_production.head_id, start, end),
                        candidate,
                        BinaryBackpointer(
                            production_id=binary_production.production_id,
                            split=split,
                            left_nonterminal_id=binary_production.left_id,
                            right_nonterminal_id=binary_production.right_id,
                        ),
                    )

    if slot_count == 0 and grammar.accepts_empty:
        entries[(grammar.start_nonterminal_id, 0, 0)] = ChartEntry(
            score=0.0,
            backpointer=EmptyBackpointer(),
        )

    chart = CkyChart(grammar, lexical_rewards, entries)
    status = (
        SolveStatus.OPTIMAL if chart.root_entry is not None else SolveStatus.INFEASIBLE_ON_SUPPORT
    )
    return CkySolve(status, chart)


def _stable_update(
    entries: dict[ChartKey, ChartEntry],
    key: ChartKey,
    candidate_score: float,
    backpointer: CkyBackpointer,
) -> None:
    existing = entries.get(key)
    if existing is None or candidate_score > existing.score:
        entries[key] = ChartEntry(candidate_score, backpointer)
