#!/usr/bin/env python3
"""Run the predeclared recursive paired study without modifying old artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from itertools import product
from pathlib import Path
from time import monotonic

from mwpc_exact.experiments import (
    ExperimentKind,
    capture_run_metadata,
    finalize_run_metadata,
    load_experiment_config,
    save_resolved_config,
)
from mwpc_exact.experiments.metadata import canonical_json_sha256
from mwpc_research.branching_study import (
    build_branching_instance,
    evaluate_branching_instance,
    summarize_branching_rows,
)
from mwpc_research.recursive_tasks import FAMILIES, recursive_grammar

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "configs/experiments/m16_branching_v1.toml"


def source_hashes() -> dict[str, str]:
    """Record the actual dirty-tree implementations in addition to Git metadata."""

    paths = [
        *ROOT.glob("src/**/*.py"),
        *ROOT.glob("crates/*/src/**/*.rs"),
        *ROOT.glob("crates/*/Cargo.*"),
        *ROOT.glob("scripts/exact_commit/*.py"),
        ROOT / "pyproject.toml",
        ROOT / "rust-toolchain.toml",
    ]
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-directory", type=Path)
    arguments = parser.parse_args()
    config = load_experiment_config(arguments.config)
    parameters = config.parameters
    expected_parameters = {
        "families",
        "seed_count",
        "support_widths",
        "weight_modes",
        "masked_positions",
        "maximum_oracle_paths",
        "selectors",
        "raw_output_root",
    }
    if set(parameters) != expected_parameters:
        raise ValueError("unknown or missing branching study parameters")
    if (
        config.question is not ExperimentKind.HEURISTIC_GAP
        or config.device != "cpu"
        or parameters["seed_count"] != 100
        or parameters["maximum_oracle_paths"] != 4096
        or tuple(parameters["families"]) != FAMILIES
        or tuple(parameters["support_widths"]) != (2, 4)
        or tuple(parameters["weight_modes"]) != ("unit", "integer_utility")
        or parameters["masked_positions"] != 4
        or tuple(parameters["selectors"])
        != ("python_exact", "rust_exact", "greedy_exact_feasibility")
        or len(config.seeds) != 1
        or config.repetitions != 1
    ):
        raise ValueError("configuration does not match the frozen branching protocol")
    run_directory = arguments.run_directory or (
        ROOT / str(parameters["raw_output_root"]) / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    )
    run_directory.mkdir(parents=True, exist_ok=False)
    save_resolved_config(config, run_directory)
    grammars = {family: recursive_grammar(family) for family in FAMILIES}
    sources = source_hashes()
    metadata = capture_run_metadata(
        config,
        run_id=run_directory.name,
        repository_root=ROOT,
        grammar_sha256=[canonical_json_sha256(grammar.to_dict()) for grammar in grammars.values()],
        require_rust=True,
        additional={
            "actual_source_sha256": sources,
            "analysis_units": "family/seed, repeated widths and objectives",
            "origin": "synthetic_feasibility_conditioned",
        },
    )
    with (run_directory / "initial-metadata.json").open("x") as output:
        json.dump(metadata, output, indent=2, allow_nan=False)
    started = monotonic()
    rows = []
    expected_rows = 12 * int(parameters["seed_count"])
    with (run_directory / "rows.jsonl").open("x") as output:
        for index, (family, seed, width, mode) in enumerate(
            product(
                FAMILIES,
                range(config.seeds[0], config.seeds[0] + int(parameters["seed_count"])),
                parameters["support_widths"],
                parameters["weight_modes"],
            )
        ):
            if monotonic() - started >= config.run_timeout_seconds:
                break
            instance = build_branching_instance(family, seed, width, mode, grammar=grammars[family])
            row = evaluate_branching_instance(
                instance,
                timeout_seconds=config.solver_timeout_seconds,
                maximum_paths=int(parameters["maximum_oracle_paths"]),
                order_offset=index,
            )
            row["run_metadata"] = metadata
            json.dump(row, output, allow_nan=False, separators=(",", ":"))
            output.write("\n")
            output.flush()
            rows.append(row)
            if row["failures"]:
                print(
                    json.dumps(
                        {
                            "correctness_gate_failed": row["instance_sha256"],
                            "failures": row["failures"],
                        }
                    ),
                    flush=True,
                )
                break
            if (index + 1) % 100 == 0:
                print(
                    json.dumps({"completed_rows": index + 1, "expected_rows": expected_rows}),
                    flush=True,
                )
    summary = summarize_branching_rows(rows)
    summary.update(
        expected_rows=expected_rows,
        complete=len(rows) == expected_rows,
        source_changed_during_run=source_hashes() != sources,
        raw_sha256=hashlib.sha256((run_directory / "rows.jsonl").read_bytes()).hexdigest(),
    )
    counts = {
        method: dict(Counter(row["selectors"][method]["status"] for row in rows))
        for method in parameters["selectors"]
    }
    if rows:
        summary["run_metadata"] = finalize_run_metadata(
            metadata,
            solver_status_counts=counts,
            publication_mode=config.publication_mode,
        )
    with (run_directory / "summary.json").open("x") as output:
        json.dump(summary, output, indent=2, allow_nan=False)
    print(
        json.dumps(
            {
                "run_directory": str(run_directory),
                "rows": len(rows),
                "correctness_failure_rows": summary["correctness_failure_rows"],
                "complete": summary["complete"],
            }
        ),
        flush=True,
    )
    return int(
        not summary["complete"]
        or summary["correctness_failure_rows"] > 0
        or summary["width_monotonicity_violations"] > 0
        or summary["source_changed_during_run"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
