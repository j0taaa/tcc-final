"""Six IID proposals and two original evaluations; source/classes fixed first."""

from collections.abc import Callable, Hashable
from typing import TypeVar

T = TypeVar("T")


def _matchings(nodes: tuple[int, ...]):
    if not nodes:
        yield ()
    else:
        for j in range(1, len(nodes)):
            for rest in _matchings(nodes[1:j] + nodes[j + 1 :]):
                yield ((nodes[0], nodes[j]), *rest)


MATCHINGS = tuple(_matchings(tuple(range(6))))
assert len(MATCHINGS) == 15


def pair(
    first: T,
    draw: Callable[[], T],
    key: Callable[[T], Hashable],
    randbelow: Callable[[int], int],
) -> tuple[T, T]:
    """Keep first literally; other draws are IID, not deduplicated or scored.

    The first must also follow the original source law. Classifier and source
    are fixed before all six draws. Integer selection is uniform independent
    randomness. No claim that a callback's law or neural code is verified.
    """
    pool = (first, *(draw() for _ in range(5)))
    labels = tuple(map(key, pool))
    scores = [sum(labels[i] == labels[j] for i, j in m) for m in MATCHINGS]
    minimum = min(scores)
    best = [m for m, score in zip(MATCHINGS, scores, strict=True) if score == minimum]
    chosen = randbelow(len(best))
    if not isinstance(chosen, int) or not 0 <= chosen < len(best):
        raise ValueError("randbelow must return an integer in the supplied range")
    partner = next(j if i == 0 else i for i, j in best[chosen] if i == 0 or j == 0)
    return first, pool[partner]
