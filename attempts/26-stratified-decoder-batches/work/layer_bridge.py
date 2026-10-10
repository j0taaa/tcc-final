"""A rank-circuit view of the independently frozen full-V JSON stack control."""

from types import SimpleNamespace

from mwpc_exact.cfg_posterior import CfgSampler, _Term

from .ranks import CfgRanks


def stack_ranks(posterior):
    """Translate sum/product representation only; preserve all original IDs.

    The five classical JSON reference files are immutable copies of A24/v8.
    This view adds no pruning and never calls a decoder in a mutable attempt.
    """
    prepared, weights = posterior.prepared, posterior.weights
    terms, inside, nodes, groups = [], [], {}, {}

    def add(alternatives):
        node = len(terms)
        alternatives = tuple(alternatives)
        terms.append(alternatives)
        inside.append(sum(CfgSampler.term_mass(t, rows, inside) for t in alternatives))
        return node

    vocabulary = range(weights.vocabulary_size)
    rows = tuple(tuple(weights.at(p, t) for t in vocabulary) for p in range(len(weights.canvas)))
    end = len(prepared.canvas)
    for state, accepting in enumerate(prepared.accepting):
        nodes[end, state] = add((_Term(),) if accepting else ())
    for p in reversed(range(end)):
        for state, outgoing in enumerate(prepared.arcs[p]):
            alternatives = []
            for target, gids in outgoing:
                for gid in gids:
                    key = p, gid
                    if key not in groups:
                        groups[key] = add(_Term(choice=(p, t)) for t in prepared.members[key])
                    alternatives.append(_Term(children=(groups[key], nodes[p + 1, target])))
            nodes[p, state] = add(alternatives)
    root = nodes[0, 0]
    if inside[root] != posterior.total:
        raise RuntimeError("rank circuit changed the full-V stack mass")
    state = SimpleNamespace(
        canvas=weights.canvas, support=SimpleNamespace(rows=(vocabulary,) * end)
    )
    plan = SimpleNamespace(
        root=root,
        terms=tuple(terms),
        order=tuple(range(len(terms))),
        state=state,
        term_mass=CfgSampler.term_mass,
    )
    view = SimpleNamespace(
        _plan=plan, _inside=tuple(inside), _weights=rows, inputs=SimpleNamespace(state=state)
    )
    return CfgRanks(view)
