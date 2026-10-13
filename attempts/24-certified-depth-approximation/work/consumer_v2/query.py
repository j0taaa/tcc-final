"""Exact class statistics and original-ID confidence queries for A24's consumer.

Class sums, block recovery, sparse outside and early stopping are classical.
This module changes the consumer's work, not its declared posterior/commit map.
"""

from fractions import Fraction
from functools import reduce
from itertools import pairwise
from math import gcd, prod
from time import monotonic

import numpy as np

from mwpc_exact.cfg_posterior import CompilationLimit

from ..certificate import CounterTable, conditional_error
from ..handoff import OverflowFrontier
from ..posterior import Posterior
from ..stack_control import StackPosterior, StackPrepared
from .block_stats import integer_weight, numpy_stats


class BoundaryWeights:
    """Exact deterministic summaries; original weights retrieved on demand."""

    def __init__(self, table, head, canvas, partition):
        self.canvas = tuple(canvas)
        self.vocabulary_size = table.adapter.vocabulary_size
        if tuple(table.class_of) != partition.class_of:
            raise ValueError("summary changed complete lexer signatures")
        self.head = np.asarray(head)
        self.free = tuple(p for p, t in enumerate(canvas) if t is None)
        if self.head.shape != (len(self.free), self.vocabulary_size):
            raise ValueError("full original head differs from free canvas")
        if not self.free:
            raise ValueError("consumer requires a progressing free position")
        self.stats = numpy_stats(self.head, partition)
        self.row_of = dict(zip(self.free, range(len(self.free)), strict=True))
        free_sums = self.stats.class_sums()
        self.sums, self.denominators = [], []
        for p, fixed in enumerate(canvas):
            if fixed is None:
                row = free_sums[self.row_of[p]]
            else:
                if type(fixed) is not int or not 0 <= fixed < self.vocabulary_size:
                    raise ValueError("invalid original fixed token")
                row = tuple(int(c == table.class_of[fixed]) for c in range(len(table.classes)))
            self.sums.append(row)
            self.denominators.append(sum(row))
        self.sums, self.denominators = tuple(self.sums), tuple(self.denominators)
        self.consumed = False

    def at(self, p, t):
        if type(p) is not int or not 0 <= p < len(self.canvas):
            raise ValueError("query position outside canvas")
        if type(t) is not int or not 0 <= t < self.vocabulary_size:
            raise ValueError("query is not an original token ID")
        fixed = self.canvas[p]
        if fixed is not None:
            return int(t == fixed)
        row = self.row_of[p]
        return integer_weight(self.head[row, t], self.stats.minimum_exponents[row])


