"""Predeclared finite family, analytical median and raw/trimmed size receipt.

Functional capacity diagnostic only; no external data, timings or benefit gate.
Every declared size is retained, including any exception/refusal.
"""

import json
import sys
from fractions import Fraction

from .rotated_index_v5 import RotatedIndex


def main():
    reports = []
    for length in (1, 2, 4, 8, 16):
        try:
            byte_of = {0: b"1.", 1: b"1", 2: b"2", 3: b"e1"}
            digit = {1: Fraction(1, 2), 2: Fraction(1, 2)}
            rows = [{0: Fraction(1)}] + [digit] * length + [{3: Fraction(1)}] + [digit] * length
            index = RotatedIndex(rows, byte_of)
            # Equal-sized exponent groups, then equal-probability significands.
            expected = ("1" + "2" * length, int("11" + "2" * (length - 1)))
            observed = index.quantile(Fraction(1, 2))
            assert observed == expected
            assert index.mass == 1
            assert index.cdf(expected) == Fraction(1, 2)
            report = {
                "block_digits": length,
                "distinct_values": 2 ** (2 * length),
                "source_states": len(index.source.edges),
                "source_edges": sum(map(len, index.source.edges)),
                "source_byte_bound": index.byte_bound,
                "raw_states": index.raw_size[0],
                "raw_edges": index.raw_size[1],
                "trimmed_states": len(index.edges),
                "trimmed_edges": sum(map(len, index.edges)),
                "median": observed,
                "mass": str(index.mass),
                "status": "PASS",
            }
        except Exception as error:
            report = {"block_digits": length, "status": "ERROR", "error": repr(error)}
        reports.append(report)
        print(json.dumps(report), flush=True)
    if any(r["status"] != "PASS" for r in reports):
        sys.exit(1)


if __name__ == "__main__":
    main()
