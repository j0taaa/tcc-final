"""Predeclared complete offline model-input replay; never rewrites M34 data."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import platform
import subprocess
from bisect import bisect_right
from fractions import Fraction as Q
from functools import partial
from pathlib import Path
from random import Random
from time import monotonic, perf_counter

from resampling import (
    BaseRejection,
    Problem,
    TangentMixture,
    WeightedForest,
    select_order,
)
from scripts.exact_commit.build_cfg_posterior_results import load_inputs
from scripts.exact_commit.run_cfg_posterior_audit import source_grammar

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.conflict_proof import read_state
from mwpc_exact.mass_certificate import ProbabilityInput

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def recognized(p, path):
    try:
        text = b"".join(p.plan.state.tokenizer_adapter.emissions[t] for t in path)
        json.loads(
            text.decode("utf-8"), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s))
        )
        return True
    except (ValueError, UnicodeDecodeError):
        return False


class EnumeratedTarget:
    def __init__(self, p, end=None):
        domains = [((p.observed[i],) if i in p.observed else row) for i, row in enumerate(p.rows)]
        if math.prod(map(len, domains)) > 1_000_000:
            raise NotImplementedError(
                "conditional Cartesian product exceeds frozen enumeration cap"
            )
        self.paths, self.weights = [], []
        for path in itertools.product(*domains):
            if end is not None and monotonic() > end:
                raise TimeoutError("enumeration preparation budget")
            if recognized(p, path):
                self.paths.append(path)
                self.weights.append(p.weight(path) * p.likelihood(path))
        if not self.paths:
            raise ValueError("zero target mass")
        scale = 1
        for weight in self.weights:
            if end is not None and monotonic() > end:
                raise TimeoutError("enumeration categorical preparation budget")
            scale = math.lcm(scale, weight.denominator)
        total, self.cumulative = 0, []
        for weight in self.weights:
            if end is not None and monotonic() > end:
                raise TimeoutError("enumeration categorical preparation budget")
            total += weight.numerator * (scale // weight.denominator)
            self.cumulative.append(total)

    def sample(self, rng, end=None):
        if end is not None and monotonic() > end:
            raise TimeoutError("enumeration sampling budget")
        return self.paths[bisect_right(self.cumulative, rng.randrange(self.cumulative[-1]))], 1


def run(args):
    protocol = json.loads((WORK / "protocol.json").read_text())
    config = protocol["replay"]
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit source/protocol before measuring")
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    runs, inputs, manifest = load_inputs()
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = {
        "source_commit": source_commit,
        "numeric_variant": args.numeric_variant,
        "protocol_sha256": hashlib.sha256((WORK / "protocol.json").read_bytes()).hexdigest(),
        "protocol_addendum_sha256": hashlib.sha256(
            (WORK / "protocol-addendum.json").read_bytes()
        ).hexdigest(),
        "note_sha256": hashlib.sha256((WORK / "received-note.md").read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "model_lineage": runs[config["phase"]]["metadata"],
        "archive_files": manifest["files"],
        "scope": "frozen-model posterior query costs; no neural training or end-to-end speed claim",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    stream = (args.output / "rows.jsonl").open("w")
    methods = [
        (
            "certified_tangent_mixture",
            partial(
                TangentMixture,
                dyadic_unaries=args.numeric_variant != "reference",
                tight_bounds=args.numeric_variant == "tight-dyadic",
            ),
        ),
        (
            "rejection_with_f_L_envelope",
            partial(BaseRejection, tight_bounds=args.numeric_variant == "tight-dyadic"),
        ),
        ("enumeration", EnumeratedTarget),
    ]

    def emit(row):
        stream.write(json.dumps(row) + "\n")
        stream.flush()

    try:
        for row in runs[config["phase"]]["rows"]:
            raw = inputs[row["archived_input"]]
            data = ProbabilityInput(
                read_state(raw["input"]),
                tuple(tuple(Q(*v) for v in r) for r in raw["probabilities"]),
            )
            started = perf_counter()
            try:
                plan = compile_cfg_sampler(
                    source_grammar("json"),
                    data.state,
                    timeout_seconds=config["compiler_deadline_seconds"],
                    max_chart_cells=config["max_cells"],
                    max_alternatives=config["max_alternatives"],
                )
                base = WeightedForest.prepare(plan, data.probabilities)
                if not base.mass:
                    raise ValueError("zero syntax mass")
            except Exception as error:
                emit(
                    {
                        "case": row["case"],
                        "archived_input": row["archived_input"],
                        "stage": "compilation",
                        "status": "unresolved",
                        "error": repr(error),
                        "elapsed_seconds": perf_counter() - started,
                    }
                )
                print(row["case"], "compilation unresolved", repr(error), flush=True)
                continue
            compile_seconds = perf_counter() - started
            free = tuple(i for i, t in enumerate(data.state.canvas) if t is None)
            ks = sorted({1, math.ceil(len(free) / 2), len(free) - 1})
            for power in config["rate_powers"]:
                rates = tuple(tuple(q**power for q in r) for r in data.probabilities)
                for k in ks:
                    event_seed = protocol["seed"] + int(
                        hashlib.sha256(f"{row['case']}/{power}/{k}".encode()).hexdigest()[:8], 16
                    )
                    rng = Random(event_seed)
                    original = base.sample(rng)
                    indices = [
                        dict((t, j) for j, t in enumerate(r)) for r in data.state.support.rows
                    ]
                    order = select_order(free, rates, original, indices, k, rng)
                    p = Problem(
                        plan, data.probabilities, rates, order, {i: original[i] for i in order}
                    )
                    event = {
                        "case": row["case"],
                        "archived_input": row["archived_input"],
                        "rate_power": power,
                        "k": k,
                        "n": len(free),
                        "event_seed": event_seed,
                        "order": order,
                        "observed": p.observed,
                        "compilation_seconds": compile_seconds,
                        "forest_nodes": len(plan.terms),
                        "forest_arcs": plan.alternatives,
                        "conditional_product": math.prod(len(p.rows[i]) for i in p.hidden),
                    }
                    for repetition in range(config["timing_repetitions"]):
                        rotated = methods[repetition:] + methods[:repetition]
                        for name, constructor in rotated:
                            record = {
                                **event,
                                "method": name,
                                "repetition": repetition,
                                "stage": "query",
                                "batches": [],
                                "status": "complete",
                            }
                            started = perf_counter()
                            try:
                                sampler = constructor(
                                    p, end=monotonic() + config["preparation_deadline_seconds"]
                                )
                                record["preparation_seconds"] = perf_counter() - started
                                if name == "certified_tangent_mixture":
                                    record["components"] = len(sampler.components)
                                    record["inside_integer_max_bits"] = max(
                                        v.bit_length()
                                        for _, _, c in sampler.components
                                        for v in c.inside
                                    )
                                sample_start = perf_counter()
                                end = monotonic() + config["sampling_deadline_seconds"]
                                sample_rng = Random(event_seed + repetition)
                                paths, attempts = [], 0
                                for size in config["accepted_batch_sizes"]:
                                    while len(paths) < size:
                                        path, count = sampler.sample(sample_rng, end)
                                        attempts += count
                                        assert recognized(p, path)
                                        assert all(
                                            path[i] == token for i, token in p.observed.items()
                                        )
                                        paths.append(path)
                                    sampling_seconds = perf_counter() - sample_start
                                    record["batches"].append(
                                        {
                                            "accepted": size,
                                            "attempts": attempts,
                                            "sampling_seconds": sampling_seconds,
                                            "query_seconds": record["preparation_seconds"]
                                            + sampling_seconds,
                                            "cold_seconds": compile_seconds
                                            + record["preparation_seconds"]
                                            + sampling_seconds,
                                            "original_token_paths": paths.copy(),
                                        }
                                    )
                            except NotImplementedError as error:
                                record.update(status="not_applicable", error=str(error))
                            except Exception as error:
                                record.update(
                                    status="unresolved",
                                    error=repr(error),
                                    elapsed_seconds=perf_counter() - started,
                                )
                            emit(record)
                    print(row["case"], "power", power, "k", k, "recorded", flush=True)
    finally:
        stream.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--numeric-variant", choices=("reference", "dyadic", "tight-dyadic"), default="reference"
    )
    run(parser.parse_args())
