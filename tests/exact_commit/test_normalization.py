from __future__ import annotations

import pytest

from mwpc_exact.reference.grammar import Nonterminal, Terminal
from mwpc_exact.reference.normalization import (
    NonterminalRef,
    SourceGrammar,
    SourceProduction,
    TerminalRef,
    enumerate_cnf_language,
    enumerate_source_language,
    normalize_to_cnf,
)

N = NonterminalRef
T = TerminalRef


def grammar_fixture(kind: str) -> SourceGrammar:
    if kind == "epsilon":
        # S -> A B | epsilon; A -> a | epsilon; B -> b
        return SourceGrammar(
            nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A"), Nonterminal(2, "B")),
            terminals=(Terminal(0, "a"), Terminal(1, "b")),
            start_nonterminal_id=0,
            productions=(
                SourceProduction(10, 0, (N(1), N(2))),
                SourceProduction(11, 0),
                SourceProduction(12, 1, (T(0),)),
                SourceProduction(13, 1),
                SourceProduction(14, 2, (T(1),)),
            ),
        )
    if kind == "unit_recursive":
        # Unit cycle S -> A -> B -> S, with exits a and b.
        return SourceGrammar(
            nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A"), Nonterminal(2, "B")),
            terminals=(Terminal(0, "a"), Terminal(1, "b")),
            start_nonterminal_id=0,
            productions=(
                SourceProduction(20, 0, (N(1),)),
                SourceProduction(21, 1, (N(2),)),
                SourceProduction(22, 1, (T(0),)),
                SourceProduction(23, 2, (N(0),)),
                SourceProduction(24, 2, (T(1),)),
            ),
        )
    if kind == "recursive":
        # S -> S A | a; A -> b, so the language is a b*.
        return SourceGrammar(
            nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A")),
            terminals=(Terminal(0, "a"), Terminal(1, "b")),
            start_nonterminal_id=0,
            productions=(
                SourceProduction(30, 0, (N(0), N(1))),
                SourceProduction(31, 0, (T(0),)),
                SourceProduction(32, 1, (T(1),)),
            ),
        )
    if kind == "ambiguous":
        # The word a b has two source derivations; language comparison is Boolean.
        return SourceGrammar(
            nonterminals=(
                Nonterminal(0, "S"),
                Nonterminal(1, "A"),
                Nonterminal(2, "B"),
                Nonterminal(3, "C"),
                Nonterminal(4, "D"),
            ),
            terminals=(Terminal(0, "a"), Terminal(1, "b")),
            start_nonterminal_id=0,
            productions=(
                SourceProduction(40, 0, (N(1), N(2))),
                SourceProduction(41, 0, (N(3), N(4))),
                SourceProduction(42, 1, (T(0),)),
                SourceProduction(43, 2, (T(1),)),
                SourceProduction(44, 3, (T(0),)),
                SourceProduction(45, 4, (T(1),)),
            ),
        )
    if kind == "long_mixed":
        # Exercises terminal isolation and deterministic right binarization.
        return SourceGrammar(
            nonterminals=(Nonterminal(0, "S"), Nonterminal(1, "A"), Nonterminal(2, "B")),
            terminals=(Terminal(0, "a"), Terminal(1, "b"), Terminal(2, "c")),
            start_nonterminal_id=0,
            productions=(
                SourceProduction(50, 0, (T(0), N(1), N(2), T(2))),
                SourceProduction(51, 1, (T(1),)),
                SourceProduction(52, 2, (T(1),)),
            ),
        )
    raise AssertionError(f"unknown fixture: {kind}")


@pytest.mark.parametrize(
    "kind", ["epsilon", "unit_recursive", "recursive", "ambiguous", "long_mixed"]
)
def test_controlled_normalization_preserves_bounded_language(kind: str) -> None:
    source = grammar_fixture(kind)

    result = normalize_to_cnf(source)

    assert enumerate_cnf_language(result.grammar, max_length=5) == enumerate_source_language(
        source, max_length=5
    )


def test_empty_acceptance_is_explicit_and_non_start_epsilon_is_removed() -> None:
    result = normalize_to_cnf(grammar_fixture("epsilon"))

    assert result.grammar.accepts_empty
    assert () in enumerate_cnf_language(result.grammar, max_length=2)
    assert all(
        production.head_id != 1 or production.terminal_id == 0
        for production in result.grammar.terminal_productions
    )


def test_unit_cycle_is_removed_and_provenance_records_the_path() -> None:
    result = normalize_to_cnf(grammar_fixture("unit_recursive"))

    start_terminal_origins = {
        result.grammar.terminal_labels[production.terminal_id]: production.source_production_ids
        for production in result.grammar.terminal_productions
        if production.head_id == result.grammar.start_nonterminal_id
    }
    assert set(start_terminal_origins) == {"a", "b"}
    assert start_terminal_origins["a"] == (20, 22)
    assert start_terminal_origins["b"] == (20, 21, 24)


def test_long_mixed_rule_creates_mapped_synthetic_symbols() -> None:
    result = normalize_to_cnf(grammar_fixture("long_mixed"))

    assert result.synthetic_nonterminal_ids
    assert all(origins for origins in result.normalized_to_source_production_ids.values())
    assert all(
        len(production.source_production_ids) >= 1
        for production in (
            *result.grammar.terminal_productions,
            *result.grammar.binary_productions,
        )
    )


def test_normalization_is_deterministic() -> None:
    source = grammar_fixture("long_mixed")

    first = normalize_to_cnf(source)
    second = normalize_to_cnf(source)

    assert first.grammar == second.grammar
    assert first.synthetic_nonterminal_ids == second.synthetic_nonterminal_ids
    assert dict(first.normalized_to_source_production_ids) == dict(
        second.normalized_to_source_production_ids
    )
