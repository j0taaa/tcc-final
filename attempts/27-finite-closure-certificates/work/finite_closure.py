"""Finite closure bounds only; classical residues/potentials, original ID mass."""

from fractions import Fraction
from math import prod
from time import monotonic

from mwpc_exact.cfg_posterior import CompilationLimit

from .frozen.lexer import finish
from .frozen.posterior import class_weights
from .frozen.stack_control import depth_effect


class FiniteClosure:
    def __init__(self, prepared, weights, *, timeout_seconds=120, sums=None):
        if not hasattr(prepared, "prefix_arcs"):
            raise ValueError("untrimmed first-overflow prefixes required")
        if weights.canvas != prepared.canvas:
            raise ValueError("fixed original frame changed; recompile")
        self.deadline = monotonic() + timeout_seconds
        self.allowed, self.weights = prepared.lexical_allowed, weights
        table = prepared.table
        sums = class_weights(table, weights) if sums is None else sums
        self.leaf = [
            [sum(row[c] for c in table.local_to_class[g]) for g in range(len(table.groups))]
            for row in sums
        ]
        self.rows = []
        for p in range(len(weights.canvas)):
            layer = {}
            for q in self.allowed[p]:
                grouped = {}
                for gid in table.by_state[q]:
                    _, target, word, _ = table.groups[gid]
                    value = self.leaf[p][gid]
                    if value and target in self.allowed[p + 1]:
                        key = target, depth_effect(word)[0]
                        grouped[key] = grouped.get(key, 0) + value
                layer[q] = tuple((s, z, w) for (s, z), w in grouped.items())
            self.rows.append(layer)
            self.guard()
        self.frontier, alpha = {}, [1]
        for p, layer in enumerate(prepared.prefix_arcs):
            following = [0] * len(prepared.prefix_layers[p + 1])
            for a, outgoing in enumerate(layer):
                for q, height, gid in prepared.overflow_arcs[p][a]:
                    key = p + 1, q, height
                    self.frontier[key] = self.frontier.get(key, 0) + alpha[a] * self.leaf[p][gid]
                for b, gids in outgoing:
                    following[b] += alpha[a] * sum(self.leaf[p][g] for g in gids)
            alpha = following
            self.guard()
        self.frontier = {key: w for key, w in self.frontier.items() if w}
        self.by_position = {}
        for (p, q, height), w in self.frontier.items():
            self.by_position.setdefault(p, []).append((q, height, w))
        self.prefix_denominators = [1]
        for value in weights.denominators:
            self.prefix_denominators.append(self.prefix_denominators[-1] * value)
        self.denominator = prod(weights.denominators)
        self.transitions = sum(len(edges) for layer in self.rows for edges in layer.values())

    def guard(self):
        if monotonic() >= self.deadline:
            raise CompilationLimit("finite closure deadline; tail unresolved")

    def residue(self, modulus):
        if type(modulus) is not int or modulus <= 0:
            raise ValueError("positive integer modulus required")
        n, total, cells = len(self.rows), 0, 0
        suffix = {
            q: [int(finish(q) is not None and r == 0) for r in range(modulus)]
            for q in self.allowed[n]
        }
        for p in reversed(range(n + 1)):
            if p < n:
                suffix = {
                    q: [
                        sum(w * suffix[s][(r + z) % modulus] for s, z, w in edges)
                        for r in range(modulus)
                    ]
                    for q, edges in self.rows[p].items()
                }
            cells += len(suffix) * modulus
            total += sum(
                w * suffix[q][height % modulus] for q, height, w in self.by_position.get(p, ())
            )
            self.guard()
        if not 0 <= total <= self.denominator:
            raise RuntimeError("exclusive residue tail mass outside [0,1]")
        return Fraction(total, self.denominator), cells

    def potential(self, exponents):
        exponents = tuple(exponents)
        if not exponents or any(type(k) is not int or k < 0 for k in exponents):
            raise ValueError("nonnegative integer potential exponents required")
        bounds, cells = {key: Fraction(1) for key in self.frontier}, 0
        shifts = [
            max((z for e in layer.values() for _, z, _ in e), default=0) for layer in self.rows
        ]
        n = len(self.rows)
        for k in exponents:
            suffix = {q: int(finish(q) is not None) for q in self.allowed[n]}
            scale = 0
            for p in reversed(range(n + 1)):
                if p < n:
                    suffix = {
                        q: sum((w * suffix[s]) << (k * (shifts[p] - z)) for s, z, w in edges)
                        for q, edges in self.rows[p].items()
                    }
                    scale += k * shifts[p]
                cells += len(suffix)
                for q, height, _ in self.by_position.get(p, ()):
                    exponent = scale + k * height
                    bound = (
                        Fraction(suffix[q], 1 << exponent)
                        if exponent >= 0
                        else Fraction(suffix[q] << -exponent)
                    )
                    # Suffix values are unnormalized integers; prefix mass
                    # is normalized only once by the original full product.
                    remaining = self.denominator // self.prefix_denominators[p]
                    key = p, q, height
                    bounds[key] = min(bounds[key], bound / remaining)
                self.guard()
        total = sum(
            Fraction(w, self.prefix_denominators[p]) * bounds[p, q, h]
            for (p, q, h), w in self.frontier.items()
        )
        if not 0 <= total <= 1:
            raise RuntimeError("exclusive potential tail bound outside [0,1]")
        return total, cells
