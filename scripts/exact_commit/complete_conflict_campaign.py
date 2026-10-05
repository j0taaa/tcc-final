#!/usr/bin/env python3
"""Complete only missing independent DP jobs, preserving interrupted bytes/provenance."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.exact_commit import run_conflict_real as original

from mwpc_exact.budget_proof import budget_proof_data
from mwpc_exact.budgeted_commit import budgeted_commit_frontier
from mwpc_exact.experiments.metadata import collect_system_metadata

ROOT = Path(__file__).resolve().parents[2]


def valid_prefix(path):
    raw = path.read_bytes()
    prefix, *suffix = raw.split(b"\0", 1)
    if suffix and any(suffix[0]):
        raise ValueError("interrupted suffix contains nonzero bytes")
    rows = [json.loads(line) for line in prefix.splitlines()]
    if not prefix.endswith(b"\n"):
        raise ValueError("partial JSON record needs explicit separate recovery")
    return prefix, rows


def worker(source, directory):
    completed = {r["instance_id"] for r in valid_prefix(source / "resource_dp-r0.jsonl")[1]}
    get_cohort = original.cohort
    original.cohort = lambda config: [
        i for i in get_cohort(config) if i[0].instance_id not in completed
    ]
    original.worker(directory, "resource_dp", 0)


def run(source, directory):
    system = collect_system_metadata(ROOT)
    if system.git_dirty is not False:
        raise ValueError("commit completion protocol before execution")
    prefix, rows = valid_prefix(source / "resource_dp-r0.jsonl")
    config = original.read(source / "config.json")
    expected = {i.instance_id for i, _ in original.cohort(config)}
    ids = [r["instance_id"] for r in rows]
    if len(ids) != len(set(ids)) or not set(ids) <= expected:
        raise ValueError("duplicate/foreign completed DP records")
    if any(r["status"] != "completed" for r in rows):
        raise ValueError("do not replace previously unresolved outcomes")
    directory.mkdir(parents=True, exist_ok=False)
    stage = directory / "continuation"
    stage.mkdir()
    original.write(stage / "config.json", config)
    metadata = {
        **original.read(source / "metadata.json"),
        "git_commit": system.git_commit,
        "hardware_software": original.system_data(system),
        "completion_scope": (
            "Only previously unexecuted independent resource-DP jobs; no rescoring/reselection"
        ),
        "interrupted_source": str(source.relative_to(ROOT)),
        "interrupted_rows_sha256": original.sha(source / "resource_dp-r0.jsonl"),
        "retained_completed_rows": len(rows),
        "retained_producer_commits": sorted({r["git_commit"] for r in rows}),
        "missing_input_ids": sorted(expected - set(ids)),
    }
    original.write(stage / "metadata.json", metadata)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.exact_commit.complete_conflict_campaign",
            "--source",
            str(source),
            "--output",
            str(stage),
            "--worker",
        ],
        check=True,
    )
    for path in source.glob("*.json"):
        if path.name not in ("manifest.json", "continuation-metadata.json"):
            shutil.copyfile(path, directory / path.name)
    for path in source.glob("*-r*.jsonl"):
        if path.name != "resource_dp-r0.jsonl":
            shutil.copyfile(path, directory / path.name)
    for path in source.glob("*-r*.jsonl"):
        for row in valid_prefix(path)[1]:
            if row.get("proof"):
                target = directory / row["proof"]
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(source / row["proof"], target)
    for path in stage.glob("proofs/*"):
        target = directory / "proofs" / path.name
        if target.exists():
            raise ValueError("continuation would overwrite a completed proof")
        shutil.copyfile(path, target)
    (directory / "resource_dp-r0.jsonl").write_bytes(
        prefix + (stage / "resource_dp-r0.jsonl").read_bytes()
    )
    regenerated = []
    inputs = {i.instance_id: i.selection_input for i, _ in original.cohort(config)}
    all_rows = [
        json.loads(line) for line in (directory / "resource_dp-r0.jsonl").read_text().splitlines()
    ]
    for row in all_rows:
        target = directory / row["proof"]
        if target.stat().st_size == 0:
            state = inputs[row["instance_id"]]
            results = budgeted_commit_frontier(state, row["max_budget"])
            proof = budget_proof_data(state, results)
            actual = [
                {
                    "budget": r.budget,
                    "status": r.status.value,
                    "objective_value": original.fraction_data(r.objective_value),
                }
                for r in results
            ]
            if actual != row["batches"]:
                raise ValueError("reconstructed missing proof disagrees with saved outcome")
            target.unlink()  # only the copied empty file; source bytes stay untouched
            original.write(target, proof)
            regenerated.append(row["proof"])
    metadata["regenerated_empty_proofs"] = regenerated
    metadata["recovery_timing_scope"] = "Proof regeneration is not a new timing measurement"
    original.write(directory / "continuation-metadata.json", metadata)
    shutil.rmtree(stage)  # copied new rows, proofs and provenance; not the interrupted source
    original.write(
        directory / "manifest.json",
        {
            str(p.relative_to(directory)): original.sha(p)
            for p in sorted(directory.rglob("*"))
            if p.is_file()
        },
    )
    original.verify(directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    (worker if args.worker else run)(args.source.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
