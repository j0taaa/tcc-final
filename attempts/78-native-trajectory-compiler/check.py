"""Small exact boundary checks for A78; no learner/decoder benchmark or model use."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from fractions import Fraction as F
from itertools import combinations, product
from math import comb, prod
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MASK = -1
TOKEN_BYTES = {17: b"a", 23: b"c", 31: b"b", 47: b"d", 59: b"#"}


def tv(p: list[F], q: list[F]) -> F:
    assert sum(p) == sum(q) == 1
    return sum((abs(a - b) for a, b in zip(p, q, strict=True)), F(0)) / 2


def hidden_context() -> dict:
    contexts = list(product((MASK, 0, 1), repeat=3))
    unseen = (0, 1, 0)

    def altered(c: tuple[int, ...]) -> F:
        return F(3, 4) if c == unseen else F(1, 2)

    queried = [c for c in contexts if c != unseen]
    assert all(altered(c) == F(1, 2) for c in queried)
    relevant = []
    for i in range(3):
        changed = list(unseen)
        changed[i] = MASK
        assert altered(tuple(changed)) != altered(unseen)
        relevant.append(i)
    return {"queried_contexts": len(queried), "unseen": unseen, "relevant": relevant}


def conditioning() -> dict:
    epsilon = F(1, 1024)
    p = [epsilon * (1 - epsilon), epsilon**2, 1 - epsilon]
    q = [p[1], p[0], p[2]]
    delta = tv(p, q)
    conditional_tv = tv([a / epsilon for a in p[:2]], [a / epsilon for a in q[:2]])
    assert delta < epsilon
    assert conditional_tv == delta / epsilon > F(99, 100)
    return {"mass_G": str(epsilon), "TV": str(delta), "conditional_TV": str(conditional_tv)}


def one_parent_codes() -> dict:
    rows = []
    for m in range(1, 6):
        bits = (m - 1).bit_length()
        queries = [tuple([s] * m) for s in (MASK, 0, 1)]
        queries += [
            tuple(s if (j >> bit) & 1 else MASK for j in range(m))
            for bit in range(bits)
            for s in (0, 1)
        ]
        assert len(queries) == 3 + 2 * bits
        cases = constants = 0
        for parent in range(m):
            for table in product((F(1, 4), F(1, 2), F(3, 4)), repeat=3):
                response = [table[c[parent] + 1] for c in queries]
                learned_table = tuple(response[:3])
                assert learned_table == table
                if len(set(learned_table)) == 1:
                    constants += 1  # A constant head has no identifiable parent.
                else:
                    probe = next(s for s in (0, 1) if learned_table[s + 1] != response[0])
                    decoded = sum(
                        (response[3 + 2 * b + probe] != response[0]) << b for b in range(bits)
                    )
                    assert decoded == parent
                cases += 1
        rows.append({"m": m, "cases": cases, "constant_cases": constants, "queries": len(queries)})
    return {"rows": rows, "cases": sum(r["cases"] for r in rows)}


def recognizes(word: bytes) -> bool:
    """Independent byte LL(1) recognition of S -> a S b | c S d | #."""
    pos = 0

    def s() -> bool:
        nonlocal pos
        if pos == len(word):
            return False
        symbol = word[pos]
        pos += 1
        if symbol == ord("#"):
            return True
        if symbol not in (ord("a"), ord("c")) or not s():
            return False
        close = ord("b") if symbol == ord("a") else ord("d")
        if pos == len(word) or word[pos] != close:
            return False
        pos += 1
        return True

    return s() and pos == len(word)


def render(x: tuple[int, ...], y: tuple[int, ...]) -> bytes:
    ids = (*(17 if b == 0 else 23 for b in x), 59, *(31 if b == 0 else 47 for b in reversed(y)))
    return b"".join(TOKEN_BYTES[i] for i in ids)


def native(parent: tuple[int, ...], x: tuple[int, ...], y: tuple[int, ...], reverse: bool) -> F:
    m = len(parent)
    canvas = [MASK] * (2 * m)
    values = x + y
    order = tuple(range(m, 2 * m)) + tuple(range(m)) if reverse else tuple(range(2 * m))
    mass = F(1)
    for i in order:
        p1 = F(1, 2)
        if i >= m and canvas[parent[i - m]] != MASK:
            p1 = F(3, 4) if canvas[parent[i - m]] == 1 else F(1, 4)
        mass *= p1 if values[i] else 1 - p1
        canvas[i] = values[i]
    return mass


def cycles(parent: tuple[int, ...]) -> list[int]:
    done: set[int] = set()
    lengths = []
    for start in range(len(parent)):
        positions: dict[int, int] = {}
        node = start
        while node not in done and node not in positions:
            positions[node] = len(positions)
            node = parent[node]
        if node in positions:
            lengths.append(len(positions) - positions[node])
        done.update(positions)
    return lengths


