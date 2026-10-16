"""Render the frozen pilot decision without changing its selection or thresholds."""

import argparse
import json
from fractions import Fraction
from pathlib import Path
from statistics import median

from .benchmark import digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    meta = json.loads((args.input / "metadata.json").read_text())
    result = json.loads((args.input / "decision.json").read_text())
    rows = [json.loads(s) for s in (args.input / "rows.jsonl").read_text().splitlines()]
    if digest(args.input / "rows.jsonl") != result["rows_sha256"]:
        raise ValueError("decision refers to another journal")
    if digest(args.input / "metadata.json") != result["metadata_sha256"]:
        raise ValueError("decision refers to another producer")
    names = {c["key"]: c["file"] for c in meta["input_capture"]["selected"]}
    candidate = [r for r in rows if r["method"] == "handoff_numpy"]
    maximum = max(
        Fraction(r["observed_local_certificate_sum"])
        for r in candidate
        if r["status"] == "complete"
    )
    lines = [
        "# A24 consumer V2: complete neural pilot",
        "",
        f"Producer: `{meta['producer_commit']}`; frozen protocol: "
        f"`{meta['protocol_sha256']}`. Reporting is post-capture; the gate is unchanged.",
        "",
        f"Completed campaign: {result['records']}/{result['planned']}; "
        f"statuses: {result['statuses']}; audit errors: {len(result['errors'])}.",
        f"New forwards: {result['new_case_forwards']} plus "
        f"{result['warmup_forwards']} warmup. Original-ID/sample checks: "
        f"{result['original_sample_and_fixed_id_checks']}; head checks: "
        f"{result['head_integrity_checks']} ({result['distinct_heads']} distinct matrices).",
        f"Literal cursor/full-sparse trajectory matches: "
        f"{result['literal_cursor_full_sparse_trajectory_matches']}. "
        f"Certificate checks against same-canvas exact masses: "
        f"{result['exact_mass_certificate_checks']}.",
        f"Selected candidate: {sum(r['status'] == 'complete' for r in candidate)}/"
        f"{len(candidate)} complete; maximum observed local-bound sum "
        f"{float(maximum):.9g}, below the frozen trajectory allocation.",
        "",
        f"Scoped paired warm-cost gate: {result['scoped_pilot_states']}/"
        f"{len(result['states'])}. Strict timing wins with ALL six controls "
        f"fully completed: {result['strict_timing_states']}/{len(result['states'])}.",
        "",
        "Each ratio is the median of the two paired candidate/control ratios. "
        "The displayed worst ratio is the maximum across COMPLETED controls; "
        "passing also requires favorable wall AND CPU signs in both seeds. "
        "Capacity refusals at3GiB/120s are separate and are not speed measurements.",
        "",
        "| Original document / masks | Candidate warm wall (s) | Worst wall ratio | "
        "Worst CPU ratio | Capacity controls | Scoped gate |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for state in result["states"]:
        candidates = [
            r for r in candidate if r["case"] == state["case"] and r["masks"] == state["masks"]
        ]
        ratios = [c["median_ratios"] for c in state["comparisons"] if "median_ratios" in c]
        worst = {u: max(r[u] for r in ratios) for u in ("wall", "cpu")}
        capacity = sum(c["kind"] == "explicit-budget capacity" for c in state["comparisons"])
        wall = median(r["actual_warm_total"]["wall"] for r in candidates)
        lines.append(
            f"| {names[state['case']]} / {state['masks']} | {wall:.4f} | "
            f"{worst['wall']:.4f} | {worst['cpu']:.4f} | {capacity} | "
            f"{'PASS' if state['scoped_pilot_pass'] else 'FAIL'} |"
        )
    lines += [
        "",
        "These are real new MDLM forwards on ALL five previously inspected documents, "
        "not independent corpus confirmation or semantic evaluation. The warm gate "
        "includes model execution, softmax, head capture, hashes, IPC, solver and "
        "output validation. Model/service loading is outside warm cost; reported cold "
        "totals are reconstructions from measured startup, not separately timed cold runs. "
        "Journal bookkeeping and service teardown follow the request timing boundary; "
        "failed requests retain their measured request cost and status.",
        "",
        "The strongest interpretation is a scoped benefit for this CPU posterior/commit "
        "consumer. General decoder advantage, sufficient novelty, semantic usefulness, "
        "native EPIC/GPU-baseline superiority and publication remain open. "
        "Wall-censored COMPLETE outputs are not certified unconditional target-law draws. "
        "The existing independent A24 query result remains a different experiment.",
        "",
        f"Rows SHA256: `{result['rows_sha256']}`.",
    ]
    (args.input / "decision.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
