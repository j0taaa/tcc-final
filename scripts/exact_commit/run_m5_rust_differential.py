#!/usr/bin/env python3
"""Run the configured M5 Python/Rust/oracle differential campaigns."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from mwpc_research.rust_differential import run_rust_differential_campaign

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _command_output(command: list[str]) -> str:
    return subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=REPOSITORY_ROOT / "configs/exact_commit/m5_rust_differential.toml",
    )
    parser.add_argument(
        "--campaign",
        action="append",
        help="run only a named campaign; repeat to select more than one",
    )
    arguments = parser.parse_args()

    config_path = arguments.config.resolve()
    config_bytes = config_path.read_bytes()
    config = tomllib.loads(config_bytes.decode("utf-8"))
    campaigns = config["campaigns"]
    selected_names = None if arguments.campaign is None else set(arguments.campaign)
    known_names = {str(campaign["name"]) for campaign in campaigns}
    if selected_names is not None and not selected_names <= known_names:
        parser.error(f"unknown campaigns: {sorted(selected_names - known_names)!r}")

    commit = _command_output(["git", "rev-parse", "HEAD"])
    common_metadata = {
        "git_commit": commit,
        "config_path": str(config_path.relative_to(REPOSITORY_ROOT)),
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "python_version": sys.version.split()[0],
        "rust_version": _command_output(["rustc", "--version"]),
        "generator_schema_version": "1",
        "binding_crate_version": "0.1.0",
        "support_policy": "explicit_epsilon_normalized_weighted_terminal_dag",
        "exactness_scope": "exact_on_represented_graph",
        "model_revision": "not_applicable",
        "tokenizer_revision": "not_applicable",
    }
    failure_root = REPOSITORY_ROOT / config["output"]["failure_directory"]
    summaries: list[dict[str, object]] = []
    failed_cases = 0
    for campaign in campaigns:
        campaign_name = str(campaign["name"])
        if selected_names is not None and campaign_name not in selected_names:
            continue
        summary = run_rust_differential_campaign(
            campaign_name=campaign_name,
            seed_start=int(campaign["seed_start"]),
            case_count=int(campaign["case_count"]),
            failure_directory=failure_root / campaign_name,
            metadata=common_metadata,
        )
        summary.write_json(REPOSITORY_ROOT / campaign["summary"])
        summaries.append(summary.to_dict())
        failed_cases += summary.failed_cases
    print(json.dumps(summaries, sort_keys=True))
    return 1 if failed_cases else 0


if __name__ == "__main__":
    raise SystemExit(main())
