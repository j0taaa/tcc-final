"""Small byte-grammar builder for the retained recursive-array application."""

from __future__ import annotations

from mwpc_exact.reference.grammar import Nonterminal, Terminal
from mwpc_exact.reference.normalization import (
    NonterminalRef,
    SourceGrammar,
    SourceProduction,
    SourceSymbol,
    TerminalRef,
)

RulePart = str | bytes


class _SourceGrammarBuilder:
    """Small deterministic helper for literal-byte source productions."""

    def __init__(self, nonterminal_names: tuple[str, ...], *, start: str) -> None:
        if len(set(nonterminal_names)) != len(nonterminal_names):
            raise ValueError("fixture nonterminal names must be unique")
        self._nonterminal_ids = {
            name: symbol_id for symbol_id, name in enumerate(nonterminal_names)
        }
        if start not in self._nonterminal_ids:
            raise ValueError("fixture start symbol must be declared")
        self._start_id = self._nonterminal_ids[start]
        self._nonterminals = tuple(
            Nonterminal(symbol_id, name) for name, symbol_id in self._nonterminal_ids.items()
        )
        self._terminal_id_by_byte: dict[int, int] = {}
        self._productions: list[SourceProduction] = []

    def rule(self, head: str, *parts: RulePart) -> None:
        """Add one source rule, expanding ``bytes`` parts byte by byte."""

        try:
            head_id = self._nonterminal_ids[head]
        except KeyError as exc:
            raise ValueError(f"unknown fixture rule head: {head!r}") from exc
        body: list[SourceSymbol] = []
        for part in parts:
            if isinstance(part, str):
                try:
                    body.append(NonterminalRef(self._nonterminal_ids[part]))
                except KeyError as exc:
                    raise ValueError(f"unknown fixture nonterminal: {part!r}") from exc
                continue
            if not isinstance(part, bytes):
                raise TypeError("fixture rule parts must be nonterminal names or bytes")
            if not part:
                raise ValueError("empty byte literals are not fixture epsilon syntax")
            for byte_value in part:
                terminal_id = self._terminal_id_by_byte.setdefault(
                    byte_value, len(self._terminal_id_by_byte)
                )
                body.append(TerminalRef(terminal_id))
        self._productions.append(
            SourceProduction(
                production_id=len(self._productions),
                head_id=head_id,
                body=tuple(body),
            )
        )

    def build(self) -> SourceGrammar:
        terminal_bytes = sorted(
            self._terminal_id_by_byte,
            key=self._terminal_id_by_byte.__getitem__,
        )
        return SourceGrammar(
            nonterminals=self._nonterminals,
            terminals=tuple(
                Terminal(self._terminal_id_by_byte[byte_value], byte_value)
                for byte_value in terminal_bytes
            ),
            start_nonterminal_id=self._start_id,
            productions=tuple(self._productions),
        )
