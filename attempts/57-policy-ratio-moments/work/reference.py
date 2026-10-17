"""Independent exact finite-prefix reference; ordinary positive weighted inference.

The small grammar is J ::= 0 | 1 | '[' J ']'. Original IDs include aliases
and epsilon. This is an arithmetic oracle, not a real-head decoder/compiler.
"""

from collections import defaultdict
from fractions import Fraction as F


def step(state, emission):
    depth, complete = state
    if emission == "":
        return state
    if not complete:
        if emission == "[":
            return depth + 1, False
        if emission in ("0", "1"):
            return depth, True
    elif emission == "]" and depth:
        return depth - 1, True
    return None


def inside(rows, emissions, eos, terminal, minimum=-1):
    """Mass by FIRST-EOS layer; accepting suffixes have multiplicative weight1."""
    messages = {(0, False): F(1)}
    stops = []
    for i, row in enumerate(rows):
        nxt, accepted = defaultdict(F), F()
        for state, mass in messages.items():
            for v, weight in enumerate(row):
                if not weight:
                    continue
                if v == eos:
                    if i >= minimum and state == (0, True):
                        accepted += mass * weight * terminal[i]
                else:
                    target = step(state, emissions[v])
                    if target is not None:
                        nxt[target] += mass * weight
        stops.append(accepted)
        messages = nxt
    return tuple(stops)


def readout(rows, emissions, eos, gates, anchors, fixed, action):
    """Exact local moment queries, including class-path and length controls."""
    n, size = len(rows), len(emissions)
    if (
        len(gates) != 2
        or len(anchors) != 2
        or any(len(r) != size or any(w < 0 for w in r) for r in rows)
        or any(len(g) != n or any(len(r) != size for r in g) for g in gates)
        or any(len(u) != n or any(w <= 0 for w in u) for u in anchors)
        or any(not 0 < g < 1 for policy in gates for row in policy for g in row)
        or not action
        or any(i in fixed or not 0 <= i < n or not 0 <= v < size for i, v in action.items())
        or any(not 0 <= i < n or not 0 <= v < size for i, v in fixed.items())
    ):
        raise ValueError("common-support smooth planner and nonempty original-ID action required")
    active = set(range(n)) - set(fixed)
    cumulative, q, rr = [], [], []
    for k in range(2):
        total, h, weights = F(), [], []
        for i, row in enumerate(rows):
            if i in active:
                total += anchors[k][i]
            h.append(total)
            weights.append(
                tuple(
                    F(v == fixed[i])
                    if i in fixed
                    else row[v]
                    * (gates[k][i][v] if i in action else 1 - gates[k][i][v])
                    * (i not in action or action[i] == v)
                    for v in range(size)
                )
            )
        cumulative.append(h)
        q.append(weights)
        rr.append({i: anchors[k][i] / gates[k][i][v] for i, v in action.items()})
    minimum = max((*fixed, *action), default=-1)
    terminal = [tuple(1 / h if h else F() for h in row) for row in cumulative]
    stop = [inside(q[k], emissions, eos, terminal[k], minimum) for k in range(2)]
    partition = [sum(t, F()) for t in stop]
    if not all(partition):
        raise ValueError("positive observed action mass required")
    sums = [sum(r.values(), F()) for r in rr]
    mixed_rows = [
        tuple(b * b / a if a else F() for a, b in zip(x, y, strict=True))
        for x, y in zip(q[0], q[1], strict=True)
    ]
    mixed_terminal = tuple(
        a / b**2 if b else F() for a, b in zip(cumulative[0], cumulative[1], strict=True)
    )
    mixed = sum(inside(mixed_rows, emissions, eos, mixed_terminal, minimum), F())
    r20 = sum((rr[1][i] ** 2 / rr[0][i] for i in action), F())
    ratio_s = sums[1] / sums[0]
    visible = ratio_s * partition[1] / partition[0]
    # Class weights are summed BEFORE squaring/dividing. EOS has its own class.
    classes = tuple(dict.fromkeys((v == eos, e) for v, e in enumerate(emissions)))
    class_rows = []
    for i in range(n):
        row = []
        for cls in classes:
            totals = [
                sum((q[k][i][v] for v, e in enumerate(emissions) if (v == eos, e) == cls), F())
                for k in range(2)
            ]
            row.append(totals[1] ** 2 / totals[0] if totals[0] else F())
        class_rows.append(tuple(row))
    class_eos = next(i for i, (is_eos, _) in enumerate(classes) if is_eos)
    class_mixed = sum(
        inside(class_rows, tuple(e for _, e in classes), class_eos, mixed_terminal, minimum),
        F(),
    )
    prior_rows = tuple(
        tuple(F(v == fixed[i]) for v in range(size)) if i in fixed else tuple(row)
        for i, row in enumerate(rows)
    )
    z = sum(inside(prior_rows, emissions, eos, (F(1),) * n, max(fixed, default=-1)), F())
    return {
        "masses": tuple(s * p / z for s, p in zip(sums, partition, strict=True)),
        "visible": visible,
        "second": {
            "full": mixed / partition[0] * r20 / sums[0],
            "anchor": mixed / partition[0] * ratio_s**2,
            "class": class_mixed / partition[0] * r20 / sums[0],
            "combined": class_mixed / partition[0] * ratio_s**2,
            "length": ratio_s**2
            * sum((b * b / a if a else F() for a, b in zip(*stop, strict=True)), F())
            / partition[0],
            "visible": visible**2,
        },
        "stops": tuple(stop),
    }
