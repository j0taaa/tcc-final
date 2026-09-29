import copy
import json
from pathlib import Path

import pytest

from mwpc_research.grounded_calls import (
    eligible_query,
    grounded_catalog,
    grounded_function,
    grounded_grade,
    scalar_call_arguments,
    text_candidates,
)

ROOT = Path(__file__).resolve().parents[2]


def schema():
    return {
        "name": "get_weather",
        "parameters": {
            "type": "dict",
            "properties": {
                "city": {"type": "string"},
                "days": {"type": "integer"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["city", "days"],
        },
    }


def test_grounding_uses_public_spans_numbers_and_schema_without_mutation():
    fn = schema()
    before = copy.deepcopy(fn)
    g = grounded_function(fn, 'Weather for "São Paulo" for three days, please.')
    assert fn == before
    assert "São Paulo" in g["parameters"]["properties"]["city"]["enum"]
    assert g["parameters"]["properties"]["days"]["enum"] == [3]
    assert g["parameters"]["properties"]["unit"] == fn["parameters"]["properties"]["unit"]
    calls = grounded_catalog(fn, 'Weather for "São Paulo" for three days, please.')
    assert "get_weather(city='São Paulo',days=3)" in calls
    assert all(scalar_call_arguments(c, fn) is not None for c in calls)
    assert all("secret answer" not in c for c in calls)


def test_grounded_grader_uses_original_schema_and_accepts_only_expected_values():
    fn = schema()
    answer = [{"get_weather": {"city": ["Paris"], "days": [2], "unit": ["", "celsius"]}}]
    assert grounded_grade("get_weather(days=2,city='Paris')", fn, answer)
    assert grounded_grade("get_weather(days=2,city='Paris',unit='celsius')", fn, answer)
    assert not grounded_grade("get_weather(days=2,city='Rome')", fn, answer)
    assert not grounded_grade("get_weather(days=2,city='Paris',unit='fahrenheit')", fn, answer)


@pytest.mark.parametrize(
    "output",
    [
        "get_weather(city='Paris',days=True)",
        "get_weather(city='Paris',days=2.0)",
        "get_weather(city='Paris')",
        "get_weather(city='Paris',days=2,extra=1)",
        "get_weather(city='Paris',days=2,unit='unknown')",
        "get_weather(**evil())",
        "wrong(city='Paris',days=2)",
        "get_weather(city=evil(),days=2)",
    ],
)
def test_original_schema_validation_rejects_malformed_or_wrong_typed_calls(output):
    assert scalar_call_arguments(output, schema()) is None


def test_candidates_are_deterministic_and_explicitly_bounded():
    question = " ".join(f"word{i}" for i in range(40)) + ' "New York"'
    a = text_candidates(question)
    assert a == text_candidates(question) and len(a) == 96
    assert "New York" in a
    with pytest.raises(ValueError):
        text_candidates("")
    with pytest.raises(ValueError):
        text_candidates("abc", limit=True)


def test_eligibility_is_independent_of_answers_and_excludes_enum_only_pilot():
    assert eligible_query([schema()])
    fn = schema()
    fn["parameters"]["properties"]["city"]["enum"] = ["Paris"]
    assert not eligible_query([fn])
    assert not eligible_query([schema(), schema()])
    fn = schema()
    fn["parameters"]["properties"]["city"]["type"] = "array"
    assert not eligible_query([fn])


def test_frozen_family_split_covers_every_selected_case_without_overlap():
    def read(split):
        return json.loads((ROOT / f"configs/experiments/m25_grounded_{split}_v1.json").read_text())[
            "tasks"
        ]

    dev, test = read("development"), read("confirmation")
    dev_names = {t["function"]["name"].casefold() for t in dev}
    test_names = {t["function"]["name"].casefold() for t in test}
    assert len(dev) == 26 and len(test) == 42
    assert len(dev_names) == 8 and len(test_names) == 42
    assert not dev_names & test_names
    assert len({t["id"] for t in dev + test}) == 68
    assert all(eligible_query([t["function"]]) for t in dev + test)


def test_catalog_encoding_preserves_split_utf8_and_rejects_insufficient_slots():
    from mwpc_research.catalog_tokens import encode_call

    class Tokenizer:
        def encode(self, call, **kwargs):
            return [0, 1, 2, 3]

        def convert_ids_to_tokens(self, token):
            return ["get(city='", "ðŁĳ", "©", "')"][token]

        def decode(self, *args, **kwargs):
            raise AssertionError("single-token Unicode decoding loses byte fragments")

    path, emissions = encode_call(Tokenizer(), "get(city='👩')", slots=6, eos=4)
    assert path == [0, 1, 2, 3, 4, 4]
    assert b"".join(emissions[t] for t in path if t != 4).decode() == "get(city='👩')"
    with pytest.raises(ValueError, match="needs 5 slots"):
        encode_call(Tokenizer(), "get(city='👩')", slots=4, eos=4)
    with pytest.raises(ValueError, match="reconstruct"):
        encode_call(Tokenizer(), "get(city='different')", slots=6, eos=4)
