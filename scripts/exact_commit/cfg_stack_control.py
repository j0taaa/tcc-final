"""Independent exact reachable-stack transfer for two-type delimiters.

Only stdlib; no grammar compiler, parsing chart or project certificate imports.
This is a strong local classical control, not an execution of another paper.
One-byte token semantics allow the necessary remaining-depth pruning below.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import lcm
from random import Random
from time import monotonic, perf_counter

Stack = tuple[int, ...]


class StackLimit(TimeoutError):
    pass


def step(stack: Stack, byte: int) -> Stack | None:
    if byte in (40, 91):
        return (*stack, byte)
    if byte in (41, 93) and stack and stack[-1] == {41: 40, 93: 91}[byte]:
        return stack[:-1]
    return None


@dataclass(frozen=True)
class StackPosterior:
    plan: StackPlan
    probabilities: tuple[tuple[Fraction, ...], ...]
    suffix: tuple[dict[Stack, Fraction], ...]
    valid_mass: Fraction
    marginals: tuple[tuple[Fraction, ...], ...]
    mass_seconds: float
    marginal_seconds: float

    def sample(self, rng: Random) -> tuple[int, ...]:
        if not self.valid_mass:
            raise ValueError("zero valid mass")
        stack: Stack = ()
        output = []
        for i, layer in enumerate(self.plan.layers):
            arcs = layer[stack]
            weights = [
                self.probabilities[i][j] * self.suffix[i + 1].get(end, Fraction())
                for j, end in arcs
            ]
            scale = lcm(*(w.denominator for w in weights))
            integers = [w.numerator * (scale // w.denominator) for w in weights]
            draw = rng.randrange(sum(integers))
            for (j, end), integer in zip(arcs, integers, strict=True):
                if draw < integer:
                    output.append(self.plan.rows[i][j])
                    stack = end
                    break
                draw -= integer
        return tuple(output)


@dataclass(frozen=True)
class StackPlan:
    rows: tuple[tuple[int, ...], ...]
    layers: tuple[dict[Stack, tuple[tuple[int, Stack], ...]], ...]
    cells: int
    transitions: int

    def evaluate(self, probabilities: tuple[tuple[Fraction, ...], ...]) -> StackPosterior:
        if len(probabilities) != len(self.rows) or any(
            len(p) != len(r) or any(x < 0 for x in p) or sum(p) > 1
            for r, p in zip(self.rows, probabilities, strict=True)
        ):
            raise ValueError("invalid original probability rows")
        started = perf_counter()
        suffix: list[dict[Stack, Fraction]] = [{} for _ in range(len(self.rows) + 1)]
        suffix[-1][()] = Fraction(1)
        for i in reversed(range(len(self.rows))):
            suffix[i] = {
                state: sum(
                    (probabilities[i][j] * suffix[i + 1].get(end, Fraction()) for j, end in arcs),
                    Fraction(),
                )
                for state, arcs in self.layers[i].items()
            }
        total = suffix[0].get((), Fraction())
        mass_seconds = perf_counter() - started
        started = perf_counter()
        marginal = []
        prefix = {(): Fraction(1)}
        for i, layer in enumerate(self.layers):
            masses = [Fraction()] * len(self.rows[i])
            next_prefix: dict[Stack, Fraction] = {}
            for state, mass in prefix.items():
                for j, end in layer[state]:
                    contribution = mass * probabilities[i][j]
                    next_prefix[end] = next_prefix.get(end, Fraction()) + contribution
                    masses[j] += contribution * suffix[i + 1].get(end, Fraction())
            marginal.append(tuple(m / total if total else Fraction() for m in masses))
            prefix = next_prefix
        if prefix.get((), Fraction()) != total:
            raise RuntimeError("forward/backward disagreement")
        return StackPosterior(
            self,
            probabilities,
            tuple(suffix),
            total,
            tuple(marginal),
            mass_seconds,
            perf_counter() - started,
        )


def compile_stack_plan(
    emissions: tuple[bytes, ...],
    rows: tuple[tuple[int, ...], ...],
    *,
    max_cells: int = 200_000,
    max_transitions: int = 1_000_000,
    timeout_seconds: float = 30,
) -> StackPlan:
    if any(len(w) != 1 for w in emissions):
        raise ValueError("remaining-depth pruning requires one-byte tokens")
    deadline = monotonic() + timeout_seconds
    states: set[Stack] = {()}
    layers = []
    cells, transitions = 1, 0
    for i, row in enumerate(rows):
        if not row or len(set(row)) != len(row):
            raise ValueError("nonempty distinct-token rows required")
        layer = {}
        following: set[Stack] = set()
        for state in sorted(states):
            if monotonic() >= deadline:
                raise StackLimit("stack compilation deadline")
            arcs = []
            for j, token in enumerate(row):
                end = step(state, emissions[token][0])
                if end is None or len(end) > len(rows) - i - 1:
                    continue
                arcs.append((j, end))
                following.add(end)
                transitions += 1
                if transitions > max_transitions or cells + len(following) > max_cells:
                    raise StackLimit("reachable-stack representation budget")
            layer[state] = tuple(arcs)
        cells += len(following)
        states = following
        layers.append(layer)
    return StackPlan(rows, tuple(layers), cells, transitions)
