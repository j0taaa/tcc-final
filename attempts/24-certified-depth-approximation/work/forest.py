"""Classical lexical forward/backward trimming; independent frozen extraction."""

from time import monotonic

from .lexer import OUT, finish


def coaccessible_layers(table, canvas, *, deadline=None):
    """Classical lexical forward/backward trimming, without weights or grammar."""
    layers = [{OUT}]

    def choices(q, fixed):
        if fixed is None:
            return table.by_state[q]
        gid = table.by_token[q][fixed]
        return () if gid < 0 else (gid,)

    for fixed in canvas:
        if deadline is not None and monotonic() >= deadline:
            raise TimeoutError("lexical coaccessibility deadline")
        layers.append({table.groups[g][1] for q in layers[-1] for g in choices(q, fixed)})
    layers[-1] = {q for q in layers[-1] if finish(q) is not None}
    for p in reversed(range(len(canvas))):
        if deadline is not None and monotonic() >= deadline:
            raise TimeoutError("lexical coaccessibility deadline")
        layers[p] = {
            q
            for q in layers[p]
            if any(table.groups[g][1] in layers[p + 1] for g in choices(q, canvas[p]))
        }
    return layers
