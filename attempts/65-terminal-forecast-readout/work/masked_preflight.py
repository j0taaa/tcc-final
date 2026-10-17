"""Literal original masked-loop replays, entirely fake heads and synthetic tokens."""

from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path
from types import SimpleNamespace

import torch
from masked_adapter import LastProposal, bit_digest, load_masked
from masked_controls import SparseEdges
from native_adapter import (
    TerminalSnapshot,
    compiled_digest,
    local_rng,
    restore_rng,
    rng_digest,
    rng_state,
)
from native_path_oracle import enumeration
from native_preflight import SCHEMA, TEXTS, SyntheticTokenizer


class FakeHead:
    def __init__(self, dtype):
        self.dtype, self.calls, self.trace = dtype, 0, []

    def __call__(self, ids):
        self.calls += 1
        p = torch.arange(ids.shape[1], device=ids.device)[:, None]
        t = torch.arange(len(TEXTS) + 3, device=ids.device)[None, :]
        weights = (1 + ((p + 1) * (t + 3) + ids.sum() + self.calls) % 11).float()
        weights[:, len(TEXTS) :] += 1024
        logits = weights.log().to(self.dtype).unsqueeze(0)
        self.trace.append(
            {
                "input_ids": ids[0].tolist(),
                "input_sha256": bit_digest(ids),
                "logits_sha256": bit_digest(logits),
            }
        )
        return SimpleNamespace(logits=logits)


def compare_control(snapshot, control):
    result, oracle = control.evaluate(snapshot), enumeration(snapshot)
    errors = [
        abs(result["alpha"] - oracle["complete_probability_ideal_arithmetic"]),
        abs(result["variance"] - oracle["conditional_variance_ideal_arithmetic"]),
        *[
            abs(a - b)
            for a, b in zip(
                result["mean"], oracle["conditional_mean_ideal_arithmetic"], strict=True
            )
        ],
    ]
    assert max(errors) <= 5e-5
    map_probability = oracle["law"][result["map_ids"]]
    best = max(oracle["law"].values())
    assert abs(map_probability - best) <= 1e-12 + 1e-9 * best
    return {
        "alpha": result["alpha"],
        "variance": result["variance"],
        "mean": result["mean"],
        "peak_states": result["peak_states"],
        "max_semantic_error": max(errors),
        "map_probability": map_probability,
        "map_is_original_id_word_map": True,
        "semantic_vector_map_claimed": False,
    }


