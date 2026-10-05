"""Evaluate every frozen fresh-probe cell; retain all statuses and certificates."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from fractions import Fraction
from itertools import product
from pathlib import Path
from random import Random
from time import perf_counter

from scripts.exact_commit.run_conflict_real import read, sha, system_data, write

from mwpc_exact import (
    CompositionalByteLevelAdapter,
    EOSMode,
    EOSPolicy,
    SupportKind,
    SupportPolicy,
    build_per_position_support,
)
from mwpc_exact.budget_proof import fraction_data
from mwpc_exact.evaluation.selection import SelectionInput
from mwpc_exact.experiments.metadata import collect_system_metadata
from mwpc_exact.language_coverage import finite_yield_bounds
from mwpc_exact.mass_certificate import PosteriorScope, ProbabilityInput, verify_mass_proof
from mwpc_exact.mass_solver import probability_partition
from mwpc_exact.probabilistic_update import certified_parallel_update
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.normalization import normalize_to_cnf

ROOT = Path(__file__).resolve().parents[2]


def independent_catalog_paths(values, emissions, slots):
    # Independent one/two-slot control: enumerate substring cut points and
    # every original token alias, rather than using the CFG/coverage DFS.
    by_bytes = defaultdict(list)
    for t, emission in enumerate(emissions):
        if emission is not None:
            by_bytes[emission].append(t)
    paths = set()
    for word in values:
        if slots == 1:
            paths.update((t,) for t in by_bytes[word])
        elif slots == 2:
            for cut in range(1, len(word)):
                paths.update(product(by_bytes[word[:cut]], by_bytes[word[cut:]]))
        else:
            raise ValueError("frozen independent control covers only one/two slots")
    return tuple(sorted(paths))


def inputs_for(archive, case, policy):
    import numpy as np

    config = read(archive / "config.json")
    adapter = CompositionalByteLevelAdapter.from_token_pieces(
        read(archive / "tokenizer-pieces.json.gz")
    )
    arrays = np.load(archive / case["array_file"], allow_pickle=False)
    raw = arrays["probabilities"]
    if (
        raw.shape != (case["slots"], adapter.vocabulary_size)
        or not np.isfinite(raw).all()
        or (raw < 0).any()
    ):
        raise ValueError("invalid archived full predictive matrix")
    full = []
    for row in raw:
        rationals = [Fraction(float(v)) for v in row]
        total = sum(rationals, Fraction())
        if not total:
            raise ValueError("zero predictive row")
        full.append(tuple(v / total for v in rationals))
    allowed = tuple(v.encode() for v in case["probe"]["values"])
    catalog = independent_catalog_paths(allowed, adapter.emissions, case["slots"])
    masked = case["masked_positions"]
    rows = {i: (t,) for i, t in enumerate(case["canvas"]) if t is not None}
    for offset, position in enumerate(masked):
        options = {path[offset] for path in catalog}
        if policy == "top8_plus_catalog":
            options.update(
                int(t)
                for t in np.argsort(-raw[offset], kind="stable")[: config["top_k"]]
                if adapter.emissions[int(t)] is not None
            )
        # No legal sequence for this physical length: retain a declared model
        # alternative, never fabricate a positive result or an empty API row.
        if not options:
            options.add(
                next(
                    int(t)
                    for t in np.argsort(-raw[offset], kind="stable")
                    if adapter.emissions[int(t)] is not None
                )
            )
        rows[position] = tuple(sorted(options))
    canvas = tuple(case["canvas"])
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(
            SupportKind.EXPLICIT, adapter.vocabulary_size, pruning_description=policy
        ),
        explicit_support=rows,
    )
    builder = _SourceGrammarBuilder(("S",), start="S")
    for value in allowed:
        builder.rule(
            "S", case["probe"]["prefix"].encode() + value + case["probe"]["suffix"].encode()
        )
    grammar = normalize_to_cnf(builder.build()).grammar
    state = SelectionInput(grammar, canvas, (), support, adapter, EOSPolicy(EOSMode.ABSENT))
    probabilities = []
    for i, row in enumerate(support.rows):
        probabilities.append(
            tuple(full[masked.index(i)][t] for t in row) if i in masked else (Fraction(1),)
        )
    predictive = ProbabilityInput(state, tuple(probabilities))
    exact = {}
    for path in catalog:
        witness = list(canvas)
        for i, t in zip(masked, path, strict=True):
            witness[i] = t
        exact[tuple(witness)] = product_mass(full, path)
    return predictive, exact


def product_mass(full, path):
    mass = Fraction(1)
    for row, t in zip(full, path, strict=True):
        mass *= row[t]
    return mass


def run(archive, output):
    config = read(archive / "config.json")
    source_metadata = read(archive / "metadata.json")
    for rel, h in read(archive / "manifest.json").items():
        if sha(archive / rel) != h:
            raise ValueError("fresh capture hash changed")
    system = collect_system_metadata(ROOT)
    if system.git_dirty is not False:
        raise ValueError("commit producing code before execution")
    output.mkdir(parents=True, exist_ok=False)
    write(output / "config.json", config)
    write(
        output / "metadata.json",
        {
            "git_commit": system.git_commit,
            "git_dirty": False,
            "hardware_software": system_data(system),
            "capture_metadata": source_metadata,
            "capture_manifest_sha256": sha(archive / "manifest.json"),
            "capture_archive": str(archive.relative_to(ROOT)),
            "seed": config["seed"],
            "claim_scope": config["claim_scope"],
            "new_model_forwards": 0,
        },
    )
    with (output / "rows.jsonl").open("x") as sink:
        for probe in config["probes"]:
            for slots in config["slots"]:
                case = read(archive / f"{probe['id']}-{slots}.json")
                for policy in config["support_policies"]:
                    started = perf_counter()
                    predictive, exact = inputs_for(archive, case, policy)
                    construction = perf_counter() - started
                    z = sum(exact.values(), Fraction())
                    before = perf_counter()
                    coverage = finite_yield_bounds(predictive.state.grammar)
                    coverage_construction = perf_counter() - before
                    for mode in config["posterior_scopes"]:
                        for limit in config["oracle_limits"]:
                            name = f"{case['id']}-{policy}-{mode}-{limit}"
                            common = {
                                "id": name,
                                "case_id": case["id"],
                                "support_policy": policy,
                                "coverage_mode": mode,
                                "oracle_limit": limit,
                                "git_commit": system.git_commit,
                                "model_revision": config["model_revision"],
                                "tokenizer_revision": config["tokenizer_revision"],
                                "config_sha256": sha(archive / "config.json"),
                                "seed": config["seed"],
                                "grammar_sha256": sha_json(predictive.state.grammar.to_dict()),
                                "support_sha256": predictive.state.support.fingerprint,
                                "exactness_scope": (
                                    predictive.state.support.exactness_scope.to_dict()
                                ),
                                "input_fingerprint": predictive.fingerprint,
                                "forward_seconds": case["forward_seconds"],
                                "input_construction_seconds": construction,
                                "coverage_construction_seconds": coverage_construction,
                                "reference_valid_mass": fraction_data(z),
                                "reference_valid_token_paths": len(exact),
                            }
                            before = perf_counter()
                            try:
                                proof = probability_partition(
                                    predictive,
                                    max_oracle_calls=limit,
                                    requested_tv=Fraction()
                                    if limit == 4096
                                    else Fraction(*config["tolerance"]),
                                    scope=PosteriorScope.FULL,
                                    timeout_seconds=config["soft_timeout_seconds"],
                                    language_coverage=coverage
                                    if mode == "finite_language_coverage"
                                    else None,
                                )
                                elapsed = perf_counter() - before
                                started = perf_counter()
                                verified = verify_mass_proof(proof, expected_input=predictive)
                                checktime = perf_counter() - started
                                if not verified.lower <= z <= verified.upper(PosteriorScope.FULL):
                                    raise ValueError(
                                        "CORRECTNESS GATE: reference outside mass envelope"
                                    )
                                actual_tv = 1 - verified.lower / z if verified.lower and z else None
                                bound = verified.tv_bound(PosteriorScope.FULL)
                                if actual_tv is not None and (bound is None or actual_tv > bound):
                                    raise ValueError(
                                        "CORRECTNESS GATE: underestimated conditional TV"
                                    )
                                sample = None
                                if proof["status"] == "certified_tolerance":
                                    update = certified_parallel_update(
                                        predictive,
                                        proof,
                                        committed_positions=case["masked_positions"],
                                        rng=Random(config["seed"]),
                                        scope=PosteriorScope.FULL,
                                        max_tv=Fraction()
                                        if limit == 4096
                                        else Fraction(*config["tolerance"]),
                                    )
                                    sample = predictive.state.tokenizer_adapter.detokenize_bytes(
                                        update.witness_token_ids
                                    ).decode()
                                    if update.witness_token_ids not in exact:
                                        raise ValueError(
                                            "CORRECTNESS GATE: sample outside declared language"
                                        )
                                filename = f"proofs/{name}.json.gz"
                                started = perf_counter()
                                write(output / filename, proof)
                                row = {
                                    **common,
                                    "status": proof["status"],
                                    "solve_and_internal_check_seconds": elapsed,
                                    "portable_check_seconds": checktime,
                                    "serialization_seconds": perf_counter() - started,
                                    "proof": filename,
                                    "lower": fraction_data(verified.lower),
                                    "unresolved": fraction_data(verified.unresolved),
                                    "omitted": fraction_data(verified.omitted),
                                    "outside_valid_upper": fraction_data(
                                        verified.outside_valid_upper
                                    ),
                                    "certified_full_tv": fraction_data(bound),
                                    "actual_full_tv": fraction_data(actual_tv),
                                    "support_tv_bound": fraction_data(
                                        verified.tv_bound(PosteriorScope.REPRESENTED)
                                    ),
                                    "oracle_calls": verified.oracle_calls,
                                    "sample": sample,
                                }
                            except Exception as error:
                                if "CORRECTNESS GATE" in str(error):
                                    raise
                                row = {
                                    **common,
                                    "status": "error",
                                    "error_type": type(error).__name__,
                                    "error": str(error),
                                    "solve_and_internal_check_seconds": perf_counter() - before,
                                }
                            sink.write(json.dumps(row, allow_nan=False) + "\n")
                            sink.flush()
                            print(
                                json.dumps(
                                    {
                                        "id": name,
                                        "status": row["status"],
                                        "seconds": row["solve_and_internal_check_seconds"],
                                    }
                                ),
                                flush=True,
                            )
    write(
        output / "manifest.json",
        {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*")) if p.is_file()},
    )


def sha_json(value):
    import hashlib

    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.capture.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
