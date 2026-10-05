"""Frozen larger-canvas MDLM audit with an independent exact array reference.

Normal tests and --verify do not load/download a model. Full logits stay in
the caller's local capture; portable original inputs and every outcome are
archived. Reference inference is standard transfer, not a competitor binary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from random import Random
from time import perf_counter

from scripts.exact_commit.capture_mdlm_probability import planned_case_ids
from scripts.exact_commit.probability_audit_controls import START, compile_array_plan
from scripts.exact_commit.run_conflict_real import read, sha, system_data, write

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    ExactBackend,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
)
from mwpc_exact.budget_proof import fraction_data
from mwpc_exact.conflict_proof import read_state, state_data
from mwpc_exact.evaluation.selection import SelectionInput
from mwpc_exact.experiments.metadata import collect_system_metadata
from mwpc_exact.language_coverage import terminal_alphabet_coverage
from mwpc_exact.mass_certificate import PosteriorScope, ProbabilityInput, verify_mass_proof
from mwpc_exact.mass_solver import probability_partition
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf

ROOT = Path(__file__).resolve().parents[2]


def is_schema_array(raw, one_child):
    if not raw or any(byte not in b"[]," for byte in raw):
        return False
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        return False
    pending = [value]
    while pending:
        item = pending.pop()
        if not isinstance(item, list) or (one_child and len(item) > 1):
            return False
        pending.extend(item)
    return True


def make_grammar(one_child):
    builder = _SourceGrammarBuilder(("S", "L"), start="S")
    builder.rule("S", b"[]")
    builder.rule("S", b"[", "S" if one_child else "L", b"]")
    if not one_child:
        builder.rule("L", "S")
        builder.rule("L", "S", b",", "L")
    return normalize_to_cnf(builder.build()).grammar


def encode_input(inputs):
    return {
        "input": state_data(inputs.state),
        "probabilities": [[fraction_data(p) for p in row] for row in inputs.probabilities],
        "input_fingerprint": inputs.fingerprint,
    }


def decode_input(data):
    result = ProbabilityInput(
        read_state(data["input"]),
        tuple(tuple(Fraction(*p) for p in row) for row in data["probabilities"]),
    )
    if result.fingerprint != data["input_fingerprint"]:
        raise ValueError("original probability input fingerprint differs")
    return result


def prepare_input(capture, case, config):
    import numpy as np

    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        read(capture / "tokenizer-pieces.json.gz")
    )
    with np.load(capture / case["array_file"], allow_pickle=False) as data:
        raw, logits = data["probabilities"], data["logits"]
    if raw.shape != (case["slots"], adapter.vocabulary_size) or not np.isfinite(raw).all():
        raise ValueError("invalid full-vocabulary probability shape")
    if (raw < 0).any() or logits.shape != raw.shape or not np.isfinite(logits).all():
        raise ValueError("invalid recorded network predictions")
    normalized = logits.astype(np.float64)
    normalized[:, config["mask_token_id"]] = -np.inf
    normalized -= normalized.max(axis=1, keepdims=True)
    expected = np.exp(normalized)
    expected /= expected.sum(axis=1, keepdims=True)
    if not np.allclose(raw, expected, rtol=2e-14, atol=0):
        raise ValueError("saved probabilities differ from original full-logit softmax")
    one_child = case["probe"]["grammar"] == "recursive_one_child_arrays"
    alphabet = {91, 93} if one_child else {91, 93, 44}
    compatible = {
        t
        for t, emission in enumerate(adapter.emissions)
        if emission is not None and set(emission) <= alphabet
    }
    masked = case["masked_positions"]
    rows = {i: (t,) for i, t in enumerate(case["canvas"]) if t is not None}
    probabilities = {i: (Fraction(1),) for i in rows}
    normalization = []
    for offset, position in enumerate(masked):
        original = tuple(Fraction(float(v)) for v in raw[offset])
        total = sum(original, Fraction())
        if not total:
            raise ValueError("zero full-vocabulary probability row")
        normalization.append(fraction_data(total))
        top = {
            int(t)
            for t in np.argsort(-raw[offset], kind="stable")[: config["top_k"]]
            if adapter.emissions[int(t)] is not None
        }
        rows[position] = tuple(sorted(compatible | top))
        probabilities[position] = tuple(original[t] / total for t in rows[position])
    canvas = tuple(case["canvas"])
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            SupportKind.EXPLICIT,
            adapter.vocabulary_size,
            pruning_description="top8_plus_complete_terminal_alphabet",
        ),
        explicit_support=rows,
    )
    state = SelectionInput(
        make_grammar(one_child), canvas, (), support, adapter, EOSPolicy(EOSMode.ABSENT)
    )
    inputs = ProbabilityInput(state, tuple(probabilities[i] for i in range(len(canvas))))
    prefix = b"".join(adapter.emissions[t] for t in canvas[: masked[0]])
    suffix = b"".join(adapter.emissions[t] for t in canvas[masked[-1] + 1 :])
    if prefix != case["probe"]["prefix"].encode() or suffix != case["probe"]["suffix"].encode():
        raise ValueError("fixed canvas differs from the declared application")
    if masked != list(range(masked[0], masked[0] + case["slots"])):
        raise ValueError("masked positions differ from finite slot specification")
    return inputs, normalization


def reference(inputs, one_child, seed, repetitions):
    alphabet = {91, 93} if one_child else {91, 93, 44}
    required = {
        token
        for token, emission in enumerate(inputs.state.tokenizer_adapter.emissions)
        if emission is not None and set(emission) <= alphabet
    }
    for fixed, row in zip(inputs.state.canvas, inputs.state.support.rows, strict=True):
        if fixed is None and not required <= set(row):
            raise ValueError("exact full-vocabulary reference lacks a compatible original token")
    started = perf_counter()
    plan = compile_array_plan(
        inputs.state.tokenizer_adapter.emissions, inputs.state.support.rows, one_child=one_child
    )
    compilation = perf_counter() - started
    plan.forward(inputs.probabilities)  # one declared warmup
    times = []
    mass = None
    for _ in range(repetitions):
        started = perf_counter()
        z, paths = plan.forward(inputs.probabilities)
        forward = perf_counter() - started
        started = perf_counter()
        suffix = plan.backward(inputs.probabilities)
        backward = perf_counter() - started
        if suffix[0].get(START, Fraction()) != z:
            raise ValueError("independent forward/backward masses disagree")
        sample = None
        started = perf_counter()
        if z:
            witness = plan.sample(inputs.probabilities, suffix, Random(seed))
            sample = inputs.state.tokenizer_adapter.detokenize_bytes(witness).decode()
            if not is_schema_array(sample.encode(), one_child):
                raise ValueError("reference sample rejected by independent JSON/schema parser")
        sampling = perf_counter() - started
        times.append(
            {"forward_seconds": forward, "backward_seconds": backward, "sample_seconds": sampling}
        )
        if mass is not None and mass != z:
            raise ValueError("reference repeated queries disagree")
        mass = z
    return {
        "valid_mass": fraction_data(z),
        "positive_valid_token_paths": paths,
        "compilation_seconds": compilation,
        "timings": times,
        "sample": sample,
        "state_cells": plan.state_cells,
        "warmup_queries": 1,
        "exactness_scope": "full_predictive_by_independent_terminal_alphabet_coverage",
        "implementation": "independent_standard_counter_forward_backward_not_published_decoder",
    }


def worker(input_path, config_path, output, limit):
    config = read(config_path)
    resource.setrlimit(resource.RLIMIT_AS, (config["address_space_bytes"],) * 2)
    encoded = read(input_path)
    inputs = decode_input(encoded)
    started = perf_counter()
    proof = probability_partition(
        inputs,
        max_oracle_calls=limit,
        requested_tv=Fraction(*config["tolerance"]),
        scope=PosteriorScope.FULL,
        backend=ExactBackend.RUST,
        language_coverage=terminal_alphabet_coverage(inputs.state.grammar),
        timeout_seconds=config["external_timeout_seconds"],
    )
    elapsed = perf_counter() - started
    write(
        output,
        {
            "proof": proof,
            "solve_internal_check_seconds": elapsed,
            "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
    )


def validate_partition(inputs, proof, z, one_child, seed, tolerance):
    started = perf_counter()
    result = verify_mass_proof(proof, expected_input=inputs)
    external_check = perf_counter() - started
    if not result.lower <= z <= result.upper(PosteriorScope.FULL):
        raise ValueError("CORRECTNESS GATE: exact mass outside certified envelope")
    for witness, mass in result.accepted:
        raw = inputs.state.tokenizer_adapter.detokenize_bytes(witness)
        if not is_schema_array(raw, one_child):
            raise ValueError("CORRECTNESS GATE: accepted witness fails independent JSON/schema")
        if mass != inputs.box_mass(tuple((t,) for t in witness)):
            raise ValueError("CORRECTNESS GATE: accepted probability differs from original rows")
    true_tv = None
    if result.lower:
        true_tv = 1 - result.lower / z
        if true_tv > result.tv_bound(PosteriorScope.FULL):
            raise ValueError("CORRECTNESS GATE: underestimated conditional error")
    generic = (
        (result.unresolved + result.omitted) / (result.lower + result.unresolved + result.omitted)
        if result.lower
        else None
    )
    sample = None
    admitted = (
        result.tv_bound(PosteriorScope.FULL) is not None
        and result.tv_bound(PosteriorScope.FULL) <= tolerance
    )
    if admitted:
        witness = result.sample(Random(seed), scope=PosteriorScope.FULL, max_tv=tolerance)
        sample = inputs.state.tokenizer_adapter.detokenize_bytes(witness).decode()
        if not is_schema_array(sample.encode(), one_child):
            raise ValueError("CORRECTNESS GATE: certificate sample fails independent JSON/schema")
    return {
        "external_check_seconds": external_check,
        "true_tv": fraction_data(true_tv),
        "certified_tv": fraction_data(result.tv_bound(PosteriorScope.FULL)),
        "generic_tv": fraction_data(generic),
        "sample": sample,
        "admitted": admitted,
        "oracle_calls": result.oracle_calls,
        "accepted_paths": len(result.accepted),
        "lower": fraction_data(result.lower),
        "upper": fraction_data(result.upper(PosteriorScope.FULL)),
    }


def run(capture, output):
    config = read(capture / "config.json")
    metadata = read(capture / "metadata.json")
    system = collect_system_metadata(ROOT)
    if system.git_dirty is not False:
        raise ValueError("commit producing code/config before the audit")
    if metadata["recorded_forwards"] != len(planned_case_ids(config)):
        raise ValueError("capture forward inventory differs from frozen grid")
    inventory = read(capture / "manifest.json")
    for name, expected in inventory.items():
        if sha(capture / name) != expected:
            raise ValueError(f"capture source changed: {name}")
    output.mkdir(parents=True, exist_ok=False)
    write(output / "config.json", config)
    write(output / "capture-metadata.json", metadata)
    write(output / "capture-manifest.json", inventory)
    write(
        output / "metadata.json",
        {
            "git_commit": system.git_commit,
            "git_dirty": False,
            "config_sha256": metadata["config_sha256"],
            "seed": config["seed"],
            "hardware_software": system_data(system),
            "model_revision": config["model_revision"],
            "tokenizer_revision": config["tokenizer_revision"],
            "full_logit_data": "ignored_local_capture_with_committed_SHA256_manifest",
        },
    )
    rows_path = output / "rows.jsonl"
    with rows_path.open("x") as rows:
        for case_id in planned_case_ids(config):
            case = read(capture / f"{case_id}.json")
            if case["id"] != case_id or case["seed"] != config["seed"]:
                raise ValueError("capture case/config lineage mismatch")
            started = perf_counter()
            inputs, normalization = prepare_input(capture, case, config)
            construction = perf_counter() - started
            encoded = encode_input(inputs)
            encoded.update(
                case=case,
                normalization=normalization,
                source_array_sha256=inventory[case["array_file"]],
            )
            input_path = output / "inputs" / f"{case_id}.json.gz"
            write(input_path, encoded)
            one_child = case["probe"]["grammar"] == "recursive_one_child_arrays"
            ref = reference(inputs, one_child, config["seed"], config["reference_repetitions"])
            write(output / "references" / f"{case_id}.json", ref)
            for limit in config["oracle_limits"]:
                artifact = output / "jobs" / f"{case_id}-k{limit}.json.gz"
                command = [
                    sys.executable,
                    "-m",
                    "scripts.exact_commit.run_probability_audit",
                    "--worker",
                    "--input",
                    str(input_path),
                    "--config",
                    str(output / "config.json"),
                    "--output",
                    str(artifact),
                    "--limit",
                    str(limit),
                ]
                started = perf_counter()
                process = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                )
                timed_out = False
                try:
                    stdout, stderr = process.communicate(timeout=config["external_timeout_seconds"])
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, stderr = process.communicate()
                    timed_out = True
                common = {
                    "id": case_id,
                    "slots": case["slots"],
                    "family": case["probe"]["grammar"],
                    "limit": limit,
                    "git_commit": system.git_commit,
                    "seed": config["seed"],
                    "model_revision": config["model_revision"],
                    "tokenizer_revision": config["tokenizer_revision"],
                    "config_sha256": metadata["config_sha256"],
                    "input_fingerprint": inputs.fingerprint,
                    "grammar_sha256": hashlib.sha256(
                        json.dumps(inputs.state.grammar.to_dict(), sort_keys=True).encode()
                    ).hexdigest(),
                    "support_sha256": inputs.state.support.fingerprint,
                    "exactness_scope": inputs.state.support.exactness_scope.to_dict(),
                    "reference_scope": PosteriorScope.FULL.value,
                    "model_forward_seconds": case["forward_seconds"],
                    "input_construction_seconds": construction,
                    "external_wall_seconds": perf_counter() - started,
                    "peak_memory_scope": "fresh_worker_max_RSS_including_imports",
                }
                if timed_out:
                    common.update(
                        status="external_timeout",
                        admitted=False,
                        worker_returncode=process.returncode,
                    )
                elif process.returncode:
                    common.update(
                        status="worker_error",
                        admitted=False,
                        worker_returncode=process.returncode,
                        diagnostic=(stdout + stderr).decode(errors="replace")[-2000:],
                    )
                else:
                    job = read(artifact)
                    checked = validate_partition(
                        inputs,
                        job["proof"],
                        Fraction(*ref["valid_mass"]),
                        one_child,
                        config["seed"],
                        Fraction(*config["tolerance"]),
                    )
                    common.update(
                        status=job["proof"]["status"],
                        **checked,
                        solve_internal_check_seconds=job["solve_internal_check_seconds"],
                        max_rss_kib=job["max_rss_kib"],
                        artifact=str(artifact.relative_to(output)),
                    )
                rows.write(json.dumps(common, sort_keys=True, allow_nan=False) + "\n")
                rows.flush()
                print(
                    json.dumps(
                        {
                            k: common[k]
                            for k in ("id", "limit", "status", "admitted", "external_wall_seconds")
                        }
                    ),
                    flush=True,
                )
    write(
        output / "manifest.json",
        {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*")) if p.is_file()},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.worker:
        worker(args.input, args.config, args.output, args.limit)
    else:
        run(args.capture.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
