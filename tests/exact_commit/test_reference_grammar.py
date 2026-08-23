from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from mwpc_exact.reference.grammar import (
    BinaryProduction,
    CnfGrammar,
    Nonterminal,
    Terminal,
    TerminalProduction,
    from_repository_cnf,
)


def balanced_ab_grammar() -> CnfGrammar:
    return CnfGrammar(
        nonterminals=(
            Nonterminal(10, "Start"),
            Nonterminal(20, "Left"),
            Nonterminal(30, "Right"),
        ),
        terminals=(Terminal(100, "a"), Terminal(200, "b")),
        start_nonterminal_id=10,
        terminal_productions=(
            TerminalProduction(1, 20, 100, (41,)),
            TerminalProduction(2, 30, 200, (42,)),
        ),
        binary_productions=(BinaryProduction(3, 10, 20, 30, (40,)),),
    )


def test_handwritten_cnf_json_round_trip_preserves_stable_ids() -> None:
    grammar = balanced_ab_grammar()

    restored = CnfGrammar.from_dict(json.loads(json.dumps(grammar.to_dict())))

    assert restored == grammar
    assert restored.nonterminal_names == {10: "Start", 20: "Left", 30: "Right"}
    assert restored.terminal_labels == {100: "a", 200: "b"}
    assert restored.binary_productions[0].source_production_ids == (40,)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"start_nonterminal_id": 99}, "start_nonterminal_id"),
        (
            {"terminal_productions": (TerminalProduction(1, 20, 999),)},
            "unknown terminal_id",
        ),
        (
            {"binary_productions": (BinaryProduction(3, 10, 20, 999),)},
            "unknown nonterminal",
        ),
    ],
)
def test_cnf_rejects_dangling_symbol_references(change: dict[str, object], message: str) -> None:
    grammar = balanced_ab_grammar()
    values: dict[str, object] = {
        "nonterminals": grammar.nonterminals,
        "terminals": grammar.terminals,
        "start_nonterminal_id": grammar.start_nonterminal_id,
        "terminal_productions": grammar.terminal_productions,
        "binary_productions": grammar.binary_productions,
    }
    values.update(change)

    with pytest.raises(ValueError, match=message):
        CnfGrammar(**values)  # type: ignore[arg-type]


def test_cnf_rejects_duplicate_production_ids_across_kinds() -> None:
    with pytest.raises(ValueError, match="globally unique"):
        CnfGrammar(
            nonterminals=(Nonterminal(0, "S"),),
            terminals=(Terminal(0, "a"),),
            start_nonterminal_id=0,
            terminal_productions=(TerminalProduction(7, 0, 0),),
            binary_productions=(BinaryProduction(7, 0, 0, 0),),
        )


@dataclass
class FakeRepositoryCFG:
    text: str

    def to_text(self) -> str:
        return self.text


def test_repository_adapter_reads_epic_cnf_serialization() -> None:
    repository_grammar = FakeRepositoryCFG(
        """Start Symbol: S_0
S_0 -> S_1 S_2 | ε
S_1 -> a
S_2 -> b
Terminals: a b
"""
    )

    grammar = from_repository_cnf(repository_grammar)

    assert grammar.nonterminal_names == {0: "S_0", 1: "S_1", 2: "S_2"}
    assert grammar.terminal_labels == {0: "a", 1: "b"}
    assert grammar.start_nonterminal_id == 0
    assert grammar.accepts_empty
    assert tuple(production.production_id for production in grammar.binary_productions) == (0,)
    assert tuple(production.production_id for production in grammar.terminal_productions) == (
        1,
        2,
    )


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("A", "unit production"),
        ("A B C", "body length 3"),
        ("A missing", "unknown nonterminal"),
    ],
)
def test_repository_adapter_rejects_non_cnf_bodies(body: str, message: str) -> None:
    repository_grammar = FakeRepositoryCFG(
        f"""Start Symbol: S
S -> {body}
A -> a
B -> b
Terminals: a b missing
"""
    )

    with pytest.raises(ValueError, match=message):
        from_repository_cnf(repository_grammar)


def test_repository_adapter_rejects_non_start_epsilon() -> None:
    repository_grammar = FakeRepositoryCFG(
        """Start Symbol: S
S -> a
A -> ε
Terminals: a
"""
    )

    with pytest.raises(ValueError, match="only the CNF start symbol"):
        from_repository_cnf(repository_grammar)
