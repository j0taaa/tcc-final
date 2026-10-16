"""Post-capture V10 consistency audit, written AFTER outputs; no model calls."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

import numpy as np

from .consumer_resource import write_json
from .llada_tokenizer_v10 import EOS, MASK, VOCABULARY

WIDTH = 64


def run(capture, analysis, tokenizer_dir, capture_pid):
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(tokenizer_dir / "tokenizer.json"))
    rows = [json.loads(x) for x in (capture / "rows.jsonl").read_text().splitlines()]
    events = [json.loads(x) for x in (capture / "events.jsonl").read_text().splitlines()]
    labels = json.loads((analysis / "known-labels-provenance.json").read_text())["labels"]
    rewards = json.loads((analysis / "reward-rows.json").read_text())
    report = json.loads((capture / "summary.json").read_text())
    protocol = json.loads((capture / "protocol.json").read_text())
    assert len(rows) == 16 and {(r["case"], r["replica"]) for r in rows} == {
        (c, r) for c in range(8) for r in range(2)
    }
    transitions, answers, correct, names = 0, 0, 0, {"warmup"}
    names.update(f"root-{case:02d}" for case in range(8))
    error_maxima = dict.fromkeys(("log_probability", "alpha", "beta", "anchor"), 0.0)
    lengths, steps = [], []
    for row in rows:
        assert row["status"] == "COMPLETE"
        fixed = {}
        for t in row["transitions"]:
            before = dict(t["fixed_before"])
            after = dict(t["fixed_after"])
            action = dict(t["action"])
            proposal = t["proposal_prefix"]
            assert before == fixed and action and not (before.keys() & action.keys())
            assert after == {**before, **action}
            assert proposal[-1] == EOS and EOS not in proposal[:-1]
            assert all(i < len(proposal) and proposal[i] == v for i, v in after.items())
            eos = next((i for i, v in before.items() if v == EOS), None)
            extent = eos + 1 if eos is not None else WIDTH
            assert t["prefix_extent"] == extent
            positions = [i for i in range(extent) if i not in before]
            assert t["queried_positions"] == positions
            if t["step"] == 0:
                assert t["step"] == 0 and not before
                assert t["head"] == f"root-{row['case']:02d}"
            else:
                name = t["head"]
                assert name not in names
                names.add(name)
                context = json.loads((capture / "heads" / f"{name}.json").read_text())
                assert dict(context["fixed"]) == before
                assert context["canvas"] == [before.get(i, MASK) for i in range(WIDTH)]
                assert context["queried_positions"] == positions
                assert context["prompt"] == protocol["prompt_ids"][row["case"]]
            assert t["status"] == "PASS"
            for k, v in t["score_errors"].items():
                error_maxima[k] = max(error_maxima[k], v)
            fixed = after
            transitions += 1
        word = row["terminal_ids"]
        assert dict(row["fixed_terminal"]) == fixed
        assert word[-1] == EOS and EOS not in word[:-1]
        assert fixed == dict(enumerate(word))
        lengths.append(len(word))
        steps.append(len(row["transitions"]))
        reward_row = next(
            r for r in rewards if (r["case"], r["replica"]) == (row["case"], row["replica"])
        )
        for key, ids_key, reward_key in (
            ("json", "terminal_ids", "candidate_correct"),
            ("paired_one_shot_json", "paired_one_shot_ids", "paired_one_shot_correct"),
        ):
            original_ids = row[ids_key]
            assert all(0 <= v < VOCABULARY for v in original_ids)
            decoded = tokenizer.decode(
                protocol["supplied_prefix_ids"] + original_ids[:-1], skip_special_tokens=False
            )
            assert decoded == row[key]
            parsed = json.loads(decoded, parse_int=Decimal, parse_float=Decimal)
            assert set(parsed) == {"answer"} and isinstance(parsed["answer"], Decimal)
            match = parsed["answer"] == Decimal(labels[row["case"]]["answer"])
            assert match == reward_row[reward_key]
            correct += int(match)
            answers += 1
    assert len(names) == 63 == report["new_forward_completions"]
    files = {p.stem for p in (capture / "heads").glob("*.npz")}
    assert files == names
    assert {p.stem for p in (capture / "heads").glob("*.json")} == names
    head_checks = 0
    for name in sorted(names):
        context = json.loads((capture / "heads" / f"{name}.json").read_text())
        with np.load(capture / "heads" / f"{name}.npz") as data:
            bits = data["logits_bf16"]
            assert bits.dtype == np.uint16
            assert bits.shape == (len(context["queried_positions"]), VOCABULARY)
            assert data["full_native_output_shape"].tolist() == [
                1,
                len(context["prompt"]) + WIDTH,
                VOCABULARY,
            ]
            assert data["positions"].tolist() == context["queried_positions"]
            assert not np.any(((bits >> 7) & 255) == 255)
        head_checks += 1
    attempts = [e for e in events if e["event"] == "forward_attempt"]
    completed = [e for e in events if e["event"] == "forward_complete"]
    assert [e["ordinal"] for e in attempts] == list(range(1, 64))
    assert {e["name"] for e in attempts} == {e["name"] for e in completed} == names
    observations = [
        json.loads(s) for s in (capture / "gpu-occupancy.jsonl").read_text().splitlines()
    ]
    assert len(observations) == report["occupancy_observations"]
    foreign = [o for o in observations if set(o.get("pids", [])) - {capture_pid}]
    assert not foreign and not any("query_error" in o for o in observations)
    assert report["whole_capture_isolation_satisfied"] and report["capture_pid"] == capture_pid
    assert observations
    result = {
        "status": "PASS",
        "scope": "post-capture consistency, not a new preregistered performance gate",
        "original_id_trace_transitions": transitions,
        "complete_trajectories": len(rows),
        "independent_tokenizer_json_decimal_answers": answers,
        "correct_answers_across_candidate_and_one_shot": correct,
        "original_bf16_full_v_head_checks": head_checks,
        "score_maximum_absolute_errors": error_maxima,
        "prefix_lengths": lengths,
        "transition_counts": steps,
        "gpu_poll_observations_during_capture": len(observations),
        "capture_pid": capture_pid,
        "foreign_gpu_polls_during_whole_capture": foreign,
        "whole_capture_isolation_condition_satisfied": not foreign,
        "gpu_poll_scope": "1s NVML observations/guards, not continuous exclusion of briefer jobs",
        "new_model_forwards": 0,
        "updates": 0,
    }
    write_json(analysis / "post-capture-independent-audit.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture", type=Path, required=True)
    ap.add_argument("--analysis", type=Path, required=True)
    ap.add_argument("--tokenizer-dir", type=Path, required=True)
    ap.add_argument("--capture-pid", type=int, required=True)
    args = ap.parse_args()
    run(args.capture, args.analysis, args.tokenizer_dir, args.capture_pid)
