"""Post-measurement audit; never imported by the frozen neural producer."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
FIRST = (
    "original_ids_sha256",
    "output",
    "status",
    "native_complete",
    "rejections",
    "recovery",
    "queries",
)


def key(row):
    return tuple(row[k] for k in ("id", "method", "temperature", "seed"))


def unique(rows):
    result = {key(row): row for row in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate measurement identity")
    return result


def parsed(text):
    def object_hook(items):
        if len({k for k, _ in items}) != len(items):
            raise ValueError("duplicate JSON key")
        return dict(items)

    def constant(value):
        raise ValueError(value)

    return json.loads(
        text,
        parse_int=Fraction,
        parse_float=Fraction,
        parse_constant=constant,
        object_pairs_hook=object_hook,
    )


def audit(raw, gold):
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    io = unique(
        [json.loads(line) for line in raw.with_suffix(".io.jsonl").read_text().splitlines()]
    )
    indexed = unique(rows)
    metadata = json.loads(raw.with_suffix(".metadata.json").read_text())
    manifest = json.loads((HERE / "gsm-inputs-v4.json").read_text())
    spec = metadata["config"]
    ids = {r["id"] for r in manifest["selections"]["train"]}
    expected = {
        (i, m["id"], t, spec["development_seeds"][0])
        for i in ids
        for m in spec["methods"]
        for t in spec["temperatures"]
    } | {(i, "deterministic", 0.0, spec["development_seeds"][0]) for i in ids}
    if set(indexed) != expected or set(io) != expected:
        raise ValueError("audit requires the complete preregistered pilot and IO journal")
    original_gold = gold.read_bytes()
    if hashlib.sha256(original_gold).hexdigest() != manifest["files"]["train"]["sha256"]:
        raise ValueError("wrong public train gold; test labels are never opened")
    source = [json.loads(line) for line in original_gold.splitlines()]
    answers = {
        i: Fraction(
            source[int(i.split(":")[1])]["answer"].rsplit("####", 1)[1].strip().replace(",", "")
        )
        for i in ids
    }
    groups = defaultdict(list)
    mismatches = []
    status = Counter()
    for row in rows:
        independently_correct = []
        for sample in row["pair"]:
            status[sample["status"]] += 1
            try:
                value = parsed(sample["output"])
                valid = (
                    isinstance(value, dict)
                    and set(value) == {"answer"}
                    and isinstance(value["answer"], Fraction)
                )
                correct = valid and value["answer"] == answers[row["id"]]
            except (ValueError, TypeError, ZeroDivisionError):
                valid, correct = False, False
            if (valid, correct) != (sample["typed_valid"], sample["correct"]):
                raise ValueError("independent verifier mismatch")
            independently_correct.append(correct)
        if any(independently_correct) != row["pass2"]:
            raise ValueError("coverage mismatch")
        if row["method"] != "deterministic":
            original = indexed[row["id"], "iid2", row["temperature"], row["seed"]]
            if tuple(row["pair"][0][k] for k in FIRST) != tuple(
                original["pair"][0][k] for k in FIRST
            ):
                mismatches.append(key(row))
        row = dict(row)
        for measure in ("wall", "cpu"):
            row[f"full_{measure}"] += io[key(row)][f"output_{measure}"]
        groups[row["method"], row["temperature"]].append(row)
    metrics = []
    for (method, temperature), group in sorted(groups.items()):
        covered = sum(r["pass2"] for r in group)
        data = dict(
            method=method,
            temperature=temperature,
            requests=len(group),
            covered=covered,
            coverage=covered / len(group),
            forwards=sum(s["forwards"] for r in group for s in r["pair"]),
            auxiliary_rows=sum(r.get("auxiliary_rows", 0) for r in group),
        )
        for measure in ("wall", "cpu"):
            total = sum(r[f"full_{measure}"] for r in group)
            data[f"total_{measure}"] = total
            data[f"{measure}_per_correct"] = total / covered if covered else None
        metrics.append(data)
    gains = []
    for m in spec["methods"]:
        if m.get("candidate"):
            for temperature in spec["temperatures"]:
                candidate = next(
                    r for r in metrics if (r["method"], r["temperature"]) == (m["id"], temperature)
                )
                control = next(
                    r for r in metrics if (r["method"], r["temperature"]) == ("iid2", temperature)
                )
                gains.append(
                    dict(
                        method=m["id"],
                        temperature=temperature,
                        gain=candidate["coverage"] - control["coverage"],
                    )
                )
    screened_out = not any(r["gain"] >= 0.02 for r in gains)
    return dict(
        rows=len(rows),
        outputs=sum(status.values()),
        statuses=dict(status),
        first_mismatches=mismatches,
        metrics=metrics,
        candidate_gains=gains,
        negative_pilot_screen=screened_out,
        source_commit=metadata["source_commit"],
        note=(
            "One seed: negative resource screen, not statistical refutation. "
            "No heldout labels or positive confirmation."
        ),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--train-gold", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.raw, args.train_gold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "rows",
                    "outputs",
                    "first_mismatches",
                    "negative_pilot_screen",
                    "candidate_gains",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
