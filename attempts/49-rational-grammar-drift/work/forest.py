"""Research adapter for an admitted immutable CFG forest, not a decoder."""

import importlib
from fractions import Fraction
from math import lcm

_planar = importlib.import_module("attempts.49-rational-grammar-drift.work.planar")


def certificate(plan, first, second, epsilon=Fraction(1, 2), max_rows=100_000, compressor=None):
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
    masses, scopes, costs = {}, {}, {}
    for node in plan.order:
        total = [0, 0]
        local_scopes, local_costs = [], []
        for term in plan.terms[node]:
            if term.choice is not None:
                position, index = term.choice
                scope, cost = frozenset([position]), 0
                value = [w[position][index] for w in weights]
            elif term.children:
                left, right = term.children
                if scopes[left] & scopes[right]:
                    raise ValueError("product repeats original slot weights")
                scope = scopes[left] | scopes[right]
                cost = costs[left] + costs[right] + 1
                value = [masses[left][j] * masses[right][j] for j in [0, 1]]
            else:
                scope, cost, value = frozenset(), 0, [1, 1]
            local_scopes.append(scope)
            local_costs.append(cost)
            total = [total[j] + value[j] for j in [0, 1]]
        if not local_scopes or any(s != local_scopes[0] for s in local_scopes):
            raise ValueError("alternatives do not share a physical slot scope")
        scope = local_scopes[0]
        if not scope and total != [1, 1]:
            raise ValueError("empty-scope node has multiple unweighted derivations")
        scopes[node], masses[node] = scope, total
        costs[node] = max(local_costs) + 1 if scope else 0
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
                if len(cores[left]) * len(cores[right]) > max_rows:
                    raise RuntimeError("research product budget: no certificate issued")
                part = reduce(
                    [(a[0] * b[0], a[1] * b[1]) for a in cores[left] for b in cores[right]]
                )
            else:
                part = [(1, 1)]
            if len(rows) + len(part) > max_rows:
                raise RuntimeError("research sum budget: no certificate issued")
            rows.extend(part)
        cores[node] = reduce(rows)
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
