#!/usr/bin/env python3
"""Select one secondary budget from complete development, before confirmation."""

import argparse
import hashlib
import json
from pathlib import Path

from summarize_policy_screen import summarize

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = ROOT / "configs/experiments"
DEVELOPMENT = ROOT / "docs/artifacts/raw/m25_grounded_v1/development"


def selected_budget(table):
    candidates = [row for row in table if row["method"] in ("exact_b4", "exact_b64")]
    if len(candidates) != 2 or len({row["n"] for row in candidates}) != 1:
        raise ValueError("Both complete budget policies are required")
    # Correctness takes priority; latency and stable name settle development ties.
    return min(
        candidates, key=lambda row: (-row["correct"], row["median_total_ms"], row["method"])
    )["method"]


def build():
    development, _ = summarize(DEVELOPMENT)
    metadata = [json.loads((DEVELOPMENT / "metadata.json").read_text())]
    if (DEVELOPMENT / "resume_segments.jsonl").exists():
        metadata += [
            json.loads(line)["metadata"]
            for line in (DEVELOPMENT / "resume_segments.jsonl").read_text().splitlines()
        ]
    choice = selected_budget(development["table"])
    base = json.loads((CONFIGS / "m25_grounded_confirmation_v1.json").read_text())
    omitted = "exact_b64" if choice == "exact_b4" else "exact_b4"
    policies = [policy for policy in base["policies"] if policy["name"] != omitted]
    outputs = {}
    for repeat in (False, True):
        identifier = "m25_grounded_confirmation" + ("_repeat" if repeat else "") + "_v2"
        config = {
            **base,
            "experiment_id": identifier,
            "output_root": "results/raw/" + identifier,
            "policies": list(reversed(policies)) if repeat else policies,
            "phase": "frozen grounded external confirmation; "
            + ("reversed method order" if repeat else "first timing repetition"),
            "development_selected_budget": choice,
            "selection_rule": "maximum development correct count, then minimum median total "
            "latency, then method name; primary confidence 0.8 unchanged",
        }
        outputs[CONFIGS / (identifier + ".json")] = config
    outputs[ROOT / "docs/evidence/m25-confirmation-freeze.json"] = {
        "development_manifest_sha256": hashlib.sha256(
            (DEVELOPMENT / "manifest.json").read_bytes()
        ).hexdigest(),
        "development_source_commits": sorted({source["git_commit"] for source in metadata}),
        "development_table": development["table"],
        "selected_budget": choice,
        "omitted_budget": omitted,
        "primary_method": base["primary_method"],
        "primary_comparator": base["primary_comparator"],
        "rule": "Maximum development accuracy among budget four/64, then minimum total "
        "latency. Confidence 0.8 is retained as the frozen primary, irrespective of its rank.",
        "controls": [p["name"] for p in policies if p["name"] not in (choice, "confidence_0.8")],
        "confirmation_cases": len(base["tasks"]),
        "runs_per_repetition": len(base["tasks"]) * len(policies),
        "support_changes": False,
        "limitations": "Selection uses development only. It does not establish superiority; "
        "all eligible confirmation cases and strong controls remain.",
    }
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        observed = list((ROOT / "results/raw").glob("m25_grounded_confirmation*/**/results.jsonl*"))
        for name in ("confirmation", "repeat"):
            observed += list((DEVELOPMENT.parent / name).glob("results.jsonl*"))
        if observed:
            raise ValueError("Confirmation outputs exist: do not reselect from observed results")
    for path, value in build().items():
        text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            assert path.read_text() == text, path
        else:
            path.write_text(text)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
