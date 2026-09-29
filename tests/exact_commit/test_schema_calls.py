import json
from pathlib import Path

import pytest

from mwpc_research.schema_calls import normalize_schema_call, schema_catalog, strict_schema_grade
from mwpc_research.tool_parser import epic_python_call_grammar

ROOT = Path(__file__).resolve().parents[2]


def test_frozen_external_subset_is_schema_only_and_all_answers_are_representable():
    config = json.loads((ROOT / "configs/experiments/m24_bfcl_enum_pilot_v1.json").read_text())
    assert len(config["tasks"]) == 8
    for task in config["tasks"]:
        catalog = schema_catalog(task["function"])
        assert any(
            strict_schema_grade(call, task["function"], task["ground_truth"]) for call in catalog
        )
        assert all(normalize_schema_call(call) == call for call in catalog)
        text, start, rules = epic_python_call_grammar(catalog)
        assert start == "S" and text and rules


def test_free_value_fields_do_not_get_filled_from_expected_answers():
    schema = {
        "name": "query",
        "parameters": {"properties": {"city": {"type": "string"}}, "required": ["city"]},
    }
    with pytest.raises(ValueError, match="unbounded"):
        schema_catalog(schema)


@pytest.mark.parametrize(
    "text",
    ["query(**x)", "query(city=evil())", 'query(city="x",city="y")', "query(1)", "(evil())()"],
)
def test_unsafe_or_unsupported_ast_is_rejected(text):
    assert normalize_schema_call(text) is None


def test_optional_omission_and_wrong_enum_are_distinct():
    schema = {
        "name": "query",
        "parameters": {
            "properties": {"state": {"type": "string", "enum": ["open", "closed"]}},
            "required": [],
        },
    }
    assert set(schema_catalog(schema)) == {
        "query()",
        "query(state='open')",
        "query(state='closed')",
    }
    answer = [{"query": {"state": ["", "open"]}}]
    assert strict_schema_grade("query()", schema, answer)
    assert strict_schema_grade('query(state="open")', schema, answer)
    assert not strict_schema_grade('query(state="closed")', schema, answer)
    assert not strict_schema_grade('query(state="unknown")', schema, answer)


def test_python_lexemes_accept_all_frozen_schema_calls():
    from constrained_diffusion.constrain_utils import EOS, compile_lex_map
    from constrained_diffusion.eval.dllm.models.llada.generate_constrained import check_valid
    from rustformlang.cfg import CFG

    config = json.loads((ROOT / "configs/experiments/m24_bfcl_enum_pilot_v1.json").read_text())
    for task in config["tasks"]:
        calls = schema_catalog(task["function"])
        text, start, rules = epic_python_call_grammar(calls)
        grammar = CFG.from_text(text, start).to_normal_form().to_normal_form()
        lex_map = compile_lex_map(rules)
        for call in calls:
            assert not check_valid([call, EOS], grammar, lex_map, grammar.get_terminals()), call


def test_epic_literal_strings_preserve_spaces_unicode_and_regex_punctuation():
    from constrained_diffusion.constrain_utils import EOS, compile_lex_map
    from constrained_diffusion.eval.dllm.models.llada.generate_constrained import check_valid
    from rustformlang.cfg import CFG

    calls = ["get(name='São Paulo')", "get(name='a#b&c~d e')", r"get(name='a+b[x].*?(x){}|^$\\z')"]
    text, start, rules = epic_python_call_grammar(calls)
    grammar = CFG.from_text(text, start).to_normal_form().to_normal_form()
    lex_map = compile_lex_map(rules)
    for call in calls:
        assert not check_valid([call, EOS], grammar, lex_map, grammar.get_terminals())
    assert check_valid(["get(name='SãoXPaulo')", EOS], grammar, lex_map, grammar.get_terminals())
