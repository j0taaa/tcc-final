"""Independent complete first90 reanalysis; negative-only, all rows retained."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median

from .cost_audit import METHODS, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    work = Path(__file__).parent
    protocol = json.loads((work / "development-protocol-v9.json").read_text())
    rows = [json.loads(x) for x in (args.input / "rows.jsonl").read_text().splitlines()]
    cases = sorted({r["case"] for r in rows})
    decision = audit(rows, cases, protocol)
    if decision != json.loads((args.input / "decision.json").read_text()):
        raise ValueError("producer decision differs from reanalysis")
    if not decision["negative_gate_proved"]:
        raise ValueError("this report cannot promote a positive result")
    summary = dict(
        records=len(rows),
        cold_statuses=dict(Counter(r["cold"]["status"] for r in rows)),
        warm_statuses=dict(Counter(r["warm"]["status"] for r in rows)),
        correct_cold=sum(r["cold"].get("correctness", False) for r in rows),
        correct_warm=sum(r["warm"].get("correctness", False) for r in rows),
        states_rejected=len(decision["rejected_states"]),
        possible_states=len(decision["possible_states"]),
        new_model_forwards=0,
        goal_met=False,
        sha256={
            n: hashlib.sha256((args.input / n).read_bytes()).hexdigest()
            for n in ("metadata.json", "rows.jsonl", "setup.json", "decision.json")
        },
    )
    lines = [
        "# A51 V9 — complete negative first90 decision",
        "",
        "All90/90 records and180 correct cold/warm operations are preserved.",
        "The frozen necessary comparison rejects the ticket/scalar candidate inALL15 states.",
        "No remaining controls or independent neural campaign are triggered.",
        "This is negative evidence for this implementation/application, not a theorem",
        "that exact numerical sampling is useless or a scientific contribution by itself.",
        "",
        "The exact interval control is CLASSICAL, retains original IDs and the same",
        "model-confidence policy. Its speed is not claimed as a newly invented algorithm.",
        "Both consume resident original binary64 CUDA weights and return original",
        "words/confidence/commit masks on CUDA. ALL numeric work/correction is charged.",
        "Common compilation and globally cached JIT setup are separately recorded;",
        "decomposed first-query totals are not true cold-process measurements.",
        "Projected totals add OLD model clocks; no new forward was performed.",
        "",
        "No tests, local installations or other model workloads ran during timings;",
        "only lightweight status reads and remote primary-literature retrieval overlapped.",
        "",
        "| State | Ticket warm wall s | Interval warm wall s | "
        "Projected paired wall ratio | CPU ratio |",
        "|---|---:|---:|---:|---:|",
    ]
    floor_cpu = []
    for case in cases:
        selected = {m: [r for r in rows if r["case"] == case and r["method"] == m] for m in METHODS}
        a, b = (median(r["warm"]["timing"]["wall"] for r in selected[m]) for m in METHODS)
        d = decision["rejected_states"][case]["median_ratios"]
        label = case[:8] + " / " + case.rsplit("-", 1)[1]
        lines.append(f"|{label}|{a:.8g}|{b:.8g}|{d['wall']:.6g}|{d['cpu']:.6g}|")
        f = [
            r["old_model_softmax"]["cpu"] / r["warm"]["projected"]["cpu"]
            for r in selected["interval_exact"]
        ]
        floor_cpu.append(median(f))
    summary["states_where_zero_decoder_cpu_cannot_meet_primary_cpu_ratio"] = sum(
        x > protocol["primary_gate"]["cpu_ratio"] for x in floor_cpu
    )
    lines.extend(
        [
            "",
            "Ratios are candidate/control; smaller is better. All15 fail the original gate.",
            "No threshold, case, comparator or admission rule changed after measurements.",
            "Even a zero-decoder-CPU floor fails the20% projected CPU requirement in"
            f"{summary['states_where_zero_decoder_cpu_cannot_meet_primary_cpu_ratio']}"
            "/15 states under these OLD common model clocks.",
            "That arithmetic diagnostic changes neither the frozen gate nor its negative result.",
            "It does not rule out benefits under a different honestly preregistered operation.",
            "",
            "The useful original contribution/publication goal remains OPEN.",
        ]
    )
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
