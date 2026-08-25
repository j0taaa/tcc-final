#!/usr/bin/env python3
"""Replay the versioned T703 abstract-gap/finite-slot counterexamples."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mwpc_exact.finite_slot_counterexamples import (
    load_finite_slot_counterexamples,
    replay_finite_slot_counterexample,
    summarize_finite_slot_counterexamples,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = REPOSITORY_ROOT / "tests/exact_commit/fixtures/finite_slot_counterexamples.json"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "docs/evidence/t703-finite-slot-counterexamples.json"


def _repository_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPOSITORY_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()

    fixture_path = arguments.fixture.resolve()
    fixture_bytes = fixture_path.read_bytes()
    cases = load_finite_slot_counterexamples(fixture_path)
    reports = tuple(replay_finite_slot_counterexample(case) for case in cases)
    summary = {
        **summarize_finite_slot_counterexamples(reports),
        "fixture_path": _repository_path(fixture_path),
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
    }
    payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    output_path = arguments.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload, encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
