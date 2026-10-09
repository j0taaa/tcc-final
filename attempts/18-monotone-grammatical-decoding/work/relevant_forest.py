"""Classical root-dependency pruning, shared by every forest comparator.

No token/probability pruning: retain every derivation of the original root.
Raw construction and this pass are both charged to each decoder.
"""

from dataclasses import replace


def relevant_forest(plan):
    if plan.root is None:
        return plan
    relevant, pending = set(), [plan.root]
    while pending:
        node = pending.pop()
        if node in relevant:
            continue
        relevant.add(node)
        pending.extend(child for term in plan.terms[node] for child in term.children)
    order = [node for node in plan.order if node in relevant]
    index = {node: i for i, node in enumerate(order)}
    return replace(
        plan,
        terms=tuple(
            tuple(
                replace(term, children=tuple(index[c] for c in term.children))
                for term in plan.terms[n]
            )
            for n in order
        ),
        order=tuple(range(len(order))),
        root=index[plan.root],
        cell_heads=tuple(plan.cell_heads[n] for n in order) if plan.cell_heads else (),
    )
