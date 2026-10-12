"""Evaluate only the unchanged predeclared2x precision gate; retain all pairs."""

import argparse
import json
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

from .ideal_controls import controls as ideal_control_bounds
from .public_controls import digest

WORK = Path(__file__).resolve().parent


def run(source, output, development_known_root=False):
    protocol_path = WORK / ("protocol-v26.json" if development_known_root else "protocol-v25.json")
    protocol = json.loads(protocol_path.read_text())
    metadata = json.loads((source / "metadata.json").read_text())
    summary = json.loads((source / "summary.json").read_text())
    assert metadata["development_only"] == development_known_root
    assert metadata["protocol_sha256"] == digest(protocol_path)
    if development_known_root:
        assert metadata["known_root_query"] and summary["known_root_query"]
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
    slots_by_case = {x["key"]: len(x["tokens"]) for x in metadata["source_origin"]["selected"]}
    pairs = []
    for row in rows:
        if row["epsilon"] != "1/10" or row["engine"] != "ordered_planar":
            continue
        independent = row["source_case"] in protocol["primary_unseen_documents"]
        result = dict(
            case=row["source_case"],
            mask_count=row["mask_count"],
            format=row["format"],
            primary_unseen=independent and not development_known_root,
            status=row["status"],
            passes_2x=False,
        )
        if development_known_root:
            result["was_unseen_in_v25"] = independent
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
            # Every successful core reports the same admitted forest node count.
            assert row["nodes"] > 0
            slots = slots_by_case[row["source_case"]]
            ideal = ideal_control_bounds(c, slots, row["nodes"])
            ideal_lower = ideal["ideal_upper_lower_bound"]
            result.update(
                ideal_controls=ideal,
                robust_against_ideal_control_rounding=bool(
                    ideal_lower > 0 and ideal_lower >= 2 * upper
                ),
            )
        pairs.append(result)
    primary = [r for r in pairs if r["primary_unseen"]]
    assert len(pairs) == 45 and len(primary) == (0 if development_known_root else 36)
    wins = [r for r in (pairs if development_known_root else primary) if r["passes_2x"]]
    robust = [r for r in wins if r.get("robust_against_ideal_control_rounding")]
    result = dict(
        status="INCOMPLETE_NOT_A_CONFIRMED_GATE"
        if summary["status"] != "COMPLETE_FUNCTIONAL_AUDIT"
        else "DEVELOPMENT_ONLY_PRECISION_REPLAY"
        if development_known_root
        else "PASS_LIMITED_PRECISION_GATE"
        if wins
        else "FAIL_LIMITED_PRECISION_GATE",
        predicate=protocol["usefulness_gate"],
        primary_pairs=len(primary),
        passed_primary_pairs=0 if development_known_root else len(wins),
        robust_primary_pairs=0 if development_known_root else len(robust),
        all45pairs=pairs,
        all360statuses=dict(Counter(r["status"] for r in rows)),
        rows_sha256=digest(source / "rows.jsonl"),
        metadata_sha256=digest(source / "metadata.json"),
        protocol_sha256=digest(protocol_path),
        claim_scope=(
            "Certificate precision only; no speed/semantic/iterative/priority/acceptance claim"
        ),
    )
    if development_known_root:
        result.update(
            development_pairs=45,
            passed_development_pairs=len(wins),
            robust_development_pairs=len(robust),
            new_forwards=0,
            independent_confirmation=False,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(
        json.dumps({k: v for k, v in result.items() if k != "all45pairs"}),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--development-known-root", action="store_true")
    args = parser.parse_args()
    run(args.source, args.output, args.development_known_root)
