"""Floating conditional messages, exact categorical dyadic tickets.

Categorical exactness DOES NOT certify the whole ideal posterior/native RNG.
Prefix-history stratification is classical; fresh uniform bits are used at
every decision, avoiding one53-bit uniform for an entire high-entropy word.
"""

import bisect
import sys
from collections import defaultdict
from fractions import Fraction as F

import numpy as np

from .numeric_json import TAIL


class IntegerCategorical:
    def __init__(self, weights):
        weights = np.asarray(weights, dtype=np.float64)
        if weights.ndim != 1 or not np.isfinite(weights).all() or (weights < 0).any():
            raise ValueError("finite nonnegative categorical vector required")
        self.ids = tuple(int(i) for i in np.flatnonzero(weights > 0))
        if not self.ids:
            raise ValueError("positive categorical mass required")
        ratios = [float(weights[i]).as_integer_ratio() for i in self.ids]
        powers = [d.bit_length() - 1 for _, d in ratios]
        self.power = max(powers)
        self.counts = tuple(n << (self.power - d) for (n, _), d in zip(ratios, powers, strict=True))
        self.cumulative = []
        total = 0
        for count in self.counts:
            total += count
            self.cumulative.append(total)
        self.total = total

    def ticket(self, value):
        if type(value) is not int or not 0 <= value < self.total:
            raise ValueError("integer ticket outside categorical support")
        return self.ids[bisect.bisect_right(self.cumulative, value)]

    def probabilities(self):
        return {i: F(n, self.total) for i, n in zip(self.ids, self.counts, strict=True)}

    def draw(self, count, rng, stratified=False):
        if type(count) is not int or not 1 <= count <= 64:
            raise ValueError("bounded positive categorical group required")
        if not stratified:
            return tuple(self.ticket(rng.randrange(self.total)) for _ in range(count))
        # k equal strata of width N on k copies of each original ticket.
        result = [
            self.ticket((j * self.total + rng.randrange(self.total)) // count) for j in range(count)
        ]
        rng.shuffle(result)
        return tuple(result)

    def payload_bytes(self):
        return sum(sys.getsizeof(v) for v in (*self.counts, *self.cumulative, *self.ids)) + sum(
            sys.getsizeof(v) for v in (self.counts, self.cumulative, self.ids)
        )


class ConditionalFloatSampler:
    def __init__(self, planner, action):
        self.planner, self.plan = planner, planner.plan
        self.action = tuple(action)
        # Existing validated readout supplies the action/domain check.
        self.statistics = planner.statistics(action)
        self.retained = dict(action)
        self.factors = planner.u.copy()
        terms = np.zeros(planner.n)
        for i, v in action:
            self.factors[i] = 0
            factor = planner.weights[i, v] * planner.gates[i, v]
            if not factor > 0:
                raise ValueError("positive retained categorical factor underflow")
            self.factors[i, self.plan.mapping[v]] = factor
            terms[i] = 1 / planner.gates[i, v]
        self.anchor = IntegerCategorical(terms)
        self.scale = np.divide(
            1.0, planner.counts, out=np.zeros(planner.n), where=planner.counts > 0
        )
        minimum = max((*planner.fixed, *self.retained), default=-1)
        self.scale[np.arange(planner.n) < minimum] = 0
        matrices = np.einsum("nc,cst->nst", self.factors, self.plan.lexical_routes, optimize=True)
        matrices[:, 20, TAIL] *= self.scale
        matrices[:, TAIL, TAIL] = 1
        self.log_query_mass = self.plan.forwards(matrices)[0]
        expected = self.statistics["log_probability"] + planner.base["logz"] - np.log(terms.sum())
        if abs(self.log_query_mass - expected) > 1e-8:
            raise ValueError("conditional query mass differs from action readout")
        self.beta = self.plan.backwards(matrices)
        self.token_cache, self.class_cache = {}, {}

    def classes(self, i, state):
        key = i, state
        if key not in self.class_cache:
            targets = self.plan.effects[:, state]
            weights = np.zeros(len(targets))
            valid = targets >= 0
            a, b = self.factors[i, valid], self.beta[i + 1, targets[valid]]
            product = a * b
            if ((a > 0) & (b > 0) & (product == 0)).any():
                raise ValueError("positive class/backward product underflow")
            weights[valid] = product
            old_eos = weights[self.plan.eos_class]
            weights[self.plan.eos_class] *= self.scale[i]
            if old_eos > 0 and self.scale[i] > 0 and weights[self.plan.eos_class] == 0:
                raise ValueError("positive EOS terminal product underflow")
            self.class_cache[key] = IntegerCategorical(weights)
        return self.class_cache[key]

    def tokens(self, i, cls):
        key = i, cls
        if key not in self.token_cache:
            p = self.planner
            members = self.plan.members[cls]
            weights = p.weights[i, members].copy()
            if i in p.fixed or i in self.retained:
                expected = p.fixed.get(i, self.retained.get(i))
                weights *= members == expected
            else:
                weights *= 1 - p.gates[i, members]
                if not (weights > 0).all():
                    raise ValueError("positive original unretained token factor underflow")
            self.token_cache[key] = IntegerCategorical(weights)
        return self.token_cache[key]

    def word_probability(self, word):
        """Exact law of THESE numerical categorical kernels, for tiny oracles."""
        state, probability = 0, F(1)
        for i, v in enumerate(word):
            cls = int(self.plan.mapping[v])
            classes = self.classes(i, state).probabilities()
            if cls not in classes:
                return F()
            members = self.plan.members[cls]
            index = int(np.searchsorted(members, v))
            tokens = self.tokens(i, cls).probabilities()
            if index not in tokens:
                return F()
            probability *= classes[cls] * tokens[index]
            state = int(self.plan.effects[cls, state])
            if state == TAIL:
                return probability if i == len(word) - 1 else F()
        return F()

    def sample(self, count, rng, stratified=False):
        if type(count) is not int or not 1 <= count <= 64:
            raise ValueError("bounded positive conditional batch required")
        words, states, done = [() for _ in range(count)], [0] * count, [False] * count
        self.partial_trace = {"prefixes": words, "states": states, "done": done}
        for i in range(self.planner.n):
            groups = defaultdict(list)
            for j in range(count):
                if not done[j]:
                    groups[words[j]].append(j)
            if not groups:
                break
            for prefix, group in groups.items():
                state = states[group[0]]
                assert all(states[j] == state and words[j] == prefix for j in group)
                selected = self.classes(i, state).draw(len(group), rng, stratified)
                by_class = defaultdict(list)
                for j, cls in zip(group, selected, strict=True):
                    by_class[cls].append(j)
                for cls, subgroup in by_class.items():
                    tokens = self.tokens(i, cls).draw(len(subgroup), rng, stratified)
                    for j, index in zip(subgroup, tokens, strict=True):
                        v = int(self.plan.members[cls][index])
                        words[j] = (*words[j], v)
                        states[j] = int(self.plan.effects[cls, state])
                        done[j] = states[j] == TAIL
        if not all(done):
            raise ValueError("conditional sampler exhausted accepting horizon")
        # Anchor posterior is independent of X; keep complete prefix histories.
        groups = defaultdict(list)
        for j, word in enumerate(words):
            groups[word].append(j)
        anchors = [None] * count
        for word, group in groups.items():
            draws = self.anchor.draw(len(group), rng, stratified)
            for j, anchor in zip(group, draws, strict=True):
                if (anchor, word[anchor]) not in self.action:
                    raise AssertionError("conditional anchor must be an original retained ID")
                anchors[j] = anchor
        return tuple(zip(words, anchors, strict=True))

    def cache_payload_bytes(self):
        return sum(
            c.payload_bytes() for c in (*self.class_cache.values(), *self.token_cache.values())
        )
