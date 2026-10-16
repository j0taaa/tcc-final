"""Small rational reference for an executed finite-ticket proposal; not a GPU decoder."""

from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import accumulate
from math import prod


def ceiling(numerator, denominator):
    return -(-numerator // denominator)


@dataclass(frozen=True)
class Category:
    counts: tuple[int, ...]
    bits: int = 64

    def __post_init__(self):
        if (
            not isinstance(self.bits, int)
            or self.bits < 1
            or not self.counts
            or any(type(a) is not int or a <= 0 for a in self.counts)
            or sum(self.counts) >= 1 << self.bits
        ):
            raise ValueError("positive integer category needs total strictly below source range")

    @property
    def total(self):
        return sum(self.counts)

    @property
    def endpoints(self):
        return (0, *accumulate(self.counts))

    def probability(self, index):
        endpoints, h = self.endpoints, 1 << self.bits
        return F(
            ceiling(h * endpoints[index + 1], self.total)
            - ceiling(h * endpoints[index], self.total),
            h,
        )

    def inverse_upper(self, index):
        if len(self.counts) == 1:
            return F(1)
        return F(self.total, self.counts[index]) / (1 - F(self.total, 1 << self.bits))

    def select(self, raw):
        if type(raw) is not int or not 0 <= raw < 1 << self.bits:
            raise ValueError("random source word outside its declared range")
        ticket = raw * self.total >> self.bits
        index = bisect_right(self.endpoints, ticket) - 1
        return index

    def draw(self, rng):
        if len(self.counts) == 1:
            return 0
        return self.select(rng.getrandbits(self.bits))


@dataclass(frozen=True)
class Edge:
    target: int
    tokens: tuple[int, ...]


class Reference:
    """Coaccessible finite layered deterministic graph; every final state accepts.

    Numeric input rows are exact Fractions, not row-normalized float surrogates.
    Every node supplies one edge Category and one token Category per edge.
    """

    def __init__(self, layers, rows, tables):
        self.layers, self.rows, self.tables = layers, rows, tables
        if not layers or len(layers) != len(rows) or len(tables) != len(layers):
            raise ValueError("inconsistent layer counts")
        if len(layers[0]) != 1:
            raise ValueError("one initial root required")
        for p, layer in enumerate(layers):
            if not layer or len(tables[p]) != len(layer):
                raise ValueError("node/table count mismatch")
            if any(not isinstance(w, F) or w < 0 for w in rows[p]):
                raise ValueError("finite nonnegative original rational weights required")
            next_count = len(layers[p + 1]) if p + 1 < len(layers) else 1
            for state, edges in enumerate(layer):
                edge_table, token_tables = tables[p][state]
                if (
                    not edges
                    or len(edge_table.counts) != len(edges)
                    or len(token_tables) != len(edges)
                ):
                    raise ValueError("each node needs matching nonempty choices")
                seen = set()
                for e, edge in enumerate(edges):
                    if not 0 <= edge.target < next_count or not edge.tokens:
                        raise ValueError("invalid layered edge")
                    if len(token_tables[e].counts) != len(edge.tokens):
                        raise ValueError("token counts mismatch")
                    for token in edge.tokens:
                        if not 0 <= token < len(rows[p]) or token in seen:
                            raise ValueError("original ID has no unique state trace")
                        seen.add(token)
        self.mass = self._backward("mass")
        if self.mass <= 0:
            raise ValueError("undefined zero-mass target")
        self.envelope = self._backward("exact_ratio")
        self.cheap_envelope = self._backward("upper_ratio")

    def _backward(self, mode):
        following = [F(1)]
        for p in range(len(self.layers) - 1, -1, -1):
            current = []
            for state, edges in enumerate(self.layers[p]):
                edge_table, token_tables = self.tables[p][state]
                values = []
                for e, edge in enumerate(edges):
                    token_table = token_tables[e]
                    if mode == "mass":
                        local = sum((self.rows[p][t] for t in edge.tokens), F())
                    else:
                        inverse = (
                            token_table.inverse_upper
                            if mode == "upper_ratio"
                            else lambda j, table=token_table: 1 / table.probability(j)
                        )
                        local = max(self.rows[p][t] * inverse(j) for j, t in enumerate(edge.tokens))
                        local *= (
                            edge_table.inverse_upper(e)
                            if mode == "upper_ratio"
                            else 1 / edge_table.probability(e)
                        )
                    values.append(local * following[edge.target])
                current.append(sum(values, F()) if mode == "mass" else max(values))
            following = current
        return following[0]

    def trace(self, word):
        if len(word) != len(self.layers):
            raise ValueError("word length differs from physical canvas")
        density, weight, state, draws = F(1), F(1), 0, []
        for p, token in enumerate(word):
            edges = self.layers[p][state]
            found = [
                (e, edge.tokens.index(token))
                for e, edge in enumerate(edges)
                if token in edge.tokens
            ]
            if len(found) != 1:
                raise ValueError("word outside graph")
            e, j = found[0]
            edge_table, token_tables = self.tables[p][state]
            for table, selected in ((edge_table, e), (token_tables[e], j)):
                density *= table.probability(selected)
                draws.append((table.total, *table.endpoints[selected : selected + 2], table.bits))
            weight *= self.rows[p][token]
            state = edges[e].target
        return weight, density, tuple(draws)

    def proposal(self, rng):
        word, state = [], 0
        for p, layer in enumerate(self.layers):
            edge_table, token_tables = self.tables[p][state]
            e = edge_table.draw(rng)
            edge = layer[state][e]
            token = edge.tokens[token_tables[e].draw(rng)]
            word.append(token)
            state = edge.target
        return tuple(word)

    def sample(self, rng, max_trials, *, upper=True):
        if type(max_trials) is not int or max_trials < 0:
            raise ValueError("fixed nonnegative trial cap required")
        envelope = self.cheap_envelope if upper else self.envelope
        for trial in range(1, max_trials + 1):
            word = self.proposal(rng)
            weight, density, trace = self.trace(word)
            recovered = prod(
                (
                    F(ceiling((1 << bits) * end, a) - ceiling((1 << bits) * start, a), 1 << bits)
                    for a, start, end, bits in trace
                ),
                start=F(1),
            )
            if recovered != density:
                raise RuntimeError("recorded trace density mismatch")
            accept = weight / (envelope * density)
            if not 0 <= accept <= 1:
                raise RuntimeError("invalid envelope; never clamp acceptance")
            if rng.randrange(accept.denominator) < accept.numerator:
                return dict(status="COMPLETE", word=word, trials=trial)
        return dict(status="FAIL", word=None, trials=max_trials)
