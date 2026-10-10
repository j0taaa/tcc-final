"""Derive the certificate article from complete immutable evidence, never hand timings."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path
from statistics import median
from zipfile import ZipFile

from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "attempts/24-certified-depth-approximation/work/evidence"
OUTPUT = ROOT / "paper/generated/m44_certified_depth_v1"


def read(path: Path):
    return json.loads(path.read_text())


def verified_decision(stage: str):
    folder = EVIDENCE / (stage + "-v1")
    raw = gzip.decompress((folder / "rows.jsonl.gz").read_bytes())
    provenance = read(folder / "provenance.json")
    expected_hash = provenance.get("rows_sha256", provenance.get("rows_uncompressed_sha256"))
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError("frozen campaign rows changed")
    saved = read(folder / "decision.json")
    if not saved["campaign_complete"] or not saved["practical_gate"]:
        raise ValueError("no confirmed complete query gate")
    # Recompute the decision from ALL original records, not only archived tables.
    with tempfile.TemporaryDirectory() as temporary:
        command = [
            sys.executable,
            "-m",
            "attempts.24-certified-depth-approximation.work.analyze",
            "--input",
            str(folder),
            "--output",
            temporary,
        ]
        if stage == "independent":
            command.extend(("--selected", "handoff"))
        subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
        if read(Path(temporary) / "decision.json") != saved:
            raise ValueError("current all-record analysis differs from frozen decision")
    return saved


def generate():
    development = verified_decision("development")
    independent = verified_decision("independent")
    envelope_folder = ROOT / "attempts/25-exact-envelope-sampling/work/evidence/development-v2"
    envelope_raw = gzip.decompress((envelope_folder / "rows.jsonl.gz").read_bytes())
    if (
        hashlib.sha256(envelope_raw).hexdigest()
        != read(envelope_folder / "provenance.json")["rows_sha256"]
    ):
        raise ValueError("exact-envelope development rows changed")
    envelope = read(envelope_folder / "decision.json")
    with tempfile.TemporaryDirectory() as temporary:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "attempts.25-exact-envelope-sampling.work.analyze",
                "--input",
                str(envelope_folder),
                "--output",
                temporary,
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        if read(Path(temporary) / "decision.json") != envelope:
            raise ValueError("exact-envelope all-record decision changed")
    if not envelope["campaign_complete"] or envelope["practical_gate"]:
        raise ValueError("revise exact-envelope narrative for this decision")
    negative = read(envelope_folder / "negative-audit.json")["blockers"]
    by_case = {(c["case"], c["mask_count"]): c for c in envelope["cases"]}
    expected_blockers = {
        (key, candidate) for key in by_case for candidate in envelope["first_benefits"]
    }
    if (
        len(negative) != len(expected_blockers)
        or {((b["case"], b["mask_count"]), b["candidate"]) for b in negative} != expected_blockers
    ):
        raise ValueError("missing error-independent negative case")
    for b in negative:
        c = by_case[b["case"], b["mask_count"]]
        value = c["decisions"][b["candidate"]]["first"]["comparisons"][b["control"]]
        if (
            value != b["comparison"]
            or value["useful"]
            or c["methods"][b["control"]]["first_statuses"] != {"complete": 3}
        ):
            raise ValueError("negative conclusion depends on an error or incomplete control")
    folder = EVIDENCE / "generation-v1"
    raw = gzip.decompress((folder / "rows.jsonl.gz").read_bytes())
    if hashlib.sha256(raw).hexdigest() != read(folder / "provenance.json")["rows_sha256"]:
        raise ValueError("generation rows changed")
    generation = [json.loads(line) for line in raw.splitlines()]
    frames = read(EVIDENCE / "independent-v1/capture-frames.json")
    with ZipFile(EVIDENCE / "first-full-head-v2/packet.zip") as archive:
        adapter = CompositionalByteLevelAdapter.from_token_pieces(
            json.loads(archive.read("vocabulary.json"))
        )
    expected = {
        (c["case"], c["mask_count"], method)
        for c in independent["cases"]
        for method in ("handoff", "exact_stack")
    }
    if (
        len(generation) != len(expected)
        or {(r["case"], r["masks"], r["method"]) for r in generation} != expected
    ):
        raise ValueError("missing, repeated or undeclared generation case")
    for row in generation:
        if row["status"] != "complete" or not row["exact_fixed_ids_preserved"]:
            raise ValueError("application conclusion needs every declared result")
        json.loads(row["output"], parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        canvas = list(frames[f"{row['case']}-{row['masks']}.json"]["canvas"])
        for step in row["steps"]:
            if step["input_canvas"] != canvas or step["response"]["status"] != "complete":
                raise ValueError("inconsistent generation transition")
            response = step["response"]
            sample, committed = response["sample"], response["committed"]
            if Fraction(response["sample_certificate"]["delta"]) > Fraction(1, 1000 * row["masks"]):
                raise ValueError("a step exceeded its uniform trajectory budget")
            if set(map(int, response["decisions"])) != {
                p for p, token in enumerate(canvas) if token is None
            }:
                raise ValueError("missing original-token confidence decision")
            if any(t is not None and sample[p] != t for p, t in enumerate(canvas)):
                raise ValueError("sample changed fixed original IDs")
            accepted = []
            for p, decision in response["decisions"].items():
                low, high = Fraction(decision["low"]), Fraction(decision["high"])
                yes = decision["accepted"]
                if (
                    (yes is True and low < Fraction(4, 5))
                    or (yes is False and high >= Fraction(4, 5))
                    or yes is None
                ):
                    raise ValueError("unresolved or contradictory confidence decision")
                if yes:
                    accepted.append(int(p))
            wanted = sorted(accepted)[:4] or [min(int(p) for p in response["decisions"])]
            if committed != wanted or any(canvas[p] is not None for p in committed):
                raise ValueError("generation did not use the shared policy")
            for p in committed:
                canvas[p] = sample[p]
        if canvas != row["original_token_ids"]:
            raise ValueError("final IDs differ from recorded commitments")
        if adapter.detokenize_bytes(canvas).decode("utf8") != row["output"]:
            raise ValueError("reported document differs from original-token output")
    amplification = read(EVIDENCE / "amplification-v1/audit.json")
    expected_amp = {
        (d["stage"], c["case"] + "-" + str(c["mask_count"]))
        for d in (development, independent)
        for c in d["cases"]
    }
    records = amplification["records"]
    if (
        len(records) != len(expected_amp)
        or {(r["stage"], r["case"]) for r in records} != expected_amp
    ):
        raise ValueError("amplification omitted a declared frame")
    guaranteed = []
    for row in records:
        if row["status"] == "strict_mass_increase_certified":
            g = Fraction(row["amplification"]["minimum_mass_ratio"])
            if g <= 1 or not row["exact_matrix_checked"] or Fraction(row["exact_mass_ratio"]) < g:
                raise ValueError("mass-amplification certificate contradicted")
            guaranteed.append(float(g))
    wins = [c for c in independent["cases"] if c["decisions"]["handoff"]["strong_benefit"]]
    summary = dict(
        development={
            k: development[k]
            for k in (
                "producer_commit",
                "rows",
                "statuses",
                "certificate_checks",
                "candidate_benefits",
            )
        },
        independent={
            k: independent[k]
            for k in (
                "producer_commit",
                "rows",
                "statuses",
                "certificate_checks",
                "candidate_benefits",
            )
        },
        independent_cold_benefits=sum(
            c["decisions"]["handoff"]["cold_benefit"] for c in independent["cases"]
        ),
        independent_cases=[
            dict(
                case=c["case"],
                masks=c["mask_count"],
                gate=c["decisions"]["handoff"]["strong_benefit"],
                cold_gate=c["decisions"]["handoff"]["cold_benefit"],
                methods={
                    name: {
                        key: value
                        for key, value in values.items()
                        if key
                        in ("statuses", "prepared_total", "cold_total", "depths", "peak_rss_kib")
                    }
                    for name, values in c["methods"].items()
                },
            )
            for c in independent["cases"]
        ],
        generation={
            method: dict(
                statuses=dict(Counter(r["status"] for r in generation if r["method"] == method)),
                new_forwards=sum(
                    r["new_model_forwards"] for r in generation if r["method"] == method
                ),
                actual_wall=sum(r["actual_case_wall"] for r in generation if r["method"] == method),
                scope="one-seed functional demo; not statistical decoder-speed confirmation",
            )
            for method in ("handoff", "exact_stack")
        },
        amplification=dict(
            statuses=dict(Counter(r["status"] for r in records)),
            guaranteed_mass_ratio_min=min(guaranteed),
            guaranteed_mass_ratio_median=median(guaranteed),
            guaranteed_mass_ratio_max=max(guaranteed),
        ),
        exact_envelope_development={
            k: envelope[k]
            for k in (
                "producer_commit",
                "rows",
                "statuses",
                "first_statuses",
                "certificate_checks",
                "first_benefits",
                "batch_benefits",
                "practical_gate",
            )
        },
    )
    table = [
        r"\begin{table}[htbp]\centering\small",
        r"\caption{All independent states: total warm query wall medians (seconds),",
        r"including the shared model forward. Exact is the cheapest completed full",
        r"control. Stars mark the all-six-control wall-and-CPU gate, not a comparison",
        r"against the row minimum alone.}\label{tab:independent}",
        r"\begin{tabular}{lrrrrrr}\toprule",
        r"Document & Masks & Depth & Handoff & Grammar-hit & Exact & Gate\\\midrule",
    ]
    for c in independent["cases"]:
        methods = c["methods"]
        h, g = methods["handoff"], methods["grammar_hit"]
        full = min(
            v["prepared_total"]["wall"]
            for k, v in methods.items()
            if k.startswith("exact_") and "prepared_total" in v
        )
        star = "*" if c["decisions"]["handoff"]["strong_benefit"] else "--"
        table.append(
            f"{c['case'][:8]} & {c['mask_count']} & {h['depths'][0]} & "
            f"{h['prepared_total']['wall']:.3f} & {g['prepared_total']['wall']:.3f} & "
            f"{full:.3f} & {star}\\\\"
        )
    table.extend((r"\bottomrule\end{tabular}\end{table}", ""))
    text = [
        r"\subsection{Complete development and independent confirmation}",
        f"Development completed {development['rows']}/{development['expected_rows']} records: "
        f"{development['statuses']['complete']} complete and "
        f"{development['statuses']['resource_refusal']} explicit resource refusals, with "
        f"{development['certificate_checks']} certificate checks against exact mass. "
        "Both variants passed three of eighteen query states; handoff was selected by "
        "the frozen tie rule, before independent capture. No strong additional "
        "handoff-over-closed runtime benefit was found.",
        f"Independent execution completed {independent['rows']}/{independent['expected_rows']} "
        f"records: {independent['statuses']['complete']} complete, "
        f"{independent['statuses']['resource_refusal']} resource refusals and "
        f"{independent['certificate_checks']} exact-mass checks, without errors. "
        f"The selected query passes {len(wins)}/15 states; closed passes the same three. "
        f"Cold benefit survives in {summary['independent_cold_benefits']}/15. "
        "The approximate first-sample gate passes two states; rejection remains "
        "cheaper on several easy cases. This is not exact-envelope evidence.",
        "",
        "\n".join(table),
        "For the three query wins, paired wall ratios against grammar-hit are "
        + ", ".join(
            f"{c['decisions']['handoff']['comparisons']['grammar_hit']['ratio_medians']['wall']:.3f}"
            for c in wins
        )
        + "; the paired CPU medians also pass. All nine repetitions have a favorable "
        "sign against completed mandatory controls. Compact controls refuse the "
        "sixteen-mask states at their explicit budgets; this does not establish "
        "universal physical infeasibility. All original outcomes, including the "
        "twelve states without strong benefit, remain in the complete report.",
        "",
        r"\subsection{Actual iterative application and reweighting}",
        "All thirty preregistered MDLM executions return valid JSON and preserve "
        "fixed original IDs: fifteen per method, with 92 genuine new forwards "
        "per method (184 total), no refusal or worker error. The interval policy "
        "resolves every confidence decision; no extra refinement is needed in "
        "this seed. The threshold-refinement boundary is exercised separately "
        "by a tiny independent CPU-service oracle. Fresh later contexts come "
        "from previous commitments, not prerecorded model predictions. One "
        "seed demonstrates integration, not statistical total-latency superiority. "
        "The trajectory guarantee is the written common-policy corollary, not "
        "an empirical measurement of the output distribution's TV.",
        "All 33 original development and independent frames yield a strict "
        "mass-increase certificate for factor four. Guaranteed ratios range "
        f"from {min(guaranteed):.5f} to {max(guaranteed):.5f}; all bounds are "
        "checked against the identity using full exact original marginals. "
        "This is not an independent recomputation of tilted products, a new "
        "neural forward, semantic accuracy or an amortized speed experiment. "
        "Small gains and all costs remain visible.",
        "",
        r"\subsection{Exact sampling is a different cost question}",
        f"The separate exact-envelope development campaign completed all {envelope['rows']} "
        f"planned records: {envelope['statuses']['complete']} complete, "
        f"{envelope['statuses']['resource_refusal']} resource refusals and "
        f"{envelope['statuses']['worker_error']} worker error, with "
        f"{envelope['certificate_checks']} checks against exact full mass. Both variants "
        "pass zero of eighteen primary first-sample gates against eleven mandatory "
        "controls, including counter+CARS; each passes one secondary batch-of-32 "
        "development gate. That secondary observation is not independently confirmed "
        "and does not authorize first-sample adoption. Controls are not charged "
        "unneeded marginals. A timeout reached the harness while disarming its timer; "
        "the raw error remains unchanged, with no capacity credit. Every one of the "
        "36 candidate/state pairs also fails against a fully completed error-free "
        "control, so that race cannot change the primary rejection. The boundary "
        "has since been repaired and tested; measurements were not rerun or relabeled. "
        "The prospectively conditional independent stage was not triggered. Thus "
        "the confirmed practical contribution remains the certified query, rather "
        "than universal or exact first-output speed.",
        "",
        r"\subsection{Reproduction and preserved negative evidence}",
        r"Protocols, capture metadata, commands, producer commits and all measured rows are in",
        r"\path{attempts/24-certified-depth-approximation/work/evidence}. The article",
        "generator recomputes both adoption decisions from all archived raw records "
        "and checks every application transition and certificate-derived threshold. "
        "This checks archived numerical conclusions; it does not rerun all neural "
        "forwards or every large solver. The small full-head packet separately "
        "closes the logits-to-softmax reproduction gap for one chosen capture.",
        "The exact general-CFG posterior, MWPC commitments and earlier decoder "
        "studies remain preserved, including failed external transfer against "
        "EPIC and controls faster than earlier implementations. Attempts 18--23 "
        "did not confirm their all-comparator development gates. Their negative "
        "outcomes were not removed or reclassified as successes. They are "
        "background evidence, rather than additional protagonists of this article.",
        "",
    ]
    return {
        "results.tex": "\n\n".join(text),
        "summary.json": json.dumps(summary, indent=2) + "\n",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in generate().items():
        path = OUTPUT / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise ValueError(f"derived certificate article differs: {path.relative_to(ROOT)}")
        else:
            OUTPUT.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print("Complete certificate evidence and derived article verified")


if __name__ == "__main__":
    main()
