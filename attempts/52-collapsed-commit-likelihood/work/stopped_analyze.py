"""Attach already KNOWN V5 labels only after the stopped resource capture closes."""

import argparse
import json
from pathlib import Path

from .consumer_resource import HERE, sha, write_json
from .two_stage import answer_equal


def run(capture, labels_path, output):
    output.mkdir(parents=True, exist_ok=False)
    status = json.loads((capture / "summary.json").read_text())
    protocol = json.loads((capture / "protocol.json").read_text())
    if status["status"] not in ("RESOURCE_PASS_AWAIT_KNOWN_LABEL_SIGNAL", "RESOURCE_GATE_NEGATIVE"):
        write_json(
            output / "summary.json", {"status": "NEGATIVE_CAPTURE_INCOMPLETE", "capture": status}
        )
        return
    rows = [json.loads(s) for s in (capture / "rows.jsonl").read_text().splitlines()]
    if len(rows) != 16:
        raise ValueError("all16 resource outcomes must remain in the record")
    if sha(labels_path) != protocol["known_label_file_sha256"]:
        raise ValueError("known label pin mismatch")
    original = json.loads(labels_path.read_text())
    labels = original["labels"]
    inputs = json.loads((HERE / "consumer-inputs-v4.json").read_text())["questions"]
    if [x["id"] for x in labels] != [x["id"] for x in inputs]:
        raise ValueError("question/known-label identity mismatch")
    answers = []
    per_case = []
    for case in range(8):
        subset = sorted((r for r in rows if r["case"] == case), key=lambda r: r["replica"])
        if [r["replica"] for r in subset] != [0, 1]:
            raise ValueError("missing/duplicate fixed replica")
        correct = []
        one = []
        for row in subset:
            reward = (
                answer_equal(row["json"], labels[case]["answer"])
                if row["status"] == "COMPLETE"
                else None
            )
            paired = (
                answer_equal(row["paired_one_shot_json"], labels[case]["answer"])
                if "paired_one_shot_json" in row
                else None
            )
            correct.append(reward)
            one.append(paired)
            answers.append(
                {
                    "case": case,
                    "replica": row["replica"],
                    "status": row["status"],
                    "candidate_correct": reward,
                    "paired_one_shot_correct": paired,
                }
            )
        per_case.append(
            {
                "case": case,
                "input_id": inputs[case]["id"],
                "candidate_correct": correct,
                "paired_one_shot_correct": one,
                "candidate_has_correct": any(x is True for x in correct),
            }
        )
    signal = sum(r["candidate_has_correct"] for r in per_case)
    resource_ok = status["status"] == "RESOURCE_PASS_AWAIT_KNOWN_LABEL_SIGNAL"
    passed = resource_ok and signal >= 2
    report = {
        "status": "RESOURCE_SIGNAL_PASS" if passed else "NEGATIVE_RESOURCE_OR_SIGNAL",
        "scope": (
            "known-development feasibility only, "
            "no semantic superiority or independent confirmation"
        ),
        "resource_condition": resource_ok,
        "signal_questions": signal,
        "candidate_complete_outputs": sum(r["candidate_correct"] is not None for r in answers),
        "candidate_correct_outputs": sum(r["candidate_correct"] is True for r in answers),
        "paired_one_shot_correct_outputs": sum(
            r["paired_one_shot_correct"] is True for r in answers
        ),
        "per_case": per_case,
        "updates": 0,
        "competitive_cost_variance_gate": False,
        "next": "may consider a NEW frozen strong-control complete-cost variance protocol"
        if passed
        else "close this initialization/application; no tuning or training campaign",
    }
    write_json(output / "summary.json", report)
    write_json(
        output / "known-labels-provenance.json",
        {
            "labels_source_sha256": sha(labels_path),
            "labels_previously_known": True,
            "capture_rows_sha256": sha(capture / "rows.jsonl"),
            "labels": labels,
        },
    )
    write_json(output / "reward-rows.json", answers)
    print(json.dumps({k: v for k, v in report.items() if k != "per_case"}, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture", type=Path, required=True)
    ap.add_argument("--known-labels", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    run(args.capture, args.known_labels, args.output)
