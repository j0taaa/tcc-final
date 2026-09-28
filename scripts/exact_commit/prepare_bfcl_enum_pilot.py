import argparse
import hashlib
import json
from pathlib import Path

from mwpc_research.schema_calls import schema_catalog

parser = argparse.ArgumentParser(description="Rebuild the schema-only BFCL pilot and coverage audit")
parser.add_argument("--check", action="store_true")
args = parser.parse_args()


def write(path, text):
    if args.check:
        assert path.read_text() == text, path
    else:
        path.write_text(text)


root = Path("results/raw/m24_external/bfcl")
rev = (root / "revision.txt").read_text().strip()
audit = {
    "upstream_commit": rev,
    "data_license": "Apache-2.0, upstream data/README.md",
    "selection": (
        "all properties are scalar enum or boolean; catalog <=512; no answer used for selection"
    ),
    "files": {},
    "current_calculator_language_coverage": 0,
}
chosen = []
answers = {
    r["id"]: r["ground_truth"]
    for r in [json.loads(s) for s in (root / "possible_answer.json").read_text().splitlines()]
}
for name in ["BFCL_v4_simple_python.json", "BFCL_v4_live_simple.json"]:
    raw = (root / name).read_bytes()
    rows = [json.loads(x) for x in raw.splitlines()]
    eligible = []
    exclusions = {}
    for r in rows:
        try:
            schema_catalog(r["function"][0])
        except ValueError as e:
            exclusions[str(e)] = exclusions.get(str(e), 0) + 1
            continue
        eligible.append(r["id"])
        chosen.append(
            {
                "id": r["id"],
                "instruction": "\n".join(m["content"] for turn in r["question"] for m in turn),
                "function": r["function"][0],
                "ground_truth": answers[r["id"]],
            }
        )
    audit["files"][name] = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "records": len(rows),
        "eligible_ids": eligible,
        "exclusions": exclusions,
    }
audit["answer_sha256"] = hashlib.sha256((root / "possible_answer.json").read_bytes()).hexdigest()
write(Path("docs/evidence/m24-bfcl-coverage.json"), json.dumps(audit, indent=2) + "\n")
cfg = json.loads(Path("configs/experiments/m24_policy_development_v1.json").read_text())
cfg.update(
    experiment_id="m24_bfcl_enum_pilot_v1",
    output_root="results/raw/m24_bfcl_enum_pilot_v1",
    phase=(
        "external schema-defined pilot: ALL 8 finite-enum cases among 658 BFCL examples; "
        "own strict AST evaluator, not official BFCL score"
    ),
    schema_calls=True,
    tasks=chosen,
    task_count=len(chosen),
    slots=32,
    max_forwards=32,
    dataset_commit=rev,
)
write(
    Path("configs/experiments/m24_bfcl_enum_pilot_v1.json"),
    json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
)
print(len(chosen))
