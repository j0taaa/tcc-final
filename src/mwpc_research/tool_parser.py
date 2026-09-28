"""Compile a finite tool language to bytes and use existing production selectors.

Unlike catalog enumeration, the represented support is the Cartesian positional
token support intersected with the byte language. Alternative tokenizations may
therefore exist and must not be described as the canonical-only catalog.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    Proposal,
    SelectionInput,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
)
from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal
from mwpc_exact.reference.normalization import (
    NonterminalRef,
    SourceGrammar,
    SourceProduction,
    TerminalRef,
    normalize_to_cnf,
)


@dataclass
class _Trie:
    children: dict[int, _Trie] = field(default_factory=dict)
    final: bool = False


def catalog_byte_grammar(calls: Sequence[str]) -> CnfGrammar:
    """Exact finite-language trie with identical suffix subtrees merged safely."""
    if not calls or any(not call for call in calls):
        raise ValueError("nonempty tool strings required")
    root = _Trie()
    for call in calls:
        node = root
        for byte in call.encode("utf-8"):
            node = node.children.setdefault(byte, _Trie())
        node.final = True
    signatures: list[tuple[bool, tuple[tuple[int, int], ...]]] = []
    interned: dict[tuple[bool, tuple[tuple[int, int], ...]], int] = {}

    def intern(node: _Trie) -> int:
        signature = (node.final, tuple((b, intern(n)) for b, n in sorted(node.children.items())))
        if signature not in interned:
            interned[signature] = len(signatures)
            signatures.append(signature)
        return interned[signature]

    start = intern(root)
    alphabet = sorted({b for _, edges in signatures for b, _ in edges})
    terminal_ids = {b: i for i, b in enumerate(alphabet)}
    productions: list[SourceProduction] = []
    for head, (final, edges) in enumerate(signatures):
        if final:
            productions.append(SourceProduction(len(productions), head, ()))
        for byte, target in edges:
            productions.append(
                SourceProduction(
                    len(productions),
                    head,
                    (TerminalRef(terminal_ids[byte]), NonterminalRef(target)),
                )
            )
    return normalize_to_cnf(
        SourceGrammar(
            tuple(Nonterminal(i, f"q{i}") for i in range(len(signatures))),
            tuple(Terminal(i, b) for i, b in enumerate(alphabet)),
            start,
            tuple(productions),
        )
    ).grammar


def epic_byte_grammar(grammar: CnfGrammar) -> tuple[str, str, dict[str, str]]:
    """Serialize exactly the same byte CNF for upstream EPIC's lexical interface."""
    if any(not isinstance(t.label, int) for t in grammar.terminals):
        raise ValueError("byte terminals required")
    names = {t.symbol_id: f"lex{t.label}" for t in grammar.terminals}
    lines = [f"N{p.head_id} -> {names[p.terminal_id]}" for p in grammar.terminal_productions]
    lines.extend(f"N{p.head_id} -> N{p.left_id} N{p.right_id}" for p in grammar.binary_productions)
    if grammar.accepts_empty:
        lines.append(f"N{grammar.start_nonterminal_id} -> epsilon")
    # Upstream regular_cover reads the first production as its start symbol.
    # Emit the actual start first so both upstream representations agree.
    start = f"N{grammar.start_nonterminal_id}"
    lines.sort(key=lambda line: line.split()[0] != start)
    lex_map = {names[t.symbol_id]: rf"\x{t.label:02x}" for t in grammar.terminals}
    return "\n".join(lines), start, lex_map


def epic_lexical_grammar(calls: Sequence[str]) -> tuple[str, str, dict[str, str]]:
    """Natural function-name/digit/punctuation lexemes for the same call catalogue."""
    if not calls:
        raise ValueError("nonempty tool language required")
    sequences = [re.findall(r"add|sub|mul|neg|abs|[0-9(),]", call) for call in calls]
    if any("".join(parts) != call for parts, call in zip(sequences, calls, strict=True)):
        raise ValueError("unsupported calculator lexeme")
    symbols = sorted({symbol for parts in sequences for symbol in parts})
    names = {symbol: f"lex{i}" for i, symbol in enumerate(symbols)}
    text = "\n".join("S -> " + " ".join(names[s] for s in parts) for parts in sequences)
    return text, "S", {names[s]: re.escape(s) for s in symbols}


def production_input(
    grammar: CnfGrammar,
    canvas: Sequence[int | None],
    proposals: Sequence[tuple[int, int, float]],
    rows: Sequence[Sequence[int]],
    adapter: CompositionalByteLevelAdapter,
    eos: int,
) -> SelectionInput:
    typed = tuple(Proposal(p, p, t, w, model_confidence=w) for p, t, w in proposals)
    explicit = {}
    for p, row in enumerate(rows):
        fixed = canvas[p]
        explicit[p] = tuple(row) if fixed is None else (fixed,)
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=adapter.vocabulary_size,
            required_special_token_ids=(eos,),
            pruning_description="tool positional domains; byte CFG; EOS-padded slots",
        ),
        explicit_support=explicit,
        proposals=typed,
    )
    return SelectionInput(
        grammar,
        tuple(canvas),
        typed,
        support,
        adapter,
        EOSPolicy(EOSMode.REQUIRED, termination_token_ids=(eos,), pad_token_id=eos),
    )
