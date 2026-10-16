"""Stopped numeric continuation after a supplied literal prefix; EOS may equal PAD."""

import json

from .prefix_runtime import extent
from .stopping import StoppedNumericJSON

PREFIX = b'{"answer":'


class NumericSuffixJSON(StoppedNumericJSON):
    def __post_init__(self):
        if any(
            type(v) is not int or not 0 <= v < len(self.emissions) for v in (self.eos, self.pad)
        ):
            raise ValueError("defined original EOT/PAD IDs required, with aliasing allowed")
        if any(type(b) is not bytes for b in self.emissions):
            raise ValueError("every original ID requires an explicit byte emission")

    def step(self, state, token):
        return super().step(10 if state == 0 else state, token)


class Number(str):
    pass


def parsed_text(text):
    def constant(value):
        raise ValueError("non-JSON numeric constant")

    def fields(items):
        if len({k for k, _ in items}) != len(items):
            raise ValueError("duplicate JSON field")
        return dict(items)

    value = json.loads(
        text,
        parse_int=Number,
        parse_float=Number,
        parse_constant=constant,
        object_pairs_hook=fields,
    )
    if (
        not isinstance(value, dict)
        or set(value) != {"answer"}
        or type(value["answer"]) is not Number
    ):
        raise ValueError("one unrestricted numeric answer field required")
    return value


def full_text(language, word):
    if (
        not word
        or word[-1] != language.eos
        or language.eos in word[:-1]
        or not language.accepts(word)
    ):
        raise ValueError("a valid original-ID suffix through FIRST true EOT is required")
    text = (PREFIX + b"".join(language.emissions[v] for v in word[:-1])).decode("utf8")
    parsed_text(text)
    return text


def terminal_prefix(language, width, fixed):
    end = extent(width, fixed, language.eos)
    if fixed.get(end - 1) == language.eos and all(i in fixed for i in range(end)):
        word = tuple(fixed[i] for i in range(end))
        full_text(language, word)
        return word
    return None
