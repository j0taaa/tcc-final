"""Small exact correctness checks; no model, benchmark or novelty claim."""

import json
from collections import deque
from fractions import Fraction as F
from functools import lru_cache
from itertools import permutations, product
from math import prod


def compositions(total, size):
    if size == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in compositions(total - first, size - 1):
            yield (first, *rest)


def transport(p, q, named):
    """Rational max-flow oracle, deliberately dense and for tiny domains only."""
    size = len(p)
    plan = [[F(0) for _ in q] for _ in p]
    lower = max([F(0), *(p[c] + q[c] - 1 for c in named)])
    left, right = list(p), list(q)
    if lower:
        c = next(c for c in named if p[c] + q[c] - 1 == lower)
        plan[c][c] = lower
        left[c] -= lower
        right[c] -= lower
    source, sink = 2 * size, 2 * size + 1
    capacity = [[F(0)] * (sink + 1) for _ in range(sink + 1)]
    for i in range(size):
        capacity[source][i] = left[i]
        capacity[size + i][sink] = right[i]
        for j in range(size):
            if i != j or i not in named:
                capacity[i][size + j] = 1
    remaining = 1 - lower
    while remaining:
        parent = {source: None}
        queue = deque([source])
        while queue and sink not in parent:
            node = queue.popleft()
            for nxt, value in enumerate(capacity[node]):
                if value > 0 and nxt not in parent:
                    parent[nxt] = node
                    queue.append(nxt)
        assert sink in parent, "Hall feasibility failed"
        amount, node = remaining, sink
        while node != source:
            previous = parent[node]
            amount = min(amount, capacity[previous][node])
            node = previous
        node = sink
        while node != source:
            previous = parent[node]
            capacity[previous][node] -= amount
            capacity[node][previous] += amount
            node = previous
        remaining -= amount
    for i in range(size):
        for j in range(size):
            plan[i][j] += capacity[size + j][i]
    assert [sum(row) for row in plan] == list(p)
    assert [sum(plan[i][j] for i in range(size)) for j in range(size)] == list(q)
    assert sum(plan[c][c] for c in named) == lower
    return plan


def sparse_transport(p, q, named):
    """Quantile atoms followed by diagonal cancellation; no hash/LP required."""
    size = len(p)
    atoms = []
    diagonal = []
    left, right = list(p), list(q)
    i, j = 0, 0
    while i < size and j < size:
        amount = min(left[i], right[j])
        if amount:
            if i == j and i in named:
                diagonal.append(len(atoms))
            atoms.append([i, j, amount])
            left[i] -= amount
            right[j] -= amount
        if not left[i]:
            i += 1
        if not right[j]:
            j += 1
    assert len(atoms) <= 2 * size - 1
    while len(diagonal) >= 2:
        a, b = diagonal[-2:]
        i, j = atoms[a][0], atoms[b][0]
        amount = min(atoms[a][2], atoms[b][2])
        atoms[a][2] -= amount
        atoms[b][2] -= amount
        atoms.extend([[i, j, amount], [j, i, amount]])
        diagonal[-2:] = [index for index in (a, b) if atoms[index][2]]
    assert len(atoms) <= 4 * size - 3
    if diagonal:
        a = diagonal[0]
        d = atoms[a][0]
        end = len(atoms)
        for index in range(end):
            j, k, mass = atoms[index]
            if j != d and k != d and mass and atoms[a][2]:
                amount = min(atoms[a][2], mass)
                atoms[a][2] -= amount
                atoms[index][2] -= amount
                atoms.extend([[d, k, amount], [j, d, amount]])
    assert len(atoms) <= 12 * size - 9
    # Aggregate only for this independent, dense verification on tiny domains.
    plan = [[F(0)] * size for _ in range(size)]
    for i, j, mass in atoms:
        plan[i][j] += mass
    assert [sum(row) for row in plan] == list(p)
    assert [sum(plan[i][j] for i in range(size)) for j in range(size)] == list(q)
    assert sum(plan[c][c] for c in named) == max([F(0), *(p[c] + q[c] - 1 for c in named)])
    return plan


