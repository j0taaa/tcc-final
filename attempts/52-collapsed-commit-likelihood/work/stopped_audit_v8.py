"""Post-capture V8 consistency audit, written AFTER outputs; no model calls."""

import argparse
import csv
import datetime as dt
import json
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from .consumer_resource import write_json


def run(capture, analysis, tokenizer_dir, capture_pid):
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(tokenizer_dir / "tokenizer.json"))
    rows = [json.loads(x) for x in (capture / "rows.jsonl").read_text().splitlines()]
    events = [json.loads(x) for x in (capture / "events.jsonl").read_text().splitlines()]
    labels = json.loads((analysis / "known-labels-provenance.json").read_text())["labels"]
    rewards = json.loads((analysis / "reward-rows.json").read_text())
    report = json.loads((capture / "summary.json").read_text())
    assert len(rows) == 16 and {(r["case"], r["replica"]) for r in rows} == {
        (c, r) for c in range(8) for r in range(2)
    }
    transitions, answers, correct, names = 0, 0, 0, {"warmup"}
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
            assert proposal[-1] == 151645 and 151645 not in proposal[:-1]
            assert all(i < len(proposal) and proposal[i] == v for i, v in after.items())
            eos = next((i for i, v in before.items() if v == 151645), None)
            extent = eos + 1 if eos is not None else 32
            assert t["prefix_extent"] == extent
            positions = [i for i in range(extent) if i not in before]
            assert t["queried_positions"] == positions
            if t["head"] == "OLD_ROOT":
                assert t["step"] == 0 and not before
            else:
                name = t["head"]
                assert name not in names
                names.add(name)
                context = json.loads((capture / "heads" / f"{name}.json").read_text())
                assert dict(context["fixed"]) == before
                assert context["canvas"] == [before.get(i, 151669) for i in range(32)]
                assert context["queried_positions"] == positions
            assert t["status"] == "PASS"
            for k, v in t["score_errors"].items():
                error_maxima[k] = max(error_maxima[k], v)
            fixed = after
            transitions += 1
        word = row["terminal_ids"]
        assert dict(row["fixed_terminal"]) == fixed
        assert word[-1] == 151645 and 151645 not in word[:-1]
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
            assert all(0 <= v < 151936 for v in original_ids)
            decoded = tokenizer.decode(original_ids[:-1], skip_special_tokens=False)
            assert decoded == row[key]
            parsed = json.loads(decoded, parse_int=Decimal, parse_float=Decimal)
            assert set(parsed) == {"answer"} and isinstance(parsed["answer"], Decimal)
            match = parsed["answer"] == Decimal(labels[row["case"]]["answer"])
            assert match == reward_row[reward_key]
            correct += int(match)
            answers += 1
    assert len(names) == 98 == report["new_forward_completions"]
    files = {p.stem for p in (capture / "heads").glob("*.npz")}
    assert files == names
    assert {p.stem for p in (capture / "heads").glob("*.json")} == names
    head_checks = 0
    for name in sorted(names):
        context = json.loads((capture / "heads" / f"{name}.json").read_text())
        with np.load(capture / "heads" / f"{name}.npz") as data:
            bits = data["logits_bf16"]
            assert bits.dtype == np.uint16
            assert bits.shape == (len(context["queried_positions"]), 151936)
            assert data["positions"].tolist() == context["queried_positions"]
            assert not np.any(((bits >> 7) & 255) == 255)
        head_checks += 1
    attempts = [e for e in events if e["event"] == "forward_attempt"]
    completed = [e for e in events if e["event"] == "forward_complete"]
    assert [e["ordinal"] for e in attempts] == list(range(1, 99))
    assert {e["name"] for e in attempts} == {e["name"] for e in completed} == names
    observations, foreign, forward_foreign = [], [], []
    start = dt.datetime(2026, 10, 16, 19, 7, 24, tzinfo=dt.UTC).timestamp()
    first_forward = min(e["utc_seconds"] for e in attempts)
    end = max(e["utc_seconds"] for e in events) + 2
    with (capture / "gpu-occupancy.csv").open() as stream:
        for observation in csv.DictReader(stream, skipinitialspace=True):
            when = (
                dt.datetime.strptime(observation["timestamp"], "%Y/%m/%d %H:%M:%S.%f")
                .replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
                .timestamp()
            )
            if start <= when <= end:
                observations.append(observation)
                if int(observation["pid"]) != capture_pid:
                    foreign.append(observation)
                    if first_forward <= when:
                        forward_foreign.append(observation)
    assert observations
    result = {
        "status": "CONSISTENCY_PASS_WHOLE_CAPTURE_ISOLATION_DEVIATION" if foreign else "PASS",
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
        "foreign_gpu_polls_during_new_forward_interval": forward_foreign,
        "whole_capture_isolation_condition_satisfied": not foreign,
        "gpu_poll_scope": "5s NVML polling; not continuous exclusion of hypothetical brief jobs",
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
