"""Prospective, instrumented EPIC diagnosis; keep the vendor unchanged."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import resource
import subprocess
import time
from collections import defaultdict
from pathlib import Path

os.environ["CONSTRAINED_DIFFUSION_REGULAR_COVER_BATCH"] = "1"
os.environ["CONSTRAINED_DIFFUSION_REGULAR_COVER_EXACT"] = "1"
os.environ["CONSTRAINED_DIFFUSION_DFA_FREE_CHECKER"] = "1"

HERE = Path(__file__).resolve().parent
MODEL = (
    Path.home()
    / ".cache/huggingface/hub/models--GSAI-ML--LLaDA-8B-Instruct"
    / "snapshots/08b83a6feb34df1a6011b80c3c00c7563e963b07"
)
CASES = (
    (
        "sum",
        "What is 2 + 3? Return the integer in the answer field.",
        {
            "type": "object",
            "properties": {"answer": {"type": "integer"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
        {"answer": 5},
    ),
    (
        "list",
        "Return the first three prime numbers in the items field.",
        {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 3,
                    "maxItems": 3,
                }
            },
            "required": ["items"],
            "additionalProperties": False,
        },
        {"items": [2, 3, 5]},
    ),
    (
        "enum",
        "Classify the sentiment: I love this. Return the label field.",
        {
            "type": "object",
            "properties": {
                "label": {"type": "string", "enum": ["positive", "negative", "neutral"]}
            },
            "required": ["label"],
            "additionalProperties": False,
        },
        {"label": "positive"},
    ),
)
ORDERS = (
    ("epic", "exact_first", "sequential"),
    ("exact_first", "sequential", "epic"),
    ("sequential", "epic", "exact_first"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite an existing record")

    def record(data):
        with args.output.open("a") as stream:
            stream.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(json.dumps(data, ensure_ascii=False), flush=True)

    import jsonschema
    import torch
    import transformers
    from constrained_diffusion.cfgs.jsonschema import schema_to_cfg
    from constrained_diffusion.constrain_utils import compile_lex_map, start_fast_enfa_instance
    from rustformlang.cfg import CFG
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    lg = importlib.import_module(
        "constrained_diffusion.eval.dllm.models.llada.generate_constrained"
    )
    rc = importlib.import_module("constrained_diffusion.regular_cover")
    torch.set_num_threads(4)
    torch.manual_seed(83001)
    record(
        {
            "type": "source",
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "model_snapshot": MODEL.name,
            "gpu": torch.cuda.get_device_name(0),
            "gpu_processes": subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-compute-apps=pid,process_name,used_gpu_memory",
                    "--format=csv,noheader",
                ],
                text=True,
            ).strip(),
        }
    )
    if torch.cuda.mem_get_info()[0] < 6.5 * 2**30:
        record({"type": "refusal", "reason": "insufficient_free_gpu_memory"})
        return
    start = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=True)
    actual = AutoModel.from_pretrained(
        MODEL,
        local_files_only=True,
        trust_remote_code=True,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
    ).eval()
    torch.cuda.synchronize()
    record(
        {
            "type": "load",
            "seconds": time.perf_counter() - start,
            "allocated_bytes": torch.cuda.memory_allocated(),
        }
    )

    original_selector = lg.select_batch_with_regular_cover
    original_check = lg.check_valid
    original_exact = rc.exact_allows_words
    original_cover = rc.cover_allows_words
    original_f = lg.F
    batch_enabled = lg.regular_cover_batch_enabled

    for case_index, (name, question, schema, expected) in enumerate(CASES):
        start = time.perf_counter()
        cfg, lexmap, subtokens = schema_to_cfg(schema)
        cfg = cfg.concatenate(CFG.from_text("S -> lexFence | $", "S")).to_normal_form()
        lexmap["lexFence"] = "```"
        lexmap = compile_lex_map(lexmap, subtokens=subtokens)
        prep_seconds = time.perf_counter() - start
        prompt_text = (
            tokenizer.apply_chat_template(
                [
                    {
                        "role": "user",
                        "content": "Answer in JSON in a code fence. Follow this schema: "
                        + json.dumps(schema)
                        + "\n"
                        + question,
                    }
                ],
                tokenize=False,
                add_generation_prompt=True,
            )
            + "```json\n"
        )
        prompt = tokenizer(prompt_text, return_tensors="pt").input_ids.to(actual.device)
        for mode in ORDERS[case_index]:
            times, counts = defaultdict(float), defaultdict(int)
            selection_events, states = [], []
            start_fast_enfa_instance((name, mode))
            rc._build_flat_rtn_cover_dfa_from_text.cache_clear()
            torch.manual_seed(83001)
            torch.cuda.reset_peak_memory_stats()
            deadline = time.perf_counter() + 120

            def timed(key, function, *a, _deadline=deadline, _times=times, _counts=counts, **kw):
                if time.perf_counter() > _deadline:
                    raise TimeoutError("cooperative decode deadline")
                torch.cuda.synchronize()
                begin = time.perf_counter()
                try:
                    return function(*a, **kw)
                finally:
                    torch.cuda.synchronize()
                    _times[key] += time.perf_counter() - begin
                    _counts[key] += 1

            class Model:
                device = actual.device

                def __call__(self, x):
                    return timed("model", actual, x)

            class Functional:
                def __getattr__(self, attr):
                    return getattr(original_f, attr)

                def softmax(self, *a, **kw):
                    return timed("decoder_softmax", original_f.softmax, *a, **kw)

            def selector(_mode=mode, _counts=counts, _times=times, _events=selection_events, **kw):
                begin = time.perf_counter()
                exact_cached = rc.exact_allows_words
                memo = {}

                def cached(**query):
                    key = tuple(query["words_full"])
                    if key not in memo:
                        memo[key] = exact_cached(**query)
                    else:
                        _counts["exact_cache_hit"] += 1
                    return memo[key]

                if _mode == "exact_first":
                    rc.exact_allows_words = cached
                try:
                    selected = None
                    if _mode == "exact_first":
                        query = {k: v for k, v in kw.items() if k != "candidates"}
                        trial = list(kw["words_full"])
                        for candidate in kw["candidates"]:
                            trial[candidate.index] = candidate.word
                        query["words_full"] = trial
                        if cached(**query):
                            _counts["exact_first_full_accept"] += 1
                            selected = list(kw["candidates"])
                    if selected is None:
                        selected = original_selector(**kw)
                    _events.append({"proposed": len(kw["candidates"]), "accepted": len(selected)})
                    return selected
                finally:
                    rc.exact_allows_words = exact_cached
                    _times["selection"] += time.perf_counter() - begin
                    _counts["selection"] += 1

            lg.select_batch_with_regular_cover = selector
            lg.check_valid = lambda *a, **kw: timed("sequential_exact", original_check, *a, **kw)
            rc.exact_allows_words = lambda **kw: timed("batch_exact", original_exact, **kw)
            rc.cover_allows_words = lambda **kw: timed("regular_cover", original_cover, **kw)
            lg.F = Functional()
            lg.regular_cover_batch_enabled = (
                (lambda: False) if mode == "sequential" else batch_enabled
            )
            start = time.perf_counter()
            last, resamples, complete, status = None, [], False, "returned"
            try:
                for yielded in lg.generate(
                    Model(),
                    prompt,
                    tokenizer,
                    constraint_lang=cfg,
                    lex_map=lexmap,
                    prompt_len=prompt.shape[1],
                    steps=8,
                    gen_length=64,
                    block_length=32,
                    temperature=0.0,
                    remasking="low_confidence",
                    subtokens=subtokens,
                    constrain=True,
                    max_resamples=100,
                ):
                    last, resamples, complete = yielded
                    states.append(last[0, prompt.shape[1] :].tolist())
                    if time.perf_counter() > deadline:
                        raise TimeoutError("cooperative decode deadline")
            except Exception as exc:
                status = type(exc).__name__ + ": " + str(exc)
            finally:
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - start
                lg.select_batch_with_regular_cover = original_selector
                lg.check_valid, lg.F = original_check, original_f
                lg.regular_cover_batch_enabled = batch_enabled
                rc.exact_allows_words, rc.cover_allows_words = original_exact, original_cover
            token_ids = last[0, prompt.shape[1] :].tolist() if last is not None else []
            raw = tokenizer.decode(token_ids, skip_special_tokens=True)
            text = raw.split("```")[0].strip()
            valid_schema, correct, validation_error = False, False, None
            try:
                value = json.loads(text)
                jsonschema.validate(value, schema)
                valid_schema, correct = True, value == expected
            except Exception as exc:
                validation_error = type(exc).__name__ + ": " + str(exc)
            record(
                {
                    "type": "decode",
                    "case": name,
                    "mode": mode,
                    "status": status,
                    "complete": complete,
                    "schema_valid": valid_schema,
                    "correct": correct,
                    "validation_error": validation_error,
                    "raw": raw,
                    "token_ids": token_ids,
                    "state_sha256": hashlib.sha256(json.dumps(states).encode()).hexdigest(),
                    "states": states,
                    "prep_seconds": prep_seconds,
                    "decode_seconds": elapsed,
                    "times": dict(times),
                    "counts": dict(counts),
                    "rejections": len(resamples),
                    "selection_events": selection_events,
                    "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                    "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                }
            )


if __name__ == "__main__":
    main()
