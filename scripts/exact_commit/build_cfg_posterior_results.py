"""Compact M34 archive, verify all input lineage, and derive manuscript products."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import math
import statistics
from collections import Counter
from fractions import Fraction
from pathlib import Path

from scripts.exact_commit.run_cfg_posterior_audit import source_grammar
from scripts.exact_commit.run_cfg_sampling_followup import valid

from mwpc_exact.cfg_posterior import CompilationLimit, compile_cfg_sampler
from mwpc_exact.conflict_proof import read_state
from mwpc_exact.mass_certificate import ProbabilityInput

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "docs/artifacts/raw/m34_cfg_posterior_v1"
PRODUCTS = ROOT / "docs/artifacts/processed/m34_cfg_posterior_v1"
GENERATED = ROOT / "paper/generated/m34_cfg_posterior_v1"
PHASES = (
    "scaling",
    "replay",
    "json-model",
    "integer-scaling",
    "integer-replay",
    "integer-json-model",
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_gzip(path, value):
    with gzip.GzipFile(str(path), "wb", mtime=0) as stream:
        stream.write(canonical(value))


def archive(source):
    ARCHIVE.mkdir(parents=True, exist_ok=False)
    components, inputs, runs, compressed_hashes = {}, {}, {}, {}
    for phase in PHASES:
        directory = source / phase
        rows = [json.loads(line) for line in (directory / "rows.jsonl").read_text().splitlines()]
        for row in rows:
            path = directory / f"{row['case']}-input.json.gz"
            raw = json.load(gzip.open(path, "rt"))
            key = digest(canonical(raw))
            compressed_hashes[f"{phase}/{row['case']}"] = digest(path.read_bytes())
            row["archived_input"] = key
            if key in inputs:
                continue
            for container, field in (
                (raw["input"], "grammar"),
                (raw["input"]["selection"], "tokenizer_adapter"),
                (raw["input"]["selection"]["support"], "permitted_token_ids"),
            ):
                value = container[field]
                reference = digest(canonical(value))
                components[reference] = value
                container[field] = {"component": reference}
            inputs[key] = raw
        runs[phase] = {
            "rows": rows,
            "config": json.loads((directory / "config.json").read_text()),
            "config_sha256": digest((directory / "config.json").read_bytes()),
            "metadata": json.loads((directory / "metadata.json").read_text()),
        }
    followup = source / "sampling-followup"
    runs["sampling-followup"] = {
        "rows": [json.loads(line) for line in (followup / "rows.jsonl").read_text().splitlines()],
        "config": json.loads((followup / "config.json").read_text()),
        "config_sha256": digest((followup / "config.json").read_bytes()),
    }
    runs["aborted"] = {
        "failure": json.loads((source / "scaling-input-error-952c24d/failure.json").read_text()),
        "metadata": json.loads((source / "scaling-input-error-952c24d/metadata.json").read_text()),
    }
    write_gzip(ARCHIVE / "components.json.gz", components)
    write_gzip(ARCHIVE / "inputs.json.gz", inputs)
    write_gzip(ARCHIVE / "runs.json.gz", runs)
    manifest = {
        "original_compressed_input_hashes": compressed_hashes,
        "files": {p.name: digest(p.read_bytes()) for p in ARCHIVE.glob("*.gz")},
        "scope": (
            "All compact original inputs/probabilities/tokenizer bytes/outcomes; "
            "full model logits remain local"
        ),
        "command_forms": [
            ".venv/bin/python -m scripts.exact_commit.run_cfg_posterior_audit "
            "--mode scaling --output DIR",
            ".venv/bin/python -m scripts.exact_commit.run_cfg_posterior_audit "
            "--mode replay --output DIR",
            ".venv/bin/python -m scripts.exact_commit.capture_cfg_json_demo --output DIR",
            ".venv/bin/python -m scripts.exact_commit.run_cfg_posterior_audit "
            "--mode MODE --replay-from OLD --output NEW",
            ".venv/bin/python -m scripts.exact_commit.run_cfg_sampling_followup "
            "--inputs ROOT --output DIR",
        ],
    }
    (ARCHIVE / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def load_inputs():
    manifest = json.loads((ARCHIVE / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if digest((ARCHIVE / name).read_bytes()) != expected:
            raise ValueError(f"archive hash mismatch: {name}")
    components = json.load(gzip.open(ARCHIVE / "components.json.gz", "rt"))
    packed = json.load(gzip.open(ARCHIVE / "inputs.json.gz", "rt"))
    restored = {}
    for key, value in packed.items():
        raw = copy.deepcopy(value)
        for container, field in (
            (raw["input"], "grammar"),
            (raw["input"]["selection"], "tokenizer_adapter"),
            (raw["input"]["selection"]["support"], "permitted_token_ids"),
        ):
            container[field] = components[container[field]["component"]]
        if digest(canonical(raw)) != key:
            raise ValueError("lossless input reconstruction failed")
        restored[key] = raw
    return json.load(gzip.open(ARCHIVE / "runs.json.gz", "rt")), restored, manifest


def results(row):
    return row["results"] if "results" in row else [row["result"]]


def median_query(result):
    return statistics.median(t["query_seconds"] for t in result["timings"])


def recompute(runs, inputs):
    """Current-code correctness replay; never replace recorded timings/results."""
    counts = Counter()
    for phase in PHASES[3:]:
        for row in runs[phase]["rows"]:
            raw = inputs[row["archived_input"]]
            data = ProbabilityInput(
                read_state(raw["input"]),
                tuple(tuple(Fraction(*p) for p in r) for r in raw["probabilities"]),
            )
            expected = results(row)[0]
            try:
                actual = compile_cfg_sampler(
                    source_grammar(row["kind"]), data.state, timeout_seconds=30
                ).evaluate(data)
            except CompilationLimit as error:
                if "valid_mass" in expected:
                    raise ValueError(
                        f"current code refused archived solved case: {row['case']}"
                    ) from error
                counts["unresolved_without_archived_oracle"] += 1
                continue
            if "valid_mass" not in expected:
                counts["resolved_without_archived_oracle"] += 1
                continue
            if actual.valid_mass != Fraction(expected["valid_mass"]) or actual.marginals != tuple(
                tuple(map(Fraction, r)) for r in expected["marginals"]
            ):
                raise ValueError(f"current posterior differs from archived result: {row['case']}")
            counts["exact_mass_and_marginals_agree"] += 1
    return dict(counts)


def summarize(runs, raw_inputs, manifest):
    report = {
        "phases": {},
        "correctness_scope": "focused independent extension tests; no whole-source refinement",
    }
    speedups = []
    comparisons = []
    for phase in PHASES:
        rows = runs[phase]["rows"]
        if len(rows) != (28 if "scaling" in phase else 9 if "json-model" in phase else 18):
            raise ValueError("incomplete cohort")
        if len({row["case"] for row in rows}) != len(rows):
            raise ValueError("duplicate cases substituted into cohort")
        counts = Counter()
        for row in rows:
            if row["config_sha256"] != runs[phase]["config_sha256"]:
                raise ValueError("config lineage mismatch")
            raw = raw_inputs[row["archived_input"]]
            data = ProbabilityInput(
                read_state(raw["input"]),
                tuple(tuple(Fraction(*p) for p in r) for r in raw["probabilities"]),
            )
            q = math.prod(sum(p) for p in data.probabilities)
            for result in results(row):
                counts[f"{result['method']}:{result['status']}"] += 1
                if "valid_mass" not in result:
                    continue
                z = Fraction(result["valid_mass"])
                if not 0 <= z <= q:
                    raise ValueError("invalid probability mass")
                if result.get("marginals"):
                    marginal = result["marginals"]
                    for m, probabilities in zip(marginal, data.probabilities, strict=True):
                        if len(m) != len(probabilities) or sum(map(Fraction, m)) != int(bool(z)):
                            raise ValueError("invalid marginal row")
                if result.get("sample"):
                    sample = result["sample"]
                    if len(sample) != len(data.state.canvas) or any(
                        token not in support or (fixed is not None and fixed != token)
                        for token, support, fixed in zip(
                            sample, data.state.support.rows, data.state.canvas, strict=True
                        )
                    ):
                        raise ValueError("sample violates original tokens/slots")
                    if row.get("kind", "json") != "dyck" and not valid(
                        data.state.tokenizer_adapter.detokenize_bytes(sample),
                        row.get("kind", "json"),
                    ):
                        raise ValueError("independent sample rejection")
            pair = results(row)
            if len(pair) == 2 and all("valid_mass" in r for r in pair):
                if pair[0]["valid_mass"] != pair[1]["valid_mass"]:
                    raise ValueError("independent control mass disagreement")
                if pair[0].get("marginals") and pair[1].get("marginals"):
                    if pair[0]["marginals"] != pair[1]["marginals"]:
                        raise ValueError("independent control marginal disagreement")
            if phase.startswith("integer-"):
                comparisons.append(
                    {
                        "phase": phase,
                        "case": row["case"],
                        "results": [
                            {
                                "method": result["method"],
                                "status": result["status"],
                                "cells": result.get("cells"),
                                "compilation_seconds": result.get("compilation_seconds"),
                                "query_seconds": median_query(result)
                                if "timings" in result
                                else None,
                            }
                            for result in results(row)
                        ],
                    }
                )
                original = next(r for r in runs[phase[8:]]["rows"] if r["case"] == row["case"])
                a, b = results(original)[0], results(row)[0]
                # Raw original and replay inputs must be byte-for-byte recoverable.
                if (
                    canonical(raw_inputs[original["archived_input"]]["input"])
                    != canonical(raw["input"])
                    or raw_inputs[original["archived_input"]]["probabilities"]
                    != raw["probabilities"]
                ):
                    raise ValueError("before/after original input changed")
                if "valid_mass" in a:
                    if (a["valid_mass"], a["marginals"]) != (
                        b.get("valid_mass"),
                        b.get("marginals"),
                    ):
                        raise ValueError("before/after exact inference disagrees")
                    speedups.append(median_query(a) / median_query(b))
        report["phases"][phase] = dict(sorted(counts.items()))
    followup = runs["sampling-followup"]["rows"]
    if len(followup) != 27:
        raise ValueError("incomplete follow-up")
    applications = []
    for row in followup:
        phase = "integer-json-model" if row["kind"] == "json" else "integer-replay"
        original = next(r for r in runs[phase]["rows"] if r["case"] == row["case"])
        if (
            row["source_input_sha256"]
            != manifest["original_compressed_input_hashes"][f"{phase}/{row['case']}"]
        ):
            raise ValueError("follow-up changed its source input")
        raw = raw_inputs[original["archived_input"]]
        q = math.prod(sum(Fraction(*p) for p in r) for r in raw["probabilities"])
        cfg = results(original)[0]
        z = Fraction(cfg["valid_mass"]) if "valid_mass" in cfg else None
        applications.append(
            {
                "case": row["case"],
                "cfg_status": cfg["status"],
                "first_cfg_seconds": cfg["compilation_seconds"]
                + median_query(cfg)
                + statistics.median(t["sample_seconds"] for t in cfg["timings"])
                if z
                else None,
                "represented_expected_rejection_attempts": str(q / z) if z else None,
                "rejection": row["rejection"],
                "reuse": row["reuse"],
            }
        )
    report.update(
        comparisons=comparisons,
        applications=applications,
        exact_before_after_pairs=len(speedups),
        median_query_refinement_ratio=statistics.median(speedups),
        rejection_statuses=dict(Counter(r["rejection"]["status"] for r in followup)),
        reuse_statuses=dict(Counter(r["reuse"]["status"] for r in followup)),
    )
    return report


def products(report):
    fresh = report["phases"]["integer-json-model"].get("cfg:EXACT_ON_SUPPORT", 0)
    replay = report["phases"]["integer-replay"].get("cfg:EXACT_ON_SUPPORT", 0)
    reuse_count = report["reuse_statuses"].get("EXACT_ON_SUPPORT", 0)
    speed = report["median_query_refinement_ratio"]
    lines = [
        "# M34: complete outcomes, including refusals and stronger controls",
        "",
        "Classical weighted CFG sampling adapted to finite original dLLM tokens. "
        "Exactness is per frozen prediction/support, "
        "not semantic quality or the future trajectory. "
        "No published competitor was timed here.",
        "",
        f"{fresh}/9 fresh full-JSON inputs finish; {replay}/18 array replays finish. "
        f"All {report['exact_before_after_pairs']} initially successful masses/marginals are "
        "unchanged. The integer/pre-binarization refinement has a paired query-time "
        "ratio reported below; both independent stack controls get the integer optimization.",
        "",
        "```json",
        json.dumps(
            {k: v for k, v in report.items() if k not in ("applications", "comparisons")}, indent=2
        ),
        "```",
        "",
        "| Case | CFG first sample (ms) | Support rejection expected trials | "
        "Rejection outcome / ms | Cached / fresh (ms) |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for r in report["applications"]:
        first = (
            f"{r['first_cfg_seconds'] * 1000:.3f}"
            if r["first_cfg_seconds"] is not None
            else r["cfg_status"]
        )
        expected = (
            f"{float(Fraction(r['represented_expected_rejection_attempts'])):.3g}"
            if r["represented_expected_rejection_attempts"]
            else "unresolved"
        )
        rejection = r["rejection"]
        reuse = r["reuse"]
        cache = (
            f"{reuse['reuse_seconds'] * 1000:.3f} / {reuse['fresh_seconds'] * 1000:.3f}"
            if "reuse_seconds" in reuse
            else reuse["status"]
        )
        lines.append(
            f"| {r['case']} | {first} | {expected} | {rejection['status']} / "
            f"{rejection['seconds'] * 1000:.3f} | {cache} |"
        )
    lines.extend(
        [
            "",
            "Rejection is cheaper on all six smaller JSON cases in this recorded seed. "
            "Trial exhaustion is not infeasibility. Expected trial counts are algebra from Z "
            "and represented mass, not measured wall-time speedups. "
            f"Cached/fresh reuse equality is checked on all {reuse_count} completed cases; "
            "reuse can still lose to a compact specialized controller. One-type counters "
            "generally remain cheaper. The 28 Dyck probes are declared mathematical scaling "
            "inputs, not external/neural quality benchmarks. Full logits remain local; "
            "losslessly deduplicated original inputs, probabilities, full tokenizer bytes, "
            "every config, outcome and source hash are archived.",
        ]
    )
    lines.extend(
        [
            "",
            "## Every final grid/application comparison",
            "",
            "Times below exclude model loading/forward and include construction separately. "
            "Method `stack` is an independent local exact controller, not published code.",
            "",
            "| Case | Method | Status | Cells | Compile / query (ms) |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in report["comparisons"]:
        for result in row["results"]:
            timing = (
                (
                    f"{result['compilation_seconds'] * 1000:.3f} / "
                    f"{result['query_seconds'] * 1000:.3f}"
                )
                if result["query_seconds"] is not None
                else "--"
            )
            lines.append(
                f"| {row['case']} | {result['method']} | {result['status']} | "
                f"{result['cells']} | {timing} |"
            )
    tex = (
        f"\\newcommand{{\\MCfgFreshExact}}{{{fresh}}}\n"
        f"\\newcommand{{\\MCfgReplayExact}}{{{replay}}}\n"
        f"\\newcommand{{\\MCfgRefinementSpeed}}{{{speed:.2f}}}\n"
        f"\\newcommand{{\\MCfgReuseExact}}{{{reuse_count}}}\n"
    )
    # Concrete rows are computed, never authored as favorable summaries.
    table = [
        r"\begin{tabular}{lrrr}\toprule",
        r"Case & First sample (ms) & Reuse (ms) & Rejection trials$^{*}$\\\midrule",
    ]
    for row in report["applications"]:
        name = row["case"]
        if not name.startswith("json-context"):
            continue
        first = (
            f"{row['first_cfg_seconds'] * 1000:.1f}"
            if row["first_cfg_seconds"] is not None
            else "limit"
        )
        cached = (
            f"{row['reuse']['reuse_seconds'] * 1000:.1f}"
            if "reuse_seconds" in row["reuse"]
            else "limit"
        )
        expected = (
            f"{float(Fraction(row['represented_expected_rejection_attempts'])):.2g}"
            if row["represented_expected_rejection_attempts"]
            else "--"
        )
        label = name.replace("json-context", "C").replace("-", "/")
        table.append(f"{label} & {first} & {cached} & {expected}\\\\")
    table.append(r"\bottomrule\end{tabular}")
    return {
        PRODUCTS / "report.json": json.dumps(report, indent=2, sort_keys=True) + "\n",
        PRODUCTS / "report.md": "\n".join(lines) + "\n",
        GENERATED / "numbers.tex": tex,
        GENERATED / "application-table.tex": "\n".join(table) + "\n",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-from", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sample", help="Recompute and sample an archived case offline")
    parser.add_argument(
        "--recompute", action="store_true", help="Recompute all 55 final inputs; no timing claims"
    )
    args = parser.parse_args()
    if args.archive_from:
        archive(args.archive_from)
    runs, inputs, manifest = load_inputs()
    if args.recompute:
        print(json.dumps(recompute(runs, inputs), sort_keys=True))
        return
    if args.sample:
        from random import Random

        row = next(
            r for phase in PHASES[3:] for r in runs[phase]["rows"] if r["case"] == args.sample
        )
        raw = inputs[row["archived_input"]]
        data = ProbabilityInput(
            read_state(raw["input"]),
            tuple(tuple(Fraction(*p) for p in r) for r in raw["probabilities"]),
        )
        try:
            result = compile_cfg_sampler(
                source_grammar(row["kind"]), data.state, timeout_seconds=30
            ).evaluate(data)
            sample = result.sample(Random(20261006)) if result.valid_mass else ()
            print(
                json.dumps(
                    {
                        "status": result.status,
                        "valid_mass": str(result.valid_mass),
                        "omitted_mass": str(result.omitted_mass),
                        "scope": result.exactness_scope.to_dict(),
                        "tokens": sample,
                        "utf8": data.state.tokenizer_adapter.detokenize_bytes(sample).decode()
                        if sample
                        else None,
                    },
                    ensure_ascii=False,
                )
            )
        except CompilationLimit as error:
            print(json.dumps({"status": "TIMEOUT_WORK_LIMIT", "detail": str(error)}))
        return
    outputs = products(summarize(runs, inputs, manifest))
    for path, text in outputs.items():
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise ValueError(f"stale generated product: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print("M34: all inputs/configs/hashes, complete outcomes and 52 unchanged exact pairs checked")


if __name__ == "__main__":
    main()
