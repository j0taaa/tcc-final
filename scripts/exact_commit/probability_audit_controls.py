"""Independent exact token-path inference for two recursive JSON-array schemas.

This reference imports neither project parsers nor probability certificates.
It is standard weighted finite-state transfer, not a reproduction of another
paper's implementation. Token aliases remain separate edges/outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import lcm
from random import Random

State = tuple[int, int]
START: State = (0, 0)
ACCEPT: State = (0, 3)


def array_step(state: State, emission: bytes, *, one_child: bool) -> State | None:
    """Stream canonical arrays whose elements are arrays; reject other bytes.

    A parent resumes in phase 1 after its child closes. Thus parents need no
    stored flags: depth and top phase (0=empty, 1=after child, 2=after comma)
    suffice. Phase 3 denotes the finished root. Empty emissions are forbidden.
    """
    if not emission:
        return None
    depth, phase = state
    for byte in emission:
        if phase == 3:
            return None
        if byte == 91 and phase in (0, 2):
            depth, phase = depth + 1, 0
        elif byte == 93 and depth > 0 and phase in (0, 1):
            depth -= 1
            phase = 1 if depth else 3
        elif byte == 44 and not one_child and depth > 0 and phase == 1:
            phase = 2
        else:
            return None
    return depth, phase


@dataclass(frozen=True)
class ArrayPlan:
    rows: tuple[tuple[int, ...], ...]
    edges: tuple[dict[State, tuple[tuple[int, State], ...]], ...]
    final_states: frozenset[State]

    @property
    def state_cells(self) -> int:
        return sum(len(layer) for layer in self.edges) + len(self.final_states)

    def backward(
        self, probabilities: tuple[tuple[Fraction, ...], ...]
    ) -> list[dict[State, Fraction]]:
        weights = self._weights(probabilities)
        suffix = [{state: Fraction(state == ACCEPT) for state in self.final_states}]
        for layer, row in zip(reversed(self.edges), reversed(weights), strict=True):
            suffix.append(
                {
                    state: sum((row[token] * suffix[-1][end] for token, end in arcs), Fraction())
                    for state, arcs in layer.items()
                }
            )
        suffix.reverse()
        return suffix

    def forward(self, probabilities: tuple[tuple[Fraction, ...], ...]) -> tuple[Fraction, int]:
        weights = self._weights(probabilities)
        masses, counts = {START: Fraction(1)}, {START: 1}
        for layer, row in zip(self.edges, weights, strict=True):
            following: dict[State, Fraction] = {}
            next_counts: dict[State, int] = {}
            for state, mass in masses.items():
                for token, end in layer[state]:
                    if not row[token]:
                        continue
                    following[end] = following.get(end, Fraction()) + mass * row[token]
                    next_counts[end] = next_counts.get(end, 0) + counts[state]
            masses, counts = following, next_counts
        return masses.get(ACCEPT, Fraction()), counts.get(ACCEPT, 0)

    def sample(
        self,
        probabilities: tuple[tuple[Fraction, ...], ...],
        suffix: list[dict[State, Fraction]],
        rng: Random,
    ) -> tuple[int, ...]:
        weights = self._weights(probabilities)
        if not suffix[0].get(START, Fraction()):
            raise ValueError("no positive-probability valid array")
        state = START
        tokens = []
        for index, (layer, row) in enumerate(zip(self.edges, weights, strict=True)):
            options = [
                (token, end, row[token] * suffix[index + 1][end])
                for token, end in layer[state]
                if row[token] * suffix[index + 1][end]
            ]
            unit = lcm(*(mass.denominator for _, _, mass in options))
            tickets = [int(mass * unit) for _, _, mass in options]
            draw = rng.randrange(sum(tickets))
            for (token, end, _), ticket in zip(options, tickets, strict=True):
                if draw < ticket:
                    tokens.append(token)
                    state = end
                    break
                draw -= ticket
        if state != ACCEPT:
            raise AssertionError("backward sampling did not finish the root")
        return tuple(tokens)

    def _weights(
        self, probabilities: tuple[tuple[Fraction, ...], ...]
    ) -> tuple[dict[int, Fraction], ...]:
        if len(probabilities) != len(self.rows):
            raise ValueError("one probability row per slot is required")
        result = []
        for tokens, values in zip(self.rows, probabilities, strict=True):
            if (
                len(tokens) != len(values)
                or any(not 0 <= v <= 1 for v in values)
                or sum(values) > 1
            ):
                raise ValueError("invalid token probabilities")
            result.append(dict(zip(tokens, values, strict=True)))
        return tuple(result)


def compile_array_plan(
    emissions: tuple[bytes | None, ...],
    rows: tuple[tuple[int, ...], ...],
    *,
    one_child: bool,
    max_state_cells: int = 100_000,
) -> ArrayPlan:
    states = {START}
    layers = []
    cache: dict[tuple[State, bytes], State | None] = {}
    for row in rows:
        if not row or len(set(row)) != len(row):
            raise ValueError("nonempty rows of distinct original token IDs are required")
        layer = {}
        following = set()
        for state in sorted(states):
            arcs = []
            for token in row:
                if type(token) is not int or not 0 <= token < len(emissions):
                    raise ValueError("invalid token ID")
                emission = emissions[token]
                if emission is None:
                    continue
                key = state, emission
                if key not in cache:
                    cache[key] = array_step(state, emission, one_child=one_child)
                end = cache[key]
                if end is not None:
                    arcs.append((token, end))
                    following.add(end)
            layer[state] = tuple(arcs)
        layers.append(layer)
        states = following
        if sum(len(part) for part in layers) + len(states) > max_state_cells:
            raise ValueError("finite-state reference exceeds its declared state budget")
    return ArrayPlan(rows, tuple(layers), frozenset(states))
