"""Controlled CFG-to-CNF normalization for the Python reference solver.

This implementation is intentionally independent of the pinned EPIC
normalizer. It removes epsilon and unit productions, isolates terminals in
long bodies, and binarizes deterministically while retaining original
production IDs for diagnostics.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TypeAlias

from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
)
from mwpc_exact.types import TerminalLabel


def _stable_id(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


@dataclass(frozen=True, slots=True)
class NonterminalRef:
    """A nonterminal occurrence in a source production body."""

    symbol_id: int

    def __post_init__(self) -> None:
        _stable_id(self.symbol_id, "nonterminal reference symbol_id")


@dataclass(frozen=True, slots=True)
class TerminalRef:
    """A terminal occurrence in a source production body."""

    symbol_id: int

    def __post_init__(self) -> None:
        _stable_id(self.symbol_id, "terminal reference symbol_id")


SourceSymbol: TypeAlias = NonterminalRef | TerminalRef


@dataclass(frozen=True, slots=True)
class SourceProduction:
    """One stable-ID production before CNF normalization."""

    production_id: int
    head_id: int
    body: tuple[SourceSymbol, ...] = ()

    def __post_init__(self) -> None:
        _stable_id(self.production_id, "source production_id")
        _stable_id(self.head_id, "source production head_id")
        body = tuple(self.body)
        if not all(isinstance(symbol, (NonterminalRef, TerminalRef)) for symbol in body):
            raise TypeError(
                "source production body must contain only NonterminalRef or TerminalRef"
            )
        object.__setattr__(self, "body", body)


@dataclass(frozen=True, slots=True)
class SourceGrammar:
    """A finite source CFG with explicitly typed symbol references."""

    nonterminals: tuple[Nonterminal, ...]
    terminals: tuple[Terminal, ...]
    start_nonterminal_id: int
    productions: tuple[SourceProduction, ...]

    def __post_init__(self) -> None:
        nonterminals = tuple(self.nonterminals)
        terminals = tuple(self.terminals)
        productions = tuple(self.productions)
        if not nonterminals:
            raise ValueError("source grammar requires at least one nonterminal")
        if not all(isinstance(item, Nonterminal) for item in nonterminals):
            raise TypeError("source nonterminals must contain only Nonterminal instances")
        if not all(isinstance(item, Terminal) for item in terminals):
            raise TypeError("source terminals must contain only Terminal instances")
        if not all(isinstance(item, SourceProduction) for item in productions):
            raise TypeError("productions must contain only SourceProduction instances")

        nonterminal_ids = tuple(item.symbol_id for item in nonterminals)
        terminal_ids = tuple(item.symbol_id for item in terminals)
        if len(set(nonterminal_ids)) != len(nonterminal_ids):
            raise ValueError("source nonterminal IDs must be unique")
        if len({item.name for item in nonterminals}) != len(nonterminals):
            raise ValueError("source nonterminal names must be unique")
        if len(set(terminal_ids)) != len(terminal_ids):
            raise ValueError("source terminal IDs must be unique")
        if len({item.label for item in terminals}) != len(terminals):
            raise ValueError("source terminal labels must be unique")
        if len({item.production_id for item in productions}) != len(productions):
            raise ValueError("source production IDs must be unique")

        nonterminal_set = set(nonterminal_ids)
        terminal_set = set(terminal_ids)
        start_id = _stable_id(self.start_nonterminal_id, "start_nonterminal_id")
        if start_id not in nonterminal_set:
            raise ValueError("source start symbol must reference a nonterminal")
        for production in productions:
            if production.head_id not in nonterminal_set:
                raise ValueError(f"source production {production.production_id} has unknown head")
            for symbol in production.body:
                if isinstance(symbol, NonterminalRef) and symbol.symbol_id not in nonterminal_set:
                    raise ValueError(
                        f"source production {production.production_id} references "
                        "an unknown nonterminal"
                    )
                if isinstance(symbol, TerminalRef) and symbol.symbol_id not in terminal_set:
                    raise ValueError(
                        f"source production {production.production_id} references "
                        "an unknown terminal"
                    )

        object.__setattr__(self, "nonterminals", nonterminals)
        object.__setattr__(self, "terminals", terminals)
        object.__setattr__(self, "productions", productions)


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """Normalized grammar and independently inspectable provenance metadata."""

    grammar: CnfGrammar
    normalized_to_source_production_ids: Mapping[int, tuple[int, ...]]
    synthetic_nonterminal_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.grammar, CnfGrammar):
            raise TypeError("grammar must be a CnfGrammar")
        mapping = {
            _stable_id(key, "normalized production ID"): tuple(value)
            for key, value in self.normalized_to_source_production_ids.items()
        }
        expected = _production_provenance(self.grammar)
        if mapping != expected:
            raise ValueError("normalized production provenance must match the CNF productions")
        synthetic_ids = tuple(
            _stable_id(item, "synthetic_nonterminal_ids item")
            for item in self.synthetic_nonterminal_ids
        )
        if len(set(synthetic_ids)) != len(synthetic_ids):
            raise ValueError("synthetic_nonterminal_ids must not contain duplicates")
        grammar_ids = {item.symbol_id for item in self.grammar.nonterminals}
        if not set(synthetic_ids) <= grammar_ids:
            raise ValueError("synthetic nonterminal IDs must exist in the CNF grammar")
        object.__setattr__(
            self,
            "normalized_to_source_production_ids",
            MappingProxyType(mapping),
        )
        object.__setattr__(self, "synthetic_nonterminal_ids", synthetic_ids)


RuleKey: TypeAlias = tuple[int, tuple[SourceSymbol, ...]]


def normalize_to_cnf(source: SourceGrammar) -> NormalizationResult:
    """Normalize ``source`` to strict binary/terminal CNF deterministically."""
    if not isinstance(source, SourceGrammar):
        raise TypeError("source must be a SourceGrammar")

    nullable = _nullable_nonterminals(source)
    accepts_empty = source.start_nonterminal_id in nullable
    epsilon_free = _expand_nullable_bodies(source, nullable)
    unit_free = _remove_unit_productions(source, epsilon_free)

    nonterminals = list(source.nonterminals)
    used_names = {item.name for item in nonterminals}
    next_nonterminal_id = max(item.symbol_id for item in nonterminals) + 1
    synthetic_ids: list[int] = []

    def new_nonterminal(name_hint: str) -> int:
        nonlocal next_nonterminal_id
        name = name_hint
        suffix = 1
        while name in used_names:
            name = f"{name_hint}_{suffix}"
            suffix += 1
        symbol_id = next_nonterminal_id
        next_nonterminal_id += 1
        used_names.add(name)
        nonterminals.append(Nonterminal(symbol_id, name))
        synthetic_ids.append(symbol_id)
        return symbol_id

    isolated: dict[RuleKey, list[int]] = {}
    terminal_proxy_ids: dict[int, int] = {}
    terminal_proxy_sources: dict[int, list[int]] = {}
    for (head_id, body), source_ids in unit_free.items():
        if len(body) < 2:
            _merge_rule(isolated, head_id, body, source_ids)
            continue
        rewritten: list[SourceSymbol] = []
        for symbol in body:
            if isinstance(symbol, NonterminalRef):
                rewritten.append(symbol)
                continue
            proxy_id = terminal_proxy_ids.get(symbol.symbol_id)
            if proxy_id is None:
                proxy_id = new_nonterminal(f"__mwpc_terminal_{symbol.symbol_id}")
                terminal_proxy_ids[symbol.symbol_id] = proxy_id
                terminal_proxy_sources[symbol.symbol_id] = []
            _append_unique(terminal_proxy_sources[symbol.symbol_id], source_ids)
            rewritten.append(NonterminalRef(proxy_id))
        _merge_rule(isolated, head_id, tuple(rewritten), source_ids)

    for terminal_id, proxy_id in terminal_proxy_ids.items():
        _merge_rule(
            isolated,
            proxy_id,
            (TerminalRef(terminal_id),),
            terminal_proxy_sources[terminal_id],
        )

    cnf_rules: dict[RuleKey, list[int]] = {}
    for (head_id, body), source_ids in isolated.items():
        if len(body) <= 2:
            _merge_rule(cnf_rules, head_id, body, source_ids)
            continue
        current_head = head_id
        for offset in range(len(body) - 2):
            next_head = new_nonterminal(f"__mwpc_binary_{head_id}_{len(synthetic_ids)}_{offset}")
            _merge_rule(
                cnf_rules,
                current_head,
                (body[offset], NonterminalRef(next_head)),
                source_ids,
            )
            current_head = next_head
        _merge_rule(cnf_rules, current_head, body[-2:], source_ids)

    terminal_productions: list[TerminalProduction] = []
    binary_productions: list[BinaryProduction] = []
    next_production_id = 0
    for (head_id, body), source_ids in cnf_rules.items():
        source_provenance = tuple(source_ids)
        if len(body) == 1 and isinstance(body[0], TerminalRef):
            terminal_productions.append(
                TerminalProduction(
                    production_id=next_production_id,
                    head_id=head_id,
                    terminal_id=body[0].symbol_id,
                    source_production_ids=source_provenance,
                )
            )
        elif len(body) == 2 and all(isinstance(symbol, NonterminalRef) for symbol in body):
            left, right = body
            assert isinstance(left, NonterminalRef)
            assert isinstance(right, NonterminalRef)
            binary_productions.append(
                BinaryProduction(
                    production_id=next_production_id,
                    head_id=head_id,
                    left_id=left.symbol_id,
                    right_id=right.symbol_id,
                    source_production_ids=source_provenance,
                )
            )
        else:  # internal invariant after epsilon/unit removal and isolation
            raise AssertionError(f"normalizer produced a non-CNF body: {body!r}")
        next_production_id += 1

    grammar = CnfGrammar(
        nonterminals=tuple(nonterminals),
        terminals=source.terminals,
        start_nonterminal_id=source.start_nonterminal_id,
        terminal_productions=tuple(terminal_productions),
        binary_productions=tuple(binary_productions),
        accepts_empty=accepts_empty,
    )
    normalized_provenance = _production_provenance(grammar)
    return NormalizationResult(grammar, normalized_provenance, tuple(synthetic_ids))


def enumerate_source_language(
    grammar: SourceGrammar, *, max_length: int
) -> frozenset[tuple[TerminalLabel, ...]]:
    """Enumerate a bounded source language by monotone fixed point."""
    if not isinstance(grammar, SourceGrammar):
        raise TypeError("grammar must be a SourceGrammar")
    limit = _length_limit(max_length)
    labels = {item.symbol_id: item.label for item in grammar.terminals}
    language: dict[int, set[tuple[TerminalLabel, ...]]] = {
        item.symbol_id: set() for item in grammar.nonterminals
    }
    changed = True
    while changed:
        changed = False
        for production in grammar.productions:
            words: set[tuple[TerminalLabel, ...]] = {()}
            for symbol in production.body:
                fragments = (
                    {(labels[symbol.symbol_id],)}
                    if isinstance(symbol, TerminalRef)
                    else language[symbol.symbol_id]
                )
                words = _bounded_concatenation(words, fragments, limit)
                if not words:
                    break
            before = len(language[production.head_id])
            language[production.head_id].update(words)
            changed = changed or len(language[production.head_id]) != before
    return frozenset(language[grammar.start_nonterminal_id])


def enumerate_cnf_language(
    grammar: CnfGrammar, *, max_length: int
) -> frozenset[tuple[TerminalLabel, ...]]:
    """Independently enumerate the bounded language of normalized CNF."""
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    limit = _length_limit(max_length)
    labels = grammar.terminal_labels
    language: dict[int, set[tuple[TerminalLabel, ...]]] = {
        item.symbol_id: set() for item in grammar.nonterminals
    }
    for terminal_production in grammar.terminal_productions:
        if limit >= 1:
            language[terminal_production.head_id].add((labels[terminal_production.terminal_id],))
    changed = True
    while changed:
        changed = False
        for binary_production in grammar.binary_productions:
            generated = _bounded_concatenation(
                language[binary_production.left_id],
                language[binary_production.right_id],
                limit,
            )
            before = len(language[binary_production.head_id])
            language[binary_production.head_id].update(generated)
            changed = changed or len(language[binary_production.head_id]) != before
    result = set(language[grammar.start_nonterminal_id])
    if grammar.accepts_empty:
        result.add(())
    return frozenset(result)


def _nullable_nonterminals(source: SourceGrammar) -> set[int]:
    nullable: set[int] = set()
    changed = True
    while changed:
        changed = False
        for production in source.productions:
            if production.head_id in nullable:
                continue
            if all(
                isinstance(symbol, NonterminalRef) and symbol.symbol_id in nullable
                for symbol in production.body
            ):
                nullable.add(production.head_id)
                changed = True
    return nullable


def _production_provenance(grammar: CnfGrammar) -> dict[int, tuple[int, ...]]:
    result = {
        production.production_id: production.source_production_ids
        for production in grammar.terminal_productions
    }
    result.update(
        {
            production.production_id: production.source_production_ids
            for production in grammar.binary_productions
        }
    )
    return result


def _expand_nullable_bodies(source: SourceGrammar, nullable: set[int]) -> dict[RuleKey, list[int]]:
    rules: dict[RuleKey, list[int]] = {}
    for production in source.productions:
        bodies: list[tuple[SourceSymbol, ...]] = [()]
        for symbol in production.body:
            extended = [(*body, symbol) for body in bodies]
            if isinstance(symbol, NonterminalRef) and symbol.symbol_id in nullable:
                bodies = [*extended, *bodies]
            else:
                bodies = extended
        for body in bodies:
            if body:
                _merge_rule(
                    rules,
                    production.head_id,
                    body,
                    (production.production_id,),
                )
    return rules


def _remove_unit_productions(
    source: SourceGrammar, rules: dict[RuleKey, list[int]]
) -> dict[RuleKey, list[int]]:
    units_by_head: dict[int, list[tuple[int, tuple[int, ...]]]] = {
        item.symbol_id: [] for item in source.nonterminals
    }
    nonunits_by_head: dict[int, list[tuple[tuple[SourceSymbol, ...], tuple[int, ...]]]] = {
        item.symbol_id: [] for item in source.nonterminals
    }
    for (head_id, body), source_ids in rules.items():
        if len(body) == 1 and isinstance(body[0], NonterminalRef):
            units_by_head[head_id].append((body[0].symbol_id, tuple(source_ids)))
        else:
            nonunits_by_head[head_id].append((body, tuple(source_ids)))

    result: dict[RuleKey, list[int]] = {}
    for nonterminal in source.nonterminals:
        paths: dict[int, tuple[int, ...]] = {nonterminal.symbol_id: ()}
        queue = deque((nonterminal.symbol_id,))
        while queue:
            current = queue.popleft()
            for target, edge_sources in units_by_head[current]:
                if target in paths:
                    continue
                paths[target] = _unique_tuple((*paths[current], *edge_sources))
                queue.append(target)
        for reachable_id, path_sources in paths.items():
            for body, body_sources in nonunits_by_head[reachable_id]:
                _merge_rule(
                    result,
                    nonterminal.symbol_id,
                    body,
                    (*path_sources, *body_sources),
                )
    return result


def _merge_rule(
    rules: dict[RuleKey, list[int]],
    head_id: int,
    body: tuple[SourceSymbol, ...],
    source_ids: Iterable[int],
) -> None:
    target = rules.setdefault((head_id, body), [])
    _append_unique(target, source_ids)


def _append_unique(target: list[int], values: Iterable[int]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _unique_tuple(values: Iterable[int]) -> tuple[int, ...]:
    result: list[int] = []
    _append_unique(result, values)
    return tuple(result)


def _length_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("max_length must be an integer")
    if value < 0:
        raise ValueError("max_length must be non-negative")
    return value


def _bounded_concatenation(
    left: Iterable[tuple[TerminalLabel, ...]],
    right: Iterable[tuple[TerminalLabel, ...]],
    limit: int,
) -> set[tuple[TerminalLabel, ...]]:
    return {
        (*left_word, *right_word)
        for left_word in left
        for right_word in right
        if len(left_word) + len(right_word) <= limit
    }
