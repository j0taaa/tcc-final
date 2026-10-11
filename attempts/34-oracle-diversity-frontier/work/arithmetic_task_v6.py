"""Executable recursive JSON; grammar/classification never sees an answer."""

import json
import re
from fractions import Fraction

LEXICAL = {
    "lexWS": r"[ \t\r\n]+",
    "lexLB": r"\{",
    "lexRB": r"\}",
    "lexLS": r"\[",
    "lexRS": r"\]",
    "lexColon": ":",
    "lexComma": ",",
    "lexKeyOp": '"op"',
    "lexKeyArgs": '"args"',
    "lexAdd": '"add"',
    "lexSub": '"sub"',
    "lexMul": '"mul"',
    "lexDiv": '"div"',
    "lexNumber": r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?",
}
# Small rules avoid an original-normalizer expansion across many nullable Ws.
GRAMMAR = """S -> W Call W
Call -> lexLB C1
C1 -> W lexKeyOp C2
C2 -> W lexColon C3
C3 -> W Op C4
C4 -> W lexComma C5
C5 -> W lexKeyArgs C6
C6 -> W lexColon C7
C7 -> W lexLS C8
C8 -> W Value C9
C9 -> W lexComma C10
C10 -> W Value C11
C11 -> W lexRS C12
C12 -> W lexRB
Value -> lexNumber | Call
Op -> lexAdd | lexSub | lexMul | lexDiv
W -> $ | lexWS"""
PREFIX = '{"op":"'


def instruction(question):
    return (
        "Solve the word problem by writing an executable arithmetic expression as JSON. "
        'A number is a leaf. Every operation is {"op":"add","args":[left,right]}, '
        "with op add, sub, mul, or div. Nest operations when needed. "
        "The root must be an operation. Use the numbers in the problem and arithmetic "
        "to express its answer. No explanations, markdown or extra fields. "
        "The JSON prefix is already supplied; continue it without repeating it.\nProblem:\n"
        + question
    )


def root_operator(text):
    match = re.match(r'^\s*\{\s*"op"\s*:\s*"(add|sub|mul|div)"', text)
    return match.group(1) if match else None


def evaluate(text):
    def fields(items):
        if len({k for k, _ in items}) != len(items):
            raise ValueError("duplicate key")
        return dict(items)

    def invalid_constant(_):
        raise ValueError("non-JSON numeric constant")

    value = json.loads(
        text,
        parse_int=Fraction,
        parse_float=Fraction,
        parse_constant=invalid_constant,
        object_pairs_hook=fields,
    )
    remaining = 1024

    def run(node, depth=0):
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 64:
            raise ValueError("interpreter resource budget")
        if isinstance(node, Fraction):
            return node
        if not isinstance(node, dict) or set(node) != {"op", "args"}:
            raise ValueError("invalid node fields/type")
        args = node["args"]
        if not isinstance(args, list) or len(args) != 2:
            raise ValueError("operation must have two arguments")
        a, b = (run(x, depth + 1) for x in args)
        op = node["op"]
        if op == "add":
            return a + b
        if op == "sub":
            return a - b
        if op == "mul":
            return a * b
        if op == "div":
            return a / b
        raise ValueError("unknown operation")

    if not isinstance(value, dict):
        raise ValueError("root must be an operation")
    return run(value)
