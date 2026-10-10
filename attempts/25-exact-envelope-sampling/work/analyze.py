"""Separate preregistered first-sample/batch gates; audit exact envelope mass."""

import argparse
import gzip
import itertools
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from statistics import median


def paired(candidate, control, repeats, field, status):
    if len(candidate) != repeats or len(control) != repeats:
        return dict(useful=False, reason="missing repetitions")
    if any(r.get(status) != "complete" or field not in r for r in candidate):
        return dict(useful=False, reason="candidate operation not complete")
    if all(r.get(status) == "resource_refusal" and "operation" in r for r in control):
        return dict(useful=True, reason="localized internal capacity for the SAME operation")
    if any(r.get(status) != "complete" or field not in r for r in control):
        return dict(useful=False, reason="mixed, erroneous or unobserved control")
    by_repeat = {r["repeat"]: r for r in candidate}
    ratios = {
        u: [by_repeat[r["repeat"]][field][u] / r[field][u] for r in control]
        for u in ("wall", "cpu")
    }
    favorable = all(x < 1 for values in ratios.values() for x in values)
    return dict(
        useful=favorable and all(median(v) <= 0.8 for v in ratios.values()),
        favorable_every_repeat=favorable,
        paired_ratios=ratios,
        ratio_medians={u: median(v) for u, v in ratios.items()},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partial", action="store_true")
    parser.add_argument("--selected", choices=("handoff", "closed"))
    args = parser.parse_args()
    path = args.input / "rows.jsonl"
    raw = (
        path.read_text()
        if path.exists()
        else gzip.decompress((args.input / "rows.jsonl.gz").read_bytes()).decode()
    )
    rows = [json.loads(line) for line in raw.splitlines()]
    metadata = json.loads((args.input / "metadata.json").read_text())
    protocol = metadata["protocol"]
    independent = metadata["stage"] == "independent"
    if independent and args.selected is None:
        raise ValueError("independent phase needs development-frozen selection")
    repeats = protocol["independent_repetitions"] if independent else protocol["repetitions"]
    allowed = set(
        itertools.product(
            [d["key"] for d in metadata["capture"]["selected"]],
            protocol["mask_counts"],
            protocol["methods"],
            range(repeats),
        )
    )
    keys = [(r["case"], r["mask_count"], r["method"], r["repeat"]) for r in rows]
    if len(set(keys)) != len(keys) or not set(keys) <= allowed:
        raise ValueError("duplicate or undeclared record")
    complete = set(keys) == allowed
    if not complete and not args.partial:
        raise ValueError("incomplete campaign; partial audit cannot adopt")
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row["case"], row["mask_count"]][row["method"]].append(row)
    benefits = {n: [] for n in protocol["candidates"]}
    batch_benefits = {n: [] for n in protocol["candidates"]}
    cases, checks = [], 0
    for (case, masks), methods in sorted(grouped.items()):
        exact = [
            r
            for name in protocol["frozen_exact_methods"]
            for r in methods.get(name, [])
            if "valid_mass" in r
        ]
        masses = {Fraction(r["valid_mass"]) for r in exact}
        if len(masses) > 1:
            raise RuntimeError("full exact controls disagree on original mass")
        mass = next(iter(masses)) if masses else None
        item = dict(
            case=case,
            mask_count=masks,
            full_mass=None if mass is None else str(mass),
            methods={},
            decisions={},
        )
        for name, records in methods.items():
            result = dict(
                statuses=dict(Counter(r["status"] for r in records)),
                first_statuses=dict(Counter(r.get("first_status") for r in records)),
            )
            for field in (
                "first_total",
                "batch_total",
                "cold_first_total",
                "cold_batch_total",
                "startup",
                "conversion",
                "preparation",
            ):
                values = [r[field] for r in records if field in r]
                if values:
                    result[field] = {u: median(v[u] for v in values) for u in ("wall", "cpu")}
            certified = [r for r in records if "certificate" in r]
            for row in certified:
                den = int(row["product_denominator"])
                lower, upper = (
                    Fraction(int(row["lower"]), den),
                    Fraction(int(row["upper_tail"]), den),
                )
                delta = (
                    None
                    if row["certificate"]["delta"] is None
                    else Fraction(row["certificate"]["delta"])
                )
                if lower + upper != Fraction(int(row["envelope_total"]), den):
                    raise RuntimeError("mixture masses inconsistent")
                if lower + upper and (
                    delta != upper / (lower + upper) or delta > Fraction(protocol["tolerance"])
                ):
                    raise RuntimeError("bad presampling normalized certificate")
                if mass is not None:
                    if not lower <= mass <= lower + upper:
                        raise RuntimeError("exact mass violates envelope coverage")
                    if mass and 1 - mass / (lower + upper) > delta:
                        raise RuntimeError("actual rejection exceeds certificate")
                    checks += 1
            if certified:
                result["depths"] = [r["certificate"]["depth"] for r in certified]
                result["certified_delta"] = certified[0]["certificate"]["delta"]
            counts = [n for r in records for n in r.get("proposal_counts", [])]
            if counts:
                result["proposal_counts"] = dict(
                    total=sum(counts), maximum=max(counts), accepted=len(counts)
                )
            item["methods"][name] = result
        for candidate in protocol["candidates"]:
            decisions = {}
            for label, field, status in (
                ("first", "first_total", "first_status"),
                ("batch", "batch_total", "status"),
                ("cold_first", "cold_first_total", "first_status"),
                ("cold_batch", "cold_batch_total", "status"),
            ):
                comparisons = {
                    name: paired(
                        methods.get(candidate, []), methods.get(name, []), repeats, field, status
                    )
                    for name in protocol["mandatory_comparators"]
                }
                decisions[label] = dict(
                    strong_benefit=complete and all(v["useful"] for v in comparisons.values()),
                    comparisons=comparisons,
                )
            if decisions["first"]["strong_benefit"]:
                benefits[candidate].append([case, masks])
            if decisions["batch"]["strong_benefit"]:
                batch_benefits[candidate].append([case, masks])
            item["decisions"][candidate] = decisions
        cases.append(item)
    selected = args.selected
    if selected is None and complete:
        selected = max(protocol["candidates"], key=lambda n: len(benefits[n]))
    report = dict(
        stage=metadata["stage"],
        producer_commit=metadata["producer_commit"],
        rows=len(rows),
        expected_rows=len(allowed),
        campaign_complete=complete,
        statuses=dict(Counter(r["status"] for r in rows)),
        first_statuses=dict(Counter(r.get("first_status") for r in rows)),
        certificate_checks=checks,
        selected=selected,
        first_benefits=benefits,
        batch_benefits=batch_benefits,
        practical_gate=bool(complete and selected and benefits[selected]),
        cases=cases,
        scope=(
            "Exact first frozen-product sample; finite proposal refusal bound; "
            "no marginals/native trajectory/semantic accuracy claim"
        ),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "decision.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        f"# Exact envelope — {metadata['stage']}",
        "",
        f"Records {len(rows)}/{len(allowed)}; {report['statuses']}.",
        f"First statuses: {report['first_statuses']}; certificate checks: {checks}.",
        f"First wins { {n: len(v) for n, v in benefits.items()} }; "
        f"batch wins { {n: len(v) for n, v in batch_benefits.items()} }.",
        f"Selected {selected}; first gate {report['practical_gate']}.",
        "",
        "All losses/refusals preserved. Partial campaigns cannot confirm benefits.",
        "",
        "| Case | Masks | Method | First status | First wall | Batch wall |",
        "|---|---:|---|---|---:|---:|",
    ]
    for item in cases:
        for name, value in item["methods"].items():
            first, batch = (
                value.get("first_total", {}).get("wall"),
                value.get("batch_total", {}).get("wall"),
            )
            lines.append(
                f"| {item['case'][:8]} | {item['mask_count']} | {name} | "
                f"{value['first_statuses']} | {'' if first is None else f'{first:.6f}'} | "
                f"{'' if batch is None else f'{batch:.6f}'} |"
            )
    (args.output / "decision.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
