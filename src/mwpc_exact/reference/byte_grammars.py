"""Precisely scoped byte-level CFG fixtures for tokenizer-aware integration.

These grammars are deterministic construction fixtures, not claims to cover
complete programming languages.  Every literal is expanded into integer byte
terminals and normalized through the independently tested controlled CNF
boundary.
"""

from __future__ import annotations

from typing import Final, TypeAlias

from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal
from mwpc_exact.reference.normalization import (
    NonterminalRef,
    SourceGrammar,
    SourceProduction,
    SourceSymbol,
    TerminalRef,
    normalize_to_cnf,
)

RulePart: TypeAlias = str | bytes

ARITHMETIC_EXPRESSION_BYTES_V1: Final = "arithmetic_expression_bytes_v1"
TINY_ASSIGNMENT_DSL_BYTES_V1: Final = "tiny_assignment_dsl_bytes_v1"
LOWER_ASCII_JSON_VALUE_SUBSET_V1: Final = "lower_ascii_json_value_subset_v1"

BYTE_GRAMMAR_FIXTURE_NAMES: Final = (
    ARITHMETIC_EXPRESSION_BYTES_V1,
    TINY_ASSIGNMENT_DSL_BYTES_V1,
    LOWER_ASCII_JSON_VALUE_SUBSET_V1,
)


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


def _digit_rules(builder: _SourceGrammarBuilder, head: str) -> None:
    for byte_value in range(ord("0"), ord("9") + 1):
        builder.rule(head, bytes((byte_value,)))


def _lowercase_rules(builder: _SourceGrammarBuilder, head: str) -> None:
    for byte_value in range(ord("a"), ord("z") + 1):
        builder.rule(head, bytes((byte_value,)))


def arithmetic_expression_bytes_v1_source() -> SourceGrammar:
    """Return the source CFG for precedence-aware ASCII arithmetic expressions."""

    builder = _SourceGrammarBuilder(
        ("Expression", "Term", "Factor", "UnsignedInteger", "Digit"),
        start="Expression",
    )
    builder.rule("Expression", "Expression", b"+", "Term")
    builder.rule("Expression", "Expression", b"-", "Term")
    builder.rule("Expression", "Term")
    builder.rule("Term", "Term", b"*", "Factor")
    builder.rule("Term", "Term", b"/", "Factor")
    builder.rule("Term", "Factor")
    builder.rule("Factor", "UnsignedInteger")
    builder.rule("Factor", b"(", "Expression", b")")
    builder.rule("UnsignedInteger", "Digit")
    builder.rule("UnsignedInteger", "UnsignedInteger", "Digit")
    _digit_rules(builder, "Digit")
    return builder.build()


def arithmetic_expression_bytes_v1() -> CnfGrammar:
    """Return normalized ``arithmetic_expression_bytes_v1``."""

    return normalize_to_cnf(arithmetic_expression_bytes_v1_source()).grammar


def tiny_assignment_dsl_bytes_v1_source() -> SourceGrammar:
    """Return the source CFG for the documented line-oriented assignment DSL."""

    builder = _SourceGrammarBuilder(
        (
            "Program",
            "Statement",
            "SetStatement",
            "PrintStatement",
            "Name",
            "NameCharacter",
            "Lowercase",
            "UnsignedInteger",
            "Digit",
        ),
        start="Program",
    )
    builder.rule("Program", "Statement")
    builder.rule("Program", "Program", b"\n", "Statement")
    builder.rule("Statement", "SetStatement")
    builder.rule("Statement", "PrintStatement")
    builder.rule("SetStatement", b"set ", "Name", b"=", "UnsignedInteger", b";")
    builder.rule("PrintStatement", b"print ", "Name", b";")
    builder.rule("Name", "Lowercase")
    builder.rule("Name", "Name", "NameCharacter")
    builder.rule("NameCharacter", "Lowercase")
    builder.rule("NameCharacter", "Digit")
    builder.rule("NameCharacter", b"_")
    builder.rule("UnsignedInteger", "Digit")
    builder.rule("UnsignedInteger", "UnsignedInteger", "Digit")
    _lowercase_rules(builder, "Lowercase")
    _digit_rules(builder, "Digit")
    return builder.build()


def tiny_assignment_dsl_bytes_v1() -> CnfGrammar:
    """Return normalized ``tiny_assignment_dsl_bytes_v1``."""

    return normalize_to_cnf(tiny_assignment_dsl_bytes_v1_source()).grammar


def lower_ascii_json_value_subset_v1_source() -> SourceGrammar:
    """Return the source CFG for the documented restricted JSON value subset."""

    builder = _SourceGrammarBuilder(
        (
            "Value",
            "Null",
            "True",
            "False",
            "Integer",
            "NonZero",
            "Digits",
            "Digit",
            "String",
            "Characters",
            "Character",
            "Lowercase",
            "Array",
            "Elements",
            "Object",
            "Members",
            "Member",
        ),
        start="Value",
    )
    for alternative in ("Null", "True", "False", "Integer", "String", "Array", "Object"):
        builder.rule("Value", alternative)
    builder.rule("Null", b"null")
    builder.rule("True", b"true")
    builder.rule("False", b"false")

    builder.rule("Integer", b"0")
    builder.rule("Integer", "NonZero")
    builder.rule("Integer", "NonZero", "Digits")
    for byte_value in range(ord("1"), ord("9") + 1):
        builder.rule("NonZero", bytes((byte_value,)))
    builder.rule("Digits", "Digit")
    builder.rule("Digits", "Digits", "Digit")
    _digit_rules(builder, "Digit")

    builder.rule("String", b'""')
    builder.rule("String", b'"', "Characters", b'"')
    builder.rule("Characters", "Character")
    builder.rule("Characters", "Characters", "Character")
    builder.rule("Character", "Lowercase")
    builder.rule("Character", "Digit")
    builder.rule("Character", b" ")
    _lowercase_rules(builder, "Lowercase")

    builder.rule("Array", b"[]")
    builder.rule("Array", b"[", "Elements", b"]")
    builder.rule("Elements", "Value")
    builder.rule("Elements", "Elements", b",", "Value")
    builder.rule("Object", b"{}")
    builder.rule("Object", b"{", "Members", b"}")
    builder.rule("Members", "Member")
    builder.rule("Members", "Members", b",", "Member")
    builder.rule("Member", "String", b":", "Value")
    return builder.build()


def lower_ascii_json_value_subset_v1() -> CnfGrammar:
    """Return normalized ``lower_ascii_json_value_subset_v1``."""

    return normalize_to_cnf(lower_ascii_json_value_subset_v1_source()).grammar
