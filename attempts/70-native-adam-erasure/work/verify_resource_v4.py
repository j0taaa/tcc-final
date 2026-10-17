"""Post-capture, stdlib-only static audit; never imports Torch or reruns a model."""

import hashlib
import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "docs/artifacts/raw/a70_nncp_resource_v4"


def read(name):
    return json.loads((PACKET / name).read_text())


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def audit():
    exit_receipt = read("exit.json")
    check(exit_receipt["child_returncode"] == 0, "Actual child failed")
    check(
        hashlib.sha256((PACKET / "console.log").read_bytes()).hexdigest()
        == exit_receipt["console_sha256"],
        "Console hash",
    )
    manifest = read("run/manifest.json")
    producer = manifest["producer_commit"]
    check(producer == exit_receipt["producer_commit"], "Producer mismatch")
    source_checks = 0
    for path, expected in manifest["sources"].items():
        original = subprocess.check_output(["git", "show", producer + ":" + path], cwd=ROOT)
        check(hashlib.sha256(original).hexdigest() == expected, "Producer source " + path)
        check(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, "Source drift")
        source_checks += 1
    check(manifest["torch"] == "2.8.0+cpu", "Torch version")
    check(manifest["torch_git"] == "a1cb3cc05d46d198467bebbb6e8fba50a325d4e7", "Torch Git")
    check(manifest["threads"] == 8 and manifest["interop"] == 1, "Thread count")
    check(len(manifest["screen_cpu_affinity"]) == 8, "Affinity")
    check(manifest["snapshot_clock_values"] == [1.0], "Common snapshot clock")
    methods = ["native_single", "native_foreach", "ideal_single", "ideal_foreach"]
    frames = ["empty", "full160"]
    expected_order = [("setup", "empty", methods[0], -1)]
    expected_order += [("warmup", f, m, -1) for f in frames for m in methods]
    for repetition in range(7):
        order = methods[repetition % 4 :] + methods[: repetition % 4]
        expected_order += [("measured", f, m, repetition) for f in frames for m in order]
    rows = [json.loads(line) for line in (PACKET / "run/records.jsonl").read_text().splitlines()]
    check(len(rows) == 65, "Complete prescribed 65-cycle capture required")
    states = {}
    observations = {}
    for index, (row, expected) in enumerate(zip(rows, expected_order, strict=True), 1):
        actual = tuple(row[key] for key in ("phase", "frame", "method", "repetition"))
        check(actual == expected and row["status"] == "COMPLETE", "Order/status")
        check(row["wall_ns"] > 0 and row["cpu_ns"] > 0, "Timer")
        check(
            row["cumulative_calls"]
            == dict.fromkeys(("forwards", "backwards", "optimizer_steps"), index),
            "Call count",
        )
        if row["phase"] != "setup":
            frame = row["frame"]
            observations.setdefault(frame, row["observation"])
            check(observations[frame] == row["observation"], "Paired observation changed")
            key = (frame, row["method"])
            states.setdefault(key, row["state_digest"])
            check(states[key] == row["state_digest"], "Paired same-method native state changed")
    summary = read("run/summary.json")
    check(summary["status"] == "COMPLETE", "Summary status")
    check(summary["calls"] == rows[-1]["cumulative_calls"] == read("run/calls.json"), "End calls")
    check(summary["measured_records"] == 56 and summary["warmups"] == 8, "Counts")
    check(summary["observations"] == observations, "Observation summary")
    conclusions = {}
    comparisons = 0
    for frame in frames:
        cells = {
            (r["method"], r["repetition"]): r
            for r in rows
            if r["phase"] == "measured" and r["frame"] == frame
        }
        passing = []
        expected_comparisons = []
        for ideal in methods[2:]:
            succeeds = True
            for native in methods[:2]:
                comparison = {"ideal": ideal, "native": native, "metrics": {}}
                for metric in ("wall_ns", "cpu_ns"):
                    values = [cells[ideal, i][metric] / cells[native, i][metric] for i in range(7)]
                    median = statistics.median(values)
                    signs = all(value < 1 for value in values)
                    comparison["metrics"][metric] = {
                        "paired_ratios": values,
                        "median_ratio": median,
                        "every_repetition_favorable": signs,
                    }
                    succeeds &= median <= 0.8 and signs
                    comparisons += 1
                expected_comparisons.append(comparison)
            if succeeds:
                passing.append(ideal)
        check(
            summary["gates"][frame]
            == {"passing_ideal_methods": passing, "comparisons": expected_comparisons},
            "Gate not independently reproduced",
        )
        conclusions[frame] = passing
        check(
            summary["native_single_foreach_state_equal_on_frames"][frame]
            == (states[frame, methods[0]] == states[frame, methods[1]]),
            "Native law observation",
        )
    return {
        "status": "PASS",
        "producer_commit": producer,
        "source_hash_checks": source_checks,
        "ordered_real_cycles": 65,
        "measured_records": 56,
        "paired_metric_comparisons": comparisons,
        "passing_ideal_methods": conclusions,
        "scope": (
            "Static integrity/paired digests/gate arithmetic; "
            "no independent tensor recomputation, proof or timing rerun"
        ),
        "packet_files": {
            str(path.relative_to(PACKET)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(PACKET.rglob("*"))
            if path.is_file()
        },
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
