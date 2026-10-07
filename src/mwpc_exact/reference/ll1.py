"""Check a sufficient, decidable unambiguity condition; never trust a flag."""

from __future__ import annotations

from mwpc_exact.reference.normalization import (
    NonterminalRef,
    SourceGrammar,
    SourceSymbol,
    TerminalRef,
)


class UnsupportedGrammar(ValueError):
    """Valid grammar outside the checked LL(1) sampling contract."""


def check_ll1(source: SourceGrammar) -> None:
    """Reject prediction conflicts, nullable left cycles and non-byte terminals.

    This certifies source-grammar unambiguity, not arbitrary CFG unambiguity.
    EOF is -1, outside the non-negative terminal-ID space.
    """
    if not isinstance(source, SourceGrammar):
        raise TypeError("source must be a SourceGrammar")
    if any(type(t.label) is not int for t in source.terminals):
        raise UnsupportedGrammar("sampling requires literal byte terminals")
    first: dict[int, set[int]] = {n.symbol_id: set() for n in source.nonterminals}
    nullable: set[int] = set()

    def prefix(body: tuple[SourceSymbol, ...]) -> tuple[set[int], bool]:
        result: set[int] = set()
        for symbol in body:
            if isinstance(symbol, TerminalRef):
                result.add(symbol.symbol_id)
                return result, False
            result.update(first[symbol.symbol_id])
            if symbol.symbol_id not in nullable:
                return result, False
        return result, True

    changed = True
    while changed:
        changed = False
        for rule in source.productions:
            labels, empty = prefix(rule.body)
            before = len(first[rule.head_id])
            first[rule.head_id].update(labels)
            changed |= len(first[rule.head_id]) != before
            if empty and rule.head_id not in nullable:
                nullable.add(rule.head_id)
                changed = True

    follow: dict[int, set[int]] = {n.symbol_id: set() for n in source.nonterminals}
    follow[source.start_nonterminal_id].add(-1)
    changed = True
    while changed:
        changed = False
        for rule in source.productions:
            for i, symbol in enumerate(rule.body):
                if isinstance(symbol, NonterminalRef):
                    labels, empty = prefix(rule.body[i + 1 :])
                    if empty:
                        labels.update(follow[rule.head_id])
                    before = len(follow[symbol.symbol_id])
                    follow[symbol.symbol_id].update(labels)
                    changed |= len(follow[symbol.symbol_id]) != before

    predictions: dict[tuple[int, int], int] = {}
    corners: dict[int, set[int]] = {n.symbol_id: set() for n in source.nonterminals}
    for rule in source.productions:
        labels, empty = prefix(rule.body)
        if empty:
            labels.update(follow[rule.head_id])
        if not labels:
            raise UnsupportedGrammar(f"production {rule.production_id} has no prediction")
        for label in labels:
            key = rule.head_id, label
            if key in predictions:
                raise UnsupportedGrammar(
                    f"LL(1) conflict: productions {predictions[key]} and {rule.production_id}"
                )
            predictions[key] = rule.production_id
        for symbol in rule.body:
            if isinstance(symbol, TerminalRef):
                break
            corners[rule.head_id].add(symbol.symbol_id)
            if symbol.symbol_id not in nullable:
                break

    pending = set(corners)
    while pending:
        leaves = {n for n in pending if not corners[n] & pending}
        if not leaves:
            raise UnsupportedGrammar("nullable left recursion")
        pending.difference_update(leaves)
