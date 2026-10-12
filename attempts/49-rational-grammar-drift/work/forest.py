"""Research adapter for an admitted immutable CFG forest, not a decoder."""

import importlib
from fractions import Fraction
from math import lcm

_planar = importlib.import_module("attempts.49-rational-grammar-drift.work.planar")


def certificate(
    plan,
    first,
    second,
    epsilon=Fraction(1, 2),
    max_rows=100_000,
    compressor=None,
    exact_passthrough=False,
):
    engine = _planar if compressor is None else compressor
    if first.state != plan.state or second.state != plan.state:
        raise ValueError("both heads must use the exact same compiled state/support")
    weights = []
    for data in [first, second]:
        head = []
        for row in data.probabilities:
            scale = lcm(*(v.denominator for v in row))
            head.append(tuple(p.numerator * (scale // p.denominator) for p in row))
        weights.append(head)
    masses, scopes, costs, event_counts = {}, {}, {}, {}
    for node in plan.order:
        total = [0, 0]
        local_scopes, local_costs, local_counts = [], [], []
        for term in plan.terms[node]:
            if term.choice is not None:
                position, index = term.choice
                scope, cost, count = frozenset([position]), 0, 1
                value = [w[position][index] for w in weights]
            elif term.children:
                left, right = term.children
                if scopes[left] & scopes[right]:
                    raise ValueError("product repeats original slot weights")
                scope = scopes[left] | scopes[right]
                extra = (
                    0
                    if exact_passthrough and min(event_counts[left], event_counts[right]) <= 1
                    else 1
                )
                cost = costs[left] + costs[right] + extra
                count = min(2, event_counts[left] * event_counts[right])
                value = [masses[left][j] * masses[right][j] for j in [0, 1]]
            else:
                scope, cost, count, value = frozenset(), 0, 1, [1, 1]
            local_scopes.append(scope)
            local_costs.append(cost)
            local_counts.append(count)
            total = [total[j] + value[j] for j in [0, 1]]
        if not local_scopes or any(s != local_scopes[0] for s in local_scopes):
            raise ValueError("alternatives do not share a physical slot scope")
        scope = local_scopes[0]
        if not scope and total != [1, 1]:
            raise ValueError("empty-scope node has multiple unweighted derivations")
        scopes[node], masses[node] = scope, total
        extra = 0 if exact_passthrough and len(plan.terms[node]) == 1 else 1
        costs[node] = max(local_costs) + extra if scope else 0
        event_counts[node] = min(2, sum(local_counts))
    if plan.root is None or 0 in masses[plan.root]:
        return dict(status="ZERO_VALID_MASS_UNDEFINED_TV")
    if scopes[plan.root] != frozenset(range(len(plan.state.canvas))):
        raise ValueError("root does not consume all original positions")
    size = max(1, costs[plan.root])
    grid = engine.grid_for(epsilon, size)
    cores = {}
    peak_rows = peak_bits = 0

    def reduce(rows):
        nonlocal peak_rows, peak_bits
        if len(rows) > max_rows:
            raise RuntimeError("research core budget: no certificate issued")
        peak_rows = max(peak_rows, len(rows))
        peak_bits = max(
            peak_bits, max((abs(x).bit_length() for row in rows for x in row), default=0)
        )
        return engine.compress(rows, grid)

    for node in plan.order:
        if not scopes[node]:
            cores[node] = [(1, 1)]
            continue
        rows = []
        for term in plan.terms[node]:
            if term.choice is not None:
                position, index = term.choice
                part = [tuple(w[position][index] for w in weights)]
            elif term.children:
                left, right = term.children
                stream_product = getattr(engine, "compress_product", None)
                if exact_passthrough and min(len(cores[left]), len(cores[right])) <= 1:
                    part = [(a[0] * b[0], a[1] * b[1]) for a in cores[left] for b in cores[right]]
                    peak_rows = max(peak_rows, len(part))
                    peak_bits = max(
                        peak_bits, max((abs(x).bit_length() for a in part for x in a), default=0)
                    )
                elif stream_product is not None:
                    count = len(cores[left]) * len(cores[right])
                    peak_rows = max(peak_rows, count)
                    product_bits = max(
                        (
                            (
                                max((abs(a[j]) for a in cores[left]), default=0)
                                * max((abs(a[j]) for a in cores[right]), default=0)
                            ).bit_length()
                            for j in [0, 1]
                        ),
                        default=0,
                    )
                    peak_bits = max(peak_bits, product_bits)
                    part = stream_product(cores[left], cores[right], grid)
                elif len(cores[left]) * len(cores[right]) > max_rows:
                    raise RuntimeError("research product budget: no certificate issued")
                else:
                    part = reduce(
                        [(a[0] * b[0], a[1] * b[1]) for a in cores[left] for b in cores[right]]
                    )
            else:
                part = [(1, 1)]
            if len(rows) + len(part) > max_rows:
                raise RuntimeError("research sum budget: no certificate issued")
            rows.extend(part)
        cores[node] = (
            [a for a in rows if a != (0, 0)]
            if exact_passthrough and len(plan.terms[node]) == 1
            else reduce(rows)
        )
    a, b = masses[plan.root]
    lower = Fraction(sum(abs(b * x - a * y) for x, y in cores[plan.root]), 2 * a * b)
    return dict(
        status="CERTIFIED_ON_ADMITTED_FOREST",
        lower=lower,
        upper=min(Fraction(1), (1 + epsilon) * lower),
        grid=grid,
        expanded_size=size,
        peak_candidate_rows=peak_rows,
        peak_integer_bits=peak_bits,
        nodes=len(plan.terms),
        alternatives=plan.alternatives,
        root_rows=len(cores[plan.root]),
    )
