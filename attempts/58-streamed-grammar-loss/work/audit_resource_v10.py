"""AFTER-data independent arithmetic audit; no new timing or gate selection."""

import json
from collections import Counter
from pathlib import Path
from statistics import median


def main():
    base = Path(__file__).parent / "evidence" / "resource-v7-initial"
    config = json.loads((base / "config.json").read_text())
    decision = json.loads((base / "summary.json").read_text())
    rows = [json.loads(line) for line in (base / "records.jsonl").read_text().splitlines()]
    metrics, witnesses = {}, {}
    assert len(rows) == 680
    for n in config["Ns"]:
        metrics[str(n)] = {}
        for name in config["candidates"] + config["first_controls"]:
            selected = sorted(
                [
                    r
                    for r in rows
                    if r.get("N") == n and r.get("method") == name and r["kind"] == "warm"
                ],
                key=lambda r: r["rep"],
            )
            assert [r["rep"] for r in selected] == [0, 1, 2]
            assert all(r["status"] == "COMPLETE" for r in selected)
            metrics[str(n)][name] = {
                "wall_ns": [r["wall_ns"] for r in selected],
                "median_wall_ns": median(r["wall_ns"] for r in selected),
                "median_CPU_ns": median(r["CPU_ns"] for r in selected),
                "peak_workspace_bytes": max(r["workspace_bytes"] for r in selected),
            }
        for name in config["candidates"]:
            candidate = metrics[str(n)][name]
            speed_failure, memory_failure = [], []
            for control in config["first_controls"]:
                other = metrics[str(n)][control]
                if (
                    candidate["median_wall_ns"] > 0.8 * other["median_wall_ns"]
                    or candidate["peak_workspace_bytes"] > 1.10 * other["peak_workspace_bytes"]
                    or any(
                        a >= b for a, b in zip(candidate["wall_ns"], other["wall_ns"], strict=True)
                    )
                ):
                    speed_failure.append(control)
                if (
                    candidate["peak_workspace_bytes"] > 0.75 * other["peak_workspace_bytes"]
                    or candidate["median_wall_ns"] > 1.10 * other["median_wall_ns"]
                ):
                    memory_failure.append(control)
            assert speed_failure and memory_failure, (n, name)
            assert not decision["phase_I"]["cells"][name][str(n)]["possible"]
            witnesses[f"{n}/{name}"] = {
                "speed_failed_against": speed_failure,
                "memory_failed_against": memory_failure,
            }
    assert decision["status"] == "NEGATIVE_PREDECLARED_SHORTCUT"
    assert len(decision["unexecuted_controls"]) == 10
    assert all(r["status"] in ("COMPLETE", "PASS") for r in rows)
    report = {
        "status": "PASS",
        "scope": "AFTER-data arithmetic audit, not independent statistical confirmation",
        "measured_producer": config["producer"],
        "records": len(rows),
        "counts": dict(Counter(r["kind"] for r in rows)),
        "scalar_gradient_output_checks": sum(r.get("checked", 0) for r in rows),
        "max_scaled_error": max(r.get("max_scaled_error", 0) for r in rows),
        "all_candidate_state_pairs_rejected": len(witnesses),
        "unexecuted_controls": decision["unexecuted_controls"],
        "metrics": metrics,
        "negative_witnesses": witnesses,
    }
    target = base.parent / "resource-audit-v10.json"
    assert not target.exists(), "preserve previous audits"
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps({k: v for k, v in report.items() if k not in ("metrics", "negative_witnesses")})
    )


if __name__ == "__main__":
    main()
