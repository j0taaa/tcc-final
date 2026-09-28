"""Controlled repair study; subprocess limits and immutable, source-linked JSONL."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import multiprocessing as mp
import resource
import subprocess
import tomllib
from collections import Counter, defaultdict
from dataclasses import asdict
from itertools import combinations, product
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

from mwpc_exact import (
    ComponentProfiler,
    CompositionalByteLevelAdapter,
    ExactBackend,
    SolveStatus,
    solve_exact_commit,
)
from mwpc_exact.experiments.metadata import canonical_json_sha256, collect_system_metadata
from mwpc_exact.repair import (
    BYTE_ADAPTER,
    json_repair_grammar,
    repair_tokens,
    strict_json_loads,
    structural_byte_support,
    structural_token_support,
)

ROOT = Path(__file__).resolve().parents[2]
REVISION = "08b83a6feb34df1a6011b80c3c00c7563e963b07"
SCHEMA = {
    "type": "object",
    "required": ["id", "payload"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer"},
        "payload": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["a", "b"],
                "additionalProperties": False,
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            },
        },
    },
}


def compact(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True)


def cases(config):
    """Corruptions are fixed by family, never selected after seeing a method's result."""
    result = []
    for index in range(config["documents"]):
        seed = config["seed"] + index
        rng = Random(seed)
        count = config["record_counts"][index % len(config["record_counts"])]
        target = {
            "id": rng.randrange(100, 999),
            "payload": [
                {"a": rng.randrange(10, 99), "b": rng.randrange(10, 99)} for _ in range(count)
            ],
        }
        clean = compact(target)
        payload_start = clean.index("[")
        for family in config["families"]:
            draft = clean
            if family == "opening":
                draft = clean[:payload_start] + clean[payload_start:].replace("{", "[")
            elif family == "closing":
                draft = clean[:-1].replace("}", "]") + "}"
            elif family == "separator":
                draft = clean[:payload_start] + clean[payload_start:].replace(":", ",")
            elif family == "missing_suffix":
                draft = clean[:-1]
            elif family == "semantic":
                wrong = json.loads(clean)
                wrong["payload"][0]["a"] += 1
                draft = compact(wrong)
            elif family != "valid":
                raise ValueError(f"unknown corruption: {family}")
            result.append(
                {
                    "case_id": f"{seed}-{family}",
                    "document_id": seed,
                    "seed": seed,
                    "family": family,
                    "draft": draft,
                    "expected": target,
                }
            )
    return result


def enumerate_min_edits(ids, rows, adapter, validator, deadline):
    """Independent increasing-Hamming-cost search, without CFG/parser internals."""
    variable = [i for i, row in enumerate(rows) if any(t != ids[i] for t in row)]
    checked = 0
    for count in range(len(variable) + 1):
        for positions in combinations(variable, count):
            for replacements in product(
                *(tuple(t for t in rows[i] if t != ids[i]) for i in positions)
            ):
                if perf_counter() >= deadline:
                    return {"status": "timeout", "output_text": None, "examined": checked}
                path = list(ids)
                for i, token in zip(positions, replacements, strict=True):
                    path[i] = token
                checked += 1
                try:
                    text = adapter.detokenize_bytes(path).decode("utf-8")
                    parsed = strict_json_loads(text)
                    validator.validate(parsed)
                except (ValueError, UnicodeError):
                    continue
                except Exception as error:
                    from jsonschema import ValidationError

                    if isinstance(error, ValidationError):
                        continue
                    raise
                return {
                    "status": "optimal",
                    "output_text": text,
                    "substitution_cost": float(count),
                    "examined": checked,
                    "guarantee": "minimum substitutions on the enumerated support and schema",
                }
    return {"status": "infeasible_on_support", "output_text": None, "examined": checked}


