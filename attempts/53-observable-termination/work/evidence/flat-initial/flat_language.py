"""Classical flat string-language analysis for a bounded acyclic graph."""

from enum import Enum


class Extremum(Enum):
    EMPTY = 0
    MANY = 1


EMPTY, MANY = Extremum.EMPTY, Extremum.MANY


def join(a, b):
    if a is EMPTY:
        return b
    if b is EMPTY or a == b:
        return a
    return MANY


def concat(a, b):
    if a is EMPTY or b is EMPTY:
        return EMPTY
    if a is MANY or b is MANY:
        return MANY
    return a + b


def classify(words):
    value = EMPTY
    for word in words:
        if type(word) is not bytes:
            raise TypeError("projected byte strings required")
        value = join(value, word)
    return value


def analyze(edges, terminals):
    """Edges are (projected output bytes, target); topological indices required.

    Terminals accept epsilon. First-EOS handling belongs in graph construction,
    not in a guessed string-trimming rule. No numeric weights/model are used.
    """
    n = len(edges)
    if any(type(i) is not int or not 0 <= i < n for i in terminals):
        raise ValueError("declared graph terminal required")
    values = [EMPTY] * n
    for i in reversed(range(n)):
        value = b"" if i in terminals else EMPTY
        for label, target in edges[i]:
            if type(label) is not bytes or type(target) is not int or not i < target < n:
                raise ValueError("bytes on strictly forward DAG edges required")
            value = join(value, concat(label, values[target]))
        values[i] = value
    return values
