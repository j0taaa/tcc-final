"""Offline audit AFTER closed72 records; golds never feed the sampler."""

import hashlib
import json
import statistics
import subprocess
from collections import Counter
from fractions import Fraction
from pathlib import Path

from .native_task import evaluate

HERE = Path(__file__).parent
MASK = 126336


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    capture = HERE / "evidence/native-v4.jsonl"
    metadata = json.loads((HERE / "evidence/native-v4.metadata.json").read_text())
    cfg = metadata["config"]
    inputs = json.loads((HERE / "native-inputs-v3.json").read_text())["records"]
    rows = [json.loads(line) for line in capture.read_text().splitlines()]
    expected = {
        (r["id"], rep, m)
        for r in inputs
        for rep in range(cfg["replicates"])
        for m in cfg["methods"]
    }
    assert len(rows) == len(expected) == 72
    assert {(r["id"], r["rep"], r["method"]) for r in rows} == expected
    assert digest(HERE / "native-inputs-v3.json") == cfg["inputs_sha256"]
    for name, sha in metadata["sources"].items():
        path = HERE / name
        assert digest(path) == sha
        relative = path.relative_to(Path.cwd())
        assert (
            subprocess.check_output(["git", "show", f"{metadata['source_commit']}:{relative}"])
            == path.read_bytes()
        )
    golds = json.loads((HERE / "native-golds-v5.json").read_text())
    assert golds["capture_sha256"] == digest(capture)
    answers = {k: Fraction(v) for k, v in golds["answers"].items()}
    prefix_lengths = {f["id"]: f["prefix_tokens"] for f in metadata["frames"]}
    originals, firsts, keys = {}, {}, set()
    original_eos_suffix_rewrites = []
    methods = {}
    invalid = []
    for row in rows:
        identifier, rep, method = row["id"], row["rep"], row["method"]
        draws, selected = row["draws"], [row["draws"][i] for i in row["selected"]]
        assert len(draws) == row["calls"] and row["selected"][0] == 0
        assert len(selected) == (3 if method == "iid3" else 2)
        assert all(0 <= d["seed"] < cfg["source_size"] for d in draws)
        if method not in ("iid2", "iid3", "seed_half"):
            assert len({d["seed"] for d in draws}) == len(draws)
        if method == "seed_half":
            assert selected[1]["seed"] == (selected[0]["seed"] + 2**31) % cfg["source_size"]
        if not row["first_preserved"] or not row["prefix_zero_forward"]:
            invalid.append((identifier, rep, method, "boundary"))
        for draw in draws:
            if draw["status"] == "ERROR":
                invalid.append((identifier, rep, method, draw.get("error_type")))
            else:
                ids = draw["first_ids"][prefix_lengths[identifier] :]
                key = next(([i, t] for i, t in enumerate(ids) if t != MASK), ["NO_PROGRESS"])
                assert key == draw["key"] and draw["prefix_forwards"] == 0
                keys.add(tuple(key))
        first_key = identifier, rep
        first_payload = selected[0]["seed"], selected[0]["status"], selected[0]["ids"]
        assert firsts.setdefault(first_key, first_payload) == first_payload
        values, correct = [], []
        for draw in selected:
            source = identifier, draw["seed"]
            original = draw["status"], draw["ids"]
            assert originals.setdefault(source, original) == original
            ending = next(
                (i for i, t in enumerate(draw["ids"]) if t in (126081, 126348)), len(draw["ids"])
            )
            for i, (initial, final) in enumerate(
                zip(draw.get("first_ids", ()), draw["ids"], strict=True)
            ):
                if initial != MASK and initial != final:
                    assert initial == 126081 and final == 126348 and i > ending
                    original_eos_suffix_rewrites.append((identifier, rep, method, i))
            try:
                value = evaluate(draw["text"]) if draw["status"] == "COMPLETE" else None
            except (ValueError, ZeroDivisionError, RecursionError, TypeError):
                value = None
            values.append(str(value) if value is not None else "FAIL")
            correct.append(value == answers[identifier])
        result = methods.setdefault(
            method,
            dict(
                rows=0,
                calls=0,
                forwards=0,
                queries=0,
                pass_k=0,
                differing_values=0,
                completed=0,
                errors=0,
                status=Counter(),
                wall=[],
                cpu=[],
                cold_wall=[],
                peak_allocated=[],
                neural_wall=[],
            ),
        )
        result["rows"] += 1
        for field in ("calls", "forwards", "queries"):
            result[field] += row[field]
        result["pass_k"] += any(correct)
        result["differing_values"] += len(set(values)) > 1
        result["completed"] += sum(d["status"] == "COMPLETE" for d in selected)
        result["errors"] += sum(d["status"] == "ERROR" for d in draws)
        result["status"].update(d["status"] for d in selected)
        result["wall"].append(row["warm"]["wall"])
        result["cpu"].append(row["warm"]["cpu"])
        result["cold_wall"].append(row["cold"]["wall"])
        result["peak_allocated"].append(row["memory"]["peak_allocated"])
        result["neural_wall"].append(row["neural"]["wall"])
    summary = {}
    for method, result in methods.items():
        series = {
            k: result.pop(k) for k in ("wall", "cpu", "cold_wall", "peak_allocated", "neural_wall")
        }
        result.update({"median_" + k: statistics.median(v) for k, v in series.items()})
        result["correct_requests_per_warm_second"] = result["pass_k"] / sum(series["wall"])
        summary[method] = result
    report = dict(
        scope="DESCRIPTIVE two-replicate external development pilot; no statistical victory",
        capture_sha256=digest(capture),
        metadata_sha256=digest(HERE / "evidence/native-v4.metadata.json"),
        producer=metadata["source_commit"],
        rows=len(rows),
        invalid_native_contract=invalid,
        distinct_first_keys=len(keys),
        original_seed_results_audited=len(originals),
        common_first_literal_preserved=len(firsts),
        original_eos_suffix_rewrites=len(original_eos_suffix_rewrites),
        new_forwards_including_four_common_heads=4 + sum(r["forwards"] for r in rows),
        methods=summary,
    )
    (HERE / "evidence/native-audit-v5.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# A39 full-native first-yield pilot — complete descriptive audit",
        "",
        "All72 planned records captured before gold export; original producer `"
        + metadata["source_commit"]
        + "`.",
        f"{report['new_forwards_including_four_common_heads']} new forwards "
        "including four shared initial heads. "
        f"{len(keys)} different first keys; eight common first trajectories "
        "unchanged across nine methods.",
        "All per-prefix checks require zero extra forwards; "
        "all repeated-seed full IDs independently audited.",
        f"Original EOS-to-PAD rewrites strictly after the final terminator: "
        f"{len(original_eos_suffix_rewrites)} across selected outcomes; "
        "other first commitments preserved. This is the native suffix policy, "
        "not an adapter change.",
        "",
        "| Method | Calls | New forwards (warm) | Median wall s | Median CPU s | "
        "Median cold s | Pass@K /8 | Peak allocated GiB |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in cfg["methods"]:
        s = summary[method]
        lines.append(
            f"| {method} | {s['calls']} | {s['forwards']} | {s['median_wall']:.3f} | "
            f"{s['median_cpu']:.3f} | {s['median_cold_wall']:.3f} | {s['pass_k']} | "
            f"{s['median_peak_allocated'] / 2**30:.3f} |"
        )
    lines += [
        "",
        "Iid3 returns THREE outputs; others return TWO. Gold labels are absent from selection.",
        "These eight paired requests do NOT establish population semantic/latency improvement.",
        "Original failures, all helpers, model queries, dense noise, parsing, "
        "copies and memory are retained/charged.",
        "A mathematical expected-forward equality is NOT equal measured "
        "forwards in each sampled pair or equal wall time.",
        f"Invalid native-contract/error records: {len(invalid)}. "
        "No publication/priority confirmation follows.",
    ]
    (HERE / "native-audit-v5.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
