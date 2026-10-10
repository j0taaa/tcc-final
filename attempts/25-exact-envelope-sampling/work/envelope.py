"""Exact original-ID rejection from a disjoint shallow/abstract-tail envelope.

No approximation in accepted samples. Lower-posterior marginals are not full
posterior marginals. Counters and prefix-hit envelopes are competent controls.
"""

import json
from bisect import bisect_right
from fractions import Fraction
from itertools import accumulate
from math import prod
from time import monotonic

from mwpc_exact.cfg_posterior import CompilationLimit

from .certificate import CounterTable
from .forest import coaccessible_layers
from .lexer import OUT, finish
from .posterior import Posterior, class_weights
from .stack_control import StackPosterior, StackPrepared


class OriginalChoices:
    def __init__(self, table, weights, sums):
        self.table, self.weights, self.sums = table, weights, sums
        self.cdfs = {}

    def choose(self, key, build_masses, rng):
        # Same exact integer inverse CDF as the compact controls; preparation
        # is local and charged once, rather than scanning full V on every draw.
        if key not in self.cdfs:
            masses = build_masses()
            cdf = tuple(accumulate(masses))
            if not cdf or cdf[-1] <= 0:
                raise ValueError("zero original conditional choice")
            positive = tuple(i for i, m in enumerate(masses) if m)
            self.cdfs[key] = cdf, positive[0] if len(positive) == 1 else None
        cdf, deterministic = self.cdfs[key]
        return (
            deterministic
            if deterministic is not None
            else bisect_right(cdf, rng.randrange(cdf[-1]))
        )

    def token(self, p, classes, rng):
        fixed = self.weights.canvas[p]
        if fixed is not None:
            return fixed
        cid = classes[
            self.choose(
                (p, "classes", tuple(classes)), lambda: [self.sums[p][c] for c in classes], rng
            )
        ]
        members = self.table.classes[cid]
        return members[
            self.choose((p, "members", cid), lambda: [self.weights.at(p, t) for t in members], rng)
        ]

    def group(self, p, gid, rng):
        return self.token(p, self.table.local_to_class[gid], rng)

    def raw(self, p, rng):
        fixed = self.weights.canvas[p]
        if fixed is not None:
            return fixed
        return self.choose((p, "raw"), lambda: self.weights.rows[p], rng)


class CounterDistribution:
    """Counter-only if depth=None, closed deep tail otherwise; same DP/limits."""

    def __init__(
        self,
        table,
        weights,
        sums,
        *,
        depth=None,
        prepared=None,
        timeout_seconds=120,
        max_states=10_000_000,
    ):
        self.table, self.weights, self.depth = table, weights, depth
        self.deadline, self.max_states = monotonic() + timeout_seconds, max_states
        self.counter = CounterTable(table)
        self.rows = self.counter.rows(weights, sums=sums)
        self.choices = OriginalChoices(table, weights, sums)
        self.classes = [[] for _ in self.counter.effects]
        for gid, code in enumerate(self.counter.of_group):
            self.classes[code].extend(table.local_to_class[gid])
        if prepared is None:
            self.allowed = coaccessible_layers(table, weights.canvas, deadline=self.deadline)
            self.suffix_closes = [0] * (len(weights.canvas) + 1)
            for p in reversed(range(len(weights.canvas))):
                words = (
                    table.groups[g][2]
                    for q in self.allowed[p]
                    for g in (
                        table.by_state[q]
                        if weights.canvas[p] is None
                        else (table.by_token[q][weights.canvas[p]],)
                    )
                    if g >= 0 and table.groups[g][1] in self.allowed[p + 1]
                )
                self.suffix_closes[p] = self.suffix_closes[p + 1] + max(
                    (sum(t in (1, 3) for t in word) for word in words), default=0
                )
        else:
            self.allowed, self.suffix_closes = prepared.lexical_allowed, prepared.suffix_closes
        self.memo = {}

    def edges(self, p, q, height, overflow):
        for code in self.counter.by_state.get(q, {}).values():
            weight = self.rows[p][code]
            _, target, net, low, high = self.counter.effects[code]
            if weight and height + low >= 0:
                exceeded = overflow or self.depth is None or height + high > self.depth
                key = p + 1, target, height + net, exceeded
                yield code, key, weight * self.beta(*key)

    def beta(self, p, q, height, overflow=True):
        if monotonic() > self.deadline:
            raise CompilationLimit("counter envelope deadline; no sample")
        key = p, q, height, overflow
        if key not in self.memo:
            if len(self.memo) >= self.max_states:
                raise CompilationLimit("counter envelope state budget; no sample")
            if q not in self.allowed[p] or height > self.suffix_closes[p]:
                result = 0
            elif p == len(self.weights.canvas):
                result = int(overflow and height == 0 and finish(q) is not None)
            else:
                result = sum(mass for _, _, mass in self.edges(p, q, height, overflow))
            self.memo[key] = result
        return self.memo[key]

    @property
    def total(self):
        return self.beta(0, OUT, 0, self.depth is None)

    def sample_from(self, p, q, height, rng, overflow=True):
        tokens = []
        while p < len(self.weights.canvas):
            edges = list(self.edges(p, q, height, overflow))
            code, key, _ = edges[Posterior.choose([e[2] for e in edges], rng)]
            tokens.append(self.choices.token(p, self.classes[code], rng))
            p, q, height, overflow = key
        return tuple(tokens)

    def sample(self, rng):
        return self.sample_from(0, OUT, 0, rng, self.depth is None)


