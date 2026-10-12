"""Isolated exact first-row sampler for the written V10 law; no model driver."""

from collections import Counter


def integer_row(labels, classes):
    b = len(labels)
    if b < 4 or classes < 2 or any(not 0 <= i < classes for i in labels):
        raise ValueError("Require >=4 IID positions and >=2 fixed declared labels")
    counts = Counter(labels)
    r = [counts[i] for i in range(classes)]
    d = [n * (n - 1) * (n - 2) * (2 * b - n - 3) for n in r]
    s2, first = sum(n * n for n in r), labels[0]
    row = []
    for j, n in enumerate(r):
        if j == first:
            value = (classes - 1) * d[first] - sum(
                min(d[first], d[k]) for k in range(classes) if k != first
            )
        else:
            base = r[first] * n * (b * b + b * (r[first] + n) - 6 * b - s2 - r[first] * n + 7)
            value = (classes - 1) * base + min(d[first], d[j])
        row.append(value)
    assert min(row) >= 0
    assert sum(row) == (classes - 1) * r[first] * (b - 1) * (b - 2) * (b - 3)
    return row


def partner(labels, classes, randbelow):
    """Return a different original position, retaining position0 literally."""
    row = integer_row(labels, classes)
    ticket = randbelow(sum(row))
    if not 0 <= ticket < sum(row):
        raise ValueError("randbelow returned an out-of-range ticket")
    for label, weight in enumerate(row):
        if ticket < weight:
            members = [i for i, value in enumerate(labels) if i and value == label]
            rank = randbelow(len(members))
            if not 0 <= rank < len(members):
                raise ValueError("randbelow returned an out-of-range position")
            return members[rank]
        ticket -= weight
    raise AssertionError("Unreachable exact ticket remainder")
