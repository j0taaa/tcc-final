"""Pure numeric consumer helpers; labels never restrict the proposal language."""

import json
import re

import numpy as np

from .test_numeric_json import Number, independent_accepts


def bf16_probabilities(bits):
    logits = (np.asarray(bits, dtype=np.uint32) << 16).view(np.float32).astype(np.float64)
    if logits.ndim != 2 or not np.isfinite(logits).all():
        raise ValueError("finite original BF16 head matrix required")
    unnormalized = np.exp(logits - logits.max(axis=1, keepdims=True))
    weights = unnormalized / unnormalized.sum(axis=1, keepdims=True)
    if not (weights > 0).all():
        raise ValueError("positive original head probabilities underflowed")
    return weights


def clamped_weights(canvas, active, active_weights, mask=151669):
    active = tuple(active)
    if active != tuple(i for i, v in enumerate(canvas) if v == mask):
        raise ValueError("head positions must be exactly the remaining active slots")
    if active_weights.shape[0] != len(active):
        raise ValueError("one original-V row per active position required")
    weights = np.zeros((len(canvas), active_weights.shape[1]), dtype=np.float64)
    for i, v in enumerate(canvas):
        if v != mask:
            if not 0 <= v < weights.shape[1]:
                raise ValueError("fixed original ID outside vocabulary")
            weights[i, v] = 1
    weights[list(active)] = active_weights
    return weights


def json_text(language, word):
    if not language.accepts(word) or not independent_accepts(language, word):
        raise AssertionError("original word, true termination or independent JSON check failed")
    return b"".join(language.emissions[v] for v in word[: word.index(language.eos)]).decode("utf8")


def normalized_number(text):
    match = re.fullmatch(r"(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?)([0-9]+))?", text)
    if match is None:
        raise ValueError("not an unrestricted JSON numeric lexeme")
    sign, whole, fraction, exponent_sign, exponent_digits = match.groups()
    fraction = fraction or ""
    digits = (whole + fraction).lstrip("0")
    if not digits:
        return 0, "0", 0, "+", "0"
    trailing = len(digits) - len(digits.rstrip("0"))
    return (
        -1 if sign else 1,
        digits.rstrip("0"),
        trailing - len(fraction),
        exponent_sign or "+",
        (exponent_digits or "0").lstrip("0") or "0",
    )


def number_equal(left, right):
    """Exact equality without expanding huge powers or converting to float."""
    a, b = normalized_number(left), normalized_number(right)
    if a[:2] != b[:2]:
        return False
    if a[0] == 0:
        return True

    # Equal significant digits require exponent_a+offset_a=exponent_b+offset_b.
    # Only labels with modest exponents are used here; retain a total exact
    # fallback for two arbitrarily huge exponent strings via decimal addition.
    def signed_sum(sign, digits, offset):
        from decimal import Decimal, localcontext

        with localcontext() as ctx:
            ctx.prec = max(len(digits), len(str(abs(offset)))) + 2
            result = Decimal(("-" if sign == "-" else "") + digits) + Decimal(offset)
            return str(result)

    return signed_sum(a[3], a[4], a[2]) == signed_sum(b[3], b[4], b[2])


def answer_equal(text, gold):
    value = json.loads(text, parse_int=Number, parse_float=Number)
    if type(value) is not dict or set(value) != {"answer"} or type(value["answer"]) is not Number:
        raise ValueError("numeric-answer object required by verifier")
    return number_equal(value["answer"], gold)
