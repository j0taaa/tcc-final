#!/usr/bin/env python3
"""Run configured finite-lattice/Python/Rust/oracle differential campaigns."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tomllib
from pathlib import Path

from mwpc_exact.finite_differential import (
    FINITE_LATTICE_GENERATOR_SCHEMA_VERSION,
    finite_grammar_family_sha256,
    run_finite_lattice_campaign,
)

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
        default=(
            REPOSITORY_ROOT
            / "configs/exact_commit/m6_finite_lattice_differential.toml"
        ),
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

    common_metadata = {
        "git_commit": _command_output(["git", "rev-parse", "HEAD"]),
        "config_path": str(config_path.relative_to(REPOSITORY_ROOT)),
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "python_version": sys.version.split()[0],
        "rust_version": _command_output(["rustc", "--version"]),
        "platform": platform.platform(),
        "machine": platform.machine() or "unknown",
        "processor": platform.processor() or "unknown",
        "generator_schema_version": str(FINITE_LATTICE_GENERATOR_SCHEMA_VERSION),
        "binding_crate_version": "0.1.0",
        "grammar_family_sha256": finite_grammar_family_sha256(),
        "support_policy": "explicit_per_position_token_rows",
        "exactness_scope": "exact_on_support",
        "finite_slot_policy": "one_ordinary_token_per_physical_slot_no_eos_pad",
        "model_revision": "not_applicable_synthetic_correctness_campaign",
        "tokenizer_revision": "synthetic_compositional_byte_v1",
        "token_byte_alphabet": "raw_bytes_0x61_0x62",
        "weight_policy": "nonnegative_integer_proposal_weights",
    }
    failure_root = REPOSITORY_ROOT / config["output"]["failure_directory"]
    summaries: list[dict[str, object]] = []
    failed_cases = 0
    for campaign in campaigns:
        campaign_name = str(campaign["name"])
        if selected_names is not None and campaign_name not in selected_names:
            continue
        summary = run_finite_lattice_campaign(
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
