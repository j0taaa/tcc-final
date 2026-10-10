"""Audit certificates and the frozen paired, full-cost adoption criterion."""

import argparse
import gzip
import itertools
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from statistics import median


def paired(candidate, control, repeats, field):
    if len(candidate) != repeats or len(control) != repeats:
        return dict(useful=False, reason="missing repetitions")
    if any(r["status"] != "complete" for r in candidate):
        return dict(useful=False, reason="candidate not complete in every repetition")
    if all(r["status"] == "resource_refusal" and "operation" in r for r in control):
        return dict(useful=True, reason="localized capacity under equal internal budgets")
    if any(r["status"] != "complete" or field not in r for r in control):
        return dict(useful=False, reason="mixed, zero, erroneous or unmeasured control")
    by_repeat = {r["repeat"]: r for r in candidate}
    ratios = {
        unit: [by_repeat[r["repeat"]][field][unit] / r[field][unit] for r in control]
        for unit in ("wall", "cpu")
    }
    favorable = all(x < 1 for values in ratios.values() for x in values)
    return dict(
        useful=favorable and all(median(values) <= 0.8 for values in ratios.values()),
        ratio_medians={unit: median(values) for unit, values in ratios.items()},
        favorable_every_repeat=favorable,
        paired_ratios=ratios,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partial", action="store_true", help="audit only; never choose/adopt")
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
        raise ValueError("independent evaluation requires the development-frozen selection")
    repeats = protocol["independent_repetitions"] if independent else protocol["repetitions"]
    allowed = set(
        itertools.product(
            [doc["key"] for doc in metadata["capture"]["selected"]],
            protocol["mask_counts"],
            protocol["methods"],
            range(repeats),
        )
    )
    keys = [(r["case"], r["mask_count"], r["method"], r["repeat"]) for r in rows]
    if len(keys) != len(set(keys)) or not set(keys) <= allowed:
        raise ValueError("duplicate or unexpected measurement row")
    complete = set(keys) == allowed
    if not complete and not args.partial:
        raise ValueError("campaign incomplete; --partial forbids positive adoption decisions")
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row["case"], row["mask_count"]][row["method"]].append(row)
    benefits = {name: [] for name in protocol["candidates"]}
    sampling_benefits = {name: [] for name in protocol["candidates"]}
    certificate_checks, cases = 0, []
    for (case, masks), methods in sorted(grouped.items()):
        item = dict(case=case, mask_count=masks, methods={}, decisions={})
        exact = [
            r
            for name in protocol["frozen_exact_methods"]
            for r in methods.get(name, [])
            if r["status"] in ("complete", "zero_valid_mass")
        ]
        for field in ("valid_mass", "exact_total", "exact_denominator", "matrix_sha256"):
            values = {r[field] for r in exact if field in r}
            if len(values) > 1:
                raise RuntimeError(f"unequal exact {field}: {case}/{masks}")
        mass = Fraction(exact[0]["valid_mass"]) if exact else None
        item["full_mass"] = None if mass is None else str(mass)
        for name, records in methods.items():
            done = [r for r in records if r["status"] == "complete"]
            result = dict(statuses=dict(Counter(r["status"] for r in records)))
            for field in (
                "prepared_total",
                "sampling_total",
                "cold_total",
                "operation",
                "startup",
                "conversion",
                "adaptive_inference",
                "outside_and_original_marginals",
            ):
                measured = [r[field] for r in done if field in r]
                if measured:
                    result[field] = {u: median(v[u] for v in measured) for u in ("wall", "cpu")}
            if done:
                result["peak_rss_kib"] = max(r["peak_rss_kib"] for r in done)
            certified = [r for r in records if r["status"] == "complete" and "certificate" in r]
            for row in certified:
                certificate = row["certificate"]
                lower = Fraction(row["lower_valid_mass"])
                upper, delta = Fraction(certificate["upper_tail"]), Fraction(certificate["delta"])
                if lower <= 0 or not 0 <= delta <= Fraction(protocol["tolerance"]):
                    raise RuntimeError(f"invalid positive-mass certificate: {case}/{masks}/{name}")
                if delta != upper / (lower + upper):
                    raise RuntimeError("reported normalized error differs from mass bound")
                if mass is not None:
                    if not lower <= mass <= lower + upper or (mass - lower) / mass > delta:
                        raise RuntimeError(
                            f"certificate violated by exact mass: {case}/{masks}/{name}"
                        )
                    certificate_checks += 1
            if certified:
                result["depths"] = [r["certificate"]["depth"] for r in certified]
                result["certified_delta"] = certified[0]["certificate"]["delta"]
                result["actual_tv"] = (
                    None
                    if mass is None
                    else str((mass - Fraction(certified[0]["lower_valid_mass"])) / mass)
                )
                result["lower_valid_mass"] = certified[0]["lower_valid_mass"]
            item["methods"][name] = result
        for candidate in protocol["candidates"]:
            records = methods.get(candidate, [])
            comparisons = {
                name: paired(records, methods.get(name, []), repeats, "prepared_total")
                for name in protocol["mandatory_comparators"]
            }
            sampling_controls = [*protocol["mandatory_comparators"], "rejection"]
            sampling = {
                name: paired(records, methods.get(name, []), repeats, "sampling_total")
                for name in sampling_controls
            }
            strong = complete and all(v["useful"] for v in comparisons.values())
            sampling_strong = complete and all(v["useful"] for v in sampling.values())
            cold = {
                name: paired(records, methods.get(name, []), repeats, "cold_total")
                for name in protocol["mandatory_comparators"]
            }
            item["decisions"][candidate] = dict(
                strong_benefit=strong,
                comparisons=comparisons,
                cold_comparisons=cold,
                cold_benefit=complete and all(v["useful"] for v in cold.values()),
                sampling_benefit=sampling_strong,
                sampling_comparisons=sampling,
            )
            if strong:
                benefits[candidate].append([case, masks])
            if sampling_strong:
                sampling_benefits[candidate].append([case, masks])
        item["handoff_vs_closed"] = paired(
            methods.get("handoff", []), methods.get("closed", []), repeats, "prepared_total"
        )
        cases.append(item)
    selected = args.selected
    if selected is None and complete:
        selected = max(protocol["candidates"], key=lambda name: len(benefits[name]))
    report = dict(
        stage=metadata["stage"],
        producer_commit=metadata["producer_commit"],
        rows=len(rows),
        expected_rows=len(allowed),
        campaign_complete=complete,
        statuses=dict(Counter(r["status"] for r in rows)),
        certificate_checks=certificate_checks,
        selected=selected,
        candidate_benefits=benefits,
        candidate_sampling_benefits=sampling_benefits,
        practical_gate=bool(selected and benefits[selected] and complete),
        cases=cases,
        scope="Certified frozen full-V query; not whole generation or semantic accuracy",
        priority="Comparative certificate proof; classical abstraction; priority not established",
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "decision.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        f"# Certified posterior — {metadata['stage']}",
        "",
        f"Records {len(rows)}/{len(allowed)}; {report['statuses']}.",
        f"Exact-ground-truth certificate checks: {certificate_checks}.",
        f"Candidate strong benefits: { {k: len(v) for k, v in benefits.items()} }.",
        f"Selected: {selected}; practical gate: {report['practical_gate']}.",
        "",
        "All refusals, zeros and errors remain. Partial campaigns cannot confirm benefits.",
        "",
        "| Case | Masks | Method | Statuses | Total wall | Total CPU | Depth |",
        "|---|---:|---|---|---:|---:|---|",
    ]
    for item in cases:
        for name, record in item["methods"].items():
            total = record.get("prepared_total", {})
            wall, cpu = total.get("wall"), total.get("cpu")
            lines.append(
                f"| {item['case'][:8]} | {item['mask_count']} | {name} | {record['statuses']} | "
                f"{'' if wall is None else f'{wall:.6f}'} | "
                f"{'' if cpu is None else f'{cpu:.6f}'} | {record.get('depths', '')} |"
            )
    (args.output / "decision.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
