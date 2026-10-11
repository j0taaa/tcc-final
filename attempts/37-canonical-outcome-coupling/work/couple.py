"""Oracle-only research reference; full draws and an independent hash RNG.

No model integration, gold answer, estimated probabilities or mutable imports
from another attempt. See theory-v1 for the guarantee and full-cost limitation.
"""

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class LinearClass:
    """Lazy random linear hash of an injective encoding of finite byte keys."""

    def __init__(self, getrandbits: Callable[[int], int]):
        self._getrandbits = getrandbits
        self._mask = 0
        self._width = 0

    def __call__(self, key: bytes) -> bool:
        if not isinstance(key, bytes):
            raise TypeError("canonical keys must be bytes")
        encoded = (1 << (8 * len(key))) | int.from_bytes(key, "big")
        width = encoded.bit_length()
        if width > self._width:
            extra = width - self._width
            bits = self._getrandbits(extra)
            if not isinstance(bits, int) or not 0 <= bits < (1 << extra):
                raise ValueError("getrandbits returned an invalid bit block")
            self._mask |= bits << self._width
            self._width = width
        return bool((self._mask & encoded).bit_count() & 1)


def pair(
    draw: Callable[[], T],
    key: Callable[[T], bytes],
    *,
    hash_bits: Callable[[int], int],
    max_draws: int | None = 12,
) -> tuple[T, T, int]:
    """Return literal first and selected draws; deterministic cap keeps second.

    draw must be iid COMPLETE generations, including failures. key is a fixed
    deterministic outcome map. hash_bits must be independent of draw. External
    exceptions propagate; a wall-time truncation has no preservation guarantee.
    """
    if max_draws is not None and (
        isinstance(max_draws, bool)
        or not isinstance(max_draws, int)
        or max_draws < 4
        or max_draws % 2
    ):
        raise ValueError("max_draws must be None or an even integer >=4")
    classify = LinearClass(hash_bits)
    first, original_second = draw(), draw()
    first_class = classify(key(first))
    if classify(key(original_second)) != first_class:
        return first, original_second, 2
    height, used = 2, 2
    while max_draws is None or used < max_draws:
        candidate = draw()
        used += 1
        height += 1 if classify(key(candidate)) == first_class else -1
        if height in (0, 3):
            return first, candidate, used
        del candidate  # Do not retain discarded payloads across another draw.
    return first, original_second, used
