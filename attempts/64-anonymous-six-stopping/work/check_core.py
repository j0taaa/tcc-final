"""Independent seven-row Farkas audit via named tapes and all15 matchings."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from fractions import Fraction as F
from itertools import product
from pathlib import Path

from verify import encode, full_row


def check(rows: dict, weights: dict) -> tuple[dict, F]:
    coefficients: Counter = Counter()
    rhs = F(0)
    for tag, y in weights.items():
        row, b = rows[tag]
        rhs += y * b
        for variable, a in row.items():
            coefficients[variable] += y * a
    assert min([F(0), *coefficients.values()]) >= 0
    assert rhs < 0
    return {tag: a for tag, a in coefficients.items() if a}, rhs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("producer_rows", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    producer = json.loads(args.producer_rows.read_text())
    assert (
        producer["source_sha256"]
        == hashlib.sha256(Path(__file__).with_name("solve.py").read_bytes()).hexdigest()
    )
    rows = {"root": ({"c:0": F(1)}, F(1)), "distinct4": ({"c:0123": F(1)}, F(0))}
    for p in ("01", "012", "0123"):
        row = {"c:" + p: F(1), "c:" + p[:-1]: F(-1)}
        row.update({f"s:{p}:{j}": F(1) for j in set(p[1:])})
        rows["flow:" + p] = row, F(0)
    tapes = [
        (0, *tail)
        for tail in product(range(4), repeat=5)
        if tuple((0, *tail).count(j) for j in range(4)) == (1, 3, 1, 1)
    ]
    assert len(tapes) == 20
    end: dict = {j: Counter() for j in (2, 3)}
    for tape in tapes:
        assert full_row(tape) == {1: F(1)}
        for h in range(2, 7):
            prefix, seen = encode(tape[:h])
            for j in (2, 3):
                if j in seen:
                    end[j][f"s:{prefix}:{seen.index(j)}"] += F(1, len(tapes))
    for j, row in end.items():
        rows[f"end:1,3,1,1:{j}"] = dict(row), F(0)
    assert set(rows) == set(producer["rows"])
    for tag, (row, b) in rows.items():
        original = producer["rows"][tag]
        assert row == {v: F(a) for v, a in original["coefficients"].items()}
        assert b == F(original["rhs"])
    weights = {
        "root": F(-1),
        "flow:01": F(-1),
        "flow:012": F(-1),
        "flow:0123": F(-1),
        "distinct4": F(1),
        "end:1,3,1,1:2": F(5),
        "end:1,3,1,1:3": F(5),
    }
    coefficients, rhs = check(rows, weights)
    assert set(coefficients) <= set(producer["variables"])
    assert rhs == -1
    rejected = 0
    for tag, value in (("root", F(1)), ("end:1,3,1,1:2", F(0))):
        corrupted = weights | {tag: value}
        try:
            check(rows, corrupted)
        except AssertionError:
            rejected += 1
            continue
        raise AssertionError("Broken Farkas certificate accepted")
    result = {
        "status": "INFEASIBLE_EXACT",
        "scope": "Original fixed matching-law LP with distinct4 constraint",
        "independent_named_tails": len(tapes),
        "independent_matching_checks": len(tapes) * 15,
        "original_producer_rows_matched": len(rows),
        "original_variables": len(producer["variables"]),
        "farkas_nonzero_rows": {tag: str(y) for tag, y in weights.items()},
        "farkas_rhs": str(rhs),
        "minimum_variable_coefficient": "0",
        "positive_coefficients": {tag: str(a) for tag, a in coefficients.items()},
        "corrupted_certificates_rejected": rejected,
        "new_solves": 0,
        "new_neural_forwards": 0,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "positive_coefficients"}))


if __name__ == "__main__":
    main()
