"""Matched summary/block/query boundary for immutable A23 compact CFG controls."""

import importlib
import sys
import types
from math import prod

from ..frozen_control import materialize
from .query import choose


def load():
    target, source, archive_hash = materialize()
    name = "_a24_consumer_compact_frozen"
    if name not in sys.modules:
        package = types.ModuleType(name)
        package.__path__ = [str(target / "attempts/23-canonical-epsilon-posterior/work")]
        sys.modules[name] = package
    modules = {
        key: importlib.import_module(name + "." + key)
        for key in ("forest", "epsilon", "lexer", "posterior")
    }
    modules["grammars"] = {
        True: modules["lexer"].lexical_grammar(marked=True),
        False: modules["lexer"].lexical_grammar(marked=False),
    }
    return modules, dict(source_commit=source, source_archive_sha256=archive_hash)


def evaluate_compact(table, weights, method, *, modules=None, **limits):
    modules = load()[0] if modules is None else modules
    if method not in ("exact_local", "exact_bidir_local", "exact_eps_local"):
        raise ValueError("unknown compact control")
    epsilon = method == "exact_eps_local"
    grammar = modules["grammars"][not epsilon]
    factory = modules["epsilon"].EpsilonPrepared if epsilon else modules["forest"].Prepared
    kind = "bidir_local" if method == "exact_bidir_local" else "local"
    prepared = factory(table, weights.canvas, grammar, kind, **limits)
    posterior = modules["posterior"].Posterior(prepared, weights)
    return posterior, dict(delta="0", depth=None, upper_tail="0")


def sample_compact(posterior, weights, rng):
    """Preserve original forest law, using identical efficient block recovery."""
    if weights.consumed:
        raise ValueError("completion already drawn")
    if not posterior.total:
        raise ValueError("zero_valid_mass")
    weights.consumed = True
    prepared, tokens, seen = posterior.prepared, list(weights.canvas), set()
    pending = [prepared.plan.root]
    while pending:
        node = pending.pop()
        terms = prepared.plan.terms[node]
        term = terms[choose([posterior.term_mass(t) for t in terms], rng)]
        if term.choice is None:
            pending.extend(term.children)
            continue
        p, i = term.choice
        if p in seen:
            raise RuntimeError("compact forest repeated an original physical slot")
        seen.add(p)
        if weights.canvas[p] is not None:
            continue
        code = prepared.rows[p][i]
        cids = prepared.table.local_to_class[code]
        cid = cids[choose([weights.sums[p][c] for c in cids], rng)]
        row = weights.row_of[p]
        bids = weights.stats.partition.class_blocks[cid]
        bid = bids[choose([weights.stats.totals[row][b] for b in bids], rng)]
        ids = weights.stats.partition.blocks[bid]
        values = [weights.at(p, t) for t in ids]
        if sum(values) != weights.stats.totals[row][bid]:
            raise RuntimeError("provider changed original compact block")
        tokens[p] = ids[choose(values, rng)]
    if len(seen) != len(tokens) or any(t is None for t in tokens):
        raise RuntimeError("compact forest omitted original physical slots")
    return tuple(tokens)


class CompactOutside:
    """Full sparse outside; no dense V-sized marginal output required."""

    def __init__(self, posterior):
        if not posterior.total:
            raise ValueError("zero_valid_mass")
        self.posterior, self.queries = posterior, 0
        prepared, plan = posterior.prepared, posterior.prepared.plan
        outside = [0] * len(plan.terms)
        outside[plan.root] = 1
        coefficients = {key: 0 for key in prepared.members}
        for node in reversed(plan.order):
            if not outside[node]:
                continue
            for term in plan.terms[node]:
                if term.choice is not None:
                    p, i = term.choice
                    coefficients[p, prepared.rows[p][i]] += outside[node]
                elif term.children:
                    for i, child in enumerate(term.children):
                        outside[child] += outside[node] * prod(
                            posterior.inside[c] for j, c in enumerate(term.children) if i != j
                        )
        conservation = [0] * len(prepared.canvas)
        for key, value in coefficients.items():
            conservation[key[0]] += posterior.leaf[key] * value
        if any(value != posterior.total for value in conservation):
            raise RuntimeError("compact outside lost original conservation")
        self.coefficients = coefficients

    def at(self, p, t):
        self.queries += 1
        post, table = self.posterior, self.posterior.prepared.table
        weight = post.weights.at(p, t)
        if post.weights.canvas[p] is not None:
            return weight * post.total
        return weight * sum(
            self.coefficients.get((p, gid), 0)
            for q in table.by_state
            if (gid := table.by_token[q][t]) >= 0
        )


def confidence_compact(posterior, word, *, threshold="4/5", budget=4):
    from fractions import Fraction

    threshold = Fraction(threshold)
    if len(word) != len(posterior.weights.canvas) or any(
        t is not None and word[p] != t for p, t in enumerate(posterior.weights.canvas)
    ):
        raise ValueError("sample changed physical canvas")
    query, accepted, decisions = CompactOutside(posterior), [], {}
    for p, fixed in enumerate(posterior.weights.canvas):
        if fixed is not None:
            continue
        value = Fraction(query.at(p, word[p]), posterior.total)
        decision = value >= threshold
        decisions[p] = dict(low=str(value), high=str(value), accepted=decision)
        if decision:
            accepted.append(p)
            if len(accepted) == budget:
                break
    return dict(
        committed=accepted or [min(decisions)],
        decisions=decisions,
        ambiguous=[],
        queries=query.queries,
    )
