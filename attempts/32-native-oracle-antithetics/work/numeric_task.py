"""Unrestricted numerical JSON schema and exact independent answer comparison."""

import hashlib
import json
from fractions import Fraction

LEXICAL = {
    "lexWS": r"[ \t\r\n]+",
    "lexLB": r"\{",
    "lexRB": r"\}",
    "lexKey": '"answer"',
    "lexColon": ":",
    "lexNumber": r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?",
}
GRAMMAR = "S -> W lexLB W lexKey W lexColon W lexNumber W lexRB W\nW -> $ | lexWS"
PREFIX = '{"answer":'
SHA = hashlib.sha256(GRAMMAR.encode()).hexdigest()


def task(question):
    return dict(
        prefix=PREFIX,
        grammar=GRAMMAR,
        lexical=LEXICAL,
        grammar_sha256=SHA,
        instruction=(
            "Solve the problem and return exactly one JSON object with the key answer "
            "and its numeric value. No explanation, units, or markdown in the output. "
            "The JSON prefix is already supplied; continue it without repeating it.\nProblem:\n"
            + question
        ),
    )


def strict_json(text):
    def fields(items):
        if len({key for key, _ in items}) != len(items):
            raise ValueError("duplicate key")
        return dict(items)

    def constant(value):
        raise ValueError("non-JSON numeric constant")

    return json.loads(
        text,
        parse_int=Fraction,
        parse_float=Fraction,
        parse_constant=constant,
        object_pairs_hook=fields,
    )


def correct(parsed, annotated_answer):
    if not isinstance(parsed, dict) or set(parsed) != {"answer"}:
        return False
    number = parsed["answer"]
    if not isinstance(number, Fraction) or "####" not in annotated_answer:
        return False
    gold = Fraction(annotated_answer.rsplit("####", 1)[1].strip().replace(",", ""))
    return number == gold
