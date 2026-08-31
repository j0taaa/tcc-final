#!/usr/bin/env python3
"""Build deterministic T1203 tables and figures from pinned Q1--Q5 rows."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from mwpc_research.final_artifacts import build_final_artifacts

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="recompute and compare every tracked output byte-for-byte",
    )
    arguments = parser.parse_args(argv)
    result = build_final_artifacts(
        arguments.config,
        repository_root=REPOSITORY_ROOT,
        verify_existing=arguments.verify_existing,
    )
    print(
        json.dumps(
            {
                "artifact_id": result.artifact_id,
                "outputs": dict(result.output_sha256),
                "sources": dict(result.source_sha256),
                "verified_existing": result.verified_existing,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
