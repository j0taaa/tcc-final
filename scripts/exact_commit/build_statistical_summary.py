#!/usr/bin/env python3
"""Build a deterministic T1202 statistical summary from pinned raw JSONL."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from mwpc_research.statistical_artifacts import build_statistical_artifact

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="recompute expected bytes and reject missing or edited output",
    )
    arguments = parser.parse_args(argv)
    result = build_statistical_artifact(
        arguments.config,
        repository_root=REPOSITORY_ROOT,
        verify_existing=arguments.verify_existing,
    )
    print(
        json.dumps(
            {
                "output": result.output_path.relative_to(REPOSITORY_ROOT).as_posix(),
                "output_sha256": result.output_sha256,
                "source_sha256": result.source_sha256,
                "verified_existing": result.verified_existing,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
