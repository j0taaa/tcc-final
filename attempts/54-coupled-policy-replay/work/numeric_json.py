"""Classical byte DFA for one unrestricted JSON-number answer, EOT and PAD."""

from dataclasses import dataclass

SPACE = frozenset(b" \t\r\n")
DIGIT = frozenset(b"0123456789")
TAIL = 21
STATE_COUNT = 22


def byte_step(state, byte):
    if state == 0:
        return 0 if byte in SPACE else 1 if byte == ord("{") else -1
    if state == 1:
        return 1 if byte in SPACE else 2 if byte == ord('"') else -1
    if 2 <= state <= 8:
        return state + 1 if byte == b'answer"'[state - 2] else -1
    if state == 9:
        return 9 if byte in SPACE else 10 if byte == ord(":") else -1
    if state == 10 and byte in SPACE:
        return 10
    if state in (10, 11):
        if state == 10 and byte == ord("-"):
            return 11
        return 12 if byte == ord("0") else 13 if byte in DIGIT else -1
    if state == 14:
        return 15 if byte in DIGIT else -1
    if state == 16:
        return 17 if byte in b"+-" else 18 if byte in DIGIT else -1
    if state == 17:
        return 18 if byte in DIGIT else -1
    if state in (12, 13, 15, 18):
        if state in (13, 15, 18) and byte in DIGIT:
            return state
        if state in (12, 13) and byte == ord("."):
            return 14
        if state in (12, 13, 15) and byte in b"eE":
            return 16
        if byte in SPACE:
            return 19
        return 20 if byte == ord("}") else -1
    if state == 19:
        return 19 if byte in SPACE else 20 if byte == ord("}") else -1
    if state == 20:
        return 20 if byte in SPACE else -1
    return -1


@dataclass(frozen=True)
class NumericJSON:
    emissions: tuple[bytes, ...]
    eos: int
    pad: int

    def __post_init__(self):
        if self.eos == self.pad or any(
            not 0 <= v < len(self.emissions) for v in (self.eos, self.pad)
        ):
            raise ValueError("distinct defined EOT/PAD IDs required")
        if any(type(b) is not bytes for b in self.emissions):
            raise ValueError("every original ID requires an explicit byte emission")

    def step(self, state, token):
        if state == TAIL:
            return TAIL if token == self.pad else -1
        if token == self.eos:
            return TAIL if state == 20 else -1
        for byte in self.emissions[token]:
            state = byte_step(state, byte)
            if state < 0:
                break
        return state

    def accepts(self, word):
        state = 0
        for token in word:
            if type(token) is not int or not 0 <= token < len(self.emissions):
                return False
            state = self.step(state, token)
            if state < 0:
                return False
        return state == TAIL

    def classes(self):
        """All original IDs, including all-dead and epsilon aliases, retained."""
        groups = {}
        for token in range(len(self.emissions)):
            effect = tuple(self.step(state, token) for state in range(STATE_COUNT))
            groups.setdefault(effect, []).append(token)
        effects = tuple(groups)
        members = tuple(tuple(groups[e]) for e in effects)
        mapping = [None] * len(self.emissions)
        for group, tokens in enumerate(members):
            for token in tokens:
                mapping[token] = group
        return effects, members, tuple(mapping)

    def small_reference_graph(self, length):
        """Only for tiny independent oracles, never expand real V at every state."""
        from .reference import DAG

        if not 1 <= length <= 64 or len(self.emissions) > 256:
            raise ValueError("explicit original-ID graph is a small-oracle API")
        layers = []
        for i in range(length):
            states = range(1) if i == 0 else range(STATE_COUNT)
            layers.append(
                tuple(
                    tuple(
                        (v, target)
                        for v in range(len(self.emissions))
                        if (target := self.step(state, v)) >= 0
                    )
                    for state in states
                )
            )
        return DAG(tuple(layers), tuple(s == TAIL for s in range(STATE_COUNT)))
