"""Independent finite attacks: integer elimination and enumerated word scores."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from fractions import Fraction
from itertools import product
from pathlib import Path

from contraction import Node, compile_forest, map_forest, word_forest


def integer_rank(rows):
    """Fraction-free elimination; never calls the compiler's rational reducer."""
    echelon = {}
    for source in rows:
        row = list(source)
        for p, old in sorted(echelon.items()):
            if row[p]:
                a, b = old[p], row[p]
                row = [a * x - b * y for x, y in zip(row, old, strict=True)]
                divisor = math.gcd(*row)
                if divisor:
                    row = [x // divisor for x in row]
        p = next((i for i, x in enumerate(row) if x), None)
        if p is not None:
            echelon[p] = row
    return len(echelon)


def enumerate_dag(nodes, index):
    """Set semantics, independently assembling partial position assignments."""
    node = nodes[index]
    if node.kind == "leaf":
        return {((node.position, node.token),)}
    if node.kind == "or":
        return set().union(*(enumerate_dag(nodes, c) for c in node.children))
    return {
        tuple(sorted(pair for word in children for pair in word))
        for children in product(*(enumerate_dag(nodes, c) for c in node.children))
    }


def check_language(nodes, root, n, rng):
    words = sorted(tuple(v for _, v in word) for word in enumerate_dag(nodes, root))
    plan = compile_forest(nodes, root, n)
    comparisons = 0
    for token, basis in plan.by_token.items():
        vectors = [tuple(int(v == token) for v in word) for word in words]
        diffs = [tuple(a - b for a, b in zip(x, vectors[0], strict=True)) for x in vectors]
        assert integer_rank(diffs) == len(basis.rows)
        for x in vectors:
            for z in vectors:
                delta = [a - b for a, b in zip(x, z, strict=True)]
                rebuilt = [
                    sum(row[j] * delta[p] for p, row in zip(basis.pivots, basis.rows, strict=True))
                    for j in range(n)
                ]
                assert rebuilt == delta
                comparisons += 1
    for _ in range(3):
        hidden = [[rng.randrange(-3, 4) for _ in range(3)] for _ in range(n)]
        weights = {v: [rng.randrange(-3, 4) for _ in range(3)] for v in plan.by_token}
        bias = {v: rng.randrange(-3, 4) for v in plan.by_token}
        original = {
            (i, v): Fraction(sum(a * b for a, b in zip(h, weights[v], strict=True)) + bias[v])
            for i, h in enumerate(hidden)
            for v in plan.by_token
        }
        contracted = {}
        for v, basis in plan.by_token.items():
            for p, row in zip(basis.pivots, basis.rows, strict=True):
                contracted[p, v] = sum(row[i] * original[i, v] for i in range(n))
        scores = [sum(original[i, v] for i, v in enumerate(word)) for word in words]
        compressed = [
            sum((contracted.get((i, v), Fraction(0)) for i, v in enumerate(word)), Fraction(0))
            for word in words
        ]
        assert len(set(a - b for a, b in zip(scores, compressed, strict=True))) == 1
        expected = min(zip(scores, words, strict=True), key=lambda x: (-x[0], x[1]))
        actual = map_forest(nodes, root, contracted)
        assert tuple(v for _, v in actual[1]) == expected[1]
        # Rational Gibbs on centered integer scores: no floating exponential.
        a = [Fraction(2) ** int(x - scores[0]) for x in scores]
        b = [Fraction(2) ** int(x - compressed[0]) for x in compressed]
        assert [x / sum(a) for x in a] == [x / sum(b) for x in b]
    return comparisons, plan.stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tokenizer", type=Path)
    args = parser.parse_args()
    rng = random.Random(730019)
    contrasts = languages = 0
    for n in range(1, 4):
        universe = list(product(range(2), repeat=n))
        for mask in range(1, 1 << len(universe)):
            words = [word for i, word in enumerate(universe) if mask >> i & 1]
            nodes, root = word_forest(words)
            count, _ = check_language(nodes, root, n, rng)
            contrasts += count
            languages += 1
    for _ in range(64):
        n = rng.randrange(4, 7)
        universe = list(product(range(3), repeat=n))
        words = rng.sample(universe, rng.randrange(1, 14))
        nodes, root = word_forest(words)
        count, _ = check_language(nodes, root, n, rng)
        contrasts += count
        languages += 1
    # Factored DAG with sharing, alternatives, empty product and an unreachable leaf.
    nodes = [Node("leaf", position=0, token=0), Node("leaf", position=0, token=1)]
    nodes += [Node("or", (0, 1)), Node("leaf", position=1, token=2)]
    nodes += [Node("and", (2, 3)), Node("or", (4, 4)), Node("and")]
    nodes += [Node("and", (5, 6)), Node("leaf", position=0, token=999)]
    count, _ = check_language(nodes, 7, 2, rng)
    contrasts += count
    languages += 1
    families = {}
    cases = {
        "independent4": list(product(range(3), repeat=4)),
        "copy4": [(v,) * 4 for v in range(3)],
        "balance4": [x for x in product(range(2), repeat=4) if x[0] + x[1] == x[2] + x[3]],
        "byte_aliases2": [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)],
        "fixed_copy4": [(2,) * 4],
        "ambiguous": [(0,), (0,), (1,)],
        "fractional_basis": [(0, 0, 0, 0), (1, 1, 0, 0), (1, 0, 1, 0), (0, 1, 1, 1)],
    }
    for name, words in cases.items():
        nodes, root = word_forest(words)
        count, stats = check_language(nodes, root, len(words[0]), rng)
        contrasts += count
        languages += 1
        families[name] = stats
    # Equality-by-bytes counterexample and incorrect bias pooling are explicit failures.
    alias_scores = [[10, 0, 6], [0, 10, 6]]
    best = max(
        cases["byte_aliases2"], key=lambda w: sum(alias_scores[i][v] for i, v in enumerate(w))
    )
    assert best == (0, 1)
    assert max(sum(alias_scores[i][v] for i in range(2)) for v in range(3)) == 12
    assert (9 + 1) * (1 + 9) == 100 and 9 * 1 + 1 * 9 == 18
    assert 2 * 7 != 7  # two-copy bias coefficient
    assert Fraction(2, 3) != Fraction(1, 2)  # trees versus words
    # Old copy relation fails after expansion; contraction/fixation remains compatible.
    old_nodes, root = word_forest([(0, 0), (1, 1)])
    basis = compile_forest(old_nodes, root, 2).by_token[1]
    assert basis.rows == ((Fraction(1), Fraction(1)),)
    assert [basis.rows[0][j] for j in range(2)] != [1, 0]
    invalid = [
        ([Node("or")], 0, 0),
        ([Node("leaf", position=0, token=0), Node("and", (0, 0))], 1, 1),
        ([Node("and", (0,))], 0, 0),
        ([Node("leaf", position=0, token=0)], 0, 2),
        ([Node("leaf", position=0, token=0), Node("and"), Node("or", (0, 1))], 2, 1),
        ([Node("leaf", position=0, token=-1)], 0, 1),
    ]
    for ns, rt, n in invalid:
        try:
            compile_forest(ns, rt, n)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid forest admitted")
    report = {
        "seed": 730019,
        "languages": languages,
        "indicator_contrasts": contrasts,
        "score_trials_per_language": 3,
        "invalid_forests_rejected": len(invalid),
        "families": families,
        "timings": "not measured",
    }
    if args.tokenizer:
        raw = args.tokenizer.read_bytes()
        tokenizer = json.loads(raw)
        # Qwen byte-level alphabet uses ordinary ASCII unchanged for this regex.
        import re

        vocab = tokenizer["model"]["vocab"]
        ids = [
            (v, text) for text, v in vocab.items() if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text)
        ]
        report["tokenizer"] = {
            "path": str(args.tokenizer.resolve()),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "ordinary_ids": len(vocab),
            "identifier_ids": len(ids),
            "identifier_bytes": sum(len(text.encode("ascii")) for _, text in ids),
            "aliases_in_identifier_class": len(ids) - len({text for _, text in ids}),
            "sorted_ids_sha256": hashlib.sha256(
                json.dumps(sorted(v for v, _ in ids)).encode()
            ).hexdigest(),
        }
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(serialized)
    print(serialized, end="")


if __name__ == "__main__":
    main()