def b1():
    cases = 0
    for size, denominator in [(3, 4), (4, 3)]:
        laws = [tuple(F(a, denominator) for a in v) for v in compositions(denominator, size)]
        for p, q in product(laws, repeat=2):
            for bits in product((False, True), repeat=size):
                named = {c for c, include in enumerate(bits) if include}
                reference = transport(p, q, named)
                sparse = sparse_transport(p, q, named)
                assert sum(sparse[c][c] for c in named) == sum(reference[c][c] for c in named)
                cases += 1
    # Original IDs 0/1 share a named class; IDs 3/4 belong to the free tail.
    groups = (0, 0, 1, 2, 2)
    ids = [
        tuple(map(F, row))
        for row in [
            (F(2, 5), F(1, 5), F(1, 5), F(1, 10), F(1, 10)),
            (F(1, 5), F(3, 10), F(2, 5), F(1, 20), F(1, 20)),
            (F(1, 10), F(1, 10), F(1, 5), F(1, 5), F(2, 5)),
        ]
    ]
    classes = [
        tuple(sum(p[v] for v, c in enumerate(groups) if c == k) for k in range(3)) for p in ids
    ]
    edges = [sparse_transport(classes[i], classes[i + 1], {0, 1}) for i in range(2)]
    joint = {}
    for word in product(range(5), repeat=3):
        cs = tuple(groups[v] for v in word)
        mass = classes[0][cs[0]]
        for i in range(2):
            mass *= edges[i][cs[i]][cs[i + 1]] / classes[i][cs[i]]
        mass *= prod(ids[i][v] / classes[i][cs[i]] for i, v in enumerate(word))
        joint[word] = mass
    assert sum(joint.values()) == 1
    for i in range(3):
        assert [sum(w for x, w in joint.items() if x[i] == v) for v in range(5)] == list(ids[i])

    def collision(x):
        return sum(groups[x[i]] == groups[x[i + 1]] and groups[x[i]] in {0, 1} for i in range(2))

    coupled = sum(w * collision(x) for x, w in joint.items())
    independent = sum(prod(ids[i][v] for i, v in enumerate(x)) * collision(x) for x in joint)
    assert coupled == F(1, 10) and independent == F(14, 25)

    def loss(i, v):
        return (i + 1) * (v - 2) ** 2

    assert sum(w * sum(loss(i, v) for i, v in enumerate(x)) for x, w in joint.items()) == sum(
        p[v] * loss(i, v) for i, p in enumerate(ids) for v in range(5)
    )
    # Three fair bits cannot all disagree around an odd cycle.
    assert (
        min(sum(x[i] == x[(i + 1) % 3] for i in range(3)) for x in product((0, 1), repeat=3)) == 1
    )
    # A grammar requiring equality makes the unconstrained zero-collision law invalid.
    fair = (F(1, 2), F(1, 2))
    zero_collision = transport(fair, fair, {0, 1})
    assert sum(zero_collision[c][c] for c in (0, 1)) == 0
    return {
        "transport_cases": cases,
        "linear_sparse_matches_flow_objective": True,
        "original_id_words": len(joint),
        "collision_coupled": str(coupled),
        "collision_iid": str(independent),
        "additive_loss_preserved": True,
        "cycle_and_grammar_counterexamples": True,
    }


def b2():
    leaves = {}

    def expand(state, trace, mass):
        remaining = [i for i, v in enumerate(state) if v is None]
        if not remaining:
            assert state not in leaves, "Non-injective trace"
            leaves[state] = (trace, mass)
            return
        count = sum(v or 0 for v in state)
        position = min(remaining) if count % 2 == 0 else max(remaining)
        p_zero = F(2 + position + count, 5 + position + 2 * count)
        for value, chance in [(0, p_zero), (1, 1 - p_zero)]:
            nxt = list(state)
            nxt[position] = value
            expand(tuple(nxt), (*trace, (position, value)), mass * chance)

    expand((None,) * 4, (), F(1))
    assert len(leaves) == 16 and sum(p for _, p in leaves.values()) == 1
    words = list(leaves)
    laws = [leaves[x][1] for x in words]
    success_sets = [{words[0]}, {words[-1]}, {x for x in words if x[0] == x[-1]}]
    checked = 0
    for k in (1, 2, 3):
        misses = [F(0)] * len(success_sets)
        total = F(0)
        for indices in permutations(range(len(words)), k):
            mass, removed = F(1), F(0)
            for index in indices:
                mass *= laws[index] / (1 - removed)
                removed += laws[index]
            total += mass
            for j, success in enumerate(success_sets):
                if all(words[i] not in success for i in indices):
                    misses[j] += mass
        assert total == 1
        for success, miss in zip(success_sets, misses, strict=True):
            a = sum(leaves[x][1] for x in success)
            assert miss <= (1 - a) ** k
            checked += 1
    # A discarded bit creates two traces for each retained one-bit answer.
    hidden = [(noise, output) for noise, output in product((0, 1), repeat=2)]
    assert len(hidden) > len({output for _, output in hidden})
    return {
        "injective_canvases": len(leaves),
        "wor_hit_inequalities": checked,
        "discarded_randomness_counterexample": True,
    }


