"""Small rational oracle for the classical potential/count envelope, not CUDA."""

from fractions import Fraction as F
from math import prod

from .reference import Category, Reference, ceiling


def construct(layers, rows, *, grid=64, bits=16, scales=None, potentials=None):
    if type(grid) is not int or grid < 1 or 2 * grid >= 1 << bits:
        raise ValueError("declared integer count budget required")
    n = len(layers)
    scales = tuple(scales) if scales is not None else (F(3, 2),) * n
    if len(scales) != n or any(s <= 0 for s in scales):
        raise ValueError("positive common layer scales required")
    upper = tuple(tuple(w * F(101, 100) for w in row) for row in rows)
    edge_upper = tuple(
        tuple(
            tuple(sum((upper[p][t] for t in edge.tokens), F()) * F(103, 100) for edge in node)
            for node in layer
        )
        for p, layer in enumerate(layers)
    )
    if potentials is None:
        h = [(F(1),)]
        for p in range(n - 1, -1, -1):
            h.append(
                tuple(
                    sum(
                        (edge_upper[p][s][e] * h[-1][edge.target] for e, edge in enumerate(node)),
                        F(),
                    )
                    / scales[p]
                    + F(1, 32)
                    for s, node in enumerate(layers[p])
                )
            )
        potentials = tuple(reversed(h))
    if len(potentials) != n + 1 or any(v <= 0 for h in potentials for v in h):
        raise ValueError("positive potentials on every declared state required")
    if tuple(potentials[-1]) != (F(1),):
        raise ValueError("accepting leaf potential must be one")

    def category(ratios):
        counts = tuple(
            max(1, ceiling((grid * r).numerator, (grid * r).denominator)) for r in ratios
        )
        if sum(counts) > 2 * grid:
            raise ValueError("count budget cap: refuse, never prune original IDs")
        table = Category(counts, bits)
        factor = F(sum(counts), grid) / (1 - F(sum(counts), 1 << bits))
        return table, factor

    tables, factors = [], []
    for p, layer in enumerate(layers):
        level, edge_factor, token_factor = [], F(), F()
        for state, node in enumerate(layer):
            e_up = edge_upper[p][state]
            edge_table, k = category(
                tuple(
                    value * potentials[p + 1][edge.target] / (scales[p] * potentials[p][state])
                    for value, edge in zip(e_up, node, strict=True)
                )
            )
            edge_factor = max(edge_factor, k)
            token_tables = []
            for e, edge in enumerate(node):
                token_table, k = category(
                    tuple(upper[p][t] / e_up[e] if e_up[e] else F() for t in edge.tokens)
                )
                token_tables.append(token_table)
                token_factor = max(token_factor, k)
            level.append((edge_table, tuple(token_tables)))
        tables.append(tuple(level))
        factors.append((edge_factor, token_factor))
    proposal = Reference(layers, rows, tuple(tables))
    envelope = (
        potentials[0][0]
        * prod(scales, start=F(1))
        * prod((k for level in factors for k in level), start=F(1))
    )
    return dict(
        proposal=proposal,
        envelope=envelope,
        potentials=potentials,
        scales=scales,
        factors=tuple(factors),
    )


def sample(prepared, rng, cap):
    proposal, envelope = prepared["proposal"], prepared["envelope"]
    for trial in range(1, cap + 1):
        word = proposal.proposal(rng)
        weight, q, _ = proposal.trace(word)
        ratio = weight / (envelope * q)
        if not 0 <= ratio <= 1:
            raise RuntimeError("bad count envelope, never clamp")
        if rng.randrange(ratio.denominator) < ratio.numerator:
            return dict(status="COMPLETE", word=word, trials=trial)
    return dict(status="FAIL", word=None, trials=cap)
