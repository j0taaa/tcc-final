"""Classical regular SUBSET of spellings of a known positive integer target."""

from dataclasses import dataclass

from .llada_suffix_v10 import NumericSuffixJSON
from .numeric_json import SPACE, TAIL


@dataclass(frozen=True)
class IntegerProxy(NumericSuffixJSON):
    digits: str = "1"

    def __post_init__(self):
        super().__post_init__()
        if (
            type(self.digits) is not str
            or not 1 <= len(self.digits) <= 12
            or self.digits[0] not in "123456789"
            or any(c not in "0123456789" for c in self.digits)
        ):
            raise ValueError("positive canonical integer with at most12 digits required")

    def byte_step(self, state, byte):
        d = len(self.digits)
        if state == 20:
            return 20 if byte in SPACE else -1
        if 0 <= state < d:
            if state == 0 and byte in SPACE:
                return 0
            return state + 1 if byte == ord(self.digits[state]) else -1
        if state in (d, d + 2, d + 5):
            if byte in SPACE:
                return d + 6
            if byte == ord("}"):
                return 20
            if state in (d, d + 2) and byte in b"eE":
                return d + 3
            if state == d and byte == ord("."):
                return d + 1
            if state in (d + 2, d + 5) and byte == ord("0"):
                return state
            return -1
        if state == d + 1:
            return d + 2 if byte == ord("0") else -1
        if state == d + 3:
            return d + 4 if byte in b"+-" else d + 5 if byte == ord("0") else -1
        if state == d + 4:
            return d + 5 if byte == ord("0") else -1
        if state == d + 6:
            return d + 6 if byte in SPACE else 20 if byte == ord("}") else -1
        return -1

    def step(self, state, token):
        if state == TAIL:
            return TAIL
        if token == self.eos:
            return TAIL if state == 20 else -1
        for byte in self.emissions[token]:
            state = self.byte_step(state, byte)
            if state < 0:
                return -1
        return state
