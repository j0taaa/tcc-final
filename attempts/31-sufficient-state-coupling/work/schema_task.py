"""Common schema-only JSON argument filling; classical CFG, not a novelty claim."""

import hashlib
import json
import re

JSON_STRING = r'"([^"\\\x00-\x1f]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})*"'
KINDS = {"string", "integer", "float", "boolean", "array", "tuple", "dict", "any"}


def eligibility(record):
    if len(record["function"]) != 1 or len(record["question"]) != 1:
        return "not_single_call"
    params = record["function"][0]["parameters"]
    props, required = params["properties"], params.get("required", [])
    if not required or any(k not in props for k in required):
        return "no_required_prefix"
    if len(props) > 12 or any(s.get("type") not in KINDS for s in props.values()):
        return "schema_scope"
    if len(json.dumps(record, ensure_ascii=False)) > 7000:
        return "input_character_budget"
    return None


def task(record):
    reason = eligibility(record)
    if reason:
        raise ValueError(reason)
    function = record["function"][0]
    params = function["parameters"]
    props, required = params["properties"], params["required"]
    fields = list(required) + [k for k in props if k not in required]
    lexical = {
        "lexWS": r"[ \t\r\n]+",
        "lexString": JSON_STRING,
        "lexInt": r"-?(0|[1-9][0-9]*)",
        "lexNumber": r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?",
    }
    grammar = ["W -> $ | lexWS"]

    def token(name, text):
        lexical["lex" + name] = re.escape(text)
        grammar.append(f"{name} -> W lex{name} W")
        return name

    for name, text in (
        ("LB", "{"),
        ("RB", "}"),
        ("LA", "["),
        ("RA", "]"),
        ("Colon", ":"),
        ("Comma", ","),
        ("True", "true"),
        ("False", "false"),
        ("Null", "null"),
    ):
        token(name, text)
    grammar += [
        "String -> W lexString W",
        "Integer -> W lexInt W",
        "Number -> W lexNumber W",
        "Bool -> True | False",
        "Value -> String | Number | Bool | Null | Object | Array",
        "Object -> LB RB | LB Members RB",
        "Members -> String Colon Value | String Colon Value Comma Members",
        "Array -> LA RA | LA Elements RA",
        "Elements -> Value | Value Comma Elements",
    ]

    def kind(spec, label):
        typ = spec["type"]
        simple = {
            "string": "String",
            "integer": "Integer",
            "float": "Number",
            "boolean": "Bool",
            "dict": "Object",
            "any": "Value",
        }
        if typ in simple:
            return simple[typ]
        item = spec.get("items", {})
        body = kind(item, label + "Item") if item.get("type") in KINDS else "Value"
        grammar.extend(
            (
                f"{label} -> LA RA | LA {label}Items RA",
                f"{label}Items -> {body} | {body} Comma {label}Items",
            )
        )
        return label

    token("NameKey", json.dumps("name"))
    token("ArgsKey", json.dumps("arguments"))
    token("FnName", json.dumps(function["name"], ensure_ascii=True))
    grammar.append("S -> LB NameKey Colon FnName Comma ArgsKey Colon Args RB")
    grammar.append("Args -> LB A0N")
    for i, field in enumerate(fields):
        name = token(f"Key{i}", json.dumps(field, ensure_ascii=True))
        value = kind(props[field], f"Type{i}")
        for prev in ("N", "Y"):
            prefix = "Comma " if prev == "Y" else ""
            grammar.append(f"A{i}{prev} -> {prefix}{name} Colon {value} A{i + 1}Y")
            if field not in required:
                grammar.append(f"A{i}{prev} -> A{i + 1}{prev}")
    grammar.extend((f"A{len(fields)}N -> RB", f"A{len(fields)}Y -> RB"))
    prefix = (
        "{"
        + json.dumps("name")
        + ":"
        + json.dumps(function["name"], ensure_ascii=True)
        + ","
        + json.dumps("arguments")
        + ":{"
        + json.dumps(fields[0], ensure_ascii=True)
        + ":"
    )
    instruction = (
        "Return exactly one JSON function call with keys name and arguments. "
        "Use the provided function and answer the user request. Required argument keys must "
        "occur first in their listed order; optional keys may follow in schema order. "
        "The JSON prefix is already supplied; continue it without repeating it.\nFunction:\n"
        + json.dumps(function, ensure_ascii=False)
        + "\nUser:\n"
        + record["question"][0][0]["content"]
    )
    source = "\n".join(grammar)
    return dict(
        prefix=prefix,
        instruction=instruction,
        grammar=source,
        lexical=lexical,
        grammar_sha256=hashlib.sha256(source.encode()).hexdigest(),
    )
