"""Generate the M28 report and manuscript numbers from independently checked raw data."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from statistics import median

from scripts.exact_commit import run_budgeted_real_replay as replay

from mwpc_exact.budget_bounds import certify_budget_batch

ROOT = replay.ROOT
RAW = ROOT / "docs/artifacts/raw/m28_budgeted_real_v1/completed"
PROCESSED = ROOT / "docs/artifacts/processed/m28_budgeted_real_v1"
PAPER = ROOT / "paper/generated/m28_budgeted_real_v1"


def generate(directory):
    rows, verification = replay.verify(directory)
    metadata = replay.read_json(directory / "metadata.json")
    exact = [r for r in rows if r["method"] == "budgeted_rational"]
    statuses = Counter(i["status"] for r in exact for i in r["frontier"])
    data = {
        **verification,
        **replay.summary(rows),
        "metadata": metadata,
        "raw_manifest_sha256": replay.sha(directory / "manifest.json"),
        "exact_frontier_statuses": dict(statuses),
        "analysis_sources_sha256": {
            str(path.relative_to(ROOT)): replay.sha(path)
            for path in (
                Path(__file__).resolve(),
                Path(replay.__file__).resolve(),
                ROOT / "src/mwpc_exact/budget_bounds.py",
            )
        },
    }
    solver_statuses = Counter(
        f"{row['method']}:{item['status']}" for row in rows for item in row["frontier"]
    )
    data["solver_status_counts"] = dict(solver_statuses)
    # Post-hoc application of the already proved M27 bound, without reoptimizing
    # any state or changing the frozen experiment. No new timing is inferred.
    relaxations = []
    optima = {
        (row["instance_id"], cap["budget"]): Fraction(*cap["objective_value"])
        for row in exact
        for cap in row["frontier"]
        if cap["status"] == "optimal"
    }
    for row in rows:
        if row["method"] != "unbudgeted_then_cap":
            continue
        state = replay.BenchmarkInstance.from_dict(
            replay.read_json(directory / row["input"])
        ).selection_input
        for cap in row["frontier"]:
            if cap["status"] != "feasible_on_support":
                continue
            certificate = certify_budget_batch(
                state,
                budget=cap["budget"],
                witness_token_ids=cap["witness_token_ids"],
                committed_positions=cap["committed_positions"],
            )
            optimum = optima.get((row["instance_id"], cap["budget"]))
            if (
                optimum is not None
                and not certificate.lower_bound <= optimum <= certificate.upper_bound
            ):
                raise ValueError("Relaxation interval contradicts a proved optimum")
            relaxations.append(
                {
                    "instance_id": row["instance_id"],
                    "budget": cap["budget"],
                    "lower_bound": replay.fraction_data(certificate.lower_bound),
                    "upper_bound": replay.fraction_data(certificate.upper_bound),
                    "optimal_under_support_expansion": certificate.optimal_under_support_expansion,
                    "input_fingerprint": certificate.input_fingerprint,
                }
            )
    tight = sum(r["optimal_under_support_expansion"] for r in relaxations)
    data["posthoc_relaxation_certificates"] = relaxations
    bound_profile_lines = []
    for profile in ("all-primary", "ordinary-primary"):
        items = [r for r in relaxations if r["instance_id"].endswith(profile)]
        positive_tight = sum(
            r["optimal_under_support_expansion"] and r["lower_bound"][0] > 0 for r in items
        )
        bound_profile_lines.append(
            f"| {profile} | {len(items)} | "
            f"{sum(r['optimal_under_support_expansion'] for r in items)} | "
            f"{sum(r['lower_bound'][0] == 0 for r in items)} | {positive_tight} |"
        )
    grouped = defaultdict(list)
    for row in exact:
        grouped[row["family"]].append(row)
    table = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{New budgeted replay on saved LLaDA states. Inputs include both reward "
        r"profiles; certificates cover caps 0--2. Median CPU seconds measure the full "
        r"frontier including its internal certificate checks, excluding model inference.}",
        r"\label{tab:budgeted-real}",
        r"\begin{tabular}{lrrrrr}",
        r"\hline",
        r"Family & Inputs & Optimal & Infeasible & Timeouts & Seconds \\",
        r"\hline",
    ]
    report = [
        "# Budgeted commitment: real-state demonstration",
        "",
        f"Producing code: `{metadata['git_commit']}`. Config: `{metadata['config_source']}` "
        f"(SHA-256 `{metadata['config_sha256']}`).",
        "",
        "The new rational budgeted method is executed here on authentic saved LLaDA "
        "states. This is offline replay, not a new denoising trajectory or an accuracy "
        "benchmark. The complete frozen cohort is 24 recursive-task snapshots and "
        "12 steps of one geocoding request, each with two declared reward profiles.",
        "",
        f"Independent verification: **{verification['verification']}**; "
        f"{verification['attempts']} method jobs, {verification['certificates']} "
        f"checked budget certificates. Optimal: {statuses['optimal']}; "
        f"infeasible on support: {statuses['infeasible_on_support']}.",
        "",
        "Optimality certifies the declared proposal weights, finite support and "
        "physical-position budget. It does not certify that the witness answers "
        "the user's request correctly. Each physical canvas and probability is "
        "inherited unchanged; the ordinary profile removes only EOS/PAD rewards.",
        "",
        "| Family | Inputs (both profiles) | Optimal caps | Infeasible caps | "
        "Timeout jobs | Median frontier seconds |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for family, items in sorted(grouped.items()):
        counts = Counter(i["status"] for r in items for i in r["frontier"])
        times = [r["solver_seconds"] for r in items if r["status"] == "complete"]
        time_text = f"{median(times):.3f}" if times else "--"
        timeouts = sum(r["status"] == "timeout" for r in items)
        values = (
            len(items),
            counts["optimal"],
            counts["infeasible_on_support"],
            timeouts,
            time_text,
        )
        table.append(family.replace("_", r"\_") + " & " + " & ".join(map(str, values)) + r" \\")
        report.append("| " + family + " | " + " | ".join(map(str, values)) + " |")
    table += [r"\hline", r"\end{tabular}", r"\end{table}"]
    report += [
        "",
        "Budget/profile variants are repeated measures. A single CPU repetition "
        "provides descriptive cost, not a statistical speed claim. Status counts "
        "retain all jobs; medians exclude unresolved jobs. Full worker time also "
        "includes proof serialization and replay of validated updates, so it is "
        "reported separately in the JSON summary.",
        "",
        "## Same-input objective comparisons",
        "",
        "Only an optimal exact result paired with an independently validated "
        "feasible batch enters an objective comparison. Unknown feasibility, "
        "infeasible native batches, errors and timeouts are not assigned a zero "
        "score. EPIC is its unchanged byte batch selector followed by a budget "
        "cap; these are not results for its full decoder, serial fallback or "
        "resampling. Native requests for serial fallback are excluded from scored "
        "comparisons rather than counted as zero-score losses. Minimum-batch "
        "filtering remains visible in native diagnostics.",
        "",
        "| Family | Profile | Comparator | Feasible paired caps | Strict exact "
        "advantages | Largest reward gap |",
        "|---|---|---|---:|---:|---:|",
    ]
    for group in data["groups"]:
        if group["method"] == "budgeted_rational":
            continue
        gap = "--" if group["max_gap"] is None else f"{float(Fraction(*group['max_gap'])):.8g}"
        report.append(
            f"| {group['family']} | {group['reward_profile']} | {group['method']} | "
            f"{group['certified_paired_budget_cases']} | {group['strict_gaps']} | {gap} |"
        )
    report += [
        "",
        "## Application of the existing quality-bound theorem",
        "",
        f"As a post-hoc analysis, the existing M27 independent relaxation checker "
        f"was applied to **all {len(relaxations)} feasible post-filtered batches**. "
        f"Its lower and upper bounds coincide in **{tight}** cases. In those cases, "
        "the existing witness plus this bound is sufficient to certify budgeted "
        "optimality, including under support expansion with unchanged proposals, "
        "weights, fixed slots, grammar and EOS/PAD semantics. No joint resource "
        "optimization is needed to check that certificate. Loose bounds remain "
        "loose; none is labelled optimal from the bound alone.",
        "",
        "This is a deterministic certification analysis of every eligible raw "
        "batch, not a new hybrid-decoder latency experiment. It demonstrates a "
        "practical use of the proved bound; it does not infer a speedup from "
        "unmeasured execution. Exact bound values are in `summary.json`.",
        "",
        "The split below exposes EOS/PAD and zero-reward contributions; zero "
        "reward is a valid but potentially trivial certificate, not evidence "
        "of useful content selection.",
        "",
        "| Profile | Feasible batches | Tight bound | Zero reward | Tight with positive reward |",
        "|---|---:|---:|---:|---:|",
        *bound_profile_lines,
        "",
        "## Every geocoding state (ordinary-token objective, budget two)",
        "",
        'Request: `Find the geographic coordinates of "Belo Horizonte".` '
        "Every saved step is shown in order. Witnesses below are certified possible "
        "completions, not newly generated final model responses. Token positions "
        "are zero-based. The `all_primary` profile and all other caps are in the raw archive.",
        "",
        "| Step | Fixed slots | Proposals | Committed positions | Reward | Witness |",
        "|---:|---:|---:|---|---:|---|",
    ]
    for row in exact:
        if row["family"] != "geocoding" or row["reward_profile"] != "ordinary_primary":
            continue
        instance = replay.BenchmarkInstance.from_dict(replay.read_json(directory / row["input"]))
        state = instance.selection_input
        cap = next((i for i in row["frontier"] if i["budget"] == 2), None)
        if cap and cap["status"] == "optimal":
            selected = str(cap["committed_positions"])
            reward = f"{float(Fraction(*cap['objective_value'])):.8g}"
            text = cap["witness_text"].replace("|", r"\|")
        else:
            selected, reward, text = "--", "--", row["status"] if cap is None else cap["status"]
        report.append(
            f"| {instance.metadata['source_forward_index']} | "
            f"{sum(t is not None for t in state.canvas)} | {len(state.proposals)} | "
            f"{selected} | {reward} | `{text}` |"
        )
    report += [
        "",
        "## Audit and reproduction",
        "",
        "The first attempt was interrupted after harness bugs in finite-batch "
        "validation and infeasible-result reporting. It is preserved in "
        "`docs/artifacts/raw/m28_budgeted_real_v1/interrupted`; it supplies no "
        "final comparisons. The corrected run uses exactly the frozen cohort, "
        "weights, supports, methods and limits. Regression tests cover both bugs.",
        "",
        "```bash",
        ".venv/bin/python scripts/exact_commit/run_budgeted_real_replay.py \\",
        "  --verify docs/artifacts/raw/m28_budgeted_real_v1/completed",
        ".venv/bin/python -m scripts.exact_commit.build_budgeted_real_results --check",
        "```",
        "",
        "`inputs/` retains every original scientific instance and source mapping; "
        "`proofs/` contains compressed portable original-input certificates; "
        "`rows.jsonl` records commitments, full witnesses, exact rational scores, "
        "all statuses, native baseline outputs and times. The manifest binds every "
        "raw file. Verification requires no model, GPU, network or reoptimization.",
        "",
    ]
    geocoding_seconds = median(
        r["solver_seconds"] for r in grouped["geocoding"] if r["status"] == "complete"
    )
    macros = {
        "MRealInputs": len(exact),
        "MRealOptimal": statuses["optimal"],
        "MRealInfeasible": statuses["infeasible_on_support"],
        "MRealCertificates": verification["certificates"],
        "MRealTimeouts": sum(r["status"] == "timeout" for r in exact),
        "MRealErrors": sum(r["status"] == "error" for r in exact),
        "MRealBoundChecked": len(relaxations),
        "MRealBoundTight": tight,
        "MRealGeoSeconds": f"{geocoding_seconds:.3f}",
    }
    for method, prefix in (
        ("confidence_preselection", "Preselection"),
        ("unbudgeted_then_cap", "Postfilter"),
        ("epic_regular_cover_then_cap", "Epic"),
    ):
        items = [
            g
            for g in data["groups"]
            if g["method"] == method and g["reward_profile"] == "ordinary_primary"
        ]
        macros[f"MReal{prefix}Pairs"] = sum(g["certified_paired_budget_cases"] for g in items)
        macros[f"MReal{prefix}Strict"] = sum(g["strict_gaps"] for g in items)
    return {
        PROCESSED / "summary.json": json.dumps(data, indent=2, sort_keys=True) + "\n",
        PROCESSED / "report.md": "\n".join(report),
        PAPER / "budgeted-real-table.tex": "\n".join(table) + "\n",
        PAPER / "numbers.tex": "% Generated from independently checked real-state replay.\n"
        + "".join(rf"\newcommand{{\{name}}}{{{value}}}" + "\n" for name, value in macros.items()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = generate(args.raw)
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise ValueError(f"Stale generated artifact: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print(f"{'Verified' if args.check else 'Generated'} {len(outputs)} M28 artifacts")


if __name__ == "__main__":
    main()
