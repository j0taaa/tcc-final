"""Validate every stored replay path and report losses and censored queries."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from scripts.exact_commit.build_cfg_posterior_results import load_inputs

from mwpc_exact.conflict_proof import read_state


def summarize(folder):
    rows = [json.loads(line) for line in (folder / "rows.jsonl").read_text().splitlines()]
    runs, inputs, _ = load_inputs()
    expected = {r["case"] for r in runs["json-model"]["rows"]}
    assert {r["case"] for r in rows} == expected, "missing predeclared cases"
    queries = [r for r in rows if r["stage"] == "query"]
    groups, stored_paths, accepted_draws = {}, 0, 0
    for row in queries:
        state = read_state(inputs[row["archived_input"]]["input"])
        assert len(row["order"]) == row["k"] == len(set(row["order"]))
        assert set(map(int, row["observed"])) == set(row["order"])
        accepted_draws += max((b["accepted"] for b in row["batches"]), default=0)
        for batch in row["batches"]:
            assert len(batch["original_token_paths"]) == batch["accepted"] <= batch["attempts"]
            for path in batch["original_token_paths"]:
                assert len(path) == len(state.canvas)
                assert all(
                    t in support for t, support in zip(path, state.support.rows, strict=True)
                )
                assert all(t is None or path[i] == t for i, t in enumerate(state.canvas))
                assert all(path[int(i)] == t for i, t in row["observed"].items())
                text = b"".join(state.tokenizer_adapter.emissions[t] for t in path)
                json.loads(
                    text.decode(),
                    parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)),
                )
                stored_paths += 1
        key = (row["case"], row["rate_power"], row["k"], row["repetition"], row["method"])
        assert key not in groups, "duplicate query"
        groups[key] = row
    events = {key[:3] for key in groups}
    assert len(queries) == len(events) * 9, "missing method/repetition rows"
    methods = sorted({row["method"] for row in queries})
    metrics = {}
    for method in methods:
        selected = [r for r in queries if r["method"] == method]
        batches = {}
        for size in (1, 4, 16):
            complete = [b for r in selected for b in r["batches"] if b["accepted"] == size]
            batches[str(size)] = {
                "completed_prefixes": len(complete),
                "median_query_seconds": median(b["query_seconds"] for b in complete)
                if complete
                else None,
                # Enumeration uses direct JSON recognition and needs no CFG
                # compilation for a standalone conditional query.
                "median_standalone_cold_seconds": median(
                    b["query_seconds"] if method == "enumeration" else b["cold_seconds"]
                    for b in complete
                )
                if complete
                else None,
            }
        metrics[method] = {
            "statuses": dict(Counter(r["status"] for r in selected)),
            "batches": batches,
        }
    comparisons = []
    for alternative in ("rejection_with_f_L_envelope", "enumeration"):
        for size in (1, 4, 16):
            ratios = []
            for event in sorted(events):
                values = defaultdict(list)
                for repetition in range(3):
                    for method in ("certified_tangent_mixture", alternative):
                        row = groups[(*event, repetition, method)]
                        batch = next((b for b in row["batches"] if b["accepted"] == size), None)
                        if batch:
                            values[method].append(batch["query_seconds"])
                # Do not select the faster surviving repetitions of a timeout.
                if all(len(values[m]) == 3 for m in ("certified_tangent_mixture", alternative)):
                    ratio = median(values[alternative]) / median(
                        values["certified_tangent_mixture"]
                    )
                    ratios.append(
                        {"case": event[0], "rate_power": event[1], "k": event[2], "ratio": ratio}
                    )
            comparisons.append(
                {
                    "alternative": alternative,
                    "batch": size,
                    "paired_events": len(ratios),
                    "mixture_faster_events": sum(r["ratio"] > 1 for r in ratios),
                    "median_alternative_over_mixture": median(r["ratio"] for r in ratios)
                    if ratios
                    else None,
                    "events": ratios,
                }
            )
    return {
        "cases": len(expected),
        "observed_events": len(events),
        "query_rows": len(queries),
        "compilation_refusals": [r for r in rows if r["stage"] == "compilation"],
        "independently_checked_stored_path_occurrences": stored_paths,
        "accepted_draws_in_recorded_prefixes": accepted_draws,
        "methods": metrics,
        "paired_comparisons": comparisons,
        "unresolved_queries": [
            {k: r[k] for k in ("case", "rate_power", "k", "method", "repetition", "error")}
            for r in queries
            if r["status"] == "unresolved"
        ],
        "files_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (folder / "metadata.json", folder / "rows.jsonl")
        },
        "scope": (
            "all frozen model inputs; timed-out prefixes remain censored; "
            "no training or novelty claim"
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.replay)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("cases", "observed_events", "query_rows", "methods")}))
