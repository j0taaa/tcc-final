"""Evaluate only the unchanged predeclared2x precision gate; retain all pairs."""

import argparse
import json
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

from .public_controls import digest

WORK = Path(__file__).resolve().parent


def run(source, output):
    protocol = json.loads((WORK / "protocol-v25.json").read_text())
    metadata = json.loads((source / "metadata.json").read_text())
    summary = json.loads((source / "summary.json").read_text())
    assert not metadata["development_only"]
    assert metadata["protocol_sha256"] == digest(WORK / "protocol-v25.json")
    rows = [json.loads(line) for line in (source / "rows.jsonl").read_text().splitlines()]
    expected = {
        (r["key"], n, kind, eps, engine)
        for r in protocol["source_corpus"]["cases"]
        for n in protocol["mask_counts"]
        for kind in protocol["formats"]
        for eps in protocol["tolerances"]
        for engine in protocol["engines"]
    }
    assert len(rows) == len(expected) == 360
    assert {
        (r["source_case"], r["mask_count"], r["format"], r["epsilon"], r["engine"]) for r in rows
    } == expected
    pairs = []
    for row in rows:
        if row["epsilon"] != "1/10" or row["engine"] != "ordered_planar":
            continue
        independent = row["source_case"] in protocol["primary_unseen_documents"]
        result = dict(
            case=row["source_case"],
            mask_count=row["mask_count"],
            format=row["format"],
            primary_unseen=independent,
            status=row["status"],
            passes_2x=False,
        )
        if row["status"] == "CERTIFIED_ON_ADMITTED_FOREST":
            c = row["controls"]
            cheap = min(
                F(c["hellinger_upper"]),
                F(c["range_upper"]),
                F(c["mass_aware"]["upper"]),
                F(c["sampler_overlap"]["upper"]),
            )
            lower, upper = F(row["lower"]), F(row["upper"])
            assert 0 <= lower <= upper <= min(1, F(11, 10) * lower)
            assert lower <= cheap
            result.update(
                lower=str(lower),
                upper=str(upper),
                strongest_scalar_upper=str(cheap),
                cheap_to_candidate_ratio=float(cheap / upper)
                if upper
                else "infinite"
                if cheap
                else "both_zero",
                passes_2x=bool(cheap > 0 and cheap >= 2 * upper),
                full_first_audit_wall_cpu=row["full_first_audit_wall_cpu"],
            )
        pairs.append(result)
    primary = [r for r in pairs if r["primary_unseen"]]
    assert len(pairs) == 45 and len(primary) == 36
    wins = [r for r in primary if r["passes_2x"]]
    result = dict(
        status="INCOMPLETE_NOT_A_CONFIRMED_GATE"
        if summary["status"] != "COMPLETE_FUNCTIONAL_AUDIT"
        else "PASS_LIMITED_PRECISION_GATE"
        if wins
        else "FAIL_LIMITED_PRECISION_GATE",
        predicate=protocol["usefulness_gate"],
        primary_pairs=36,
        passed_primary_pairs=len(wins),
        all45pairs=pairs,
        all360statuses=dict(Counter(r["status"] for r in rows)),
        rows_sha256=digest(source / "rows.jsonl"),
        metadata_sha256=digest(source / "metadata.json"),
        protocol_sha256=digest(WORK / "protocol-v25.json"),
        claim_scope=(
            "Certificate precision only; no speed/semantic/iterative/priority/acceptance claim"
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in ["status", "primary_pairs", "passed_primary_pairs", "all360statuses"]
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)
