"""Tiny ENUMERATED rational reference, not the polynomial compiler or trainer.

Returns loss=log(log_ratio)+offset and exact ORIGINAL source-logit derivatives.
Classical conditional log/CRPS scores; no neural readout or native binding.
"""

import itertools
import json
from fractions import Fraction


def meaning(data):
    """Exact sign/order and normalized mantissa; do not expand10^order."""

    def integer_value(text):
        result = 0
        for char in text.removeprefix("-").removeprefix("+"):
            result = 10 * result + ord(char) - ord("0")
        return -result if text.startswith("-") else result

    try:
        parsed = json.loads(
            data.decode("ascii"), parse_int=lambda s: ("NUM", s), parse_float=lambda s: ("NUM", s)
        )
        if not isinstance(parsed, tuple) or parsed[0] != "NUM":
            return None
        body, _, exponent = parsed[1].lower().partition("e")
        sign = -1 if body.startswith("-") else 1
        integer, _, fractional = body.removeprefix("-").partition(".")
        significant = (integer + fractional).lstrip("0")
        if not significant:
            return (0, 0), Fraction(0)
        coefficient, digits = integer_value(significant), len(significant)
        order = integer_value(exponent or "0") - len(fractional) + digits - 1
        return (sign, order), Fraction(coefficient, 10 ** (digits - 1))
    except (UnicodeError, ValueError):
        return None


def score(rows, byte_of, label):
    """Fixed original slots; aliases/empty bytes/JSON whitespace retained."""
    rows = [{t: Fraction(w) for t, w in row.items()} for row in rows]
    if any(w < 0 for row in rows for w in row.values()):
        raise ValueError("nonnegative finite rational weights required")
    target = meaning(label)
    if target is None:
        raise ValueError("numerical JSON label required")
    category, observed_mantissa = target
    pool = []
    for tape in itertools.product(*rows):
        weight = Fraction(1)
        for token, row in zip(tape, rows, strict=True):
            weight *= row[token]
        semantic = meaning(b"".join(byte_of[t] for t in tape))
        if weight and semantic is not None:
            pool.append((tape, weight, *semantic))
    total = sum((w for _, w, _, _ in pool), Fraction(0))
    if not total:
        raise ValueError("EMPTY numerical support")
    selected = [(t, w, m) for t, w, c, m in pool if c == category]
    mass = sum((w for _, w, _ in selected), Fraction(0))
    if not mass:
        raise ValueError("UNSUPPORTED semantic category: infinite loss")
    selected = [(t, w / mass, m) for t, w, m in selected]
    gradient = {(i, t): Fraction(0) for i, row in enumerate(rows) for t in row}
    for tape, weight, _, _ in pool:
        for i, token in enumerate(tape):
            gradient[i, token] += weight / total
    for tape, weight, _ in selected:
        for i, token in enumerate(tape):
            gradient[i, token] -= weight
    crps = Fraction(0)
    if category != (0, 0):
        cross = sum((w * min(m, observed_mantissa) for _, w, m in selected), Fraction(0))
        pair = sum((w * v * min(m, n) for _, w, m in selected for _, v, n in selected), Fraction(0))
        crps = observed_mantissa - 2 * cross + pair
        features = [
            2
            * (
                sum((v * min(m, n) for _, v, n in selected), Fraction(0))
                - min(m, observed_mantissa)
            )
            for _, _, m in selected
        ]
        center = sum((w * f for (_, w, _), f in zip(selected, features, strict=True)), Fraction(0))
        for (tape, weight, _), feature in zip(selected, features, strict=True):
            for i, token in enumerate(tape):
                gradient[i, token] += weight * (feature - center) / 9
    return {
        "log_ratio": total / mass,
        "offset": crps / 9,
        "crps": crps,
        "gradient": gradient,
        "valid_traces": len(pool),
        "Z": total,
        "B": mass,
    }
