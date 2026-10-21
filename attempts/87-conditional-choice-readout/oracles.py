"""Exact CPU correctness audits; no model, decoder timing, or empirical claims.

Columns are token-equivalence partitions: columns[position][class] is a token ID.
The graph audit assumes oracle heads supported on the declared choice set.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from fractions import Fraction
from itertools import combinations_with_replacement, product
from math import comb, gcd, prod

Code = tuple[tuple[int, ...], ...]
Mass = int | Fraction


def validate(code: Code) -> tuple[int, int]:
    if not code or len(code[0]) < 2:
        raise ValueError("at least one position and two classes are required")
    k = len(code[0])
    if any(len(column) != k for column in code):
        raise ValueError("columns have different class counts")
    words = {tuple(column[c] for column in code) for c in range(k)}
    if len(words) != k:
        raise ValueError("classes must have distinct token sequences")
    return k, len(code)


def block_counts(code: Code) -> Counter[int]:
    """Sparse counts of class subsets, including the irrelevant universal block."""
    counts: Counter[int] = Counter()
    for column in code:
        groups: dict[int, int] = {}
        for c, token in enumerate(column):
            groups[token] = groups.get(token, 0) | (1 << c)
        counts.update(groups.values())
    return counts


def is_balanced(code: Code) -> bool:
    k, _ = validate(code)
    by_size: dict[int, list[int]] = {}
    for block, multiplicity in block_counts(code).items():
        size = block.bit_count()
        if size < k:
            by_size.setdefault(size, []).append(multiplicity)
    return all(
        len(counts) == comb(k, size) and min(counts) == max(counts)
        for size, counts in by_size.items()
    )


def scores(code: Code, masses: tuple[Mass, ...]) -> tuple[Mass, ...]:
    """Unnormalized exact product scores; a common normalization cancels."""
    k, _ = validate(code)
    if len(masses) != k or any(value < 0 for value in masses):
        raise ValueError("invalid posterior weights")
    if sum(masses) <= 0:
        raise ValueError("posterior has zero mass")
    # Compute independently by columns, rather than reusing block_counts.
    return tuple(
        prod(sum(masses[j] for j in range(k) if column[j] == column[c]) for column in code)
        for c in range(k)
    )


def maximizers(values: tuple[Mass, ...]) -> frozenset[int]:
    best = max(values)
    return frozenset(i for i, value in enumerate(values) if value == best)


def violating_pair(code: Code) -> tuple[int, int]:
    k, _ = validate(code)
    counts = block_counts(code)
    for block, count in sorted(counts.items()):
        for a in range(k):
            if not block & (1 << a):
                continue
            for b in range(k):
                if block & (1 << b):
                    continue
                swapped = block ^ (1 << a) ^ (1 << b)
                if counts[swapped] != count:
                    return a, b
    raise ValueError("balanced code has no violating pair")


def wrong_map_witness(
    code: Code, rng: random.Random, max_draws: int = 128
) -> tuple[tuple[Mass, ...], int] | None:
    """A bounded randomized construction; None means INCONCLUSIVE, not success.

    On the top-tie hyperplane the score difference is a nonzero homogeneous
    polynomial of degree L. Fixing the tied coordinates to T=2L+1 leaves a
    nonzero polynomial in the others. Schwartz--Zippel gives failure <=1/2
    per independent draw from {1,...,2L}. The final perturbation is rational.
    """
    k, length = validate(code)
    a, b = violating_pair(code)
    top = 2 * length + 1
    for draw in range(1, max_draws + 1):
        weights: list[Mass] = [rng.randint(1, 2 * length) for _ in range(k)]
        weights[a] = weights[b] = top
        before = scores(code, tuple(weights))
        difference = before[a] - before[b]
        if difference == 0:
            continue
        winner, loser = (a, b) if difference > 0 else (b, a)
        total = sum(weights)
        assert isinstance(total, int)
        epsilon = Fraction(1, 4 * length * (total + 1) ** length)
        weights[loser] += epsilon
        witness = tuple(weights)
        after = scores(code, witness)
        # Integer gap before perturbation >=1. Along this segment the absolute
        # derivative of the difference is <=2L(U+1)^(L-1), so its sign remains.
        assert maximizers(witness) == frozenset({loser})
        assert after[winner] > after[loser]
        assert loser not in maximizers(after)
        return witness, draw
    return None


def partitions(k: int) -> tuple[tuple[int, ...], ...]:
    """Restricted-growth strings enumerate each set partition exactly once."""
    result: list[tuple[int, ...]] = []

    def visit(prefix: tuple[int, ...], largest: int) -> None:
        if len(prefix) == k:
            result.append(prefix)
            return
        for token in range(largest + 2):
            visit((*prefix, token), max(largest, token))

    visit((0,), 0)
    return tuple(result)


def matrix_rank(matrix: list[list[int]], width: int) -> int:
    """Independent fraction-free Gaussian elimination over the rationals."""
    rows = [row[:] for row in matrix]
    rank = 0
    for column in range(width):
        pivot = next((r for r in range(rank, len(rows)) if rows[r][column]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for r in range(rank + 1, len(rows)):
            if not rows[r][column]:
                continue
            left, right = rows[rank][column], rows[r][column]
            rows[r] = [left * x - right * y for x, y in zip(rows[r], rows[rank], strict=True)]
            divisor = gcd(*rows[r])
            if divisor:
                rows[r] = [value // divisor for value in rows[r]]
        rank += 1
    return rank


def is_forest(edges: list[tuple[int, int]]) -> bool:
    parent = list(range(6))

    def find(vertex: int) -> int:
        while parent[vertex] != vertex:
            vertex = parent[vertex]
        return vertex

    for left, right in edges:
        a, b = find(left), find(right)
        if a == b:
            return False
        parent[a] = b
    return True


def audit_graphs() -> int:
    possible = [(left, 3 + right) for left in range(3) for right in range(3)]
    cases = 0
    for graph in range(1 << 9):
        edges = [edge for i, edge in enumerate(possible) if graph & (1 << i)]
        for queried in range(1 << 6):
            revealed = [i for i, (a, b) in enumerate(edges) if queried & ((1 << a) | (1 << b))]
            matrix = [[int(v in edge) for edge in edges] for v in range(6)]
            matrix += [[int(i == j) for j in range(len(edges))] for i in revealed]
            residual = [edge for i, edge in enumerate(edges) if i not in revealed]
            assert (matrix_rank(matrix, len(edges)) == len(edges)) == is_forest(residual)
            cases += 1
    return cases


def from_words(words: tuple[str, ...]) -> Code:
    if len({len(word) for word in words}) != 1:
        raise ValueError("explicitly padded equal-length words are required")
    return tuple(tuple(ord(word[i]) for word in words) for i in range(len(words[0])))


def audit_named() -> int:
    three = from_words(("00", "01", "10"))
    weights = (30, 40, 30)
    assert not is_balanced(three)
    assert maximizers(weights) == frozenset({1})
    assert scores(three, weights) == (4200, 2800, 1800)
    assert maximizers(scores(three, weights)) == frozenset({0})

    # All 15 five-class cuts, with the four-cut/three-cut K4 metric identity.
    cuts = [mask for mask in range(1, 31) if mask & 1]
    cuts = [mask for mask in cuts if mask not in {19, 21, 25}] + [17, 29, 27, 23]
    five = tuple(tuple((mask >> c) & 1 for c in range(5)) for mask in cuts)
    assert len(five) == 16 and not is_balanced(five)
    assert all(
        sum(column[a] != column[b] for column in five) == 8
        for a in range(5)
        for b in range(a + 1, 5)
    )
    weights = (249, 251, 200, 150, 150)
    assert maximizers(weights) == frozenset({1})
    assert maximizers(scores(five, weights)) == frozenset({0})

    # Raw heads include an outside-G word: inversion's supported-G premise fails.
    # P(000)=.30, P(111)=.29, P(110)=.41; allowed choices are only 000 and 111.
    true_allowed = (30, 29)
    raw_product = (30 * 30 * 71, 70 * 70 * 29)
    assert maximizers(true_allowed) == frozenset({0})
    assert maximizers(raw_product) == frozenset({1})
    return 3


def audit() -> dict[str, int | str]:
    totals: dict[str, int | str] = {
        "balanced_codes": 0,
        "balanced_posteriors": 0,
        "imbalanced_codes": 0,
        "witnesses": 0,
        "witness_draws": 0,
        "inconclusive_witnesses": 0,
        "indistinguishable_codes_skipped": 0,
    }
    rng = random.Random(0)

    def add(key: str, amount: int = 1) -> None:
        value = totals[key]
        assert isinstance(value, int)
        totals[key] = value + amount

    for k in range(2, 5):
        assert len(partitions(k)) == {2: 2, 3: 5, 4: 15}[k]
        for length in range(1, 4):
            for code in combinations_with_replacement(partitions(k), length):
                try:
                    validate(code)
                except ValueError:
                    add("indistinguishable_codes_skipped")
                    continue
                if is_balanced(code):
                    add("balanced_codes")
                    for weights in product(range(1, 5), repeat=k):
                        values = scores(code, weights)
                        assert maximizers(values) == maximizers(weights)
                        assert all(
                            (values[a] > values[b]) == (weights[a] > weights[b])
                            for a in range(k)
                            for b in range(k)
                        )
                        add("balanced_posteriors")
                else:
                    add("imbalanced_codes")
                    result = wrong_map_witness(code, rng)
                    if result is None:
                        add("inconclusive_witnesses")
                    else:
                        add("witnesses")
                        add("witness_draws", result[1])
    totals["bipartite_cases"] = audit_graphs()
    assert totals["bipartite_cases"] == 32768
    totals["named_cases"] = audit_named()
    totals["status"] = "INCONCLUSIVE" if totals["inconclusive_witnesses"] else "PASS"
    return totals


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(audit(), sort_keys=True, allow_nan=False))
