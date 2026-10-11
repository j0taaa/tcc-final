"""Predeclared root/left choice, original contiguous prefix only; no golds."""

import re
from fractions import Fraction


def choice(text):
    root = re.match(r'^\s*\{\s*"op"\s*:\s*"(add|sub|mul|div)"', text)
    if root is None:
        return "ROOT_UNKNOWN", "LEFT_UNKNOWN"
    args = re.match(r'\s*,\s*"args"\s*:\s*\[\s*', text[root.end() :])
    if args is None:
        return root[1], "LEFT_UNKNOWN"
    suffix = text[root.end() + args.end() :]
    child = re.match(r'^\{\s*"op"\s*:\s*"(add|sub|mul|div)"', suffix)
    if child is not None:
        return root[1], "CALL:" + child[1]
    number = re.match(r"^(-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\s*,", suffix)
    if number is not None and len(number[1]) <= 256:
        exponent = re.search(r"[eE]([+-]?[0-9]+)$", number[1])
        if exponent is None or abs(int(exponent[1])) <= 1024:
            return root[1], "NUMBER:" + str(Fraction(number[1]))
    return root[1], "LEFT_UNKNOWN"


def snapshot_key(snapshot, tokenizer, chat_length):
    if snapshot is None:
        return "NO_YIELD", "LEFT_UNKNOWN"
    ids = snapshot[0][0, chat_length:].tolist()
    end = next((i for i, t in enumerate(ids) if t in (126336, 126081, 126348)), len(ids))
    return choice(tokenizer.decode(ids[:end], skip_special_tokens=False))