class PrefixTail:
    """Grammar through first overflow, then counter or unrestricted product."""

    def __init__(self, prepared, weights, sums, *, counter=None, timeout_seconds=120):
        if not hasattr(prepared, "prefix_arcs"):
            raise ValueError("tail needs the UNTRIMMED first-overflow prefix DAG")
        if tuple(weights.canvas) != prepared.canvas:
            raise ValueError("tail changed the compiled original fixed frame")
        self.prepared, self.weights, self.table, self.counter = (
            prepared,
            weights,
            prepared.table,
            counter,
        )
        self.deadline = monotonic() + timeout_seconds
        self.choices = OriginalChoices(self.table, weights, sums)
        self.leaf = [
            [
                sum(sums[p][cid] for cid in self.table.local_to_class[g])
                for g in range(len(self.table.groups))
            ]
            for p in range(len(weights.canvas))
        ]
        self.denominators = [1] * (len(weights.canvas) + 1)
        for p in reversed(range(len(weights.canvas))):
            self.denominators[p] = self.denominators[p + 1] * weights.denominators[p]
        self.beta = [[0] * len(layer) for layer in prepared.prefix_layers]
        for p in reversed(range(len(prepared.prefix_arcs))):
            for a in range(len(prepared.prefix_layers[p])):
                self.beta[p][a] = sum(mass for _, _, mass in self.edges(p, a))
                if monotonic() > self.deadline:
                    raise CompilationLimit("grammar envelope deadline; no sample")
        self.total = self.beta[0][0]

    def edges(self, p, a):
        for b, gids in self.prepared.prefix_arcs[p][a]:
            for gid in gids:
                yield gid, (False, b), self.leaf[p][gid] * self.beta[p + 1][b]
        for q, height, gid in self.prepared.overflow_arcs[p][a]:
            if not self.leaf[p][gid]:
                continue
            suffix = (
                self.counter.beta(p + 1, q, height)
                if self.counter is not None
                else self.denominators[p + 1]
            )
            yield gid, (True, q, height), self.leaf[p][gid] * suffix

    def sample(self, rng):
        tokens, a = [], 0
        for p in range(len(self.weights.canvas)):
            edges = list(self.edges(p, a))
            gid, destination, _ = edges[Posterior.choose([e[2] for e in edges], rng)]
            tokens.append(self.choices.group(p, gid, rng))
            if destination[0]:
                if self.counter is None:
                    tokens.extend(
                        self.choices.raw(j, rng) for j in range(p + 1, len(self.weights.canvas))
                    )
                else:
                    tokens.extend(self.counter.sample_from(p + 1, *destination[1:], rng))
                return tuple(tokens)
            a = destination[1]
        raise RuntimeError("tail sample ended without first overflow")


