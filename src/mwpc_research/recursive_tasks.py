"""Nonliteral recursive byte grammars with parser-independent task checkers.

These are research tasks, not runtime grammar/compiler abstractions. A task's
answer constraints never change its family's grammar.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from random import Random

from mwpc_exact.reference.grammar import CnfGrammar, Nonterminal, Terminal
from mwpc_exact.reference.normalization import (
    NonterminalRef,
    SourceGrammar,
    SourceProduction,
    TerminalRef,
    normalize_to_cnf,
)

FAMILIES = ("brackets", "arithmetic", "nested_json")
_WHITESPACE = " \t\r\n"


def family_rules(family: str) -> dict[str, tuple[tuple[str, ...], ...]]:
    """Return literal-byte productions, with uppercase names as nonterminals."""

    if family == "brackets":
        return {"S": (("(", "S", ")", "S"), ("[", "S", "]", "S"), ())}
    if family not in FAMILIES:
        raise ValueError(f"unknown recursive task family: {family}")
    rules = {
        "S": (("W", "A", "W"),),
        "D": tuple((digit,) for digit in "0123456789"),
        "W": ((), *((character, "W") for character in _WHITESPACE)),
    }
    if family == "arithmetic":
        rules["A"] = (("D",), ("(", "S", "+", "S", ")"), ("(", "S", "*", "S", ")"))
    else:
        rules["A"] = (("D",), ("[", "L", "]"))
        rules["L"] = (("W",), ("S",), ("S", ",", "L1"))
        rules["L1"] = (("S",), ("S", ",", "L1"))
    return rules


def recursive_grammar(family: str) -> CnfGrammar:
    """Compile the answer-independent byte CFG through the existing normalizer."""

    rules = family_rules(family)
    names = {name: index for index, name in enumerate(rules)}
    alphabet = sorted(
        {
            symbol
            for bodies in rules.values()
            for body in bodies
            for symbol in body
            if symbol not in names
        }
    )
    terminal_ids = {symbol: index for index, symbol in enumerate(alphabet)}
    productions = tuple(
        SourceProduction(
            index,
            names[head],
            tuple(
                NonterminalRef(names[symbol])
                if symbol in names
                else TerminalRef(terminal_ids[symbol])
                for symbol in body
            ),
        )
        for index, (head, body) in enumerate(
            (head, body) for head, bodies in rules.items() for body in bodies
        )
    )
    return normalize_to_cnf(
        SourceGrammar(
            tuple(Nonterminal(index, name) for name, index in names.items()),
            tuple(Terminal(index, ord(symbol)) for symbol, index in terminal_ids.items()),
            names["S"],
            productions,
        )
    ).grammar


def epic_grammar_spec(family: str) -> tuple[str, dict[str, str]]:
    """Same byte language for the pinned EPIC baseline, not a literal answer."""

    rules = family_rules(family)
    alphabet = sorted(
        {
            symbol
            for bodies in rules.values()
            for body in bodies
            for symbol in body
            if symbol not in rules
        }
    )
    tokens = {symbol: f"byte{ord(symbol):02x}" for symbol in alphabet}
    text = "\n".join(
        head
        + " -> "
        + " | ".join(
            " ".join(symbol if symbol in rules else tokens[symbol] for symbol in body)
            if body
            else "epsilon"
            for body in bodies
        )
        for head, bodies in rules.items()
    )
    # Rust's byte regex syntax accepts explicit hex escapes, including whitespace.
    return text, {tokens[symbol]: rf"\x{ord(symbol):02x}" for symbol in alphabet}


@dataclass(frozen=True, slots=True)
class CheckedOutput:
    syntax_valid: bool
    depth: int = 0
    leaves: tuple[int, ...] = ()
    value: int | None = None


def check_syntax(family: str, content: bytes) -> CheckedOutput:
    """Recognize/evaluate without calling normalization, CKY or the solver.

    Inputs exceeding the study's 4096-byte checker envelope are rejected.
    Syntax is separate from every task-specific functional constraint.
    """

    if family not in FAMILIES:
        raise ValueError(f"unknown recursive task family: {family}")
    if len(content) > 4096:
        return CheckedOutput(False)
    try:
        text = content.decode("ascii")
        if family == "brackets":
            stack: list[str] = []
            depth = 0
            counts = [0, 0]
            for character in text:
                if character in "([":
                    stack.append(character)
                    counts[character == "["] += 1
                    depth = max(depth, len(stack))
                elif (
                    character not in ")]"
                    or not stack
                    or stack.pop() != {")": "(", "]": "["}[character]
                ):
                    return CheckedOutput(False)
            return CheckedOutput(not stack, depth, tuple(counts))
        if family == "nested_json":
            if any(character not in "0123456789[]," + _WHITESPACE for character in text):
                return CheckedOutput(False)
            parsed = json.loads(text)

            def visit(value: object, depth: int) -> tuple[tuple[int, ...], int]:
                if type(value) is int and 0 <= value <= 9:
                    return (value,), depth
                if not isinstance(value, list):
                    raise ValueError("JSON leaf must be a single decimal digit")
                children = [visit(child, depth + 1) for child in value]
                return (
                    tuple(leaf for leaves, _ in children for leaf in leaves),
                    max((level for _, level in children), default=depth + 1),
                )

            leaves, depth = visit(parsed, 0)
            return CheckedOutput(True, depth, leaves)

        position = 0

        def skip_space() -> None:
            nonlocal position
            while position < len(text) and text[position] in _WHITESPACE:
                position += 1

        def expression() -> tuple[int, tuple[int, ...], int]:
            nonlocal position
            skip_space()
            if position == len(text):
                raise ValueError("missing expression")
            character = text[position]
            position += 1
            if character in "0123456789":
                result: tuple[int, tuple[int, ...], int] = int(character), (int(character),), 0
            elif character == "(":
                left, left_leaves, left_depth = expression()
                operator = text[position]
                position += 1
                if operator not in "+*":
                    raise ValueError("invalid operator")
                right, right_leaves, right_depth = expression()
                if text[position] != ")":
                    raise ValueError("missing closing parenthesis")
                position += 1
                result = (
                    left + right if operator == "+" else left * right,
                    left_leaves + right_leaves,
                    1 + max(left_depth, right_depth),
                )
            else:
                raise ValueError("invalid expression")
            skip_space()
            return result

        value, leaves, depth = expression()
        return CheckedOutput(position == len(text), depth, leaves, value)
    except (UnicodeDecodeError, ValueError, IndexError, RecursionError):
        return CheckedOutput(False)


@dataclass(frozen=True, slots=True)
class RecursiveTask:
    task_id: str
    family: str
    prompt: str
    required_leaves: tuple[int, ...]
    minimum_depth: int
    target_value: int | None = None

    def check(self, content: bytes) -> tuple[CheckedOutput, bool]:
        checked = check_syntax(self.family, content)
        leaves_match = (
            Counter(checked.leaves) == Counter(self.required_leaves)
            if self.family == "arithmetic"
            else checked.leaves == self.required_leaves
        )
        success = (
            checked.syntax_valid
            and checked.depth >= self.minimum_depth
            and leaves_match
            and (self.target_value is None or checked.value == self.target_value)
        )
        return checked, success


def generated_witness(family: str, seed: int) -> bytes:
    """Seeded feasible synthetic context; never a claimed sample of model logits."""

    random = Random(seed)
    if family == "brackets":
        pairs = [random.choice(("()", "[]")) for _ in range(3)]
        return (pairs[0][0] + pairs[1] + pairs[2] + pairs[0][1]).encode()
    digits = [str(random.randrange(4)) for _ in range(3)]
    if family == "arithmetic":
        operators = [random.choice("+*") for _ in range(2)]
        return f"({digits[0]}{operators[0]}({digits[1]}{operators[1]}{digits[2]}))".encode()
    if family == "nested_json":
        return f"[{digits[0]},[{digits[1]},{digits[2]}]]".encode()
    raise ValueError(f"unknown recursive task family: {family}")
