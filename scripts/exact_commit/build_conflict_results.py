#!/usr/bin/env python3
"""Independently audit complete exact campaigns and generate all result prose."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from scripts.exact_commit.run_conflict_real import cohort, read, sha, verify

from mwpc_exact.budget_bounds import budget_input_fingerprint
from mwpc_exact.lean_bridge import verify_with_lean

ROOT = Path(__file__).resolve().parents[2]
PRIMARY = ROOT / "docs/artifacts/raw/m29_conflict_v1/primary"
FOLLOWUP = ROOT / "docs/artifacts/raw/m29_conflict_v1/followup"
PROCESSED = ROOT / "docs/artifacts/processed/m29_conflict_v1"
GENERATED = ROOT / "paper/generated/m29_conflict_v1"


def audit(directory):
    config = read(directory / "config.json")
    metadata = read(directory / "metadata.json")
    source = ROOT / config["input_archive"]
    source_manifest = read(source / "manifest.json")
    if sha(source / "rows.jsonl") != source_manifest["rows.jsonl"]:
        raise ValueError("comparison source scores changed")
    manifest = read(directory / "manifest.json")
    actual = {
        str(p.relative_to(directory))
        for p in directory.rglob("*")
        if p.is_file() and p.name != "manifest.json"
    }
    if actual != set(manifest):
        raise ValueError("archive contains missing or unlisted files")
    if metadata["config_sha256"] != sha(ROOT / metadata["config_source"]):
        raise ValueError("producing configuration changed")
    expected_files = {
        f"{m}-r{r}.jsonl" for m in config["methods"] for r in range(config["repetitions"][m])
    }
    if {p.name for p in directory.glob("*-r*.jsonl")} != expected_files:
        raise ValueError("missing method or repetition")
    verify(directory)
    instances = {i.instance_id: i for i, _ in cohort(config)}
    commits = {metadata["git_commit"]}
    if (directory / "continuation-metadata.json").exists():
        continuation = read(directory / "continuation-metadata.json")
        commits.add(continuation["git_commit"])
        metadata = {**metadata, "continuation": continuation}
    rows = []
    for filename in sorted(expected_files):
        records = [json.loads(line) for line in (directory / filename).read_text().splitlines()]
        method = filename.split("-r")[0]
        repetition = int(filename.split("-r")[1].split(".")[0])
        budgets = [max(config["budgets"])] if method == "resource_dp" else config["budgets"]
        expected = {(instance, b) for instance in instances for b in budgets}
        actual_grid = [(r["instance_id"], r["max_budget"]) for r in records]
        if len(actual_grid) != len(set(actual_grid)) or set(actual_grid) != expected:
            raise ValueError("complete frozen instance/budget grid was not retained")
        for row in records:
            instance = instances[row["instance_id"]]
            state = instance.selection_input
            if (
                row["method"] != method
                or row["repetition"] != repetition
                or row["git_commit"] not in commits
                or row["config_sha256"] != metadata["config_sha256"]
                or row["input_fingerprint"] != budget_input_fingerprint(state)
                or row["exactness_scope"] != state.support.exactness_scope.to_dict()
                or row["support_sha256"] != state.support.fingerprint
                or row["model_revision"] != instance.metadata["model_revision"]
                or row["tokenizer_revision"] != instance.metadata["tokenizer_revision"]
            ):
                raise ValueError("result metadata differs from its original input")
            if row["status"] == "completed":
                caps = config["budgets"] if method == "resource_dp" else [row["max_budget"]]
                if sorted(b["budget"] for b in row["batches"]) != caps:
                    raise ValueError("completed row dropped a budget/status")
                if method != "ranked_subsets" and not row.get("proof"):
                    raise ValueError("exact certified solver omitted its proof")
            rows.append(row)
    return rows, metadata


def summarize(rows):
    group = defaultdict(list)
    for row in rows:
        group[row["method"], row["family"], row["instance_id"], row["repetition"]].append(row)
    totals = defaultdict(list)
    for (method, family, instance, _repetition), values in group.items():
        if any(r["status"] != "completed" for r in values):
            continue
        totals[method, family, instance].append(sum(r["solve_seconds"] for r in values))
    per_input = {key: median(values) for key, values in totals.items()}
    methods = sorted({row["method"] for row in rows})
    families = sorted({row["family"] for row in rows})
    table = []
    for family in families:
        record = {"family": family, "methods": {}}
        for method in methods:
            values = [
                value for (m, f, _), value in per_input.items() if m == method and f == family
            ]
            if values:
                record["methods"][method] = {
                    "inputs": len(values),
                    "median_frontier_seconds": median(values),
                }
        table.append(record)
    paired = {}
    for comparator in (
        "resource_dp",
        "ranked_subsets",
        "conflict_cold",
        "conflict_reuse",
        "witness_only",
    ):
        ratios = []
        faster = 0
        for (method, family, instance), elapsed in per_input.items():
            if method != "proof_reuse" or (comparator, family, instance) not in per_input:
                continue
            other = per_input[comparator, family, instance]
            ratios.append(other / elapsed)
            faster += elapsed < other
        paired[comparator] = {
            "paired_inputs": len(ratios),
            "faster_inputs": faster,
            "median_paired_speed_ratio": median(ratios) if ratios else None,
        }
    queries = {}
    statuses = Counter()
    for method in methods:
        selected = [r for r in rows if r["method"] == method]
        batches = [b for r in selected for b in r.get("batches", [])]
        queries[method] = {
            "budget_results": len(batches),
            "oracle_calls": sum(b.get("oracle_calls", 0) for b in batches),
            "zero_oracle_optimal": sum(
                b["status"] == "optimal" and b.get("oracle_calls") == 0 for b in batches
            ),
            "positive_zero_oracle_optimal": sum(
                b["status"] == "optimal"
                and b.get("oracle_calls") == 0
                and b["objective_value"][0] > 0
                for b in batches
            ),
            "max_process_peak_rss_kib": max(r.get("peak_rss_kib", 0) for r in selected),
        }
        statuses.update(f"{method}:{r['status']}" for r in selected)
    return {
        "family_frontiers": table,
        "paired_speed": paired,
        "queries": queries,
        "job_status_counts": dict(statuses),
        "rows": len(rows),
    }


def render(summary, provenance):
    out = [
        "# Certified exact commitment with two-sided proof reuse",
        "",
        "All methods use the same 72 original inputs, 36 saved LLaDA states and two reward "
        "profiles. All caps 0, 1 and 2 are retained. These are repeated measures, not 72 "
        "independent requests. No new model generation or semantic-quality benefit is claimed.",
        "",
        "Independent original-input/certificate and complete-cohort audit: **PASS**.",
        "",
        "The general conflict-learning/hitting-set and certificate principles are established. "
        "The implemented incremental contribution is exact budgeted token commitment with "
        "portable original-input proofs and two-sided reuse across changing logits/support.",
        "",
        "## Mathematically established use",
        "",
        "Every returned optimum maximizes the unchanged rational budget objective. A CFG "
        "conflict forbids its supersets; certified master covers upper-bound every feasible "
        "batch. Negative proofs transport under retained-support contraction; positive "
        "witnesses are revalidated and may survive expansion. If a stored witness attains "
        "the current master bound, exact commitment needs zero new CFG-oracle queries.",
        "",
        "With H learned conflicts and T solves of budget at most B, feasibility queries are "
        "bounded by T+(B+1)H. In the documented fixed two-slot family, cold solving uses "
        "4T queries and two-sided reuse uses four total. Proofs and correspondence are in "
        "`docs/research/m29-conflict-commitment.md`; Lean checks the specified cover, transport "
        "and query-count theorems, rather than claiming source-level refinement.",
        "",
        "## Complete real-state timing",
        "",
        "The DP computes the common frontier once. Other methods' times below sum the three "
        "budget queries per input, then take the median of their three repetitions and the "
        "median across all inputs of the family. DP has one fresh repetition. Solve time "
        "includes mandatory internal proof construction/checking; portable serialization "
        "and external verification are separate. Each worker uses the same pinned CPU.",
        "",
        "| Family | DP | Ranked subsets | Conflict cold | Conflict reuse | Witness only | "
        "Two-sided reuse |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    order = (
        "resource_dp",
        "ranked_subsets",
        "conflict_cold",
        "conflict_reuse",
        "witness_only",
        "proof_reuse",
    )
    for family in summary["family_frontiers"]:
        values = [f"{family['methods'][m]['median_frontier_seconds']:.6f}" for m in order]
        out.append(f"| {family['family']} | " + " | ".join(values) + " |")
    out.extend(
        [
            "",
            "## Every comparator retained",
            "",
            "| Comparator | Paired inputs | Two-sided faster | Median paired speed ratio |",
            "|---|---:|---:|---:|",
        ]
    )
    for comparator, comparison in summary["paired_speed"].items():
        out.append(
            f"| {comparator} | {comparison['paired_inputs']} | "
            f"{comparison['faster_inputs']} | "
            f"{comparison['median_paired_speed_ratio']:.3f} |"
        )
    out.extend(
        [
            "",
            "A ratio above one favors two-sided reuse. This is a measured computation "
            "comparison on the complete development/replay cohort; no population confidence "
            "or advantage over the full EPIC decoder follows. The simple ranked exact "
            "comparator remains visible even when it is faster.",
            "",
            "## Query counts, including zero-reward cases",
            "",
            "| Method | Budget results | CFG-oracle calls | Zero-call optima | "
            "Positive-reward zero-call optima |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for method, q in summary["queries"].items():
        out.append(
            f"| {method} | {q['budget_results']} | {q['oracle_calls']} | "
            f"{q['zero_oracle_optimal']} | {q['positive_zero_oracle_optimal']} |"
        )
    out.extend(
        [
            "",
            "DP query counts are not applicable: it performs weighted resource parsing "
            "directly. The reference grammar oracle is unchanged across the other methods.",
            "",
            "## Provenance and limits",
            "",
            "The two-sided/witness-only follow-up was developed after seeing conflict-only "
            "costs on these inputs. Its config was frozen before execution; this is an "
            "engineering improvement evaluated on the same cohort, not held-out confirmation.",
            "",
            "Status counts: `" + json.dumps(summary["job_status_counts"], sort_keys=True) + "`.",
            "",
            "Producing commits: `" + "`, `".join(p["git_commit"] for p in provenance) + "`.",
            "",
            "Configs, raw rows and compressed certificates are retained under "
            "`docs/artifacts/raw/m29_conflict_v1/`. The initial metadata-serialization failure "
            "occurred before any model-state evaluation and is documented separately.",
            "",
            "The method optimizes provided model weights; neither these proofs nor "
            "the timings certify correct interpretation of a request. Large conflict sets "
            "can make the master search expensive. Exact-on-support, finite slots and "
            "deadline/infeasibility distinctions remain explicit.",
            "",
        ]
    )
    return "\n".join(out)


def outputs():
    first, p1 = audit(PRIMARY)
    second, p2 = audit(FOLLOWUP)
    summary = summarize([*first, *second])
    summary["provenance"] = [p1, p2]
    summary["portable_certificates"] = sum(bool(row.get("proof")) for row in [*first, *second])
    summary["raw_manifest_sha256"] = [
        sha(PRIMARY / "manifest.json"),
        sha(FOLLOWUP / "manifest.json"),
    ]
    summary["source_sha256"] = {
        str(p.relative_to(ROOT)): sha(p)
        for p in (
            Path(__file__),
            ROOT / "src/mwpc_exact/proof_reuse.py",
            ROOT / "src/mwpc_exact/conflict_certificate.py",
            ROOT / "src/mwpc_exact/conflict_commit.py",
        )
    }
    geo = next(f["methods"] for f in summary["family_frontiers"] if f["family"] == "geocoding")
    dp_ratio = summary["paired_speed"]["resource_dp"]["median_paired_speed_ratio"]
    ranked_ratio = summary["paired_speed"]["ranked_subsets"]["median_paired_speed_ratio"]
    macros = {
        "MReuseDPSpeed": f"{dp_ratio:.1f}",
        "MReuseRankSpeed": f"{ranked_ratio:.2f}",
        "MReuseRankWins": str(summary["paired_speed"]["ranked_subsets"]["faster_inputs"]),
        "MReuseGeoSeconds": f"{geo['proof_reuse']['median_frontier_seconds']:.3f}",
        "MReuseGeoDPSeconds": f"{geo['resource_dp']['median_frontier_seconds']:.3f}",
        "MReuseZeroPositive": str(
            summary["queries"]["proof_reuse"]["positive_zero_oracle_optimal"]
        ),
        "MReuseCalls": str(summary["queries"]["proof_reuse"]["oracle_calls"]),
        "MReuseRankCalls": str(summary["queries"]["ranked_subsets"]["oracle_calls"]),
    }
    tex = (
        "% Generated from independently verified M29 archives.\n"
        + "\n".join("\\newcommand{\\" + name + "}{" + value + "}" for name, value in macros.items())
        + "\n"
    )
    return {
        PROCESSED / "summary.json": json.dumps(summary, sort_keys=True, indent=2) + "\n",
        PROCESSED / "report.md": render(summary, [p1, p2]),
        GENERATED / "numbers.tex": tex,
    }


def lean_conflicts(lake):
    unique = {}
    for directory in (PRIMARY, FOLLOWUP):
        for path in sorted((directory / "proofs").glob("*.json.gz")):
            data = read(path)
            for conflict in data.get("conflicts", []):
                proof = conflict["proof"]
                unique[proof["input_fingerprint"]] = proof
    results = {
        fingerprint: verify_with_lean(proof, formal_directory=ROOT / "formal", lake=lake)
        for fingerprint, proof in sorted(unique.items())
    }
    destination = ROOT / "docs/evidence/m29-concrete-conflicts-lean.json"
    destination.write_text(
        json.dumps(
            {"verification": "PASS", "unique_conflicts": len(results), "cases": results},
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    print(f"Lean checked {len(results)} distinct CFG conflict proofs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--lean")
    args = parser.parse_args()
    for path, content in outputs().items():
        if args.check:
            if path.read_text() != content:
                raise ValueError(f"generated artifact differs: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    if args.lean:
        lean_conflicts(args.lean)


if __name__ == "__main__":
    main()
