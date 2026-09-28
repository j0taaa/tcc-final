#!/usr/bin/env python3
"""Replay the upstream wrapper's official completion on saved final token states."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import platform
import re
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from mwpc_research.tool_parser import catalog_byte_grammar, epic_byte_grammar, epic_lexical_grammar
from mwpc_research.tool_screen import execute_tool_call, normalize_tool_call

ROOT = Path(__file__).resolve().parents[2]


def recover(row, calls, timeout_seconds=120):
    from constrained_diffusion.constrain_utils import (
        EOS,
        autocomplete_valid,
        compile_lex_map,
        generated_language,
        partial_output_from_tokens,
    )
    from rustformlang.cfg import CFG

    if row["status"] == "complete":
        return {
            "recovery_status": "not_needed",
            "recovery_output": None,
            "recovery_seconds": 0.0,
            "recreated_setup_seconds": 0.0,
            "recovery_failure": None,
        }
    begin = time.perf_counter()
    text, start, rules = (
        epic_lexical_grammar(calls)
        if row["method"].startswith("epic_lexical_")
        else epic_byte_grammar(catalog_byte_grammar(calls))
    )
    assert rules == row["epic_lex_rules"]
    grammar = CFG.from_text(text, start).to_normal_form().to_normal_form()
    lex_map = compile_lex_map(rules)
    emissions = {int(t): bytes(b).decode() for t, b in row["token_emissions"].items()}
    words = [
        None if t == 126336 else EOS if t in (126081, 126348) else emissions[t]
        for t in row["token_ids"]
    ]
    setup = time.perf_counter() - begin
    previous = signal.getsignal(signal.SIGALRM)

    def deadline(*_):
        raise TimeoutError("official recovery deadline")

    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    begin = time.perf_counter()
    output = None
    failure = None
    try:
        partial, first_gap, eos_adj = partial_output_from_tokens(words, None)
        output = autocomplete_valid(
            partial_output=partial,
            first_token_gap=first_gap,
            last_token_eos_adj=eos_adj,
            generated_lang=generated_language(words, lex_map, grammar.get_terminals()),
            lex_map=rules,
            subtokens={},
            constraint_lang=grammar,
        )
        status = "recovered" if output is not None else "no_completion"
    except TimeoutError as exc:
        status = "timeout"
        failure = str(exc)
    except Exception as exc:
        status = "error"
        failure = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        elapsed = time.perf_counter() - begin
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    # Independently preserve fixed fragments; gaps may be any string, as upstream.
    fragments = []
    for word in words:
        if word is EOS:
            break
        fragments.append(".*" if word is None else re.escape(word))
    if EOS not in words:
        # The original wrapper permits an open tail when EOS was never committed.
        fragments.append(".*")
    preserved = output is None or re.fullmatch("".join(fragments), output, re.DOTALL) is not None
    return {
        "recovery_status": status,
        "recovery_output": output,
        "recovery_seconds": elapsed,
        "recreated_setup_seconds": setup,
        "recovery_failure": failure,
        "fixed_fragments_preserved": preserved,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config_bytes = args.config.read_bytes()
    config = json.loads(config_bytes)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise SystemExit("Freeze source/config before recovery replay")
    import torch

    torch.set_num_threads(config["cpu_threads"])
    output = ROOT / config["output_root"] / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output.mkdir(parents=True, exist_ok=False)
    (output / "config.json").write_bytes(config_bytes)
    metadata = {
        "git_commit": commit,
        "seed": config["seed"],
        "python": platform.python_version(),
        "cpu": platform.processor(),
        "torch": importlib.metadata.version("torch"),
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "upstream_commit": subprocess.check_output(
            ["git", "-C", "vendor/EPIC-Decoding", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "model_forwards": 0,
        "kind": "official_wrapper_recovery_replay",
        "timing_scope": (
            "CPU recovery only; setup recreated outside timing; not a jointly timed pipeline"
        ),
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    for relative in config["cohorts"]:
        folder = ROOT / relative
        support = json.loads((folder / "support.json").read_text())
        compressed = (folder / "results.jsonl.gz").read_bytes()
        parent_hash = hashlib.sha256(compressed).hexdigest()
        rows = [json.loads(line) for line in gzip.decompress(compressed).splitlines()]
        for index, row in enumerate(rows):
            if row["method"] == "exact":
                continue
            calls = [support["catalog"][i] for i in row["active_catalog_indices"]]
            result = recover(row, calls, config["timeout_seconds"])
            effective = (
                result["recovery_output"]
                if result["recovery_status"] == "recovered"
                else row["output"]
            )
            complete = row["status"] == "complete" or result["recovery_status"] == "recovered"
            normal = normalize_tool_call(effective)
            record = {
                **metadata,
                **result,
                "cohort": relative,
                "parent_sha256": parent_hash,
                "parent_record": index,
                "task_id": row["task"]["id"],
                "method": row["method"],
                "model_id": row["model_id"],
                "model_revision": row["model_revision"],
                "tokenizer_revision": row["tokenizer_revision"],
                "generation_seed": row["seed"],
                "active_grammar_hash": row["active_grammar_hash"],
                "support_scope": "upstream abstract gaps and open tail; no finite-slot certificate",
                "effective_output": effective,
                "effective_complete": complete,
                "correct": complete and normal == row["task"]["expected"],
                "numeric_correct": complete
                and normal in calls
                and execute_tool_call(effective) == execute_tool_call(row["task"]["expected"]),
                "valid_call": complete and normal in calls,
            }
            with (output / "results.jsonl").open("a") as stream:
                stream.write(json.dumps(record, allow_nan=False) + "\n")
        print(json.dumps({"cohort": relative, "parent_records": len(rows)}), flush=True)
    print(f"ARTIFACT_DIR={output}", flush=True)


if __name__ == "__main__":
    main()
