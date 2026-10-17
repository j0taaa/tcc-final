"""Export seven exact rows from the original frozen producer; no new solve."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from solve import build


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    selected = {
        "root",
        "flow:01",
        "flow:012",
        "flow:0123",
        "distinct4",
        "end:1,3,1,1:2",
        "end:1,3,1,1:3",
    }
    problem = build()
    rows = {
        tag: {"coefficients": {problem["names"][j]: str(a) for j, a in row.items()}, "rhs": str(b)}
        for tag, row, b in problem["rows"]
        if tag in selected
    }
    assert set(rows) == selected
    result = {
        "source_sha256": hashlib.sha256(
            Path(__file__).with_name("solve.py").read_bytes()
        ).hexdigest(),
        "variables": problem["names"],
        "rows": rows,
        "new_solves": 0,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "exported_original_rows": len(rows),
                "variables": len(problem["names"]),
                "new_solves": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
