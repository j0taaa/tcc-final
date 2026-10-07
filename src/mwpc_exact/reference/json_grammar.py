"""Predictive byte grammar for RFC 8259 JSON syntax, including UTF-8 strings.

Duplicate keys, large numbers and escaped surrogate code units remain syntax.
Semantic/schema validation is deliberately a separate application concern.
"""

from __future__ import annotations

from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import SourceGrammar


def json_source_grammar() -> SourceGrammar:
    names = (
        "S",
        "V",
        "W",
        "A",
        "Items",
        "MoreItems",
        "O",
        "Members",
        "MoreMembers",
        "String",
        "Chars",
        "Char",
        "Escape",
        "Hex",
        "Cont",
        "ContA",
        "ContB",
        "ContC",
        "ContD",
        "N",
        "Unsigned",
        "Nonzero",
        "Digit",
        "Digits",
        "Fraction",
        "Exponent",
        "Sign",
    )
    b = _SourceGrammarBuilder(names, start="S")
    b.rule("S", "W", "V", "W")
    for name in ("A", "O", "String", "N"):
        b.rule("V", name)
    for literal in (b"true", b"false", b"null"):
        b.rule("V", literal)
    b.rule("W")
    for byte in b" \t\r\n":
        b.rule("W", bytes([byte]), "W")
    b.rule("A", b"[", "W", "Items", b"]")
    b.rule("Items")
    b.rule("Items", "V", "W", "MoreItems")
    b.rule("MoreItems")
    b.rule("MoreItems", b",", "W", "V", "W", "MoreItems")
    b.rule("O", b"{", "W", "Members", b"}")
    b.rule("Members")
    b.rule("Members", "String", "W", b":", "W", "V", "W", "MoreMembers")
    b.rule("MoreMembers")
    b.rule("MoreMembers", b",", "W", "String", "W", b":", "W", "V", "W", "MoreMembers")
    b.rule("String", b'"', "Chars", b'"')
    b.rule("Chars")
    b.rule("Chars", "Char", "Chars")
    for byte in range(32, 128):
        if byte not in (34, 92):
            b.rule("Char", bytes([byte]))
    b.rule("Char", b"\\", "Escape")
    for byte in b'"\\/bfnrt':
        b.rule("Escape", bytes([byte]))
    b.rule("Escape", b"u", "Hex", "Hex", "Hex", "Hex")
    for byte in b"0123456789abcdefABCDEF":
        b.rule("Hex", bytes([byte]))
    for name, low, high in (
        ("Cont", 128, 191),
        ("ContA", 160, 191),
        ("ContB", 128, 159),
        ("ContC", 144, 191),
        ("ContD", 128, 143),
    ):
        for byte in range(low, high + 1):
            b.rule(name, bytes([byte]))
    for byte in range(194, 224):
        b.rule("Char", bytes([byte]), "Cont")
    for byte in range(224, 240):
        first = "ContA" if byte == 224 else "ContB" if byte == 237 else "Cont"
        b.rule("Char", bytes([byte]), first, "Cont")
    for byte in range(240, 245):
        first = "ContC" if byte == 240 else "ContD" if byte == 244 else "Cont"
        b.rule("Char", bytes([byte]), first, "Cont", "Cont")
    b.rule("N", b"-", "Unsigned")
    b.rule("N", "Unsigned")
    b.rule("Unsigned", b"0", "Fraction", "Exponent")
    b.rule("Unsigned", "Nonzero", "Digits", "Fraction", "Exponent")
    for byte in b"123456789":
        b.rule("Nonzero", bytes([byte]))
    for byte in b"0123456789":
        b.rule("Digit", bytes([byte]))
    b.rule("Digits")
    b.rule("Digits", "Digit", "Digits")
    b.rule("Fraction")
    b.rule("Fraction", b".", "Digit", "Digits")
    b.rule("Exponent")
    for byte in b"eE":
        b.rule("Exponent", bytes([byte]), "Sign", "Digit", "Digits")
    b.rule("Sign")
    b.rule("Sign", b"+")
    b.rule("Sign", b"-")
    return b.build()
