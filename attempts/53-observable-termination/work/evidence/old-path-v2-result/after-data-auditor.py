"""AFTER-data reconstruction of earliest stops/cache counts, no new certificates."""

import argparse
import json
from pathlib import Path


def run(capture, screen):
    rows = [json.loads(s) for s in (capture / "rows.jsonl").read_text().splitlines()]
    states = [json.loads(s) for s in (screen / "states.jsonl").read_text().splitlines()]
    report = json.loads((screen / "summary.json").read_text())
    assert len(rows) == 16 and len(states) == 86 and report["status"] == "NECESSITY_NEGATIVE"
    methods = ("original", "cheap_prefix", "raw_singleton", "projected_singleton")
    logical = {m: 0 for m in methods}
    heads = {m: set() for m in methods}
    paths = []
    for row in rows:
        subset = [s for s in states if (s["case"], s["replica"]) == (row["case"], row["replica"])]
        assert [s["step"] for s in subset] == list(range(len(row["transitions"]) + 1))
        first = {}
        for method in methods:
            stop = next(
                s["step"]
                for s in subset
                if s["flags"][method] and s["available_previous_witness"] is not None
            )
            first[method] = stop
            logical[method] += stop
            heads[method].update(t["head"] for t in row["transitions"] if t["step"] < stop)
        for state in subset:
            step = state["step"]
            fixed = dict(state["fixed"])
            expected = (
                dict(row["transitions"][step]["fixed_before"])
                if step < len(row["transitions"])
                else dict(row["fixed_terminal"])
            )
            assert fixed == expected and state["status"] == "PASS"
            witness = state["available_previous_witness"]
            assert witness == (
                None if step == 0 else row["transitions"][step - 1]["proposal_prefix"]
            )
            if witness is not None:
                assert all(i < len(witness) and witness[i] == v for i, v in fixed.items())
            for result in state["results"]:
                assert result["kind"] in ("ONE", "MANY")
        paths.append(
            {
                "case": row["case"],
                "replica": row["replica"],
                "first_stop": first,
                "original_steps": len(row["transitions"]),
            }
        )
    unique = {m: len(h) + 1 for m, h in heads.items()}
    assert paths == report["path_results"] and logical == report["logical_forward_requests"]
    assert unique == report["unique_heads_plus_common_warmup"]
    ratio = unique["projected_singleton"] / min(unique[m] for m in methods[:-1])
    strict = [
        q
        for q in range(8)
        if sum(r["first_stop"]["projected_singleton"] for r in paths if r["case"] == q)
        < sum(r["first_stop"]["cheap_prefix"] for r in paths if r["case"] == q)
    ]
    assert (
        ratio == report["ratio_to_strongest_control"]
        and strict == report["strict_questions_vs_cheap_prefix"]
    )
    assert ratio > 0.8 and len(strict) < 2
    assert (
        report["new_model_forwards"]
        == report["new_auxiliary_words"]
        == report["new_decoder_paths"]
        == report["updates"]
        == 0
    )
    result = {
        "status": "PASS",
        "scope": "AFTER-data state/witness/count audit, not independent evaluation",
        "paths": 16,
        "states": 86,
        "unique_heads_plus_common_warmup": unique,
        "ratio_to_strongest_control": ratio,
        "new_model_forwards": 0,
        "new_certificates": 0,
    }
    (screen / "post-screen-independent-count-audit.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("capture", "screen"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    run(a.capture, a.screen)
