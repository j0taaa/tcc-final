#!/usr/bin/env python3
"""Replay a frozen, complete cohort of real dLLM states; never run a new model.

Each method runs in a bounded subprocess. Portable original-input proofs, exact
rational scores, native EPIC diagnostics and all unsuccessful attempts survive.
Use --verify for independent proof/batch checks and deterministic report rebuild.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import resource
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import fields, replace
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from statistics import median
from time import perf_counter

from mwpc_exact import (
    BenchmarkGrammar,
    BenchmarkInstance,
    ComponentProfiler,
    CompositionalByteLevelAdapter,
    ExactBackend,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
)
from mwpc_exact.budget_bounds import budget_input_fingerprint, validate_budget_batch
from mwpc_exact.budget_proof import fraction_data, read_budget_proof, verify_budget_proof
from mwpc_exact.evaluation.selection import select_exact_mwpc
from mwpc_exact.experiments.metadata import canonical_json_sha256, collect_system_metadata
from mwpc_research.live_evidence import snapshot_instance
from mwpc_research.tool_parser import catalog_byte_grammar, production_input

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "configs/experiments/m28_budgeted_real_replay_v1.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(
        gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    )


def write_json(path, value):
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def validate_sources(config, root=ROOT):
    for relative, expected in config["input_sha256"].items():
        if sha(root / relative) != expected:
            raise ValueError(f"Source hash mismatch: {relative}")
    paths = sorted((root / config["snapshots_directory"]).glob("*.json"))
    if len(paths) != config["expected_snapshots"] or any(
        str(path.relative_to(root)) not in config["input_sha256"] for path in paths
    ):
        raise ValueError("Snapshot cohort differs from the frozen config")
    return paths


def query_instance(record, step):
    """Losslessly compact token IDs; retain the original 64 slots and all domains."""
    saved = record["support"]
    ids = sorted({token for path in saved["paths"] for token in path})
    local = {token: i for i, token in enumerate(ids)}
    eos = 126081
    adapter = CompositionalByteLevelAdapter(
        tuple(None if t == eos else bytes(saved["emissions"][str(t)]) for t in ids)
    )
    rows = [
        tuple(sorted({local[path[p]] for path in saved["paths"]}))
        for p in range(record["config"]["slots"])
    ]
    grammar = catalog_byte_grammar(saved["catalog"])
    state = production_input(
        grammar,
        tuple(None if t is None else local[t] for t in step["canvas_before"]),
        tuple((p, local[t], w) for p, t, w in step["proposals"]),
        rows,
        adapter,
        local[eos],
    )
    return BenchmarkInstance(
        instance_id=f"geocoding-v2-step{step['step']:02}",
        grammar=BenchmarkGrammar("geocoding", grammar),
        selection_input=state,
        metadata={
            "origin": "real_model_precommit",
            "model_token_ids": ids,
            "source_seed": record["config"]["seed"],
            "source_task_id": "geocoding-v2",
            "source_forward_index": step["step"],
            "source_strategy": record["policy"]["name"],
            "target_injected": False,
            "model_revision": record["config"]["revision"],
            "tokenizer_revision": record["config"]["revision"],
            "historical_forward_seconds": step["forward_seconds"],
            "request": record["request"],
        },
    )


def cases(config, root=ROOT):
    originals = []
    for path in validate_sources(config, root):
        saved = read_json(path)
        if saved["target_injected"] or saved["source_strategy"] != "unconstrained":
            raise ValueError("Expected an unmodified pre-commit model capture")
        start = perf_counter()
        instance = snapshot_instance(saved, config["top_k"], len(saved["canvas"]))
        originals.append((instance, str(path.relative_to(root)), perf_counter() - start))
    record = read_json(root / config["query_record"])
    if (
        record["mode"] != "live"
        or len(record["generation"]["trace"]) != config["expected_query_steps"]
    ):
        raise ValueError("Query cohort differs from the frozen live trace")
    for step in record["generation"]["trace"]:
        start = perf_counter()
        originals.append(
            (query_instance(record, step), config["query_record"], perf_counter() - start)
        )
    for original, source, reconstruction_seconds in originals:
        if any(original.metadata[k] != config[k] for k in ("model_revision", "tokenizer_revision")):
            raise ValueError("Model/tokenizer revision mismatch")
        for profile in config["reward_profiles"]:
            state = original.selection_input
            specials = {*state.eos_policy.termination_token_ids, state.eos_policy.pad_token_id}
            excluded = ()
            if profile == "ordinary_primary":
                excluded = tuple(p.proposal_id for p in state.proposals if p.token_id in specials)
                state = replace(
                    state, proposals=tuple(p for p in state.proposals if p.token_id not in specials)
                )
            elif profile != "all_primary":
                raise ValueError("Unknown reward profile")
            yield replace(
                original,
                instance_id=f"{original.instance_id}-{profile.replace('_', '-')}",
                selection_input=state,
                metadata={
                    **dict(original.metadata),
                    "reward_profile": profile,
                    "excluded_special_proposal_ids": excluded,
                    "source_path": source,
                    "source_sha256": config["input_sha256"][source],
                    "input_reconstruction_seconds": reconstruction_seconds,
                    "proposal_policy": config["proposal_policy"],
                },
            )


def batch_row(state, budget, witness, positions):
    checked = validate_budget_batch(
        state, budget=budget, witness_token_ids=witness, committed_positions=positions
    )
    return {
        "budget": budget,
        "status": "feasible_on_support",
        "objective_value": fraction_data(checked.reward),
        "committed_positions": list(checked.committed_positions),
        "committed_proposal_ids": list(checked.committed_proposal_ids),
        "matched_proposal_ids": list(checked.matched_proposal_ids),
        "witness_token_ids": list(checked.witness_token_ids),
        "witness_text": checked.emitted_bytes.decode("utf-8"),
        "independent_batch_validation": True,
    }


def top_positions(state, witness, budget, permitted=None):
    rewards = defaultdict(Fraction)
    for p in state.proposals:
        if (
            p.weight > 0
            and witness[p.position] == p.token_id
            and (permitted is None or p.proposal_id in permitted)
        ):
            rewards[p.position] += Fraction(p.weight)
    return tuple(sorted(sorted(rewards, key=lambda p: (-rewards[p], p))[:budget]))


def finite_witness(state, assignments, timeout):
    canvas = tuple(assignments.get(p, t) for p, t in enumerate(state.canvas))
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            kind=SupportKind.EXPLICIT,
            vocabulary_size=state.tokenizer_adapter.vocabulary_size,
            required_special_token_ids=state.support.exactness_scope.included_special_tokens,
        ),
        explicit_support={
            p: row if canvas[p] is None else (canvas[p],)
            for p, row in enumerate(state.support.rows)
        },
    )
    restricted = replace(state, canvas=canvas, support=support, proposals=())
    return select_exact_mwpc(restricted, backend=ExactBackend.RUST, timeout_seconds=timeout)


def native_epic(state, config):
    from constrained_diffusion.constrain_utils import EOS, compile_lex_map
    from rustformlang.cfg import CFG

    from mwpc_exact.evaluation.epic_regular_cover import (
        EpicSelectionContext,
        select_epic_regular_cover,
    )
    from mwpc_research.tool_parser import epic_byte_grammar

    os.environ.update(config["epic_environment"])
    text, start, lex_rules = epic_byte_grammar(state.grammar)
    cfg = CFG.from_text(text, start).to_normal_form()
    specials = {*state.eos_policy.termination_token_ids, state.eos_policy.pad_token_id}

    def decode(token):
        return (
            EOS if token in specials else state.tokenizer_adapter.token_bytes(token).decode("utf-8")
        )

    context = EpicSelectionContext(
        words_full=tuple(None if t is None else decode(t) for t in state.canvas),
        prompt_length=0,
        cfg=cfg,
        decode_token=decode,
        lex_map=compile_lex_map(lex_rules),
        terminals=tuple(lex_rules),
    )
    return select_epic_regular_cover(state, context)


def baseline(state, method, config):
    rows = []
    timeout = config["finite_validation_timeout_seconds"]
    common = None
    if method == "unbudgeted_then_cap":
        common = select_exact_mwpc(state, backend=ExactBackend.RUST, timeout_seconds=timeout)
    elif method == "epic_regular_cover_then_cap":
        common = native_epic(state, config)
    for cap in range(1, config["max_budget"] + 1):
        start = perf_counter()
        if method == "confidence_preselection":
            chosen = sorted(state.proposals, key=lambda p: (-p.weight, p.position))[:cap]
            result = select_exact_mwpc(
                replace(state, proposals=tuple(chosen)),
                backend=ExactBackend.RUST,
                timeout_seconds=timeout,
            )
            witness = result.witness_token_ids
            positions = (
                ()
                if result.status.value != "optimal" or not witness
                else top_positions(state, witness, cap, {p.proposal_id for p in chosen})
            )
        elif method == "unbudgeted_then_cap":
            result = common
            witness = result.witness_token_ids
            positions = (
                ()
                if result.status.value != "optimal" or not witness
                else top_positions(state, witness, cap)
            )
        else:
            if common.status.value != "heuristic":
                rows.append({"budget": cap, "status": common.status.value, "objective_value": None})
                continue
            chosen = sorted(
                (p for p in state.proposals if p.proposal_id in common.selected_proposal_ids),
                key=lambda p: (-p.weight, p.position),
            )[:cap]
            result = finite_witness(state, {p.position: p.token_id for p in chosen}, timeout)
            witness = result.witness_token_ids
            positions = tuple(sorted(p.position for p in chosen))
        if result.status.value == "optimal" and witness is not None:
            row = batch_row(state, cap, witness, positions)
        else:
            row = {
                "budget": cap,
                "status": "infeasible_batch_on_support"
                if method == "epic_regular_cover_then_cap"
                and result.status.value == "infeasible_on_support"
                else result.status.value,
                "objective_value": None,
            }
        row["cap_and_validation_seconds"] = perf_counter() - start
        rows.append(row)
    return {"frontier": rows, "native_result": None if common is None else common.to_dict()}


def worker(job_path, output):
    job = read_json(job_path)
    config = job["config"]
    limit = config["max_address_space_mib"] * 1024**2
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    instance = BenchmarkInstance.from_dict(read_json(Path(job["input"])))
    state = instance.selection_input
    started = perf_counter()
    try:
        if job["method"] == "budgeted_rational":
            from mwpc_exact.budget_proof import budget_proof_data
            from mwpc_exact.budgeted_commit import (
                budgeted_commit_frontier,
                budgeted_progress_update,
            )

            profiler = ComponentProfiler(enabled=True)
            frontier = budgeted_commit_frontier(state, config["max_budget"], profiler=profiler)
            solve_seconds = perf_counter() - started
            proof = budget_proof_data(state, frontier)
            proof_name = f"proofs/{instance.instance_id}.json.gz"
            write_json(Path(job["directory"]) / proof_name, proof)
            rows = []
            for result in frontier:
                row = {
                    "budget": result.budget,
                    "status": result.status.value,
                    "objective_value": None,
                }
                if result.witness_token_ids is not None:
                    row = batch_row(
                        state, result.budget, result.witness_token_ids, result.committed_positions
                    )
                    row["status"] = result.status.value
                    if result.budget:
                        update_start = perf_counter()
                        updated, fallback = budgeted_progress_update(state, result)
                        row.update(
                            canvas_after=list(updated),
                            fallback_positions=list(fallback),
                            validated_update_seconds=perf_counter() - update_start,
                        )
                rows.append(row)
            report = {
                "frontier": rows,
                "proof": proof_name,
                "solver_seconds": solve_seconds,
                "profile": profiler.snapshot().to_dict(),
            }
        else:
            report = baseline(state, job["method"], config)
        report["status"] = "complete"
    except Exception as exc:
        report = {"status": "error", "frontier": [], "error": f"{type(exc).__name__}: {exc}"}
    report["worker_seconds"] = perf_counter() - started
    report["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    write_json(output, report)


def bounded_job(job, timeout):
    """No in-process signal timeout: the parent retains failures and kills children."""
    with tempfile.TemporaryDirectory(prefix="mwpc-real-replay-") as tmp:
        job_path, result_path = Path(tmp) / "job.json", Path(tmp) / "result.json"
        write_json(job_path, job)
        start = perf_counter()
        try:
            process = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    str(job_path),
                    "--output",
                    str(result_path),
                ],
                cwd=ROOT,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
            result = (
                read_json(result_path)
                if result_path.exists()
                else {
                    "status": "error",
                    "frontier": [],
                    "error": process.stderr[-2000:],
                    "returncode": process.returncode,
                }
            )
        except subprocess.TimeoutExpired:
            result = {"status": "timeout", "frontier": [], "timeout_seconds": timeout}
        result["process_seconds"] = perf_counter() - start
        return result


def run(config_path, directory):
    config = read_json(config_path)
    frozen = list(cases(config))
    system = collect_system_metadata(ROOT)
    if system.git_dirty is not False:
        raise ValueError(
            "Archive-producing execution requires committed code/config and a clean checkout"
        )
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory / "config.json", config)
    metadata = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "config_sha256": sha(config_path),
        "config_source": str(config_path.resolve().relative_to(ROOT)),
        "git_commit": system.git_commit,
        "git_dirty": system.git_dirty,
        "model_id": config["model_id"],
        "model_revision": config["model_revision"],
        "tokenizer_revision": config["tokenizer_revision"],
        "hardware_software": {
            f.name: dict(getattr(system, f.name))
            if f.name == "thread_environment"
            else getattr(system, f.name)
            for f in fields(system)
        },
        "source_model_metadata": read_json(
            ROOT / "docs/artifacts/raw/m17_review_v1/confirmation/metadata.json"
        ),
        "new_model_forward_seconds": None,
        "new_model_forwards": 0,
        "timing_scope": config["timing_scope"],
        "comparison_scope": config["comparison_scope"],
        "exactness_scope": "exact_on_support",
        "instance_count": len(frozen),
    }
    write_json(directory / "metadata.json", metadata)
    with (directory / "rows.jsonl").open("x") as output:
        for index, instance in enumerate(frozen):
            input_path = directory / "inputs" / f"{instance.instance_id}.json.gz"
            write_json(input_path, instance.to_dict())
            for method in config["methods"]:
                if (
                    method.startswith("epic")
                    and instance.metadata["reward_profile"] != "ordinary_primary"
                ):
                    continue
                job = {
                    "config": config,
                    "input": str(input_path.resolve()),
                    "method": method,
                    "directory": str(directory.resolve()),
                }
                timeout = (
                    config["budgeted_timeout_seconds"]
                    if method == "budgeted_rational"
                    else config["baseline_timeout_seconds"]
                )
                result = bounded_job(job, timeout)
                row = {
                    "instance_id": instance.instance_id,
                    "input": str(input_path.relative_to(directory)),
                    "input_fingerprint": budget_input_fingerprint(instance.selection_input),
                    "grammar_hash": canonical_json_sha256(
                        instance.selection_input.grammar.to_dict()
                    ),
                    "support": instance.selection_input.support.to_dict(),
                    "family": instance.grammar.grammar_id,
                    "reward_profile": instance.metadata["reward_profile"],
                    "seed": instance.metadata["source_seed"],
                    "method": method,
                    "git_commit": system.git_commit,
                    "model_id": config["model_id"],
                    "model_revision": config["model_revision"],
                    "tokenizer_revision": config["tokenizer_revision"],
                    "config_sha256": metadata["config_sha256"],
                    "exactness_scope": "exact_on_support",
                    "metadata_file": "metadata.json",
                    **result,
                }
                output.write(json.dumps(row, allow_nan=False) + "\n")
                output.flush()
                print(
                    f"{index + 1}/{len(frozen)} {instance.instance_id} {method}: "
                    f"{result['status']} ({result['process_seconds']:.2f}s)",
                    flush=True,
                )
    all_rows = [json.loads(line) for line in (directory / "rows.jsonl").read_text().splitlines()]
    write_json(
        directory / "status-counts.json",
        dict(Counter((r["method"] + ":" + r["status"]) for r in all_rows)),
    )
    write_json(
        directory / "manifest.json",
        {
            str(p.relative_to(directory)): sha(p)
            for p in sorted(directory.rglob("*"))
            if p.is_file()
        },
    )


def verify(directory):
    """Rebind every proof to a reconstructed archive input and check every batch."""
    manifest = read_json(directory / "manifest.json")
    inventory = {
        str(p.relative_to(directory))
        for p in directory.rglob("*")
        if p.is_file() and p != directory / "manifest.json"
    }
    if set(manifest) != inventory:
        raise ValueError("Archive manifest does not cover exactly the raw inventory")
    for name, digest in manifest.items():
        if sha(directory / name) != digest:
            raise ValueError(f"Archive hash mismatch: {name}")
    config = read_json(directory / "config.json")
    metadata = read_json(directory / "metadata.json")
    source_config = ROOT / metadata["config_source"]
    if sha(source_config) != metadata["config_sha256"] or read_json(source_config) != config:
        raise ValueError("Archive config differs from its immutable source")
    expected = {i.instance_id: i for i in cases(config)}
    rows = [json.loads(line) for line in (directory / "rows.jsonl").read_text().splitlines()]
    seen = set()
    certificates = 0
    for row in rows:
        key = (row["instance_id"], row["method"])
        if key in seen:
            raise ValueError("Duplicate attempted method/state")
        seen.add(key)
        original = expected[row["instance_id"]].selection_input
        instance = BenchmarkInstance.from_dict(read_json(directory / row["input"]))
        state = instance.selection_input
        if budget_input_fingerprint(state) != budget_input_fingerprint(original) or row[
            "input_fingerprint"
        ] != budget_input_fingerprint(state):
            raise ValueError("Saved instance differs from frozen source")
        if row["method"] == "budgeted_rational" and row["status"] == "complete":
            proof = read_json(directory / row["proof"])
            verify_budget_proof(proof)
            proof_state, frontier = read_budget_proof(proof)
            if budget_input_fingerprint(proof_state) != budget_input_fingerprint(state):
                raise ValueError("Proof belongs to a different original input")
            if len(frontier) != config["max_budget"] + 1 or len(row["frontier"]) != len(frontier):
                raise ValueError("Incomplete certified frontier")
            for result, item in zip(frontier, row["frontier"], strict=True):
                if (result.budget, result.status.value, fraction_data(result.objective_value)) != (
                    item["budget"],
                    item["status"],
                    item["objective_value"],
                ):
                    raise ValueError("Raw row does not match portable proof")
                if result.witness_token_ids is not None and (
                    list(result.witness_token_ids),
                    list(result.committed_positions),
                ) != (item["witness_token_ids"], item["committed_positions"]):
                    raise ValueError("Raw row witness differs from proof")
            certificates += len(frontier)
        for item in row["frontier"]:
            if item.get("witness_token_ids") is None:
                continue
            checked = batch_row(
                state, item["budget"], item["witness_token_ids"], item["committed_positions"]
            )
            for field in (
                "objective_value",
                "committed_proposal_ids",
                "matched_proposal_ids",
                "witness_text",
            ):
                if item[field] != checked[field]:
                    raise ValueError(f"Independent batch mismatch: {field}")
            if "canvas_after" in item:
                changed = {
                    p
                    for p, (before, after) in enumerate(
                        zip(state.canvas, item["canvas_after"], strict=True)
                    )
                    if before != after
                }
                if (
                    changed != set(item["committed_positions"]) | set(item["fallback_positions"])
                    or len(changed) > item["budget"]
                ):
                    raise ValueError("Incorrect physical update")
                if any(
                    state.canvas[p] is not None
                    or item["canvas_after"][p] != item["witness_token_ids"][p]
                    for p in changed
                ):
                    raise ValueError("Update is not a witness-preserving extension")
    expected_jobs = {
        (i, method)
        for i, instance in expected.items()
        for method in config["methods"]
        if not method.startswith("epic")
        or instance.metadata["reward_profile"] == "ordinary_primary"
    }
    if seen != expected_jobs:
        raise ValueError("Missing or unexpected cohort jobs")
    return rows, {
        "verification": "PASS",
        "instances": len(expected),
        "attempts": len(rows),
        "certificates": certificates,
    }


def summary(rows):
    groups = defaultdict(list)
    paired = {}
    for row in rows:
        groups[row["family"], row["reward_profile"], row["method"]].append(row)
        paired[row["instance_id"], row["method"]] = row
    result = []
    for (family, profile, method), items in sorted(groups.items()):
        completed = [r for r in items if r["status"] == "complete"]
        statuses = Counter(i["status"] for r in completed for i in r["frontier"])
        gaps = []
        for row in items:
            exact = paired.get((row["instance_id"], "budgeted_rational"))
            if method == "budgeted_rational" or exact is None:
                continue
            by_cap = {i["budget"]: i for i in exact["frontier"]}
            for item in row["frontier"]:
                optimal = by_cap.get(item["budget"])
                if (
                    optimal
                    and optimal["status"] == "optimal"
                    and item["status"] == "feasible_on_support"
                ):
                    gap = Fraction(*optimal["objective_value"]) - Fraction(*item["objective_value"])
                    if gap < 0:
                        raise ValueError("Feasible baseline exceeds the certified optimum")
                    gaps.append(gap)
        result.append(
            {
                "family": family,
                "reward_profile": profile,
                "method": method,
                "attempts": len(items),
                "execution_statuses": dict(Counter(r["status"] for r in items)),
                "frontier_statuses": dict(statuses),
                "completed_worker_seconds_median": median(r["worker_seconds"] for r in completed)
                if completed
                else None,
                "certified_paired_budget_cases": len(gaps),
                "strict_gaps": sum(g > 0 for g in gaps),
                "max_gap": fraction_data(max(gaps)) if gaps else None,
            }
        )
    return {
        "groups": result,
        "analysis_unit": "Source states; profiles and budgets are repeated measures, "
        "not independent tasks",
        "timing_censoring": "Complete-worker median excludes timed-out/error jobs, which remain "
        "in status counts; includes checking/proof serialization/update replay. "
        "No GPU speed claim.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.output)
    elif args.verify:
        rows, report = verify(args.verify)
        data = {**report, **summary(rows)}
        if args.summary:
            write_json(args.summary, data)
        print(json.dumps(data, indent=2))
    elif args.output:
        run(args.config, args.output)
    else:
        parser.error("--output or --verify is required")


if __name__ == "__main__":
    main()