class ExactEnvelope:
    def __init__(self, posterior, tail):
        if posterior is None and tail is None:
            raise ValueError("empty envelope")
        if posterior is not None and tail is not None and posterior.weights is not tail.weights:
            raise ValueError("mixture changed original product weights")
        self.posterior, self.tail = posterior, tail
        self.weights = posterior.weights if posterior is not None else tail.weights
        self.table = posterior.prepared.table if posterior is not None else tail.table
        self.lower = 0 if posterior is None else posterior.total
        self.upper_tail = 0 if tail is None else tail.total
        self.total = self.lower + self.upper_tail
        if not 0 <= self.total <= prod(self.weights.denominators):
            raise RuntimeError("disjoint envelope mass outside [0,1]")
        self.delta = Fraction(self.upper_tail, self.total) if self.total else None

    def propose(self, rng):
        if not self.total:
            raise ValueError("zero envelope mass")
        branch = Posterior.choose([self.lower, self.upper_tail], rng)
        return (self.posterior if branch == 0 else self.tail).sample(rng)

    def valid(self, tokens):
        if any(
            fixed is not None and tokens[p] != fixed for p, fixed in enumerate(self.weights.canvas)
        ):
            raise RuntimeError("envelope changed fixed original token")
        if any(self.table.adapter.emissions[t] is None for t in tokens):
            return False
        try:
            json.loads(
                self.table.adapter.detokenize_bytes(tokens).decode("utf8"),
                parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
            )
            return True
        except RecursionError as error:
            raise CompilationLimit(
                "JSON recognizer recursion resources; validity inconclusive"
            ) from error
        except (ValueError, UnicodeDecodeError):
            return False

    def sample(self, rng, *, max_trials=1000):
        if type(max_trials) is not int or max_trials <= 0:
            raise ValueError("positive integer proposal budget required")
        for trial in range(1, max_trials + 1):
            word = self.propose(rng)
            if self.valid(word):
                return word, trial
        raise CompilationLimit("envelope proposal budget; no valid sample returned")


def prepare_envelope(
    table,
    weights,
    depth,
    *,
    method="handoff",
    timeout_seconds=120,
    max_edges=10_000_000,
    max_cells=10_000_000,
    max_terms=50_000_000,
    sums=None,
    max_rejection=None,
):
    if method not in ("handoff", "closed", "grammar_hit", "counter_only"):
        raise ValueError("unknown envelope")
    deadline = monotonic() + timeout_seconds
    sums = class_weights(table, weights) if sums is None else sums

    def remaining():
        seconds = deadline - monotonic()
        if seconds <= 0:
            raise CompilationLimit("whole envelope preparation deadline; no sample")
        return seconds

    if method == "counter_only":
        return ExactEnvelope(
            None, CounterDistribution(table, weights, sums, timeout_seconds=remaining())
        )
    prepared = StackPrepared(
        table,
        weights.canvas,
        max_depth=depth,
        track_overflow=depth is not None and method != "closed",
        max_edges=max_edges,
        max_cells=max_cells,
        max_terms=max_terms,
        timeout_seconds=remaining(),
    )
    posterior = StackPosterior(prepared, weights, sums=sums)
    if depth is None:
        return ExactEnvelope(posterior, None)
    if method == "handoff" and max_rejection is not None:
        hit = ExactEnvelope(
            posterior, PrefixTail(prepared, weights, sums, timeout_seconds=remaining())
        )
        if hit.delta is not None and hit.delta <= max_rejection:
            hit.bound = "grammar_hit"
            return hit
    counter = (
        CounterDistribution(
            table,
            weights,
            sums,
            depth=depth if method == "closed" else None,
            prepared=prepared,
            timeout_seconds=remaining(),
        )
        if method != "grammar_hit"
        else None
    )
    tail = (
        counter
        if method == "closed"
        else PrefixTail(prepared, weights, sums, counter=counter, timeout_seconds=remaining())
    )
    return ExactEnvelope(posterior, tail)
