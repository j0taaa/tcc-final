"""Classical six-pool towers; V3 proves this particular law's population safety."""

from collections.abc import Callable, Hashable
from typing import TypeVar

T = TypeVar("T")


def pair6(
    draw: Callable[[], T], key: Callable[[T], Hashable], randbelow: Callable[[int], int]
) -> tuple[T, T]:
    """Six IID complete sources, fixed key, independent unbiased randbelow.

    This is not a native dLLM adapter. All sources, key work and downstream
    work count. Failed/incomplete sources must be original payloads in draw's
    law; no silent retry. The first returned object is literally the first.
    """
    pool = [draw() for _ in range(6)]
    labels = [key(value) for value in pool]
    order = list(dict.fromkeys(labels))
    for j in range(len(order) - 1, 0, -1):
        other = randbelow(j + 1)
        order[j], order[other] = order[other], order[j]
    tickets = [label for label in order for _ in range(2 * labels.count(label))]
    first_tickets = [index for index, label in enumerate(tickets) if label == labels[0]]
    location = first_tickets[randbelow(len(first_tickets))]
    partner = tickets[(location + 6) % 12]
    eligible = [index for index in range(1, 6) if labels[index] == partner]
    return pool[0], pool[eligible[randbelow(len(eligible))]]
