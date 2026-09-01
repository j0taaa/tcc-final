#!/usr/bin/env python3
"""Build the three budgeted M13 result tables from pinned evidence."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from mwpc_research.article_results import build_article_results

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
    result = build_article_results(
        arguments.config,
        repository_root=REPOSITORY_ROOT,
        verify_existing=arguments.verify_existing,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
