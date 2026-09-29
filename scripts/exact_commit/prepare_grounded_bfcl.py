#!/usr/bin/env python3
"""Freeze M25 eligibility/splits from schemas, then attach answers for evaluation."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from mwpc_research.grounded_calls import eligible_query, grounded_catalog, grounded_grade

ROOT = Path(__file__).resolve().parents[2]


def build():
    old = ROOT / "results/raw/m24_external/bfcl"
    inputs = [
        (
            "BFCL_v4_simple_python.json",
            ROOT / "results/raw/m25_external/simple_python_answers.json",
        ),
        ("BFCL_v4_live_simple.json", old / "possible_answer.json"),
    ]
    selected, audit = (
        [],
        {
            "sources": {},
            "selection": "M25 scalar query rule; schemas only",
            "split_seed": "m25-250929:",
        },
    )
    for name, answer_path in inputs:
        raw = (old / name).read_bytes()
        records = [json.loads(line) for line in raw.splitlines()]
        eligible = [r for r in records if eligible_query(r["function"])]
        audit["sources"][name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "records": len(records),
            "eligible_ids": [r["id"] for r in eligible],
            "answer_sha256": hashlib.sha256(answer_path.read_bytes()).hexdigest(),
        }
        # Eligibility is determined before associating labels.
        answers = {
            r["id"]: r["ground_truth"]
            for r in map(json.loads, answer_path.read_text().splitlines())
        }
        selected.extend(
            {
                "id": r["id"],
                "instruction": "\n".join(m["content"] for turn in r["question"] for m in turn),
                "function": r["function"][0],
                "ground_truth": answers[r["id"]],
            }
            for r in eligible
        )
    families = sorted(
        {t["function"]["name"].casefold() for t in selected},
        key=lambda s: hashlib.sha256(("m25-250929:" + s).encode()).hexdigest(),
    )
    dev = set(families[:8])
    audit["development_families"] = sorted(dev)
    audit["confirmation_families"] = sorted(set(families) - dev)
    coverage = []
    for t in selected:
        try:
            calls = grounded_catalog(t["function"], t["instruction"])
            coverage.append(
                {
                    "id": t["id"],
                    "catalog_size": len(calls),
                    "answer_in_catalog": any(
                        grounded_grade(c, t["function"], t["ground_truth"]) for c in calls
                    ),
                    "support_status": "represented",
                }
            )
        except ValueError as exc:
            coverage.append({"id": t["id"], "support_status": "unsupported", "reason": str(exc)})
    audit["coverage_after_selection"] = coverage
    audit["eligible_cases"] = len(selected)
    audit["family_count"] = len(families)
    base = json.loads((ROOT / "configs/experiments/m24_bfcl_enum_pilot_v1.json").read_text())
    base.update(
        grounded_calls=True,
        slots=64,
        max_forwards=64,
        max_generation_seconds=120,
        primary_method="confidence_0.8",
        primary_comparator="epic_lexical_32",
        support=(
            "question spans up to six words, schema enums/defaults, question numbers; "
            "top96 strings; byte CFG and finite 64 slots; exact_on_support"
        ),
        seed=250929,
    )
    base["policies"] = [
        {"name": "confidence_0.8", "kind": "confidence", "threshold": 0.8},
        {"name": "exact_b4", "kind": "exact", "proposal_budget": 4},
        {"name": "exact_b64", "kind": "exact", "proposal_budget": 64},
        {
            "name": "greedy_confidence_0.8",
            "kind": "confidence",
            "threshold": 0.8,
            "selector": "greedy",
        },
        *[
            {"name": f"epic_lexical_{n}", "kind": "epic", "method": f"epic_lexical_{n}"}
            for n in (8, 32, 64)
        ],
        *[{"name": f"catalog_map{n}", "kind": "catalog_map", "commit_cap": n} for n in (8, 64)],
    ]
    outputs = {ROOT / "docs/evidence/m25-grounding-coverage.json": audit}
    for split in ("development", "confirmation"):
        tasks = [
            t
            for t in selected
            if (t["function"]["name"].casefold() in dev) == (split == "development")
        ]
        c = {
            **base,
            "tasks": tasks,
            "task_count": len(tasks),
            "phase": f"grounded external {split}; family-disjoint, own scalar AST checker",
        }
        c["experiment_id"] = f"m25_grounded_{split}_v1"
        c["output_root"] = "results/raw/" + c["experiment_id"]
        outputs[ROOT / f"configs/experiments/{c['experiment_id']}.json"] = c
        if split == "development":
            smoke = {
                **c,
                "tasks": tasks[:2],
                "task_count": min(2, len(tasks)),
                "experiment_id": "m25_grounded_smoke_v1",
                "output_root": "results/raw/m25_grounded_smoke_v1",
                "phase": "grounded external development smoke; not confirmation",
            }
            outputs[ROOT / "configs/experiments/m25_grounded_smoke_v1.json"] = smoke
    return outputs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    for path, value in build().items():
        text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            assert path.read_text() == text, path
        else:
            path.write_text(text)
        if "task_count" in value:
            print(path.name, value["task_count"])
        elif "coverage_after_selection" in value:
            print(
                "audit",
                value["eligible_cases"],
                Counter(r["support_status"] for r in value["coverage_after_selection"]),
                sum(r.get("answer_in_catalog", False) for r in value["coverage_after_selection"]),
            )


if __name__ == "__main__":
    main()