def child(send, job, adapter, grammar, validator, seconds, memory_mib):
    resource.setrlimit(resource.RLIMIT_AS, (memory_mib * 1024**2,) * 2)
    started = perf_counter()
    try:
        method = job["method"]
        if method in ("exact", "greedy"):
            profiler = ComponentProfiler(enabled=True)
            result = repair_tokens(
                job["ids"],
                adapter=adapter,
                grammar=grammar,
                alternatives=job["rows"],
                protected_byte_spans=job["locks"],
                method=method,
                backend=ExactBackend.RUST,
                timeout_seconds=seconds,
                profiler=profiler,
            ).to_dict()
            result["components"] = profiler.snapshot().to_dict()
        elif method == "feasibility":
            from mwpc_exact.repair import prepare_repair

            state, _ = prepare_repair(
                job["ids"],
                adapter=adapter,
                grammar=grammar,
                alternatives=job["rows"],
                protected_byte_spans=job["locks"],
            )
            profiler = ComponentProfiler(enabled=True)
            witness = solve_exact_commit(
                grammar,
                canvas=state.canvas,
                support=state.support,
                proposals=(),
                tokenizer_adapter=adapter,
                eos_policy=state.eos_policy,
                backend=ExactBackend.RUST,
                timeout_seconds=max(0.0, seconds - (perf_counter() - started)),
                profiler=profiler,
            )
            result = {
                "status": "feasible_on_support"
                if witness.status is SolveStatus.OPTIMAL
                else witness.status.value,
                "output_text": adapter.detokenize_bytes(witness.witness_token_ids).decode("utf-8")
                if witness.status is SolveStatus.OPTIMAL
                else None,
                "objective": "feasibility only; no edit-minimality guarantee",
                "certificate": witness.to_dict(),
                "components": profiler.snapshot().to_dict(),
            }
            if witness.status is SolveStatus.OPTIMAL:
                result["substitution_cost"] = float(
                    sum(a != b for a, b in zip(job["ids"], witness.witness_token_ids, strict=True))
                )
        elif method == "enumeration":
            result = enumerate_min_edits(
                job["ids"], job["rows"], adapter, validator, started + seconds
            )
        elif method == "unchanged":
            result = {"status": "unchanged", "output_text": job["draft"]}
        else:
            from json_repair import repair_json

            options = (
                {}
                if method == "json_repair"
                else {"schema": SCHEMA, "schema_repair_mode": method.removeprefix("schema_")}
            )
            result = {"status": "repaired", "output_text": repair_json(job["draft"], **options)}
        elapsed = perf_counter() - started
        if elapsed >= seconds:
            result = {"status": "timeout", "output_text": None, "phase": "whole repair"}
    except MemoryError:
        result = {"status": "error", "output_text": None, "error": "memory limit"}
    except Exception as error:
        result = {
            "status": "error",
            "output_text": None,
            "error": f"{type(error).__name__}: {error}",
        }
    result["repair_seconds"] = perf_counter() - started
    result["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    send.send(result)
    send.close()


def run_job(job, adapter, grammar, validator, config):
    # fork shares immutable tokenizer/grammar; time excludes one-time loading.
    context = mp.get_context("fork")
    receive, send = context.Pipe(duplex=False)
    seconds = max(0.0, config["timeout_seconds"] - job["construction_seconds"])
    process = context.Process(
        target=child, args=(send, job, adapter, grammar, validator, seconds, config["memory_mib"])
    )
    started = perf_counter()
    process.start()
    send.close()
    if receive.poll(seconds + config["supervisor_grace_seconds"]):
        try:
            result = receive.recv()
        except EOFError:
            result = {
                "status": "error",
                "output_text": None,
                "error": "worker exited without result",
            }
    else:
        result = {"status": "timeout", "output_text": None, "phase": "supervisor"}
    if process.is_alive():
        process.join(timeout=0.05)
    if process.is_alive():
        process.kill()
    process.join()
    receive.close()
    result["supervised_wall_seconds"] = perf_counter() - started
    result["construction_seconds"] = job["construction_seconds"]
    result["total_seconds"] = result.get("repair_seconds", seconds) + job["construction_seconds"]
    if result["total_seconds"] >= config["timeout_seconds"] and result["status"] != "error":
        result.update(status="timeout", output_text=None)
        result.pop("certificate", None)
        result.pop("substitution_cost", None)
    return result


def evaluate(output, expected):
    result = {
        "syntax_valid": False,
        "schema_valid": False,
        "semantic_success": False,
        "id_preserved": False,
    }
    if not isinstance(output, str):
        return result
    try:
        value = strict_json_loads(output)
    except (ValueError, UnicodeError):
        return result
    result["syntax_valid"] = True
    from jsonschema import Draft202012Validator

    result["schema_valid"] = Draft202012Validator(SCHEMA).is_valid(value)
    result["semantic_success"] = json.dumps(value, sort_keys=True) == json.dumps(
        expected, sort_keys=True
    )
    result["id_preserved"] = (
        isinstance(value, dict) and type(value.get("id")) is int and value["id"] == expected["id"]
    )
    return result


def load_tokenizer():
    from huggingface_hub import try_to_load_from_cache
    from tokenizers import Tokenizer

    path = try_to_load_from_cache("GSAI-ML/LLaDA-8B-Instruct", "tokenizer.json", revision=REVISION)
    if not isinstance(path, str):
        raise RuntimeError("pinned tokenizer not cached; no automatic network access")
    tokenizer = Tokenizer.from_file(path)
    pieces = tuple(
        tokenizer.id_to_token(i) if i < 126080 else None for i in range(tokenizer.get_vocab_size())
    )
    return (
        tokenizer,
        CompositionalByteLevelAdapter.from_token_pieces(pieces),
        hashlib.sha256(Path(path).read_bytes()).hexdigest(),
    )


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["profile"], row["case"]["family"], row["method"]].append(row)
    summary = []
    for (profile, family, method), group in sorted(groups.items()):
        summary.append(
            {
                "profile": profile,
                "family": family,
                "method": method,
                "runs": len(group),
                "documents": len({r["case"]["document_id"] for r in group}),
                "successes": sum(r["evaluation"]["semantic_success"] for r in group),
                "schema_valid": sum(r["evaluation"]["schema_valid"] for r in group),
                "id_preserved": sum(r["evaluation"]["id_preserved"] for r in group),
                "status_counts": dict(Counter(r["result"]["status"] for r in group)),
                "median_total_ms": 1000 * median(r["result"]["total_seconds"] for r in group),
            }
        )
    paired = defaultdict(lambda: defaultdict(list))
    for row in rows:
        paired[row["profile"], row["case"]["family"], row["case"]["document_id"]][
            row["method"]
        ].append(row)
    comparisons = defaultdict(list)
    for (profile, family, _document), methods in paired.items():
        exact = methods["exact"]
        for method, baseline in methods.items():
            if method == "exact":
                continue
            exact_ok = all(r["evaluation"]["semantic_success"] for r in exact)
            baseline_ok = all(r["evaluation"]["semantic_success"] for r in baseline)
            ratio = None
            if exact_ok and baseline_ok:
                ratio = median(r["result"]["total_seconds"] for r in baseline) / median(
                    r["result"]["total_seconds"] for r in exact
                )
            comparisons[profile, family, method].append((exact_ok, baseline_ok, ratio))
    paired_summary = []
    for (profile, family, method), pairs in sorted(comparisons.items()):
        ratios = [ratio for a, b, ratio in pairs if ratio is not None]
        interval = None
        if ratios:
            rng = Random(212000)
            samples = sorted(median(rng.choices(ratios, k=len(ratios))) for _ in range(2000))
            interval = [samples[49], samples[1949]]
        paired_summary.append(
            {
                "profile": profile,
                "family": family,
                "comparator": method,
                "documents": len(pairs),
                "exact_only_success": sum(a and not b for a, b, _ in pairs),
                "comparator_only_success": sum(b and not a for a, b, _ in pairs),
                "both_success": sum(a and b for a, b, _ in pairs),
                "neither_success": sum(not a and not b for a, b, _ in pairs),
                "median_paired_speedup": median(ratios) if ratios else None,
                "speedup_bootstrap_95": interval,
            }
        )
    return {
        "groups": summary,
        "paired_documents": paired_summary,
        "scope": "controlled corruption; no model inference; no population error-rate claim",
    }


