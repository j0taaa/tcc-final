"""Independent named-tape matching, operation and rational LP dual audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import product
from math import factorial
from pathlib import Path


def encode(word: tuple[int, ...]) -> tuple[str, list[int]]:
    seen = []
    code = ""
    for j in word:
        if j not in seen:
            seen.append(j)
        code += str(seen.index(j))
    return code, seen


def matchings(positions: tuple[int, ...]) -> list[tuple[tuple[int, int], ...]]:
    if not positions:
        return [()]
    first, *rest = positions
    return [
        ((first, j), *pairs) for j in rest for pairs in matchings(tuple(v for v in rest if v != j))
    ]


ALL_MATCHINGS = matchings(tuple(range(6)))
assert len(ALL_MATCHINGS) == 15


def full_row(word: tuple[int, ...]) -> dict[int, F]:
    scores = [sum(word[i] == word[j] for i, j in pairs) for pairs in ALL_MATCHINGS]
    best = min(scores)
    row: Counter = Counter()
    for pairs, score in zip(ALL_MATCHINGS, scores, strict=True):
        if score == best:
            edge = next(edge for edge in pairs if 0 in edge)
            index = edge[1] if edge[0] == 0 else edge[0]
            row[word[index]] += 1
    total = sum(row.values())
    return {j: F(v, total) for j, v in row.items()}


def audit(cert: dict) -> dict:
    x = {tag: F(v) for tag, v in cert["primal"].items()}
    dual = {tag: F(v) for tag, v in cert["dual"].items()}
    tapes = [(0, *tail) for tail in product(range(6), repeat=5)]
    patterns = sorted(
        {encode(t[:h])[0] for t in tapes for h in range(1, 7)}, key=lambda s: (len(s), s)
    )
    expected_names = {"c:" + p for p in patterns if len(p) != 6}
    for p in patterns:
        for j in set(p[1:]):
            expected_names.add(f"s:{p}:{j}")
    assert set(x) == expected_names and min(x.values()) >= 0
    rows = {"root": ({"c:0": F(1)}, F(1))}
    for p in patterns:
        if len(p) > 1:
            row = {"c:" + p[:-1]: F(-1)}
            for tag in expected_names:
                if tag == "c:" + p or tag.startswith("s:" + p + ":"):
                    row[tag] = F(1)
            rows["flow:" + p] = row, F(0)
    rows["distinct4"] = {"c:0123": F(1)}, F(0)
    cumulative: dict = defaultdict(Counter)
    targets: dict = {}
    sizes: Counter = Counter()
    endpoint_rows: dict = defaultdict(Counter)
    costs: dict[str, F] = {}
    steps = 0
    distinct_words = 0
    nonfirst_checks = 0
    for tape in tapes:
        code, _ = encode(tape)
        n = tuple(tape.count(j) for j in range(6))
        target = full_row(tape)
        targets[n] = target
        sizes[n] += 1
        alive, work = F(1), F(1)
        output: Counter = Counter()
        for h in range(2, 7):
            work += alive
            prefix, seen = encode(tape[:h])
            reach = x["c:" + prefix[:-1]]
            assert alive == reach
            for j in set(prefix[1:]):
                probability = x[f"s:{prefix}:{j}"]
                if probability:
                    assert reach > 0
                    stop = alive * probability / reach
                    actual = seen[int(j)]
                    raw_index = next(i for i in range(1, h) if tape[i] == actual)
                    assert raw_index != 0 and tape[raw_index] == actual
                    nonfirst_checks += 1
                    output[actual] += stop
                if tuple(sorted(n[1:], reverse=True)) == n[1:]:
                    endpoint_rows[n, seen[int(j)]][f"s:{prefix}:{j}"] += 1
            alive = x.get("c:" + prefix, F(0))
            assert sum(output.values()) + alive == 1
            if h < 4:
                assert alive == 1
            if h == 4 and len(set(tape[:4])) == 4:
                assert alive == 0
            steps += 1
        assert alive == 0 and sum(output.values()) == 1
        if len(set(tape)) == 6:
            assert work == 4
            distinct_words += 1
        cumulative[n].update(output)
        if code in costs:
            assert costs[code] == work
        costs[code] = work
    for n, outputs in cumulative.items():
        for j in range(6):
            assert outputs[j] / sizes[n] == targets[n].get(j, F(0))
        if tuple(sorted(n[1:], reverse=True)) == n[1:]:
            compact = tuple(v for v in n if v)
            for j in range(len(compact)):
                row = {tag: F(v, sizes[n]) for tag, v in endpoint_rows[n, j].items()}
                tag = "end:" + ",".join(map(str, compact)) + f":{j}"
                rows[tag] = row, targets[n].get(j, F(0))
    assert set(dual) == set(rows)
    for row, b in rows.values():
        assert sum((a * x[tag] for tag, a in row.items()), F(0)) == b
    objective = dict.fromkeys(expected_names, F(0))
    for p in patterns:
        if len(p) < 6:
            k = len(set(p))
            probability = F(factorial(2), factorial(3 - k) * 3 ** (len(p) - 1)) if k <= 3 else F(0)
            objective["c:" + p] = probability
    reduced: Counter = Counter()
    for tag, (row, _) in rows.items():
        for variable, a in row.items():
            reduced[variable] += dual[tag] * a
    assert all(reduced[tag] <= objective[tag] for tag in x)
    primal_value = 1 + sum((objective[tag] * x[tag] for tag in x), F(0))
    bound = 1 + sum((dual[tag] * b for tag, (_, b) in rows.items()), F(0))
    assert primal_value == bound
    weighted = []
    laws = [
        [F(1, 3)] * 3,
        [F(1, 2), F(1, 3), F(1, 6)],
        [F(1, 2)] * 2,
        [F(9, 10), F(1, 20), F(1, 20)],
        [F(1)],
    ]
    for masses in laws:
        mean = F(0)
        for tape in product(range(len(masses)), repeat=6):
            probability = F(1)
            for j in tape:
                probability *= masses[j]
            mean += probability * costs[encode(tape)[0]]
        weighted.append({"p": list(map(str, masses)), "expected_calls": str(mean)})
    uniforms = {}
    for m in (2, 3, 4, 6, 128):
        mean = F(1)
        for p in patterns:
            if len(p) < 6:
                k = len(set(p))
                probability = (
                    F(factorial(m - 1), factorial(m - k) * m ** (len(p) - 1)) if k <= m else F(0)
                )
                mean += probability * x["c:" + p]
        uniforms[str(m)] = str(mean)
    assert F(uniforms["3"]) == primal_value == F(weighted[0]["expected_calls"])
    return {
        "status": "VERIFIED",
        "secondary_U3_cost": str(primal_value),
        "secondary_U3_dual_bound": str(bound),
        "named_tail_words_first0": len(tapes),
        "anonymous_prefixes": len(patterns),
        "variables": len(x),
        "rows": len(rows),
        "multiset_groups": len(sizes),
        "distinct_named_words": distinct_words,
        "operational_prefix_steps": steps,
        "nonfirst_checks": nonfirst_checks,
        "distinct_word_expected_calls": "4",
        "weighted_laws": weighted,
        "uniform_expected_calls": uniforms,
        "new_neural_forwards": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cert = json.loads(args.certificate.read_text())
    result = audit(cert)
    for kind, tag in (("primal", "c:0"), ("dual", "root")):
        damaged = json.loads(json.dumps(cert))
        damaged[kind][tag] = str(F(damaged[kind][tag]) + 1)
        try:
            audit(damaged)
        except AssertionError:
            continue
        raise AssertionError("Corrupted certificate accepted")
    result["corrupted_certificates_rejected"] = 2
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
