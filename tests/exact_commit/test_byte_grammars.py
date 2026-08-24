from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

from mwpc_exact.reference.byte_grammars import (
    ARITHMETIC_EXPRESSION_BYTES_V1,
    BYTE_GRAMMAR_FIXTURE_NAMES,
    LOWER_ASCII_JSON_VALUE_SUBSET_V1,
    TINY_ASSIGNMENT_DSL_BYTES_V1,
    arithmetic_expression_bytes_v1,
    lower_ascii_json_value_subset_v1,
    tiny_assignment_dsl_bytes_v1,
)
from mwpc_exact.reference.grammar import CnfGrammar
from mwpc_exact.reference.recognizer import recognizes_cnf

FIXTURE_DIR = Path(__file__).with_name("fixtures")
CORPUS_PATH = FIXTURE_DIR / "byte_grammar_corpus.json"
DOCUMENTATION_PATH = FIXTURE_DIR / "byte_grammars.md"

FACTORIES: Mapping[str, Callable[[], CnfGrammar]] = {
    ARITHMETIC_EXPRESSION_BYTES_V1: arithmetic_expression_bytes_v1,
    TINY_ASSIGNMENT_DSL_BYTES_V1: tiny_assignment_dsl_bytes_v1,
    LOWER_ASCII_JSON_VALUE_SUBSET_V1: lower_ascii_json_value_subset_v1,
}


def load_corpus() -> dict[str, object]:
    data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


@pytest.mark.parametrize("fixture_name", BYTE_GRAMMAR_FIXTURE_NAMES)
def test_boolean_recognizer_matches_every_versioned_corpus_label(fixture_name: str) -> None:
    corpus = load_corpus()
    assert corpus["schema_version"] == 1
    assert corpus["encoding"] == "ASCII strings encoded to raw bytes without preprocessing"
    grammars = corpus["grammars"]
    assert isinstance(grammars, dict)
    assert set(grammars) == set(BYTE_GRAMMAR_FIXTURE_NAMES)
    fixture = grammars[fixture_name]
    assert isinstance(fixture, dict)
    cases = fixture["cases"]
    assert isinstance(cases, list)
    assert cases
    grammar = FACTORIES[fixture_name]()

    observed_labels: set[bool] = set()
    for case in cases:
        assert isinstance(case, dict)
        assert set(case) == {"input", "accepted", "why"}
        raw_input = case["input"]
        expected = case["accepted"]
        reason = case["why"]
        assert isinstance(raw_input, str)
        assert isinstance(expected, bool)
        assert isinstance(reason, str) and reason
        terminal_labels = tuple(raw_input.encode("ascii"))
        observed_labels.add(expected)
        assert recognizes_cnf(grammar, terminal_labels) is expected, (
            f"{fixture_name} misclassified {raw_input!r}: {reason}"
        )
    assert observed_labels == {False, True}


@pytest.mark.parametrize("fixture_name", BYTE_GRAMMAR_FIXTURE_NAMES)
def test_byte_grammar_construction_is_cnf_deterministic_and_nonempty(
    fixture_name: str,
) -> None:
    first = FACTORIES[fixture_name]()
    second = FACTORIES[fixture_name]()

    assert first == second
    assert not first.accepts_empty
    assert first.terminal_productions
    assert first.binary_productions
    assert all(
        isinstance(label, int) and not isinstance(label, bool) and 0 <= label <= 255
        for label in first.terminal_labels.values()
    )


def test_fixture_names_and_documentation_state_exact_language_scope() -> None:
    assert BYTE_GRAMMAR_FIXTURE_NAMES == (
        "arithmetic_expression_bytes_v1",
        "tiny_assignment_dsl_bytes_v1",
        "lower_ascii_json_value_subset_v1",
    )
    assert "subset" in LOWER_ASCII_JSON_VALUE_SUBSET_V1

    documentation = DOCUMENTATION_PATH.read_text(encoding="utf-8")
    for fixture_name in BYTE_GRAMMAR_FIXTURE_NAMES:
        assert f"`{fixture_name}`" in documentation
    normalized_documentation = " ".join(documentation.split())
    assert "not a JSON grammar" in normalized_documentation
    assert "deliberately allows leading zeros" in normalized_documentation
    assert "no leading/trailing LF or blank lines" in normalized_documentation
