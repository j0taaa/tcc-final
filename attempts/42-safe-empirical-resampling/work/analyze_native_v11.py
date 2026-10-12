"""Summarize every native diagnostic record; not a performance-win gate."""

import json
from pathlib import Path

HERE = Path(__file__).parent
source = HERE / "evidence/native-boundary-v11.json"
data = json.loads(source.read_text())
results, forwards = [], 0
for record in data["records"]:
    sources = record["sources"]
    assert len(sources) == 8 and all("root_boundary" in row for row in sources)
    assert all("final" in row for row in sources[:2])
    row = dict(
        id=record["id"],
        first_roots=[s["first_yield"]["root"] for s in sources],
        root_labels=[s["root_boundary"]["root"] for s in sources],
    )
    row["full_completion_status"] = []
    for completed in sources[:2]:
        try:
            json.loads(completed["text"])
            valid = True
        except ValueError:
            valid = False
        row["full_completion_status"].append(
            dict(
                native_complete=completed["final"]["complete"],
                syntactic_json=valid,
                executable_json=completed["executable_json"],
            )
        )
    for clock in ("wall", "cpu"):
        prefix = [s["first_cost"][clock] + s["root_additional_cost"][clock] for s in sources]
        tail = sum(s["continuation_cost"][clock] for s in sources[:2])
        common = record["common_setup"][clock]
        two = common + sum(prefix[:2]) + tail + sum(s["disposal_cost"][clock] for s in sources[:2])
        eight = common + sum(prefix) + tail + sum(s["disposal_cost"][clock] for s in sources)
        row[clock] = dict(
            observed_prefix_mean=sum(prefix) / 8,
            observed_full_mean=(sum(prefix[:2]) + tail) / 2,
            diagnostic_two_cost=two,
            diagnostic_eight_cost=eight,
            diagnostic_cost_ratio=eight / two,
        )
    forwards += 1 + sum(
        s["first_forwards"] + s["root_additional_forwards"] + s.get("continuation_forwards", 0)
        for s in sources
    )
    results.append(row)
out = dict(
    scope=(
        "Four OLD development inputs,32 new native sources/8 completions. "
        "No coupling, golds, independent confirmation or statistical latency gate."
    ),
    source_records=32,
    completed_original_sources=8,
    new_model_forwards=forwards,
    decision=(
        "Root-known source boundary is too late in these diagnostics. "
        "All first-yield roots are pending; no useful cheap-root coupling established."
    ),
    results=results,
)
(HERE / "evidence/native-boundary-summary-v11.json").write_text(json.dumps(out, indent=2) + "\n")
print({k: v for k, v in out.items() if k != "results"})
