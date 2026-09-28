"""Finite schema-only API pilot; never derive allowed values from gold answers."""

from __future__ import annotations

import ast
from itertools import product
from typing import Any


def normalize_schema_call(text: str) -> str | None:
    try:
        node = ast.parse(text.strip(), mode="eval").body
        if not isinstance(node, ast.Call) or node.args:
            return None

        def name(n: ast.expr) -> str:
            if isinstance(n, ast.Name):
                return n.id
            if isinstance(n, ast.Attribute):
                return name(n.value) + "." + n.attr
            raise ValueError("invalid function name")

        arguments = {}
        for kw in node.keywords:
            if kw.arg is None or kw.arg in arguments:
                return None
            value = ast.literal_eval(kw.value)
            if type(value) not in (str, int, float, bool):
                return None
            arguments[kw.arg] = value
        return (
            name(node.func)
            + "("
            + ",".join(f"{k}={v!r}" for k, v in sorted(arguments.items()))
            + ")"
        )
    except (SyntaxError, ValueError, TypeError, RecursionError):
        return None


def schema_catalog(function: dict[str, Any], *, limit: int = 512) -> tuple[str, ...]:
    """Enumerate all scalar enum/boolean arguments and optional omissions."""
    properties = function["parameters"]["properties"]
    required = set(function["parameters"].get("required", []))
    missing = object()
    names, domains = [], []
    size = 1
    for name, prop in sorted(properties.items()):
        values = prop.get("enum", [False, True] if prop.get("type") == "boolean" else None)
        if not values or any(type(v) not in (str, int, float, bool) for v in values):
            raise ValueError("schema requires an unbounded or unsupported argument")
        domain = list(values) + ([missing] if name not in required else [])
        size *= len(domain)
        if size > limit:
            raise ValueError("schema catalog size limit")
        names.append(name)
        domains.append(domain)
    calls = []
    for values in product(*domains):
        call = (
            function["name"]
            + "("
            + ",".join(
                f"{name}={value!r}"
                for name, value in zip(names, values, strict=True)
                if value is not missing
            )
            + ")"
        )
        normalized = normalize_schema_call(call)
        if normalized is None:
            raise ValueError("unsupported function or parameter name")
        calls.append(normalized)
    return tuple(sorted(set(calls)))


def strict_schema_grade(text: str, function: dict[str, Any], answers: list[dict[str, Any]]) -> bool:
    """Own strict scalar AST evaluator against public BFCL acceptable values.

    This is not the official BFCL checker (which also normalizes strings).
    Empty-string acceptable values mean optional omission in this BFCL subset.
    """
    normalized = normalize_schema_call(text)
    if normalized is None or normalized not in schema_catalog(function):
        return False
    node = ast.parse(normalized, mode="eval").body
    assert isinstance(node, ast.Call)
    actual = {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords}
    for answer in answers:
        expected = answer.get(function["name"])
        if expected is None:
            continue
        if all(
            (key not in actual and "" in values)
            or (
                key in actual
                and any(type(actual[key]) is type(v) and actual[key] == v for v in values)
            )
            for key, values in expected.items()
        ) and all(key in expected for key in actual):
            return True
    return False