def elimination_width(parent: tuple[int, ...]) -> int:
    graph = {i: set() for i in range(len(parent))}
    for i, j in enumerate(parent):
        if i != j:
            graph[i].add(j)
            graph[j].add(i)
    width = 0
    while graph:
        node = min(graph, key=lambda v: (len(graph[v]), v))
        neighbors = graph.pop(node)
        width = max(width, len(neighbors))
        for a, b in combinations(sorted(neighbors), 2):
            graph[a].add(b)
            graph[b].add(a)
        for v in neighbors:
            graph[v].remove(node)
    return width


def grammar_family() -> dict:
    rows = []
    for m in range(1, 5):
        words = list(product((0, 1), repeat=m))
        pairs = [(x, y, recognizes(render(x, y))) for x in words for y in words]
        assert all(valid == (x == y) for x, y, valid in pairs)
        largest_width = maps = nonuniform = enumerated = 0
        for parent in product(range(m), repeat=m):
            total = valid_mass = F(0)
            valid_weights = []
            for x, y, valid in pairs:
                mass = native(parent, x, y, reverse=False)
                assert native(parent, x, y, reverse=True) == F(1, 4**m)
                total += mass
                enumerated += 1
                if valid:
                    matches = sum(x[j] == x[i] for i, j in enumerate(parent))
                    assert mass == F(3**matches, 8**m)
                    valid_weights.append(mass)
                    valid_mass += mass
            assert total == 1
            formula = F(1, 2**m) * prod(1 + F(1, 2**c) for c in cycles(parent))
            assert valid_mass == formula
            posterior = [p / valid_mass for p in valid_weights]
            distance = tv(posterior, [F(1, 2**m)] * (2**m))
            assert (distance == 0) == (parent == tuple(range(m)))
            nonuniform += distance > 0
            width = elimination_width(parent)
            assert width <= 2
            largest_width = max(largest_width, width)
            maps += 1
        rows.append(
            {
                "m": m,
                "maps": maps,
                "native_words": enumerated,
                "byte_recognitions": len(pairs),
                "nonuniform_conditionals": nonuniform,
                "largest_executed_width": largest_width,
            }
        )
    return {"rows": rows, "maps": sum(r["maps"] for r in rows)}


def single_cycle() -> dict:
    rows = []
    for m in (1, 2, 4, 8, 16, 32, 64):
        partition = 1 + F(1, 2**m)
        p = [F(2 * comb(m, d) * 3 ** (m - d), 4**m) / partition for d in range(0, m + 1, 2)]
        uniform = [F(2 * comb(m, d), 2**m) for d in range(0, m + 1, 2)]
        raw_valid = partition / 2**m
        assert sum(p) == sum(uniform) == 1
        rows.append({"m": m, "Z": str(raw_valid), "TV_root_projected": str(tv(p, uniform))})
    return {"rows": rows}


def parse_multiplicity() -> dict:
    word_law = [F(1, 2), F(1, 2)]
    unique_extension = [p * 1 for p in word_law]
    ambiguous = [word_law[0], word_law[1] * 2]
    parse_law = [p / sum(ambiguous) for p in ambiguous]
    assert unique_extension == word_law
    assert parse_law == [F(1, 3), F(2, 3)]
    assert tv(word_law, parse_law) == F(1, 6)
    return {
        "word_law": list(map(str, word_law)),
        "parse_law": list(map(str, parse_law)),
        "TV": str(tv(word_law, parse_law)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    relative = str(HERE.relative_to(ROOT))
    frozen = [f"{relative}/{name}" for name in ("check.py", "sources.json")]
    assert not subprocess.check_output(["git", "status", "--porcelain", "--", *frozen], cwd=ROOT)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    metadata = {
        "kind": "producer",
        "commit": commit,
        "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sources_sha256": hashlib.sha256((HERE / "sources.json").read_bytes()).hexdigest(),
        "model_forwards": 0,
        "GPU": False,
        "timings": False,
        "RNG_bits": 0,
    }
    checks = (
        hidden_context,
        conditioning,
        one_parent_codes,
        grammar_family,
        single_cycle,
        parse_multiplicity,
    )
    with args.output.open("x", encoding="utf-8") as output:

        def emit(record: dict) -> None:
            output.write(json.dumps(record, sort_keys=True) + "\n")
            output.flush()

        emit(metadata)
        try:
            for check in checks:
                emit({"kind": "check", "name": check.__name__, "status": "PASS", **check()})
        except BaseException as exc:
            emit({"kind": "failure", "type": type(exc).__name__, "error": str(exc)})
            raise
        emit(
            {
                "kind": "summary",
                "status": "PASS",
                "checks": len(checks),
                "scientific_gate": "NO_USABLE_SMALL_DEPENDENCY_CONTRACT",
            }
        )
    print(f"PASS: {len(checks)} exact boundary checks; no neural or timing claim.")


if __name__ == "__main__":
    main()
