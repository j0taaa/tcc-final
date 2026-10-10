"""Deterministic original-token counter bounds, exact conditioned TV certificate.

No neural dependencies, no guessed physical depth ceiling, no probability tail
renormalization. Counter effects aggregate original IDs once per lexer state.
"""

from fractions import Fraction
from math import prod
from time import monotonic

from mwpc_exact.cfg_posterior import CompilationLimit

from .forest import coaccessible_layers
from .lexer import OUT, finish
from .posterior import class_weights
from .stack_control import depth_effect


class CounterTable:
    def __init__(self, table):
        self.original = table
        self.effects, self.by_state, self.of_group = [], {}, []
        for q, target, word, _ in table.groups:
            key = target, *depth_effect(word)
            mapping = self.by_state.setdefault(q, {})
            code = mapping.get(key)
            if code is None:
                code = len(self.effects)
                mapping[key] = code
                self.effects.append((q, *key))
            self.of_group.append(code)

    def rows(self, weights, *, sums=None):
        original = self.original
        if weights.vocabulary_size != original.adapter.vocabulary_size:
            raise ValueError("counter weights changed original vocabulary")
        sums = class_weights(original, weights) if sums is None else sums
        result = []
        for p, fixed in enumerate(weights.canvas):
            row = [0] * len(self.effects)
            for gid, code in enumerate(self.of_group):
                if fixed is None:
                    row[code] += sum(sums[p][cid] for cid in original.local_to_class[gid])
                else:
                    q = original.groups[gid][0]
                    row[code] += int(original.by_token[q][fixed] == gid)
            result.append(row)
        return result

    def tail(self, weights, depth, *, mode="closed", timeout_seconds=120, max_states=10_000_000):
        if type(depth) is not int or depth < 0:
            raise ValueError("depth must be a nonnegative integer")
        if mode not in ("closed", "hit", "suffix_hit"):
            raise ValueError("counter mode must be closed, hit or suffix_hit")
        deadline = monotonic() + timeout_seconds
        rows = self.rows(weights)
        if monotonic() > deadline:
            raise CompilationLimit("counter row aggregation deadline; tail unresolved")
        allowed = (
            coaccessible_layers(self.original, weights.canvas, deadline=deadline)
            if mode != "hit"
            else None
        )
        suffix_closes = [0] * (len(rows) + 1)
        if allowed is not None:
            for p in reversed(range(len(rows))):
                fixed = weights.canvas[p]
                original = self.original
                words = (
                    original.groups[gid][2]
                    for q in allowed[p]
                    for gid in (
                        original.by_state[q] if fixed is None else (original.by_token[q][fixed],)
                    )
                    if gid >= 0 and original.groups[gid][1] in allowed[p + 1]
                )
                suffix_closes[p] = suffix_closes[p + 1] + max(
                    (sum(t in (1, 3) for t in word) for word in words), default=0
                )
        layer, absorbed, visited, transitions = {(OUT, 0, False): 1}, 0, 1, 0
        for p, row in enumerate(rows):
            following = {}
            absorbed *= weights.denominators[p]
            for (q, height, overflow), mass in layer.items():
                for code in self.by_state.get(q, {}).values():
                    weight = row[code]
                    if not weight:
                        continue
                    _, target, net, low, high = self.effects[code]
                    if height + low < 0:
                        continue
                    if allowed is not None and target not in allowed[p + 1]:
                        continue
                    if allowed is not None and height + net > suffix_closes[p + 1]:
                        continue
                    value = mass * weight
                    exceeded = overflow or height + high > depth
                    if mode != "closed" and exceeded:
                        absorbed += value
                    else:
                        key = target, height + net, exceeded
                        following[key] = following.get(key, 0) + value
                    transitions += 1
                    if transitions % 256 == 0 and monotonic() > deadline:
                        raise CompilationLimit("counter transition deadline; tail unresolved")
            layer = following
            visited += len(layer)
            if visited > max_states:
                raise CompilationLimit("counter state budget; tail unresolved")
            if monotonic() > deadline:
                raise CompilationLimit("counter layer deadline; tail unresolved")
        total = (
            absorbed
            if mode != "closed"
            else sum(
                mass
                for (q, height, overflow), mass in layer.items()
                if height == 0 and overflow and finish(q) is not None
            )
        )
        denominator = prod(weights.denominators)
        if not 0 <= total <= denominator:
            raise RuntimeError("counter event mass outside [0,1]")
        return Fraction(total, denominator), {"states": visited, "transitions": transitions}


def conditional_error(lower_mass, upper_tail):
    if not 0 <= lower_mass <= 1 or not 0 <= upper_tail <= 1:
        raise ValueError("certificate masses must be in [0,1]")
    if not lower_mass:
        raise ValueError("zero lower valid mass: no conditioned sampler certified")
    return upper_tail / (lower_mass + upper_tail)
