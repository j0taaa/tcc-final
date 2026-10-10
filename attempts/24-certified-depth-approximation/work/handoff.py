"""Exact mass of grammar-first-overflow with relaxed balanced continuation."""

from fractions import Fraction
from functools import cache
from math import prod
from time import monotonic

from mwpc_exact.cfg_posterior import CompilationLimit

from .lexer import finish
from .posterior import class_weights


class OverflowFrontier:
    def __init__(self, prepared, weights, *, timeout_seconds=120, sums=None):
        if not hasattr(prepared, "prefix_arcs"):
            raise ValueError("bound requires an untrimmed first-overflow prefix DAG")
        if tuple(weights.canvas) != prepared.canvas:
            raise ValueError("bound requires the declared fixed frame; recompile after changes")
        deadline = monotonic() + timeout_seconds
        table = prepared.table
        self.weights, self.table = weights, table
        self.sums = class_weights(table, weights) if sums is None else sums
        leaf = [
            [
                sum(self.sums[p][cid] for cid in table.local_to_class[g])
                for g in range(len(table.groups))
            ]
            for p in range(len(weights.canvas))
        ]
        self.suffix_denominators = [1] * (len(weights.canvas) + 1)
        for p in reversed(range(len(weights.canvas))):
            self.suffix_denominators[p] = self.suffix_denominators[p + 1] * weights.denominators[p]
        self.frontier, self.boundaries = {}, 0
        alpha = [1]
        for p, layer in enumerate(prepared.prefix_arcs):
            following = [0] * len(prepared.prefix_layers[p + 1])
            for a, outgoing in enumerate(layer):
                if not alpha[a]:
                    continue
                for q, height, gid in prepared.overflow_arcs[p][a]:
                    value = alpha[a] * leaf[p][gid]
                    if value:
                        key = p + 1, q, height
                        self.frontier[key] = self.frontier.get(key, 0) + value
                        self.boundaries += 1
                for b, gids in outgoing:
                    following[b] += alpha[a] * sum(leaf[p][g] for g in gids)
                if monotonic() > deadline:
                    raise CompilationLimit("grammar prefix deadline; tail unresolved")
            alpha = following
        self.denominator = prod(weights.denominators)
        total = sum(
            value * self.suffix_denominators[p] for (p, _, _), value in self.frontier.items()
        )
        if not 0 <= total <= self.denominator:
            raise RuntimeError("first-overflow event probability outside [0,1]")
        self.mass = Fraction(total, self.denominator)

    def handoff(self, counter, *, timeout_seconds=120, max_states=10_000_000):
        if counter.original is not self.table:
            raise ValueError("counter changed lexical table")
        deadline = monotonic() + timeout_seconds
        counter_rows = counter.rows(self.weights, sums=self.sums)
        transitions = 0

        @cache
        def continuation(p, q, height):
            nonlocal transitions
            if monotonic() > deadline:
                raise CompilationLimit("handoff counter deadline; tail unresolved")
            if continuation.cache_info().currsize >= max_states:
                raise CompilationLimit("handoff counter state budget; tail unresolved")
            if p == len(self.weights.canvas):
                return int(height == 0 and finish(q) is not None)
            total = 0
            for code in counter.by_state.get(q, {}).values():
                weight = counter_rows[p][code]
                _, target, net, low, _ = counter.effects[code]
                if weight and height + low >= 0:
                    total += weight * continuation(p + 1, target, height + net)
                    transitions += 1
            return total

        total = sum(value * continuation(*key) for key, value in self.frontier.items())
        if not 0 <= total <= self.denominator:
            raise RuntimeError("handoff event probability outside [0,1]")
        return Fraction(total, self.denominator), dict(
            boundaries=self.boundaries,
            frontier_states=len(self.frontier),
            counter_states=continuation.cache_info().currsize,
            counter_transitions=transitions,
        )


def overflow_bound(prepared, weights, *, counter=None, timeout_seconds=120, max_states=10_000_000):
    frontier = OverflowFrontier(prepared, weights, timeout_seconds=timeout_seconds)
    if counter is not None:
        return frontier.handoff(counter, timeout_seconds=timeout_seconds, max_states=max_states)
    return frontier.mass, dict(
        boundaries=frontier.boundaries, frontier_states=len(frontier.frontier)
    )