def choose(masses, rng):
    # Cancel common units so equivalent exact numeric interfaces use equal tickets.
    divisor = reduce(gcd, masses, 0)
    return Posterior.choose([v // divisor for v in masses] if divisor > 1 else masses, rng)


def sample(posterior, weights, rng):
    """A28's class/block disintegration, on A24's bounded or complete stack DAG."""
    if weights.consumed:
        raise ValueError("this consumer has already sampled its completion")
    if not posterior.total:
        raise ValueError("zero_valid_mass")
    weights.consumed = True
    classes, state = [], 0
    for p, layer in enumerate(posterior.prepared.arcs):
        out = layer[state]
        b, gids = out[
            choose(
                [
                    w * posterior.beta[p + 1][b]
                    for (b, _), w in zip(out, posterior.arc_weights[p][state], strict=True)
                ],
                rng,
            )
        ]
        gid = gids[choose([posterior.leaf[p, g] for g in gids], rng)]
        cids = posterior.prepared.table.local_to_class[gid]
        classes.append(cids[choose([weights.sums[p][c] for c in cids], rng)])
        state = b
    tokens = list(weights.canvas)
    for p in weights.free:
        row = weights.row_of[p]
        bids = weights.stats.partition.class_blocks[classes[p]]
        bid = bids[choose([weights.stats.totals[row][b] for b in bids], rng)]
        ids = weights.stats.partition.blocks[bid]
        values = [weights.at(p, t) for t in ids]
        if sum(values) != weights.stats.totals[row][bid]:
            raise RuntimeError("immutable provider changed selected original block")
        tokens[p] = ids[choose(values, rng)]
    return tuple(tokens)


class ConfidenceCursor:
    """Prefix outside propagation; requested positions must be nondecreasing."""

    def __init__(self, posterior):
        if not posterior.total:
            raise ValueError("zero_valid_mass")
        self.posterior = posterior
        self.position, self.alpha, self.queries, self.edge_visits = 0, [1], 0, 0

    def at(self, p, t):
        post, prepared = self.posterior, self.posterior.prepared
        weight = post.weights.at(p, t)
        if p < self.position:
            raise ValueError("confidence cursor cannot go backward")
        while self.position < p:
            i = self.position
            following = [0] * len(prepared.layers[i + 1])
            for a, outgoing in enumerate(prepared.arcs[i]):
                if self.alpha[a]:
                    for (b, _), mass in zip(outgoing, post.arc_weights[i][a], strict=True):
                        following[b] += self.alpha[a] * mass
                        self.edge_visits += 1
            self.alpha, self.position = following, i + 1
        self.queries += 1
        if sum(a * b for a, b in zip(self.alpha, post.beta[p], strict=True)) != post.total:
            raise RuntimeError("prefix outside lost original mass conservation")
        if post.weights.canvas[p] is not None:
            return post.total * weight
        coefficient, table = 0, prepared.table
        for a, (q, _) in enumerate(prepared.layers[p]):
            if not self.alpha[a]:
                continue
            gid = table.by_token[q][t]
            if gid >= 0:
                for b, gids in prepared.arcs[p][a]:
                    self.edge_visits += 1
                    if gid in gids:
                        coefficient += self.alpha[a] * post.beta[p + 1][b]
        numerator = coefficient * weight
        if not 0 <= numerator <= post.total:
            raise RuntimeError("queried original numerator outside posterior mass")
        return numerator


class FullSparseOutside:
    """Competent full outside control, without allocating V-sized output rows."""

    def __init__(self, posterior):
        if not posterior.total:
            raise ValueError("zero_valid_mass")
        self.posterior, self.queries = posterior, 0
        prepared = posterior.prepared
        alpha, coefficients = [1], {key: 0 for key in prepared.members}
        for p, layer in enumerate(prepared.arcs):
            following = [0] * len(prepared.layers[p + 1])
            for a, outgoing in enumerate(layer):
                if not alpha[a]:
                    continue
                for (b, gids), mass in zip(outgoing, posterior.arc_weights[p][a], strict=True):
                    for gid in gids:
                        coefficients[p, gid] += alpha[a] * posterior.beta[p + 1][b]
                    following[b] += alpha[a] * mass
            alpha = following
        conservation = [0] * len(prepared.canvas)
        for key, value in coefficients.items():
            conservation[key[0]] += posterior.leaf[key] * value
        if any(value != posterior.total for value in conservation):
            raise RuntimeError("sparse outside lost original marginal conservation")
        self.coefficients = coefficients

    def at(self, p, t):
        post, table = self.posterior, self.posterior.prepared.table
        weight = post.weights.at(p, t)
        self.queries += 1
        if post.weights.canvas[p] is not None:
            return weight * post.total
        coefficient = sum(
            self.coefficients.get((p, gid), 0)
            for q in table.by_state
            if (gid := table.by_token[q][t]) >= 0
        )
        return weight * coefficient


def commits(posterior, word, upper, threshold, budget, outside="cursor"):
    if len(word) != len(posterior.weights.canvas):
        raise ValueError("sample differs from physical canvas")
    if any(t is not None and word[p] != t for p, t in enumerate(posterior.weights.canvas)):
        raise ValueError("sample changed fixed original ID")
    if type(budget) is not int or budget <= 0:
        raise ValueError("positive commitment budget required")
    threshold, upper = Fraction(threshold), Fraction(upper)
    if not 0 <= threshold <= 1 or upper.denominator != 1 or upper < 0:
        raise ValueError("invalid threshold or integer tail units")
    factory = {"cursor": ConfidenceCursor, "full_sparse": FullSparseOutside}.get(outside)
    if factory is None:
        raise ValueError("unknown outside interface")
    cursor = factory(posterior)
    accepted, decisions = [], {}
    for p, fixed in enumerate(posterior.weights.canvas):
        if fixed is not None:
            if word[p] != fixed:
                raise ValueError("sample changed fixed original ID")
            continue
        value = cursor.at(p, word[p])
        low = Fraction(value, posterior.total + upper.numerator)
        high = Fraction(value + upper.numerator, posterior.total + upper.numerator)
        decision = True if low >= threshold else False if high < threshold else None
        decisions[p] = dict(low=str(low), high=str(high), accepted=decision)
        if decision is None:
            return dict(committed=None, decisions=decisions, ambiguous=[p], queries=cursor.queries)
        if decision:
            accepted.append(p)
            if len(accepted) == budget:
                break
    if not decisions:
        raise ValueError("no free original positions")
    return dict(
        committed=accepted or [min(decisions)],
        decisions=decisions,
        ambiguous=[],
        queries=cursor.queries,
    )


def evaluate(
    table,
    weights,
    tolerance,
    *,
    method="handoff",
    depths=(1, 2, 3, 4, 6, 8, 12),
    timeout_seconds=120,
    max_cells=10_000_000,
    max_edges=10_000_000,
    max_terms=50_000_000,
):
    """A24 adaptive control flow, supplied the SAME exact summaries for all methods."""
    tolerance = Fraction(tolerance)
    if not 0 < tolerance < 1:
        raise ValueError("tolerance must be strictly between zero and one")
    if method not in ("closed", "handoff", "grammar_hit", "suffix_hit", "exact_stack"):
        raise ValueError("unknown posterior method")
    if not depths or any(type(d) is not int or d < 0 for d in depths):
        raise ValueError("depths must be nonnegative integers")
    if any(a >= b for a, b in pairwise(depths)):
        raise ValueError("depths must be strictly increasing")
    end, attempts = monotonic() + timeout_seconds, []
    counter = CounterTable(table) if method not in ("grammar_hit", "exact_stack") else None

    def remaining():
        value = end - monotonic()
        if value <= 0:
            raise CompilationLimit("adaptive query deadline; no sample certified")
        return value

    for depth in (None,) if method == "exact_stack" else (*depths, None):
        tracked = depth is not None and method in ("grammar_hit", "handoff")
        prepared = StackPrepared(
            table,
            weights.canvas,
            max_depth=depth,
            track_overflow=tracked,
            timeout_seconds=remaining(),
            max_cells=max_cells,
            max_edges=max_edges,
            max_terms=max_terms,
        )
        posterior = StackPosterior(prepared, weights, sums=weights.sums)
        upper, used = Fraction(), "full" if depth is None else "zero_lower_mass"
        if posterior.total and depth is not None:
            if tracked:
                frontier = OverflowFrontier(
                    prepared, weights, sums=weights.sums, timeout_seconds=remaining()
                )
                upper, used = frontier.mass, "grammar_hit"
                if method == "handoff" and conditional_error(posterior.mass, upper) > tolerance:
                    upper, _ = frontier.handoff(counter, timeout_seconds=remaining())
                    used = "handoff"
            else:
                upper, _ = counter.tail(
                    weights, depth, mode=method, sums=weights.sums, timeout_seconds=remaining()
                )
                used = method
        delta = conditional_error(posterior.mass, upper) if posterior.total else None
        attempts.append(
            dict(
                depth=depth,
                lower_mass=str(posterior.mass),
                upper_tail=str(upper),
                delta=None if delta is None else str(delta),
                bound=used,
                nodes=prepared.graph_nodes,
                edges=prepared.graph_edges,
            )
        )
        remaining()
        if depth is None or (delta is not None and delta <= tolerance):
            return posterior, dict(
                depth=depth,
                delta="0" if depth is None else str(delta),
                upper_tail=str(upper),
                attempts=attempts,
            )
    raise RuntimeError("adaptive decoder lost its full fallback")


def confidence(posterior, certificate, word, *, threshold="4/5", budget=4, outside="cursor"):
    upper = Fraction(certificate["upper_tail"]) * prod(posterior.weights.denominators)
    return commits(posterior, word, upper, threshold, budget, outside)
