"""Question/schema-derived finite scalar support for external function calls.

Grounding has no answer argument. The original schema remains the evaluator's
source of truth; bounded candidate domains are an explicitly pruned support.
"""

from __future__ import annotations

import ast
import copy
import re
from collections.abc import Sequence
from math import isfinite
from typing import Any

from mwpc_research.schema_calls import normalize_schema_call, schema_catalog

QUERY_NAMES = (
    "weather",
    "forecast",
    "search",
    "find",
    "get",
    "lookup",
    "query",
    "check",
    "retrieve",
    "fetch",
)
NUMBER_WORDS = dict(
    enumerate(
        (
            "zero one two three four five six seven eight nine ten eleven twelve thirteen "
            "fourteen fifteen sixteen seventeen eighteen nineteen twenty"
        ).split()
    )
)


def eligible_query(functions: Sequence[dict[str, Any]]) -> bool:
    if len(functions) != 1:
        return False
    fn = functions[0]
    props = fn["parameters"].get("properties", {})
    return (
        1 <= len(props) <= 3
        and all(
            p.get("type") in ("string", "integer", "number", "float", "boolean")
            for p in props.values()
        )
        and sum(p.get("type") == "string" and not p.get("enum") for p in props.values()) == 1
        and any(word in fn["name"].casefold() for word in QUERY_NAMES)
    )


def text_candidates(question: str, *, limit: int = 96) -> tuple[str, ...]:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("nonempty question required")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("positive candidate limit required")
    ranked: dict[str, tuple[int, int, int, str]] = {}

    def add(text: str, priority: int, offset: int) -> None:
        text = text.strip(" \t\n.,?!:;\"'")
        if not text or len(text) > 100:
            return
        key = (priority, -len(text.split()), offset, text)
        if text not in ranked or key < ranked[text]:
            ranked[text] = key

    for match in re.finditer(r'"([^"\n]+)"|\x27([^\x27\n]+)\x27', question):
        add(match.group(1) or match.group(2), 0, match.start())
    for match in re.finditer(r"\b[A-Z][\w'-]*(?:[ ,]+[A-Z][\w'-]*){0,5}", question):
        add(match.group(), 1, match.start())
    words = list(re.finditer(r"[\w]+(?:[-'./][\w]+)*", question, re.UNICODE))
    for length in range(1, 7):
        for start in range(len(words) - length + 1):
            phrase = question[words[start].start() : words[start + length - 1].end()]
            add(phrase, 2, words[start].start())
            add(phrase.lower(), 3, words[start].start())
    return tuple(sorted(ranked, key=ranked.__getitem__)[:limit])


def grounded_function(function: dict[str, Any], question: str) -> dict[str, Any]:
    """Add bounded enums from public input only; leave original function unchanged."""
    result = copy.deepcopy(function)
    strings = text_candidates(question)
    numbers = [float(m.group()) for m in re.finditer(r"(?<!\w)[+-]?\d+(?:\.\d+)?", question)]
    numbers += [
        float(n)
        for n, word in NUMBER_WORDS.items()
        if re.search(r"\b" + word + r"\b", question, re.I)
    ]
    for prop in result["parameters"]["properties"].values():
        if prop.get("enum") or prop.get("type") == "boolean":
            continue
        kind = prop.get("type")
        default = prop.get("default")
        if kind == "string":
            values: list[Any] = list(strings)
            if isinstance(default, str):
                values.insert(0, default)
            prop["enum"] = list(dict.fromkeys(values))[:96]
        elif kind in ("integer", "number", "float"):
            numeric = [n for n in numbers if isfinite(n)]
            if type(default) in (int, float) and isfinite(default):
                numeric.insert(0, float(default))
            if not numeric:
                numeric = list(map(float, range(11)))
            if kind == "integer":
                prop["enum"] = sorted({int(n) for n in numeric if n.is_integer()})
            else:
                prop["enum"] = sorted(set(numeric))
            if not prop["enum"]:
                # This is an explicit fallback domain, not an answer-derived value.
                prop["enum"] = list(range(11))
        else:
            raise ValueError(f"unsupported scalar type: {kind}")
    return result


def grounded_catalog(function: dict[str, Any], question: str) -> tuple[str, ...]:
    return schema_catalog(grounded_function(function, question), limit=4096)


def scalar_call_arguments(text: str, function: dict[str, Any]) -> dict[str, Any] | None:
    normalized = normalize_schema_call(text)
    if normalized is None or not normalized.startswith(function["name"] + "("):
        return None
    node = ast.parse(normalized, mode="eval").body
    assert isinstance(node, ast.Call)
    values: dict[str, Any] = {}
    for kw in node.keywords:
        assert kw.arg is not None
        values[kw.arg] = ast.literal_eval(kw.value)
    props = function["parameters"]["properties"]
    if not set(function["parameters"].get("required", [])).issubset(values):
        return None
    for name, value in values.items():
        if name not in props:
            return None
        prop = props[name]
        expected = {
            "string": (str,),
            "integer": (int,),
            "number": (int, float),
            "float": (int, float),
            "boolean": (bool,),
        }.get(prop["type"], ())
        if type(value) not in expected:
            return None
        if type(value) in (int, float) and not isfinite(value):
            return None
        if "enum" in prop and not any(type(value) is type(v) and value == v for v in prop["enum"]):
            return None
    return values


def grounded_grade(text: str, function: dict[str, Any], answers: list[dict[str, Any]]) -> bool:
    """Own scalar AST checker against original schema and public acceptable values."""
    actual = scalar_call_arguments(text, function)
    if actual is None:
        return False
    for answer in answers:
        expected = answer.get(function["name"])
        if expected is None or any(key not in expected for key in actual):
            continue
        if all(
            (key not in actual and "" in choices)
            or (
                key in actual
                and any(
                    (
                        type(actual[key]) is type(value)
                        or (type(actual[key]) in (int, float) and type(value) in (int, float))
                    )
                    and actual[key] == value
                    for value in choices
                )
            )
            for key, choices in expected.items()
        ):
            return True
    return False