def b3():
    documents = [
        json.dumps({"a": a, "b": b}, separators=(",", ":"))
        for a, b in product(('"a', "\\a"), ("x", "y"))
    ]
    assert len({len(d) for d in documents}) == 1
    mutable = [i for i in range(len(documents[0])) if len({d[i] for d in documents}) > 1]
    checked, early = 0, False
    for witness in documents:
        for bits in product((False, True), repeat=len(mutable)):
            pins = {i: witness[i] for i in range(len(witness)) if i not in mutable}
            pins.update({i: witness[i] for i, take in zip(mutable, bits, strict=True) if take})
            valid = [d for d in documents if all(d[i] == v for i, v in pins.items())]
            assert valid
            start = witness.index('"b":')
            # The schema fixes path identity; all bytes of this literal are pinned.
            if all(i in pins for i in range(start, len(witness))):
                values = {json.loads(d)["b"] for d in valid}
                assert len(values) == 1
                checked += 1
                early |= len({json.loads(d)["a"] for d in valid}) > 1
    assert early
    # Same pinned local field at the same offsets, different semantic paths.
    flat = '{"a":0,' + " " * 6 + '"b":1} '
    nested = '{"a":{' + " " * 7 + '"b":1}}'
    assert len(flat) == len(nested) and flat[13:18] == nested[13:18]
    assert "b" in json.loads(flat) and "b" not in json.loads(nested)
    return {
        "sound_publications": checked,
        "early_field_exists": early,
        "local_path_counterexample": True,
    }


def b4():
    desired = (F(3, 5), F(2, 5))
    coupling = {(1, 0): F(3, 5), (0, 1): F(2, 5)}
    assert sum(coupling.values()) == 1
    assert tuple(sum(w * x[i] for x, w in coupling.items()) for i in range(2)) == desired
    product_weights = {
        x: prod(desired[i] if v else 1 - desired[i] for i, v in enumerate(x)) for x in coupling
    }
    conditional = product_weights[(1, 0)] / sum(product_weights.values())
    assert conditional == F(9, 13) and conditional - desired[0] == F(6, 65)
    # Farkas separator y=(1,-1,-1): y*A=0, y*b=-2/5<0.
    assert all(1 - sum(x) == 0 for x in coupling)
    assert 1 - F(7, 10) - F(7, 10) == -F(2, 5)
    return {
        "exact_marginal_witness": True,
        "conditioning_distortion": "6/65",
        "infeasible_dual_value": "-2/5",
    }


def b5():
    states = tuple(product((0, 1), repeat=3))
    decision = {x: x[1] if x[0] == 0 else x[2] for x in states}

    @lru_cache(None)
    def depth(remaining):
        if len({decision[x] for x in remaining}) == 1:
            return 0
        costs = []
        for i in range(3):
            branches = [tuple(x for x in remaining if x[i] == v) for v in (0, 1)]
            if all(branches):
                costs.append(1 + max(depth(branch) for branch in branches))
        return min(costs)

    assert depth(states) == 2
    # Independent lower bound: no single attribute resolves every branch.
    assert all(
        any(len({decision[x] for x in states if x[i] == v}) > 1 for v in (0, 1)) for i in range(3)
    )
    # Constructive upper bound: ask selector, then only the selected payload.
    for x in states:
        known = {0: x[0], 1 if x[0] == 0 else 2: x[1] if x[0] == 0 else x[2]}
        possible = {decision[y] for y in states if all(y[i] == v for i, v in known.items())}
        assert possible == {decision[x]}
    assert decision[(0, 0, 0)] != decision[(1, 0, 1)]
    return {
        "completion_states": len(states),
        "optimal_worst_case_questions": 2,
        "default_counterexample": True,
    }


if __name__ == "__main__":
    print(json.dumps({"B1": b1(), "B2": b2(), "B3": b3(), "B4": b4(), "B5": b5()}, indent=2))
