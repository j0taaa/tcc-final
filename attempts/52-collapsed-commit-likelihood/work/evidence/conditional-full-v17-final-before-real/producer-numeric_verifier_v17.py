"""Independent positive-integer equality via significant/exponent STRINGS.

No exponent expansion, float conversion or bound on the generated exponent.
Known labels here are positive canonical integers; generation stays unrestricted.
"""

import json
import re


class NumericLexeme(str):
    pass


def unique_object(items):
    if len({k for k, _ in items}) != len(items):
        raise ValueError("duplicate JSON key")
    return dict(items)


def independent_answer_equal(text, gold):
    if re.fullmatch(r"[1-9][0-9]*", gold) is None:
        raise ValueError("known positive canonical integer label required")
    value = json.loads(
        text, parse_int=NumericLexeme, parse_float=NumericLexeme, object_pairs_hook=unique_object
    )
    if (
        type(value) is not dict
        or set(value) != {"answer"}
        or type(value["answer"]) is not NumericLexeme
    ):
        raise ValueError("one numeric answer required")
    match = re.fullmatch(
        r"(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?)([0-9]+))?", value["answer"]
    )
    if match is None:
        raise ValueError("JSON numeric lexeme required")
    sign, whole, fraction, exponent_sign, exponent_digits = match.groups()
    if sign:
        return False
    fraction = fraction or ""
    digits = (whole + fraction).lstrip("0")
    if not digits:
        return False
    core = digits.rstrip("0")
    gold_core = gold.rstrip("0")
    if core != gold_core:
        return False
    exponent_required = (len(gold) - len(gold_core)) - (len(digits) - len(core) - len(fraction))
    exponent = (exponent_digits or "0").lstrip("0") or "0"
    if exponent_required == 0:
        return exponent == "0"
    return exponent == str(abs(exponent_required)) and (
        (exponent_sign == "-") == (exponent_required < 0)
    )
