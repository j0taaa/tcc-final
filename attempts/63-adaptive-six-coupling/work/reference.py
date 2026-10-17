"""Original-payload cap-six coupling, three fixed keys; frozen V3 attaining table."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

ACTIONS = {
    "0000": 0,
    "0001": 1,
    "0011": 1,
    "0101": 1,
    "0110": 1,
    "0111": 1,
    "00100": 0,
    "00121": 1,
    "00122": 2,
    "01000": 0,
    "01002": 1,
    "01020": 1,
    "01021": 1,
    "01022": 2,
    "01120": 1,
    "01121": 1,
    "01200": 1,
    "01201": 1,
    "01202": 2,
    "01210": 1,
    "01211": 1,
    "01220": 2,
    "01222": 2,
    "001010": 0,
    "001011": 1,
    "001012": 2,
    "001020": 0,
    "001021": 2,
    "001022": 1,
    "001200": 0,
    "001201": 2,
    "001202": 1,
    "010010": 0,
    "010011": 1,
    "010012": 2,
    "011220": 1,
    "011221": 1,
    "011222": 2,
    "012120": 1,
    "012121": 1,
    "012122": 2,
    "012210": 1,
    "012211": 1,
    "012212": 2,
}


def couple(draw: Callable[[], T], key: Callable[[T], int]) -> tuple[T, T, int]:
    """Retain literal first; use keys only to select a literal nonfirst payload."""
    seen: dict[int, str] = {}
    payloads, names = [], []
    for _ in range(6):
        payload = draw()
        actual = key(payload)
        if actual not in (0, 1, 2):
            raise ValueError("The fixed observable must take values in {0,1,2}.")
        name = seen.setdefault(actual, str(len(seen)))
        payloads.append(payload)
        names.append(name)
        chosen = ACTIONS.get("".join(names))
        if chosen is not None:
            index = next(i for i in range(1, len(names)) if names[i] == str(chosen))
            return payloads[0], payloads[index], len(payloads)
    raise RuntimeError("The frozen policy failed to stop by six calls.")
