from __future__ import annotations

import gzip
import json
from itertools import product
from pathlib import Path

import pytest

from mwpc_exact.reference.recognizer import recognizes_cnf
from mwpc_research.recursive_tasks import (
    FAMILIES,
    RecursiveTask,
    check_syntax,
    epic_grammar_spec,
    generated_witness,
    recursive_grammar,
)


@pytest.mark.parametrize(
    ("family", "alphabet", "maximum_length"),
    [("brackets", b"()[]", 6), ("arithmetic", b"0+()", 5), ("nested_json", b"0[],", 5)],
)
def test_recursive_grammar_agrees_with_independent_checker_exhaustively(
    family: str,
    alphabet: bytes,
    maximum_length: int,
) -> None:
    grammar = recursive_grammar(family)
    for length in range(maximum_length + 1):
        for labels in product(alphabet, repeat=length):
            content = bytes(labels)
            assert recognizes_cnf(grammar, labels) == check_syntax(family, content).syntax_valid, (
                family,
                content,
            )


@pytest.mark.parametrize(
    ("family", "content", "valid"),
    [
        ("brackets", b"([[]])()", True),
        ("brackets", b"([)]", False),
        ("brackets", b"( )", False),
        ("arithmetic", b" ((1 + 2) * 3) \n", True),
        ("arithmetic", b"1+2", False),
        ("arithmetic", b"(1+)", False),
        ("arithmetic", b"01", False),
        ("arithmetic", b"(1/2)", False),
        ("nested_json", b" [ 1, [2, 3], [] ] \n", True),
        ("nested_json", b"[ ]", True),
        ("nested_json", b"[0,]", False),
        ("nested_json", b"[-0]", False),
        ("nested_json", b"[10]", False),
        ("nested_json", b"[1.0]", False),
        ("nested_json", b"[true]", False),
        ("nested_json", b'{"x":0}', False),
    ],
)
def test_recursive_grammar_and_checker_edge_cases(family: str, content: bytes, valid: bool) -> None:
    assert check_syntax(family, content).syntax_valid is valid
    assert recognizes_cnf(recursive_grammar(family), tuple(content)) is valid


@pytest.mark.parametrize("family", FAMILIES)
def test_generated_context_is_valid_and_seeded(family: str) -> None:
    grammar = recursive_grammar(family)
    for seed in range(160100, 160110):
        content = generated_witness(family, seed)
        assert content == generated_witness(family, seed)
        assert check_syntax(family, content).syntax_valid, seed
        assert recognizes_cnf(grammar, tuple(content)), seed


def test_tasks_have_multiple_correct_answers_and_separate_semantic_failures() -> None:
    root = Path(__file__).resolve().parents[2]
    with gzip.open(
        root / "docs/artifacts/raw/m17_review_v1/pilot-v2/rows.jsonl.gz", "rt"
    ) as source:
        recorded = {row["task"]["task_id"]: row["task"] for row in map(json.loads, source)}
    tasks = {
        key: RecursiveTask(**{**task, "required_leaves": tuple(task["required_leaves"])})
        for key, task in recorded.items()
    }
    assert len(tasks) == 12
    alternatives = {
        "brackets-0": (b"[()]()", b"([]())"),
        "arithmetic-0": (b"(1+(2+3))", b"((3+1)+2)"),
        "nested_json-0": (b"[1,[2,3]]", b"[[1,2],3]"),
    }
    for task_id, contents in alternatives.items():
        task = tasks[task_id]
        for content in contents:
            assert task.check(content)[1]
    for task_id, content in (
        ("brackets-0", b"()"),
        ("arithmetic-0", b"(1+(2*3))"),
        ("nested_json-0", b"[[3,2],1]"),
    ):
        checked, success = tasks[task_id].check(content)
        assert checked.syntax_valid
        assert not success


def test_unknown_family_and_non_ascii_input_are_explicit() -> None:
    with pytest.raises(ValueError, match="unknown"):
        recursive_grammar("literal")
    with pytest.raises(ValueError, match="unknown"):
        check_syntax("literal", b"0")
    for family in FAMILIES:
        assert not check_syntax(family, b"\xff").syntax_valid


@pytest.mark.integration
@pytest.mark.parametrize("family", FAMILIES)
def test_epic_grammar_represents_the_same_recursive_byte_language(family: str) -> None:
    module = pytest.importorskip("rustformlang.cfg")
    text, lex_map = epic_grammar_spec(family)
    grammar = module.CFG.from_text(text, "S").to_normal_form()
    alphabet = {"brackets": b"()[]", "arithmetic": b"0+()", "nested_json": b"0[],"}[family]
    for length in range(5):
        for word in product(alphabet, repeat=length):
            assert (
                grammar.accepts([f"byte{value:02x}" for value in word])
                == check_syntax(family, bytes(word)).syntax_valid
            ), (family, word)
    for seed in range(160100, 160110):
        word = generated_witness(family, seed)
        assert grammar.accepts([f"byte{value:02x}" for value in word]), seed
    assert all(expression.startswith("\\x") for expression in lex_map.values())
