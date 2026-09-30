#!/usr/bin/env python3
"""Generate, validate and execute a read-only geographic query, or replay evidence."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from mwpc_exact import CompositionalByteLevelAdapter
from mwpc_research.catalog_tokens import encode_call
from mwpc_research.geocoding import (
    FUNCTION,
    display_record,
    fetch_location,
    geocoding_catalog,
    read_record,
    save_record,
    validated_url,
)
from mwpc_research.tool_parser import catalog_byte_grammar

ROOT = Path(__file__).resolve().parents[2]


def live(args):
    from run_policy_screen import EOS, MASK, decode, policy_scope

    config = json.loads(args.config.read_text())
    request = args.request or config["request"]
    policy = next((p for p in config["policies"] if p["name"] == args.method), None)
    if policy is None:
        raise ValueError("Unknown method; choose one of the policies in the demo configuration")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise ValueError("Commit the tested demo source before recording live evidence")
    # Heavy model dependencies are deliberately imported only in live mode.
    import torch
    from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

    torch.set_num_threads(config["cpu_threads"])
    torch.manual_seed(config["seed"])
    torch.cuda.manual_seed_all(config["seed"])
    tokenizer = AutoTokenizer.from_pretrained(
        config["model_id"], revision=config["revision"], local_files_only=True
    )
    support_policy = config.get("grounding_policy", "question_spans_v1")
    calls = geocoding_catalog(request, support_policy)
    paths, emissions = [], {}
    for call in calls:
        path, pieces = encode_call(tokenizer, call, slots=config["slots"], eos=EOS)
        paths.append(path)
        emissions.update(pieces)
    grammar = catalog_byte_grammar(calls)
    rows = [sorted({p[i] for p in paths}) for i in range(config["slots"])]
    loading = time.perf_counter()
    model = AutoModel.from_pretrained(
        config["model_id"],
        revision=config["revision"],
        local_files_only=True,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        ),
    ).eval()
    assert model.config._commit_hash == config["revision"]
    load_seconds = time.perf_counter() - loading
    adapter = CompositionalByteLevelAdapter(
        tuple(emissions.get(i) for i in range(model.config.vocab_size))
    )
    prompt_text = (
        "Return only one Python function call using keyword arguments. "
        "Use the documented function and argument values. Function schema: "
        + json.dumps(FUNCTION, ensure_ascii=False)
        + "\nRequest: "
        + request
    )
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt_text}], add_generation_prompt=True, tokenize=True
    )
    with torch.inference_mode():
        for _ in range(2):
            model(torch.tensor([prompt + [MASK] * config["slots"]], device="cuda"))
    torch.cuda.synchronize()
    if policy["kind"] == "epic":
        from epic_tool_runner import run_epic

        generation = run_epic(
            model=model,
            tokenizer=tokenizer,
            prompt=prompt,
            grammar=grammar,
            rows=rows,
            calls=calls,
            config=config,
            method=policy["method"],
        )
    else:
        generation = decode(
            model=model,
            tokenizer=tokenizer,
            request=prompt_text,
            calls=calls,
            paths=paths,
            grammar=grammar,
            rows=rows,
            adapter=adapter,
            policy=policy,
            config=config,
        )
    record = {
        "mode": "live",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "config": config,
        "request": request,
        "function": FUNCTION,
        "policy": policy,
        "exactness_scope": policy_scope(policy),
        "generation": generation,
        "support": {
            "catalog": calls,
            "paths": paths,
            "emissions": {t: list(b) for t, b in emissions.items()},
        },
        "grammar_sha256": hashlib.sha256(json.dumps(calls).encode()).hexdigest(),
        "model_loading_seconds": load_seconds,
        "hardware": torch.cuda.get_device_name(0),
        "python": platform.python_version(),
        "versions": {
            p: importlib.metadata.version(p) for p in ("torch", "transformers", "bitsandbytes")
        },
        "status": generation["status"],
        "api": None,
        "failure": generation.get("failure"),
    }
    if generation["status"] == "complete":
        try:
            validated_url(generation["output"], request, support_policy)
            record["api"] = fetch_location(generation["output"], request, support_policy)
            record["status"] = (
                "query_complete" if record["api"]["payload"].get("results") else "query_empty"
            )
        except Exception as exc:
            record["status"] = "query_failed"
            record["failure"] = {"type": type(exc).__name__, "message": str(exc)}
    directory = args.output or ROOT / "results/demo" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    save_record(directory, record)
    print(json.dumps(display_record(record, replay=False), indent=2, ensure_ascii=False))
    print(f"Evidence: {directory}")
    return record["status"] in ("query_complete", "query_empty")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("live", "replay"), default="replay")
    p.add_argument("--record", type=Path, default=ROOT / "docs/artifacts/demo/geocoding_v2")
    p.add_argument("--config", type=Path, default=ROOT / "configs/demo/geocoding_v2.json")
    p.add_argument("--request")
    p.add_argument("--method", default="confidence_0.8")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.mode == "replay":
        if args.request or args.output:
            p.error("--request and --output apply to live mode only")
        print(
            json.dumps(
                display_record(read_record(args.record), replay=True), indent=2, ensure_ascii=False
            )
        )
    elif not live(args):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
