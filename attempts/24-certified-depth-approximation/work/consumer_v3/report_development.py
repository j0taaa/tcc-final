"""Generate the complete first-stage negative decision from immutable rows."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median

from .development_audit import FIRST_METHODS, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    work = Path(__file__).resolve().parents[1]
    protocol = json.loads((work / "consumer-v4-development-protocol.json").read_text())
    rows = [json.loads(line) for line in (args.input / "rows.jsonl").read_text().splitlines()]
    cases = sorted({r["case"] for r in rows})
    decision = audit(rows, cases, protocol)
    if decision != json.loads((args.input / "decision.json").read_text()):
        raise ValueError("producer decision differs from independent reanalysis")
    if not decision["negative_gate_proved"]:
        raise ValueError("this negative-only report cannot declare a positive result")
    summary = dict(
        record_count=len(rows),
        cold_statuses=dict(Counter(r["cold"]["status"] for r in rows)),
        warm_statuses=dict(Counter(r["warm"]["status"] for r in rows)),
        correct_cold=sum(bool(r["cold"].get("correctness_gate")) for r in rows),
        correct_warm=sum(bool(r["warm"].get("correctness_gate")) for r in rows),
        exact_common_ranking_checks=sum(r["warm"].get("exact_common_ranking", False) for r in rows),
        literal_cpu_cache_matches=sum(r.get("cache_literal_match", False) for r in rows),
        source_files={
            name: hashlib.sha256((args.input / name).read_bytes()).hexdigest()
            for name in ("metadata.json", "rows.jsonl", "decision.json")
        },
        new_model_forwards=0,
        all_candidate_states_rejected=True,
        positive_timing_claim=False,
        user_scientific_goal_met=False,
    )
    lines = [
        "# A24 consumer V4 — negative operational gate",
        "",
        f"All{len(rows)}/315 first-stage records are present. "
        f"Cold/warm correct:{summary['correct_cold']}/{summary['correct_warm']}.",
        "The frozen necessary comparisons reject BOTH candidates in ALL15 states.",
        "The other450 records are not executed: they cannot reverse a failed mandatory comparison.",
        "No positive result or independent neural capture follows from this stage.",
        "",
        "Input:OLD full-V heads, now under JSON EOT PAD*. Source0c75b91, Torch2.13/CUDA13.",
        "Methods reuse compilation and fresh numeric work. "
        "GPU controls avoid CPU integer summaries.",
        "All outputs/commit masks are on CUDA; exact oracle work is outside every timer.",
        "Projected totals add the OLD recorded model/softmax clock; no new forward was performed.",
        "Only lightweight status reads/remote literature retrieval overlapped; "
        "no local tests, model work or installations ran during the timings.",
        "",
        "| Method | Median warm wall s | Median warm CPU s | Max observed confidence error |",
        "|---|---:|---:|---:|",
    ]
    for method in FIRST_METHODS:
        selected = [r for r in rows if r["method"] == method]
        wall = median(r["warm"]["measured"]["wall"] for r in selected)
        cpu = median(r["warm"]["measured"]["cpu"] for r in selected)
        error = max(r["warm"]["max_absolute_confidence_error"] for r in selected)
        lines.append(f"|{method}|{wall:.9g}|{cpu:.9g}|{error:.9g}|")
    lines.extend(
        [
            "",
            "Across-state medians above are descriptive, not paired speedup gates.",
            "The decision.json contains EACH state and its completed rejection witnesses.",
            "The sparse/quotient/layered GPU algorithms are classical controls, "
            "not our new theory.",
            "A24's earlier limited CPU query result remains historical "
            "under its original comparators; "
            "it does not establish an advantage against these stronger implementations.",
            "The numeric/correction contract of the fast backend "
            "is a separate possible research direction.",
            "Its originality and a useful independent complete application "
            "remain to be established.",
            "",
        ]
    )
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (args.output / "report.md").write_text("\n".join(lines))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
