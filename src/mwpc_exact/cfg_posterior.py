"""Exact frozen mean-field conditioning on checked recursive byte grammars.

Classical sum-product parsing, specialized to original finite token paths.
No sequence/stack enumeration; no parse-count bias accepted as probabilities.
Only ABSENT EOS is currently supported. Rational arithmetic is deliberate.
"""

from __future__ import annotations

import heapq
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from math import isfinite, lcm
from random import Random
from time import monotonic, perf_counter

from mwpc_exact.eos_policy import EOSMode
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.ll1 import UnsupportedGrammar, check_ll1
from mwpc_exact.reference.normalization import SourceGrammar, normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.types import ExactnessScope

Cell = tuple[int, int, int]  # head, DAG start, DAG end
Choice = tuple[int, int]  # physical position, original support-row index


class CompilationLimit(TimeoutError):
    """Unresolved work/deadline limit, never evidence of zero valid mass."""


class PosteriorStatus(StrEnum):
    EXACT_ON_SUPPORT = "exact_on_support"
    ZERO_MASS_ON_SUPPORT = "zero_valid_probability_on_support"


@dataclass(frozen=True)
class _Term:
    children: tuple[int, ...] = ()
    choice: Choice | None = None


def _categorical(weights: tuple[Fraction, ...], rng: Random) -> int:
    scale = lcm(*(w.denominator for w in weights))
    integers = tuple(w.numerator * (scale // w.denominator) for w in weights)
    draw = rng.randrange(sum(integers))
    for i, weight in enumerate(integers):
        if draw < weight:
            return i
        draw -= weight
    raise AssertionError("integer categorical draw exceeded total weight")


@dataclass(frozen=True)
class CfgPosterior:
    """Exact represented valid mass and marginals; original tail stays explicit."""

    inputs: ProbabilityInput
    valid_mass: Fraction
    marginals: tuple[tuple[Fraction, ...], ...]
    _plan: CfgSampler
    _inside: tuple[Fraction, ...]
    inside_seconds: float
    marginal_seconds: float

    @property
    def status(self) -> PosteriorStatus:
        return (
            PosteriorStatus.EXACT_ON_SUPPORT
            if self.valid_mass
            else PosteriorStatus.ZERO_MASS_ON_SUPPORT
        )

    @property
    def exactness_scope(self) -> ExactnessScope:
        return self.inputs.state.support.exactness_scope

    @property
    def omitted_mass(self) -> Fraction:
        return self.inputs.omitted_mass

    def sample(self, rng: Random) -> tuple[int, ...]:
        """Draw one complete original-token assignment, conditional on support."""
        if not isinstance(rng, Random):
            raise TypeError("rng must be an explicitly supplied Random instance")
        if not self.valid_mass or self._plan.root is None:
            raise ValueError("ZERO_MASS_ON_SUPPORT: no conditional sample exists")
        pending = [self._plan.root]
        output: list[int] = []
        while pending:
            node = pending.pop()
            terms = self._plan.terms[node]
            values = tuple(self._plan.term_mass(t, self.inputs, self._inside) for t in terms)
            term = terms[_categorical(values, rng)]
            if term.choice is not None:
                position, index = term.choice
                if position != len(output):
                    raise RuntimeError("sample did not preserve physical token order")
                output.append(self.inputs.state.support.rows[position][index])
            pending.extend(reversed(term.children))
        if len(output) != len(self.inputs.state.canvas):
            raise RuntimeError("sample did not consume exactly the original token slots")
        return tuple(output)


@dataclass(frozen=True)
class CfgSampler:
    """Immutable arithmetic forest reusable under arbitrary unary reweighting."""

    state: SelectionInput
    terms: tuple[tuple[_Term, ...], ...]
    order: tuple[int, ...]
    root: int | None
    graph_vertices: int
    graph_edges: int

    @property
    def alternatives(self) -> int:
        return sum(map(len, self.terms))

    @staticmethod
    def term_mass(term: _Term, inputs: ProbabilityInput, inside: Sequence[Fraction]) -> Fraction:
        if term.choice is not None:
            position, index = term.choice
            return inputs.probabilities[position][index]
        if term.children:
            left, right = term.children
            return inside[left] * inside[right]
        return Fraction(1)

    def evaluate(self, inputs: ProbabilityInput) -> CfgPosterior:
        """Inside and outside evaluation; no compilation or feasibility oracle."""
        state = inputs.state
        if (
            state.grammar != self.state.grammar
            or state.canvas != self.state.canvas
            or state.support != self.state.support
            or state.tokenizer_adapter != self.state.tokenizer_adapter
            or state.eos_policy != self.state.eos_policy
        ):
            raise ValueError("reweighting changed the compiled constraint/token support")
        started = perf_counter()
        inside = [Fraction()] * len(self.terms)
        for node in self.order:
            inside[node] = sum(
                (self.term_mass(t, inputs, inside) for t in self.terms[node]), Fraction()
            )
        values = tuple(inside)
        total = values[self.root] if self.root is not None else Fraction()
        inside_seconds = perf_counter() - started
        started = perf_counter()
        outside = [Fraction()] * len(self.terms)
        masses = [[Fraction()] * len(row) for row in state.support.rows]
        if self.root is not None:
            outside[self.root] = Fraction(1)
        for node in reversed(self.order):
            if not outside[node]:
                continue
            for term in self.terms[node]:
                if term.choice is not None:
                    position, index = term.choice
                    masses[position][index] += outside[node] * self.term_mass(term, inputs, values)
                elif term.children:
                    left, right = term.children
                    outside[left] += outside[node] * values[right]
                    outside[right] += outside[node] * values[left]
        if total > 1 or any(sum(row) != total for row in masses):
            raise RuntimeError("probability/physical-slot invariant failed")
        marginals = tuple(tuple(v / total if total else Fraction() for v in row) for row in masses)
        return CfgPosterior(
            inputs, total, marginals, self, values, inside_seconds, perf_counter() - started
        )


def compile_cfg_sampler(
    source: SourceGrammar,
    state: SelectionInput,
    *,
    max_chart_cells: int = 200_000,
    max_alternatives: int = 1_000_000,
    timeout_seconds: float | None = None,
) -> CfgSampler:
    """Compile a sparse sum-product forest with explicit unresolved limits.

    Each finalized child span is strictly smaller than its parent. A priority
    agenda therefore joins each pair once, after both children are finalized.
    No probability-based pruning is performed: zero unaries may later change.
    """
    for limit in (max_chart_cells, max_alternatives):
        if type(limit) is not int or limit < 0:
            raise ValueError("compilation limits must be non-negative integers")
    if timeout_seconds is not None and (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not isfinite(timeout_seconds)
        or timeout_seconds < 0
    ):
        raise ValueError("timeout must be finite and non-negative")
    deadline = None if timeout_seconds is None else monotonic() + timeout_seconds

    def check_limit() -> None:
        if deadline is not None and monotonic() >= deadline:
            raise CompilationLimit("compilation deadline; feasibility remains unresolved")

    check_limit()
    check_ll1(source)
    if state.grammar != normalize_to_cnf(source).grammar:
        raise ValueError("input grammar does not match the checked source normalization")
    if state.eos_policy.mode is not EOSMode.ABSENT:
        raise UnsupportedGrammar("CFG posterior currently supports only ABSENT EOS")
    grammar = state.grammar
    labels = {t.label: t.symbol_id for t in grammar.terminals}
    edges: list[tuple[int, int, int, Choice | None]] = []
    boundary = 0
    vertices = 1
    # Last-byte closures avoid epsilon arcs even when a token prefixes another.
    for position, row in enumerate(state.support.rows):
        check_limit()
        words = {
            j: state.tokenizer_adapter.emissions[token]
            for j, token in enumerate(row)
            if state.tokenizer_adapter.emissions[token] is not None
        }
        prefixes = sorted(
            {w[:i] for w in words.values() if w for i in range(1, len(w))},
            key=lambda p: (len(p), p),
        )
        nodes = {b"": boundary}
        for p in prefixes:
            nodes[p] = vertices
            vertices += 1
            edges.append((nodes[p[:-1]], nodes[p], p[-1], None))
        end = vertices
        vertices += 1
        for j, word in words.items():
            assert word is not None
            edges.append((nodes[word[:-1]], end, word[-1], (position, j)))
        boundary = end

    terminal_heads: dict[int, list[int]] = defaultdict(list)
    left_rules: dict[int, list[tuple[int, int]]] = defaultdict(list)
    right_rules: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for rule in grammar.terminal_productions:
        terminal_heads[rule.terminal_id].append(rule.head_id)
    for binary in grammar.binary_productions:
        left_rules[binary.left_id].append((binary.head_id, binary.right_id))
        right_rules[binary.right_id].append((binary.head_id, binary.left_id))
    ids: dict[Cell, int] = {}
    keys: list[Cell] = []
    terms: list[list[_Term]] = []
    agenda: list[tuple[int, int]] = []
    alternatives = 0

    def add(key: Cell, term: _Term) -> None:
        nonlocal alternatives
        if alternatives >= max_alternatives or (key not in ids and len(ids) >= max_chart_cells):
            raise CompilationLimit("compiled forest budget; feasibility remains unresolved")
        if key not in ids:
            ids[key] = len(keys)
            keys.append(key)
            terms.append([])
            heapq.heappush(agenda, (key[2] - key[1], ids[key]))
        terms[ids[key]].append(term)
        alternatives += 1

    for start, end, label, choice in edges:
        for head in terminal_heads.get(labels.get(label, -1), ()):
            add((head, start, end), _Term(choice=choice))
    starts: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    ends: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    order = []
    while agenda:
        check_limit()
        _, node = heapq.heappop(agenda)
        head, start, end = keys[node]
        for parent, right in left_rules[head]:
            for target, child in starts[right, end]:
                add((parent, start, target), _Term((node, child)))
        for parent, left in right_rules[head]:
            for origin, child in ends[left, start]:
                add((parent, origin, end), _Term((child, node)))
        starts[head, start].append((end, node))
        ends[head, end].append((start, node))
        order.append(node)
    root = ids.get((grammar.start_nonterminal_id, 0, boundary))
    return CfgSampler(state, tuple(map(tuple, terms)), tuple(order), root, vertices, len(edges))
