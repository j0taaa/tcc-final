"""Finite decomposable AND/OR affine compiler. No Torch or model dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Node:
    kind: str
    children: tuple[int, ...] = ()
    position: int = -1
    token: int = -1


@dataclass(frozen=True)
class Basis:
    pivots: tuple[int, ...]
    rows: tuple[tuple[Fraction, ...], ...]


@dataclass
class Plan:
    by_token: dict[int, Basis]
    groups: dict[Basis, list[int]]
    stats: dict[str, int]


def reduced_basis(vectors: tuple[tuple[int, ...], ...], n: int) -> Basis:
    """Incremental rational row reduction, with bounded number of retained rows."""
    rows: dict[int, list[Fraction]] = {}
    for vector in vectors:
        row = list(map(Fraction, vector))
        for pivot in sorted(rows):
            factor = row[pivot]
            if factor:
                row = [a - factor * b for a, b in zip(row, rows[pivot], strict=True)]
        pivot = next((j for j in range(n) if row[j]), None)
        if pivot is None:
            continue
        scale = row[pivot]
        row = [x / scale for x in row]
        for other, old in rows.items():
            factor = old[pivot]
            if factor:
                rows[other] = [a - factor * b for a, b in zip(old, row, strict=True)]
        rows[pivot] = row
    pivots = tuple(sorted(rows))
    return Basis(pivots, tuple(tuple(rows[p]) for p in pivots))


def compile_forest(nodes: list[Node], root: int, n: int) -> Plan:
    """Reject malformed forests; ignore nodes unreachable from the root.

    Leaves carry absolute positions. AND assembles assignments by position,
    so disjoint scopes may interleave; the output order is always 0,...,n-1.
    ORs are productive and smooth. Empty AND is the empty assignment.
    """
    if n < 0 or not 0 <= root < len(nodes):
        raise ValueError("invalid root or length")
    reachable = set()
    pending = [root]
    while pending:
        index = pending.pop()
        if index in reachable:
            continue
        reachable.add(index)
        node = nodes[index]
        if any(child < 0 or child >= index for child in node.children):
            raise ValueError("children must precede parents (acyclic DAG)")
        pending.extend(node.children)
    scopes: dict[int, int] = {}
    anchors: dict[int, dict[int, int]] = {}
    generators: dict[int, set[tuple[int, int]]] = {}
    all_tokens = set()
    for index in sorted(reachable):
        node = nodes[index]
        if node.kind == "leaf":
            if node.children or not 0 <= node.position < n or node.token < 0:
                raise ValueError("invalid leaf")
            scopes[index] = 1 << node.position
            anchors[index] = {node.token: scopes[index]}
            all_tokens.add(node.token)
        elif node.kind == "and":
            scope = 0
            anchor: dict[int, int] = {}
            for child in node.children:
                if scope & scopes[child]:
                    raise ValueError("AND scopes overlap")
                scope |= scopes[child]
                for token, mask in anchors[child].items():
                    anchor[token] = anchor.get(token, 0) | mask
            scopes[index], anchors[index] = scope, anchor
        elif node.kind == "or":
            if not node.children:
                raise ValueError("unproductive OR")
            first = node.children[0]
            scope, anchor = scopes[first], anchors[first]
            if any(scopes[child] != scope for child in node.children):
                raise ValueError("OR scopes differ")
            scopes[index], anchors[index] = scope, anchor
            for child in node.children[1:]:
                alternative = anchors[child]
                for token in anchor.keys() | alternative.keys():
                    left, right = alternative.get(token, 0), anchor.get(token, 0)
                    plus, minus = left & ~right, right & ~left
                    if not plus and not minus:
                        continue
                    # Canonicalize sign before grouping equal generator sets.
                    least = (plus | minus) & -(plus | minus)
                    if minus & least:
                        plus, minus = minus, plus
                    generators.setdefault(token, set()).add((plus, minus))
        else:
            raise ValueError("unknown node kind")
    if scopes[root] != (1 << n) - 1:
        raise ValueError("root does not cover every slot")
    cache: dict[tuple[tuple[int, int], ...], Basis] = {}
    by_token = {}
    groups: dict[Basis, list[int]] = {}
    for token in sorted(all_tokens):
        key = tuple(sorted(generators.get(token, ())))
        if key not in cache:
            vectors = tuple(
                tuple(((plus >> j) & 1) - ((minus >> j) & 1) for j in range(n))
                for plus, minus in key
            )
            cache[key] = reduced_basis(vectors, n)
        basis = cache[key]
        by_token[token] = basis
        groups.setdefault(basis, []).append(token)
    entries = [x for basis in groups for row in basis.rows for x in row]
    return Plan(
        by_token,
        groups,
        {
            "nodes": len(reachable),
            "edges": sum(len(nodes[i].children) for i in reachable),
            "ids": len(all_tokens),
            "groups": len(groups),
            "sum_q": sum(len(b.pivots) for b in by_token.values()),
            "group_nnz": sum(bool(x) for x in entries),
            "stored_rational_bits": sum(
                1 + abs(x.numerator).bit_length() + x.denominator.bit_length() for x in entries
            ),
            "max_coefficient_bits": max(
                (max(abs(x.numerator).bit_length(), x.denominator.bit_length()) for x in entries),
                default=0,
            ),
        },
    )


def word_forest(words: list[tuple[int, ...]]) -> tuple[list[Node], int]:
    """Explicit finite grammar; only small oracle inputs, not a CFG parser."""
    nodes: list[Node] = []
    alternatives = []
    for word in words:
        children = []
        for position, token in enumerate(word):
            children.append(len(nodes))
            nodes.append(Node("leaf", position=position, token=token))
        alternatives.append(len(nodes))
        nodes.append(Node("and", tuple(children)))
    nodes.append(Node("or", tuple(alternatives)))
    return nodes, len(nodes) - 1


def map_forest(
    nodes: list[Node], root: int, unaries: dict[tuple[int, int], Fraction]
) -> tuple[Fraction, tuple[tuple[int, int], ...]]:
    """Max-plus DAG evaluation, lexicographic original-ID tie breaking."""
    values: dict[int, tuple[Fraction, tuple[tuple[int, int], ...]]] = {}

    def visit(index: int):
        if index in values:
            return values[index]
        node = nodes[index]
        if node.kind == "leaf":
            value = unaries.get((node.position, node.token), Fraction(0))
            result = value, ((node.position, node.token),)
        elif node.kind == "and":
            children = [visit(child) for child in node.children]
            result = (
                sum((score for score, _ in children), Fraction(0)),
                tuple(sorted(pair for _, word in children for pair in word)),
            )
        else:
            result = min((visit(child) for child in node.children), key=lambda x: (-x[0], x[1]))
        values[index] = result
        return result

    return visit(root)
