"""Competent common work: stable partial support and complete-word check."""

import json


def stable_topk(values, k):
    cutoff = values.topk(k, sorted=False).values.min()
    higher = (values > cutoff).nonzero().flatten().tolist()
    ties = (values == cutoff).nonzero().flatten()[: k - len(higher)].tolist()
    return tuple(sorted((*higher, *ties), key=lambda t: (-float(values[t]), t)))


def complete_point(canvas, rows, adapter, proposals, *, threshold, cap):
    free = {p for p, t in enumerate(canvas) if t is None}
    if len(proposals) != len(free) or {p for p, _, _ in proposals} != free:
        return None
    witness = list(canvas)
    for p, t, _ in proposals:
        if t not in rows[p]:
            return None
        witness[p] = t
    try:
        text = adapter.detokenize_bytes(tuple(witness)).decode()

        def reject(value):
            raise ValueError(value)

        json.loads(text, parse_constant=reject)
    except (ValueError, UnicodeDecodeError):
        return None
    eligible = [(p, t) for p, t, w in proposals if w >= threshold]
    updates = tuple(eligible[:cap]) if eligible else tuple((p, t) for p, t, _ in proposals[:1])
    return updates, tuple(witness)


def keep_engine(engine, updates, witness):
    if hasattr(engine, "current"):
        engine.current = witness
    if hasattr(engine, "minimum_position"):
        engine.minimum_position = None
    for p, t in updates:
        if hasattr(engine, "commit"):
            engine.commit(p, t)
        elif hasattr(engine, "fix"):
            engine.fix(p, t)
        else:
            engine.canvas[p] = t
