"""Independent Boolean recognizer for strict CNF grammars."""

from __future__ import annotations

from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.types import TerminalLabel


def recognizes_cnf(grammar: CnfGrammar, terminal_labels: tuple[TerminalLabel, ...]) -> bool:
    """Return whether ``grammar`` accepts exactly ``terminal_labels``.

    This recognizer stores only Boolean reachability. It does not import the
    weighted CKY chart or trust its scores and backpointers.
    """
    if not isinstance(grammar, CnfGrammar):
        raise TypeError("grammar must be a CnfGrammar")
    if not isinstance(terminal_labels, tuple):
        raise TypeError("terminal_labels must be a tuple")
    if not terminal_labels:
        return grammar.accepts_empty

    labels = grammar.terminal_labels
    chart: set[tuple[int, int, int]] = set()
    for position, label in enumerate(terminal_labels):
        for terminal_production in grammar.terminal_productions:
            if labels[terminal_production.terminal_id] == label:
                chart.add((terminal_production.head_id, position, position + 1))

    length = len(terminal_labels)
    for span_width in range(2, length + 1):
        for start in range(length - span_width + 1):
            end = start + span_width
            for binary_production in grammar.binary_productions:
                if any(
                    (binary_production.left_id, start, split) in chart
                    and (binary_production.right_id, split, end) in chart
                    for split in range(start + 1, end)
                ):
                    chart.add((binary_production.head_id, start, end))

    return (grammar.start_nonterminal_id, 0, length) in chart
