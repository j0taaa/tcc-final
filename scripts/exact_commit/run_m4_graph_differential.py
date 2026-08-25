#!/usr/bin/env python3
"""Run the configured M4 graph differential campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from mwpc_research.graph_differential import run_graph_differential_campaign

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=REPOSITORY_ROOT / "configs/exact_commit/m4_graph_differential.toml",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--failure-dir", type=Path)
    arguments = parser.parse_args()

    config_path = arguments.config.resolve()
    config_bytes = config_path.read_bytes()
    config = tomllib.loads(config_bytes.decode("utf-8"))
    campaign = config["campaign"]
    output = (
        REPOSITORY_ROOT / config["output"]["summary"]
        if arguments.output is None
        else arguments.output
    )
    failure_directory = (
        REPOSITORY_ROOT / config["output"]["failure_directory"]
        if arguments.failure_dir is None
        else arguments.failure_dir
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    summary = run_graph_differential_campaign(
        seed_start=int(campaign["seed_start"]),
        case_count=int(campaign["case_count"]),
        failure_directory=failure_directory,
        metadata={
            "git_commit": commit,
            "config_path": str(config_path.relative_to(REPOSITORY_ROOT)),
            "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
            "python_version": sys.version.split()[0],
            "generator_schema_version": "1",
            "support_policy": "explicit_weighted_terminal_epsilon_dag",
            "exactness_scope": "exact_on_represented_graph",
            "model_revision": "not_applicable",
            "tokenizer_revision": "not_applicable",
        },
    )
    summary.write_json(output)
    print(json.dumps(summary.to_dict(), sort_keys=True))
    return 1 if summary.failed_cases else 0


if __name__ == "__main__":
    raise SystemExit(main())
