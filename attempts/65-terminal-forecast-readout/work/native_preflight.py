"""Pinned native constrained-step replay with synthetic logits, no backbone."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import time
import traceback
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import torch
from native_adapter import (
    TerminalSnapshot,
    compiled_digest,
    load_native,
    local_rng,
    restore_rng,
    rng_digest,
    rng_state,
    tensor_digest,
)
from native_path_oracle import enumeration, independent_marginal_error

TEXTS = [
    "<pad>",
    "<eot>",
    "<thought>",
    "<keep>",
    '{"probabilities":{"a":',
    ',"b":',
    "}}",
    "0",
    "1",
    "0.0",
    "0.00",
    "0.1",
    "0.10",
    "0.2",
    "0.8",
    "0.9",
    "1.00",
    ".",
    "2",
    "8",
    "9",
    "0.",
    ".1",
    ".10",
    "0.1",
]
SCHEMA = {
    "type": "object",
    "properties": {
        "probabilities": {
            "type": "object",
            "properties": {label: {"type": "number", "x-prob": True} for label in ("a", "b")},
            "required": ["a", "b"],
        }
    },
    "required": ["probabilities"],
}


class SyntheticTokenizer:
    name_or_path = (
        "a65-native-preflight-v3-" + hashlib.sha256(repr(TEXTS).encode()).hexdigest()[:12]
    )
    eos_token = "<pad>"
    all_special_tokens = TEXTS[:4]

    def __len__(self):
        return len(TEXTS)

    def get_vocab(self):
        return {f"original-id-{i}": i for i in range(len(TEXTS))}

    def decode(self, token):
        return TEXTS[int(token)]

    def convert_tokens_to_ids(self, text):
        return TEXTS.index(text)


def fixtures():
    return [
        {"name": "full", "length": 8, "budget": 8, "offset": 0, "prefix": (), "pins": {}},
        {
            "name": "thinking_offset",
            "length": 10,
            "budget": 8,
            "offset": 2,
            "prefix": (),
            "pins": {0: 2, 1: 3},
        },
        {
            "name": "original_alias_pin",
            "length": 8,
            "budget": 8,
            "offset": 0,
            "prefix": (),
            "pins": {1: 24},
        },
        {
            "name": "nonterminal_canvas",
            "length": 6,
            "budget": 10,
            "offset": 0,
            "prefix": (),
            "pins": {},
        },
        {
            "name": "zero_sum",
            "length": 8,
            "budget": 8,
            "offset": 0,
            "prefix": (),
            "pins": {1: 10, 3: 10},
        },
        {
            "name": "prefix_inside_number",
            "length": 6,
            "budget": 8,
            "offset": 0,
            "prefix": (4, 21),
            "pins": {},
        },
    ]


def step_inputs(fixture: dict, index: int, device: str, read_only: bool) -> dict:
    length, vocab = fixture["length"], len(TEXTS) + 3
    values = [[1 + ((p + 1) * (t + 3) + index) % 11 for t in range(vocab)] for p in range(length)]
    weights = torch.tensor(values, device=device, dtype=torch.float32)
    weights[:, len(TEXTS) :] += 1024
    pins = torch.zeros((3, length), device=device, dtype=torch.bool)
    seeds = torch.zeros((3, length), device=device, dtype=torch.long)
    for p, t in fixture["pins"].items():
        pins[1, p], seeds[1, p] = True, t
    canvas = torch.zeros((3, length), device=device, dtype=torch.long)
    canvas[0], canvas[2] = 2, 3
    canvas[1] = torch.where(pins[1], seeds[1], -1)
    return {
        "offsets": [fixture["offset"]],
        "logits": weights.log().unsqueeze(0),
        "decode_slots": torch.tensor([1], device=device),
        "decode_idx": torch.tensor([0], device=device),
        "all_slots": torch.arange(3, device=device),
        "valid_canvas_len": torch.tensor([length], device=device),
        "canvas": canvas,
        "argmax_canvas": torch.full_like(canvas, 3),
        "step_tensor": torch.zeros(3, device=device, dtype=torch.long),
        "is_encoder_phase": torch.zeros(3, device=device, dtype=torch.bool),
        "confident_tensor": torch.zeros(3, device=device, dtype=torch.bool),
        "sc_embeds": torch.ones((3, length, 4), device=device),
        "embed_weight": torch.arange(vocab * 4, device=device, dtype=torch.float32).reshape(
            vocab, 4
        )
        / 100,
        "normalizer": 0.5,
        "history": torch.full((3, 2, length), 3, device=device, dtype=torch.long),
        "history_len_tensor": torch.zeros(3, device=device, dtype=torch.long),
        "max_steps_tensor": torch.ones(3, device=device, dtype=torch.long),
        "pin_mask": pins,
        "seed_canvas": seeds,
        "read_only": torch.full((3,), read_only, device=device, dtype=torch.bool),
        "sampled": torch.zeros((1, length), device=device, dtype=torch.long),
        "num_sampled": torch.zeros(1, device=device, dtype=torch.long),
        "draft_tokens": torch.full_like(canvas, 3),
        "max_denoising_steps": 1,
        "t_min": 1.0,
        "t_max": 1.0,
        "confidence_threshold": 0.1,
        "vocab_size": vocab,
        "CL": length,
        "ST": 2,
        "entropy_bound": 1.0,
        "sc_vocab_start": 0,
        "sc_vocab_end": vocab,
        "tp_size": 1,
        "tp_group_name": "unused-no-tensor-parallel",
        "compute_sc": True,
    }


def state_digest(inputs: dict, matcher) -> dict:
    return {
        "tensors": {
            name: tensor_digest(value) for name, value in inputs.items() if torch.is_tensor(value)
        },
        "matcher": [matcher.node, matcher.num_accepted, matcher.max_new_tokens],
        "compiled": compiled_digest(matcher.compiled),
    }


def new_matcher(runtime, compiled, fixture, device):
    matcher = runtime["matcher"].ConstraintMatcher(compiled, fixture["budget"])
    if fixture["prefix"]:
        ids = torch.tensor(fixture["prefix"], device=device)
        assert matcher.accept_tokens(ids), "declared accepted prefix is invalid"
    return matcher


def run_step(
    runtime, compiled, tokenizer, fixture, index, device, seed, read_only, capture, counters
):
    matcher = new_matcher(runtime, compiled, fixture, device)
    inputs = step_inputs(fixture, index, device, read_only)
    captured = {}
    functions = runtime["functions"]
    original = functions["_propose"]

    def hook(batch, matchers, offsets, scores, tokens, temperature):
        counters["native_propose_calls"] += 1
        if temperature == 1.0:
            captured["initial_scores"] = scores.detach().clone()
        if capture and temperature == 0.0:
            captured["snapshot"] = TerminalSnapshot.capture(
                runtime,
                matchers[0],
                scores,
                tokens,
                offsets[0],
                fixture["prefix"],
                tokenizer,
                ("a", "b"),
            )
            captured["rng_before_terminal"] = rng_state()
        ids = original(batch, matchers, offsets, scores, tokens, temperature)
        if capture and temperature == 0.0:
            captured["first_ids"] = tuple(ids[0].tolist())
            captured["rng_after_terminal"] = rng_state()
        return ids

    with local_rng(seed):
        functions["_propose"] = hook
        try:
            result = functions["_constrained_step"](matchers=[matcher], **inputs)
            counters["synthetic_native_steps"] += 1
        finally:
            functions["_propose"] = original
        captured["rng_after_step"] = rng_digest()
    inputs["returned_log_probs"] = result
    captured.update(inputs=inputs, matcher=matcher, digest=state_digest(inputs, matcher))
    return captured


def record_case(
    runtime, compiled, tokenizer, fixture, index, device, seed, read_only, counters, cache
):
    baseline = run_step(
        runtime, compiled, tokenizer, fixture, index, device, seed, read_only, False, counters
    )
    actual = run_step(
        runtime, compiled, tokenizer, fixture, index, device, seed, read_only, True, counters
    )
    assert baseline["digest"] == actual["digest"]
    assert (
        baseline["rng_after_step"]
        == actual["rng_after_step"]
        == rng_digest(actual["rng_after_terminal"])
    )
    snapshot = actual["snapshot"]
    ids = actual["first_ids"]
    assert ids == tuple(actual["inputs"]["argmax_canvas"][1].tolist())
    assert torch.equal(snapshot.scores, actual["inputs"]["returned_log_probs"])
    assert all(0 <= t < len(TEXTS) for t in ids)
    for p, token in fixture["pins"].items():
        assert ids[p] == token
    assert tuple(ids[: fixture["offset"]]) == tuple(
        snapshot.tokens[0, : fixture["offset"]].tolist()
    )
    assert torch.isneginf(snapshot.scores[..., len(TEXTS) :]).all()
    parent_rng = rng_state()
    try:
        restore_rng(actual["rng_before_terminal"])
        replay = snapshot.draw()
        counters["native_propose_calls"] += 1
        assert replay == ids and rng_digest() == rng_digest(actual["rng_after_terminal"])
    finally:
        restore_rng(parent_rng)
    key = (
        device,
        fixture["name"],
        tensor_digest(snapshot.scores),
        snapshot.node,
        snapshot.accepted,
    )
    if key not in cache:
        law = enumeration(snapshot)
        error = independent_marginal_error(snapshot, actual["initial_scores"])
        assert error <= 5e-5, (fixture["name"], device, error)
        cache[key] = law, error
    law, error = cache[key]
    assert ids in law["law"]
    # Simulate the engine advancing and reusing buffers AFTER the capture.
    assert actual["matcher"].accept_tokens(torch.tensor(ids[fixture["offset"] :], device=device))
    actual["inputs"]["returned_log_probs"].fill_(0)
    protected = state_digest(actual["inputs"], actual["matcher"])
    original_snapshot = (
        tensor_digest(snapshot.scores),
        tensor_digest(snapshot.tokens),
        snapshot.node,
        snapshot.accepted,
        snapshot.prefix,
    )
    outputs = []
    for budget in (0, 1, 7):
        before = rng_digest()
        output = snapshot.readout(ids, budget, 10000 + seed * 100 + index * 10 + budget)
        counters["native_propose_calls"] += output["helpers_called"]
        counters["additional_helpers"] += output["helpers_called"]
        assert rng_digest() == before
        assert protected == state_digest(actual["inputs"], actual["matcher"])
        assert original_snapshot == (
            tensor_digest(snapshot.scores),
            tensor_digest(snapshot.tokens),
            snapshot.node,
            snapshot.accepted,
            snapshot.prefix,
        )
        assert output["original_ids"] == ids
        for sample in output["samples"]:
            assert tuple(sample["ids"]) in law["law"]
            assert sample["rng_before"] != sample["rng_after"]
        if output["samples"]:
            assert len({s["rng_before"] for s in output["samples"]}) == len(output["samples"])
        if output["mean"] is not None:
            mean = tuple(map(F, output["mean"]))
            assert sum(mean) == 1 and min(mean) >= 0
            rendered = json.loads(output["rendered"], parse_float=F, parse_int=F)["probabilities"]
            assert sum(rendered.values()) == 1 and min(rendered.values()) >= 0
            assert all(
                abs(rendered[label] - mean[j]) < F(1, 10**8)
                for j, label in enumerate(snapshot.labels)
            )
        else:
            assert not output["helpers_called"]
        outputs.append(output)
    # Every independently enumerated positive state path is observed/classified,
    # including unobserved-to-this-RNG incomplete paths; no statistical gate.
    complete = incomplete = zero = 0
    for word in law["law"]:
        raw = snapshot.observe(word)
        if raw is None:
            incomplete += 1
        else:
            complete += 1
            zero += sum(raw) == 0
    if fixture["name"] == "nonterminal_canvas":
        assert complete and incomplete
    if fixture["name"] == "zero_sum":
        assert complete and zero == complete
    return {
        "fixture": fixture["name"],
        "device": device,
        "seed": seed,
        "read_only": read_only,
        "status": "PASS",
        "synthetic_logits": True,
        "new_neural_forwards": 0,
        "literal_full_step_and_terminal_replay": True,
        "original_ids": ids,
        "capture_node": snapshot.node,
        "capture_accepted": snapshot.accepted,
        "live_node_after_advance": actual["matcher"].node,
        "captured_score_sha256": original_snapshot[0],
        "whole_state_sha256": protected,
        "path_reference": {k: v for k, v in law.items() if k != "law"},
        "positive_complete_paths": complete,
        "positive_incomplete_paths": incomplete,
        "positive_zero_sum_paths": zero,
        "max_marginal_error": error,
        "readouts": outputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "preserve earlier drafts and choose a new output directory"
    args.output.mkdir(parents=True)
    started = time.monotonic()
    initial_rng = rng_state()
    precision, threads = torch.get_float32_matmul_precision(), torch.get_num_threads()
    records, cache = [], {}
    counters = {"native_propose_calls": 0, "synthetic_native_steps": 0, "additional_helpers": 0}
    metadata = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "numpy": np.__version__,
        "automata_lib": importlib.metadata.version("automata-lib"),
        "status": "RUNNING",
        "scope": "Native sampler functions with SYNTHETIC logits; no serving/model reproduction",
        "new_neural_forwards": 0,
        "copied_source_modified": False,
    }
    try:
        torch.set_num_threads(1)
        torch.set_float32_matmul_precision("highest")
        assert torch.cuda.is_available(), "the prospective CPU+CUDA preflight requires CUDA"
        runtime = load_native()
        tokenizer = SyntheticTokenizer()
        metadata["origin"] = runtime["origin"]
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
            for index, fixture in enumerate(fixtures()):
                for seed in (17, 29):
                    for read_only in (False, True):
                        if time.monotonic() - started > 600:
                            raise RuntimeError("declared total preflight time guard exceeded")
                        row = record_case(
                            runtime,
                            compiled,
                            tokenizer,
                            fixture,
                            index,
                            device,
                            seed,
                            read_only,
                            counters,
                            cache,
                        )
                        records.append(row)
                        with (args.output / "records.jsonl").open("a") as stream:
                            stream.write(json.dumps(row) + "\n")
                        print(
                            json.dumps(
                                {
                                    k: row[k]
                                    for k in ("fixture", "device", "seed", "read_only", "status")
                                }
                            ),
                            flush=True,
                        )
                        if torch.cuda.max_memory_allocated() > 2 * 1024**3:
                            raise RuntimeError("declared GPU allocation guard exceeded")
            compiler.close()
        assert len(records) == 48
        metadata.update(
            status="PASS",
            records=len(records),
            **counters,
            max_marginal_error=max(r["max_marginal_error"] for r in records),
            peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),
            actual_native_rng_iid_proved=False,
            full_vllm_service_executed=False,
        )
    except Exception as error:
        metadata.update(status="ERROR", records=len(records), error=repr(error), **counters)
        (args.output / "traceback.txt").write_text(traceback.format_exc())
        raise
    finally:
        restore_rng(initial_rng)
        torch.set_float32_matmul_precision(precision)
        torch.set_num_threads(threads)
        metadata["caller_rng_restored"] = rng_digest() == rng_digest(initial_rng)
        metadata["caller_precision_restored"] = torch.get_float32_matmul_precision() == precision
        metadata["caller_threads_restored"] = torch.get_num_threads() == threads
        (args.output / "summary.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({k: v for k, v in metadata.items() if k != "origin"}))


if __name__ == "__main__":
    main()