def run_case(runtime, compiled, tokenizer, control, device, seed, dtype, length, steps):
    prompt = torch.tensor([[2, 3]], device=device)
    trajectories = []
    for capture in (False, True):
        model = FakeHead(dtype)
        matcher = runtime["matcher"].ConstraintMatcher(compiled, length)
        hook = LastProposal(runtime, tokenizer, ("a", "b"), 1, 0, steps, 4)
        config = {
            "steps": steps,
            "gen_length": length,
            "block_length": length,
            "temperature": 0.0,
            "cfg_scale": 0.0,
            "remasking": "low_confidence",
            "vocab_size": len(TEXTS),
            "matcher": matcher,
            "commit_by": "constrained",
        }
        with local_rng(seed):
            if capture:
                with hook.attach(matcher):
                    output = runtime["loop"].generate(model, prompt, 27, **config)
            else:
                output = runtime["loop"].generate(model, prompt, 27, **config)
            after = rng_digest()
        trajectories.append((output, model.trace, after))
    assert torch.equal(trajectories[0][0], trajectories[1][0])
    assert trajectories[0][1:] == trajectories[1][1:]
    ids = tuple(output[0, prompt.shape[1] :].tolist())
    assert ids == hook.first and all(t < len(TEXTS) for t in ids)
    assert not (output == 27).any()
    assert hook.snapshot.node == matcher.node and matcher.num_accepted == 0
    assert all((t == -1 or t == ids[p]) for p, t in enumerate(hook.snapshot.tokens[0].tolist()))
    caller = rng_state()
    try:
        restore_rng(hook.before_rng)
        assert hook.snapshot.draw() == ids
        assert rng_digest() == rng_digest(hook.after_rng)
    finally:
        restore_rng(caller)
    original_snapshot = bit_digest(hook.snapshot.scores), bit_digest(hook.snapshot.tokens)
    assert matcher.accept_tokens(torch.tensor(ids, device=device))
    hook.caller_logits.fill_(0)
    preserved = (
        compiled_digest(compiled),
        matcher.node,
        matcher.num_accepted,
        bit_digest(output),
        rng_digest(),
    )
    readouts = []
    for budget in (0, 1, 7):
        readouts.append(hook.snapshot.readout(ids, budget, 650600 + 100 * seed + length + budget))
        assert (
            compiled_digest(compiled),
            matcher.node,
            matcher.num_accepted,
            bit_digest(output),
            rng_digest(),
        ) == preserved
        assert original_snapshot == (
            bit_digest(hook.snapshot.scores),
            bit_digest(hook.snapshot.tokens),
        )
    return {
        "device": device,
        "seed": seed,
        "dtype": str(dtype),
        "length": length,
        "steps": steps,
        "status": "PASS",
        "original_response_ids": ids,
        "literal_full_trace": trajectories[1][1],
        "fake_forward_calls": 2 * steps,
        "new_neural_forwards": 0,
        "helper_calls": sum(r["helpers_called"] for r in readouts),
        "readouts": readouts,
        "control": compare_control(hook.snapshot, control),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    started, before = time.monotonic(), rng_state()
    threads, precision = torch.get_num_threads(), torch.get_float32_matmul_precision()
    report = {
        "status": "RUNNING",
        "rows": [],
        "new_neural_forwards": 0,
        "pretrained_model_tokenizer_loaded": False,
    }
    try:
        assert torch.__version__ == "2.8.0+cu128" and torch.cuda.is_available()
        torch.set_num_threads(1)
        torch.set_float32_matmul_precision("highest")
        runtime, tokenizer = load_masked(), SyntheticTokenizer()
        for device in ("cpu", "cuda:0"):
            compiler = runtime["matcher"].ConstraintCompiler(
                tokenizer,
                eos_token="<pad>",
                eot_token="<eot>",
                device=device,
                matmul_dtype=torch.float64,
                cache_size=1,
                compile_workers=0,
            )
            compiled = compiler.compile_json_schema(SCHEMA)
            control = SparseEdges(compiled, tokenizer)
            for seed, dtype, (length, steps) in itertools.product(
                (17, 29), (torch.float32, torch.bfloat16), ((8, 2), (64, 16))
            ):
                if (
                    time.monotonic() - started > 600
                    or torch.cuda.max_memory_allocated() > 2 * 1024**3
                ):
                    raise RuntimeError("Prospective preflight resource guard exceeded")
                row = run_case(
                    runtime, compiled, tokenizer, control, device, seed, dtype, length, steps
                )
                report["rows"].append(row)
                with (args.output / "records.jsonl").open("a") as stream:
                    stream.write(json.dumps(row) + "\n")
                print(
                    json.dumps(
                        {k: row[k] for k in ("device", "seed", "dtype", "length", "status")}
                    ),
                    flush=True,
                )
            # Independent mixed complete/incomplete support, not selected by RNG.
            partial = FakeHead(torch.float32)(torch.full((1, 6), 27, device=device)).logits
            matcher = runtime["matcher"].ConstraintMatcher(compiled, 10)
            snapshot = TerminalSnapshot.capture(
                runtime,
                matcher,
                partial,
                torch.full((1, 6), -1, device=device),
                0,
                (),
                tokenizer,
                ("a", "b"),
            )
            check = compare_control(snapshot, control)
            assert 0 < check["alpha"] < 1
            report.setdefault("partial_support_checks", []).append({"device": device, **check})
            compiler.close()
        assert len(report["rows"]) == 16
        report.update(
            status="PASS",
            fake_forward_calls=sum(r["fake_forward_calls"] for r in report["rows"]),
            additional_diagnostic_fake_heads=2,
            helpers=sum(r["helper_calls"] for r in report["rows"]),
            max_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
        )
    except Exception as error:
        report.update(status="ERROR", error=repr(error))
        raise
    finally:
        restore_rng(before)
        torch.set_num_threads(threads)
        torch.set_float32_matmul_precision(precision)
        report["caller_rng_restored"] = rng_digest() == rng_digest(before)
        (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}))


if __name__ == "__main__":
    main()
