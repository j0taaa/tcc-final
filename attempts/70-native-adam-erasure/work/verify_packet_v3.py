"""AFTER-data static provenance/count audit; no numerical kernel rerun."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import struct
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fbits(x: float) -> int:
    return struct.unpack("<I", struct.pack("<f", x))[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    here = Path(__file__).resolve().parent
    packet = root / "docs/artifacts/raw/a70_native_erasure_v3_bounds"
    summary = json.loads((packet / "summary.json").read_text())
    assert summary["status"] == "PASS"
    for name, sha in summary["artifacts"].items():
        assert digest(packet / name) == sha
    producer = summary["source"]["commit"]
    for name, sha in summary["source"]["files"].items():
        original = subprocess.check_output(["git", "show", f"{producer}:{name}"], cwd=root)
        assert hashlib.sha256(original).hexdigest() == sha == digest(root / name)
    assert (here / "native_v1.c").read_bytes() == re.sub(
        rb"\ba70_v3_", b"", (here / "native_v3.c").read_bytes()
    )
    previous = root / "docs/artifacts/raw/a70_native_erasure_v1_initial"
    assert (previous / "schedule.f32").read_bytes() == (packet / "schedule.f32").read_bytes()
    assert (previous / "primitives.json").read_bytes() == (packet / "primitives.json").read_bytes()
    rows = [json.loads(line) for line in (packet / "cases.jsonl").read_text().splitlines()]
    expected = itertools.product(
        (-1, -0.01, 0.01, 1),
        (1, 1024),
        (-0.1, 0.001, 0.1),
        (-0.2, 0, 0.0001, 0.2),
        (0, 1, 15, 128, 512, 4096, 32768, 65536),
    )
    by_gap: dict[str, dict[str, int]] = {}
    for index, (row, case) in enumerate(zip(rows, expected, strict=True)):
        w, s, g0, g, h = case
        assert row["case"] == index and row["status"] == "COMPLETE"
        assert [row[name] for name in ("w0", "s", "g0", "g", "h")] == [
            fbits(w),
            s,
            fbits(g0),
            fbits(g),
            h,
        ]
        work = row["work"]
        assert 0 <= work["head"] <= min(512, h)
        assert work["zero_moment_steps"] <= h
        assert work["control_absorption_moment_steps"] == work["native_zero_steps"] == h
        record = by_gap.setdefault(
            str(h),
            dict(
                rows=0,
                frozen=0,
                erased=0,
                head_steps=0,
                moment_steps=0,
                weight_steps=0,
                control_moment_steps=0,
            ),
        )
        for name, amount in (
            ("rows", 1),
            ("frozen", int(work["frozen"])),
            ("erased", int(work["erased"])),
            ("head_steps", work["head"]),
            ("moment_steps", work["zero_moment_steps"]),
            ("weight_steps", work["zero_weight_steps"]),
            ("control_moment_steps", h),
        ):
            record[name] += amount
    assert len(rows) == 768
    assert sum(x["erased"] for x in by_gap.values()) == summary["counts"]["erased"] == 128
    old_rows = [
        json.loads(line)
        for line in (root / "docs/artifacts/raw/a70_native_erasure_v2_frozen/cases.jsonl")
        .read_text()
        .splitlines()
    ]
    for new, old in zip(rows, old_rows, strict=True):
        normalized = dict(
            new,
            work={key: value for key, value in new["work"].items() if key != "bound_unavailable"},
        )
        assert normalized == old
    regressions = json.loads((packet / "admission-regressions.json").read_text())
    assert len(regressions["cases"]) == summary["admission_regressions"] == 8
    assert sum(row["work"]["bound_unavailable"] for row in regressions["cases"]) == 6
    assert regressions["context_refusals"] == 4
    receipt = json.loads((root / "docs/evidence/a70-v3-bounds-exit.json").read_text())
    assert receipt["direct_exit_code"] == 0 and receipt["producer_commit"] == producer
    assert digest(root / receipt["log"]) == receipt["log_sha256"]
    result = dict(
        kind="AFTER-data static provenance/complete-grid/iteration-count audit ONLY",
        verifier_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        numerical_producer_commit=producer,
        all_768_predeclared_rows=True,
        original_768_rows_unchanged=True,
        adverse_admission_cases=8,
        unavailable_bound_fallbacks=6,
        frozen_source_hashes_match=True,
        c_namespace_reversal_byte_identical=True,
        previous_schedule_and_primitive_packet_identical=True,
        per_gap=by_gap,
        counts_are_full_latency=False,
        numerical_kernel_rerun=False,
        independent_dataset_or_model=False,
        goal="OPEN",
    )
    assert not args.output.exists()
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
