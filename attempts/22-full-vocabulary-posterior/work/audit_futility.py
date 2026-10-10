"""Negative-only logical audit of unchanged necessary conditions on partial rows.

This was added AFTER timing started, never used to declare a victory. A fixed
unfavorable sign, a candidate refusal, or a strict majority of ratios >0.8
cannot be repaired by measuring remaining repetitions. Missing rows are NOT
fabricated. A complete control row precludes the all-refusal capacity branch.
"""

import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path


def audit(folder):
    meta = json.loads((folder / "metadata.json").read_text())
    proto = meta["protocol"]
    path = folder / "rows.jsonl"
    raw = (
        path.read_bytes()
        if path.exists()
        else gzip.decompress((folder / "rows.jsonl.gz").read_bytes())
    )
    rows = [json.loads(s) for s in raw.splitlines()]
    by_key = {(r["case"], r["mask_count"], r["method"], r["repeat"]): r for r in rows}
    assert len(rows) == len(by_key)
    repeats = proto["repetitions"]
    cases = []
    for doc, size in itertools.product(meta["capture"]["selected"], proto["mask_counts"]):
        entry = dict(case=doc["key"], mask_count=size, candidates={})
        for name in proto["candidates"]:
            reasons = []
            for rep in range(repeats):
                own = by_key.get((doc["key"], size, name, rep))
                if own is None:
                    continue
                if own["status"] in ("resource_refusal", "zero_valid_mass"):
                    reasons.append(
                        dict(repeat=rep, reason="candidate_not_complete", status=own["status"])
                    )
                elif own["status"] == "complete":
                    for ctrl in proto["exact_controls"]:
                        other = by_key.get((doc["key"], size, ctrl, rep))
                        if other is None or other["status"] != "complete":
                            continue
                        bad = [
                            u
                            for u in ("wall", "cpu")
                            if own["prepared_total"][u] >= other["prepared_total"][u]
                        ]
                        if bad:
                            reasons.append(
                                dict(
                                    repeat=rep,
                                    comparator=ctrl,
                                    reason="required_sign_failed",
                                    units=bad,
                                )
                            )
            for ctrl in proto["exact_controls"]:
                for unit in ("wall", "cpu"):
                    bad_pairs = []
                    for rep in range(repeats):
                        own = by_key.get((doc["key"], size, name, rep))
                        other = by_key.get((doc["key"], size, ctrl, rep))
                        if own and other and own["status"] == other["status"] == "complete":
                            ratio = own["prepared_total"][unit] / other["prepared_total"][unit]
                            if ratio > 0.8:
                                bad_pairs.append(dict(repeat=rep, ratio=ratio))
                    if len(bad_pairs) > repeats // 2:
                        reasons.append(
                            dict(
                                comparator=ctrl,
                                unit=unit,
                                reason="median_cannot_reach_frozen_threshold",
                                pairs=bad_pairs,
                            )
                        )
            entry["candidates"][name] = dict(irreversibly_rejected=bool(reasons), reasons=reasons)
        cases.append(entry)
    return dict(
        scope="Negative-only logical futility; remaining timings not run; no victory claim.",
        rows=len(rows),
        expected_rows=len(cases) * len(proto["methods"]) * repeats,
        producer_commit=meta["producer_commit"],
        rows_sha256=hashlib.sha256(raw).hexdigest(),
        cases=cases,
        all_candidates_rejected=all(
            c["irreversibly_rejected"] for e in cases for c in e["candidates"].values()
        ),
        proof=(
            "Success requires the candidate complete in every repetition. "
            "A control already complete cannot become all-refused. If all control rows complete, "
            "every paired sign must be favorable and the median in BOTH units <=0.8. "
            "Mixed control statuses satisfy neither branch. A strict majority of fixed "
            "ratios >0.8 forces median >0.8 regardless of remaining values. "
            "Each recorded violation cannot be repaired by later measurements."
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.input)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("rows", "expected_rows", "all_candidates_rejected")}))


if __name__ == "__main__":
    main()
