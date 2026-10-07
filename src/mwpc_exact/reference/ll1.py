"""Check a sufficient, decidable unambiguity condition; never trust a flag."""

from __future__ import annotations

from mwpc_exact.reference.limits import WorkBudget
from mwpc_exact.reference.normalization import (
    NonterminalRef,
    SourceGrammar,
    SourceSymbol,
    TerminalRef,
)


class UnsupportedGrammar(ValueError):
    """Valid grammar outside the checked LL(1) sampling contract."""


def check_ll1(source: SourceGrammar, *, budget: WorkBudget | None = None) -> None:
    """Reject prediction conflicts, nullable left cycles and non-byte terminals.

    This certifies source-grammar unambiguity, not arbitrary CFG unambiguity.
    EOF is -1, outside the non-negative terminal-ID space.
    """
    if not isinstance(source, SourceGrammar):
        raise TypeError("source must be a SourceGrammar")
    budget = budget if budget is not None else WorkBudget()
    for terminal in source.terminals:
        budget.consume()
        if type(terminal.label) is not int or not 0 <= terminal.label <= 255:
            raise UnsupportedGrammar("sampling requires literal byte terminals")
    first: dict[int, set[int]] = {}
    for n in source.nonterminals:
        budget.consume()
        first[n.symbol_id] = set()
    nullable: set[int] = set()

    def prefix(body: tuple[SourceSymbol, ...]) -> tuple[set[int], bool]:
        result: set[int] = set()
        for symbol in body:
            budget.consume()
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
            budget.consume()
            labels, empty = prefix(rule.body)
            before = len(first[rule.head_id])
            first[rule.head_id].update(labels)
            changed |= len(first[rule.head_id]) != before
            if empty and rule.head_id not in nullable:
                nullable.add(rule.head_id)
                changed = True

    budget.consume(len(source.nonterminals))
    follow: dict[int, set[int]] = {n.symbol_id: set() for n in source.nonterminals}
    follow[source.start_nonterminal_id].add(-1)
    changed = True
    while changed:
        changed = False
        for rule in source.productions:
            budget.consume()
            for i, symbol in enumerate(rule.body):
                budget.consume(1 + len(rule.body) - i)
                if isinstance(symbol, NonterminalRef):
                    labels, empty = prefix(rule.body[i + 1 :])
                    if empty:
                        labels.update(follow[rule.head_id])
                    before = len(follow[symbol.symbol_id])
                    follow[symbol.symbol_id].update(labels)
                    changed |= len(follow[symbol.symbol_id]) != before

    predictions: dict[tuple[int, int], int] = {}
    budget.consume(len(source.nonterminals))
    corners: dict[int, set[int]] = {n.symbol_id: set() for n in source.nonterminals}
    for rule in source.productions:
        budget.consume()
        labels, empty = prefix(rule.body)
        if empty:
            labels.update(follow[rule.head_id])
        if not labels:
            raise UnsupportedGrammar(f"production {rule.production_id} has no prediction")
        for label in labels:
            budget.consume()
            key = rule.head_id, label
            if key in predictions:
                raise UnsupportedGrammar(
                    f"LL(1) conflict: productions {predictions[key]} and {rule.production_id}"
                )
            predictions[key] = rule.production_id
        for symbol in rule.body:
            budget.consume()
            if isinstance(symbol, TerminalRef):
                break
            corners[rule.head_id].add(symbol.symbol_id)
            if symbol.symbol_id not in nullable:
                break

    pending = set(corners)
    while pending:
        budget.consume(sum(1 + len(corners[n]) for n in pending))
        leaves = {n for n in pending if not corners[n] & pending}
        if not leaves:
            raise UnsupportedGrammar("nullable left recursion")
        pending.difference_update(leaves)