def read_archive(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    for filename, key in (("rows.jsonl.gz", "rows_sha256"), ("metadata.json", "metadata_sha256")):
        if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != manifest[key]:
            raise ValueError(f"archive hash mismatch: {filename}")
    with gzip.open(directory / "rows.jsonl.gz", "rt") as file:
        rows = [json.loads(line) for line in file]
    if len(rows) != manifest["rows"]:
        raise ValueError("archive row count mismatch")
    for row in rows:
        if evaluate(row["result"].get("output_text"), row["case"]["expected"]) != row["evaluation"]:
            raise ValueError("independent output evaluation mismatch")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--analyze", type=Path)
    args = parser.parse_args()
    if args.analyze:
        rows = read_archive(args.analyze)
        print(json.dumps(summarize(rows), indent=2))
        return
    if args.config is None or args.run_directory is None:
        parser.error("--config and --run-directory are required")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise RuntimeError("freeze source/config in a clean local commit before measurement")
    config = tomllib.loads(args.config.read_text())
    if importlib.metadata.version("json-repair") != config["json_repair_version"]:
        raise RuntimeError("comparator version differs from frozen config")
    from json_repair import repair_json
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(SCHEMA)
    # Warm dependency initialization equally; no input-specific repair decisions cached.
    repair_json('{"id":0,"payload":[]}', schema=SCHEMA)
    tokenizer, llada_adapter, tokenizer_hash = (
        load_tokenizer() if "llada" in config["profiles"] else (None, None, None)
    )
    grammar = json_repair_grammar(
        record_schema=config["grammar_profile"] == "schema", root_object=True
    )
    metadata = {
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "git_dirty": False,
        "config": config,
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "grammar_sha256": canonical_json_sha256(grammar.to_dict()),
        "schema_sha256": canonical_json_sha256(SCHEMA),
        "model": {
            "id": None,
            "revision": None,
            "reason": "controlled corruption; no model inference",
        },
        "tokenizer": {
            "id": "GSAI-ML/LLaDA-8B-Instruct",
            "revision": REVISION,
            "file_sha256": tokenizer_hash,
        },
        "exactness_scope": "exact_on_support",
        "support_policy": (
            "structural same-byte-length token alternatives; original retained; "
            "max 32 variants; finite slots; no EOS"
        ),
        "system": asdict(collect_system_metadata(ROOT)),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("json-repair", "jsonschema", "tokenizers")
        },
    }
    output = args.run_directory
    output.mkdir(parents=True, exist_ok=False)
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    rows = []
    with gzip.open(output / "rows.jsonl.gz", "wt") as raw:
        for case_index, case in enumerate(cases(config)):
            for profile in config["profiles"]:
                adapter = BYTE_ADAPTER if profile == "bytes" else llada_adapter
                began = perf_counter()
                ids = (
                    tuple(case["draft"].encode())
                    if profile == "bytes"
                    else tuple(tokenizer.encode(case["draft"], add_special_tokens=False).ids)
                )
                if adapter.detokenize_bytes(ids) != case["draft"].encode():
                    raise RuntimeError("tokenizer round trip differs from raw bytes")
                support = (
                    structural_byte_support(case["draft"])
                    if profile == "bytes"
                    else structural_token_support(ids, adapter)
                )
                # The ID location follows the shared input format, not a target answer.
                locks = ((6, case["draft"].index(",")),)
                from mwpc_exact.repair import prepare_repair

                state, locked = prepare_repair(
                    ids,
                    adapter=adapter,
                    grammar=grammar,
                    alternatives=support,
                    protected_byte_spans=locks,
                )
                construction = perf_counter() - began
                for repetition in range(config["repetitions"]):
                    methods = config["methods"]
                    shift = (case_index + repetition) % len(methods)
                    for method in methods[shift:] + methods[:shift]:
                        job = {
                            "method": method,
                            "draft": case["draft"],
                            "ids": ids,
                            "rows": state.support.rows,
                            "locks": locks,
                            "construction_seconds": construction
                            if method in ("exact", "greedy", "enumeration", "feasibility")
                            else 0.0,
                        }
                        result = run_job(job, adapter, grammar, validator, config)
                        row = {
                            "metadata": metadata,
                            "profile": profile,
                            "case": case,
                            "method": method,
                            "repetition": repetition,
                            "input_sha256": canonical_json_sha256(case["draft"]),
                            "support_sha256": canonical_json_sha256(state.support.rows),
                            "draft_token_ids": ids,
                            "support_rows": state.support.rows,
                            "protected_positions": locked,
                            "result": result,
                            "evaluation": evaluate(result.get("output_text"), case["expected"]),
                        }
                        raw.write(json.dumps(row, allow_nan=False) + "\n")
                        raw.flush()
                        rows.append(row)
            print(f"{case_index + 1}/{len(cases(config))} cases", flush=True)
    manifest = {
        "rows": len(rows),
        "rows_sha256": hashlib.sha256((output / "rows.jsonl.gz").read_bytes()).hexdigest(),
        "metadata_sha256": hashlib.sha256((output / "metadata.json").read_bytes()).hexdigest(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "summary.json").write_text(json.dumps(summarize(rows), indent=2) + "\n")


if __name__ == "__main__":
    main()
