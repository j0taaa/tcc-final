"""Frozen all-input conditional iid posterior audit; no neural training claim."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path
from random import Random
from time import monotonic, perf_counter, process_time

from controls import iid_controls
from replay import recognized
from resampling import (
    Problem,
    WeightedForest,
    decision_cache_statistics,
    select_order,
)
from scripts.exact_commit.build_cfg_posterior_results import load_inputs
from scripts.exact_commit.run_cfg_posterior_audit import source_grammar

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.conflict_proof import read_state
from mwpc_exact.mass_certificate import ProbabilityInput

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[2]


def run(output, batch_size=1024, strengthened=False):
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("commit source and protocol before measuring")
    protocol_path = WORK / "bulk-utility-protocol.json"
    config = json.loads(protocol_path.read_text())
    addendum = WORK / "bulk-precision-addendum.json"
    if batch_size == 4096:
        config.update(json.loads(addendum.read_text()))
    native = json.loads((WORK / "protocol.json").read_text())
    runs, inputs, manifest = load_inputs()
    methods = list(iid_controls(strengthened).items())
    output.mkdir(parents=True, exist_ok=False)
    (output / "metadata.json").write_text(
        json.dumps(
            dict(
                producer=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                protocol_sha256=hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
                source_inputs=manifest["files"],
                batch_size=batch_size,
                methods=[name for name, _ in methods],
                strengthened=strengthened,
                prefix_checkpoint=1024 if strengthened and batch_size == 4096 else None,
                refinement_sha256=hashlib.sha256(
                    (WORK / "envelope-profile-refinement.md").read_bytes()
                ).hexdigest()
                if strengthened
                else None,
                precision_addendum_sha256=hashlib.sha256(addendum.read_bytes()).hexdigest()
                if batch_size == 4096
                else None,
                load=Path("/proc/loadavg").read_text().strip(),
            ),
            indent=2,
        )
        + "\n"
    )
    with (output / "rows.jsonl").open("x") as stream:

        def emit(row):
            stream.write(json.dumps(row) + "\n")
            stream.flush()

        for archived in runs["json-model"]["rows"]:
            raw = inputs[archived["archived_input"]]
            data = ProbabilityInput(
                read_state(raw["input"]),
                tuple(tuple(Q(*v) for v in row) for row in raw["probabilities"]),
            )
            start = perf_counter()
            cpu_start = process_time()
            try:
                plan = compile_cfg_sampler(
                    source_grammar("json"),
                    data.state,
                    timeout_seconds=30,
                    max_chart_cells=200000,
                    max_alternatives=1000000,
                )
                base = WeightedForest.prepare(plan, data.probabilities)
            except Exception as error:
                emit(
                    dict(
                        case=archived["case"],
                        stage="compile",
                        status="unresolved",
                        error=repr(error),
                        seconds=perf_counter() - start,
                        cpu_seconds=process_time() - cpu_start,
                    )
                )
                continue
            compilation = perf_counter() - start
            compile_cpu = process_time() - cpu_start
            free = tuple(i for i, t in enumerate(data.state.canvas) if t is None)
            indices = [dict((t, j) for j, t in enumerate(row)) for row in data.state.support.rows]
            for power in (1, 2):
                rates = tuple(tuple(q**power for q in row) for row in data.probabilities)
                for k in sorted({1, math.ceil(len(free) / 2), len(free) - 1}):
                    seed = native["seed"] + int(
                        hashlib.sha256(f"{archived['case']}/{power}/{k}".encode()).hexdigest()[:8],
                        16,
                    )
                    rng = Random(seed)
                    original = base.sample(rng)
                    order = select_order(free, rates, original, indices, k, rng)
                    p = Problem(
                        plan, data.probabilities, rates, order, {i: original[i] for i in order}
                    )
                    for rep in range(3):
                        for name, constructor in methods[rep:] + methods[:rep]:
                            row = dict(
                                case=archived["case"],
                                power=power,
                                k=k,
                                order=order,
                                observed=p.observed,
                                repetition=rep,
                                method=name,
                                stage="query",
                                status="complete",
                                accepted=0,
                                attempts=0,
                                compilation_seconds=compilation,
                                compilation_cpu_seconds=compile_cpu,
                                load=Path("/proc/loadavg").read_text().strip(),
                            )
                            start = perf_counter()
                            cpu_start = process_time()
                            sampler = None
                            histograms = [Counter() for _ in p.rows]
                            digest = hashlib.sha256()
                            try:
                                sampler = constructor(
                                    p, end=monotonic() + config["preparation_deadline_seconds"]
                                )
                                row.update(
                                    preparation_seconds=perf_counter() - start,
                                    preparation_cpu_seconds=process_time() - cpu_start,
                                )
                                sample_start = perf_counter()
                                sample_cpu = process_time()
                                end = monotonic() + config["sampling_deadline_seconds"]
                                rng = Random(seed + rep)
                                for _ in range(config["accepted_batch_size"]):
                                    path, count = sampler.sample(rng, end)
                                    assert recognized(p, path)
                                    assert all(path[i] == t for i, t in p.observed.items())
                                    assert all(
                                        t in domain for t, domain in zip(path, p.rows, strict=True)
                                    )
                                    row["accepted"] += 1
                                    row["attempts"] += count
                                    digest.update(
                                        json.dumps(path, separators=(",", ":")).encode() + b"\n"
                                    )
                                    for histogram, t in zip(histograms, path, strict=True):
                                        histogram[t] += 1
                                    if (
                                        strengthened
                                        and batch_size == 4096
                                        and row["accepted"] == 1024
                                    ):
                                        row["prefix_1024"] = dict(
                                            status="complete",
                                            accepted=1024,
                                            attempts=row["attempts"],
                                            seconds=perf_counter() - start,
                                            cpu_seconds=process_time() - cpu_start,
                                            sampling_seconds=perf_counter() - sample_start,
                                            sampling_cpu_seconds=process_time() - sample_cpu,
                                            histograms=[dict(h) for h in histograms],
                                            paths_sha256=digest.hexdigest(),
                                            **decision_cache_statistics(sampler),
                                        )
                                row.update(
                                    sampling_seconds=perf_counter() - sample_start,
                                    sampling_cpu_seconds=process_time() - sample_cpu,
                                )
                            except NotImplementedError as error:
                                row.update(status="not_applicable", error=repr(error))
                            except Exception as error:
                                row.update(status="unresolved", error=repr(error))
                            row.update(
                                seconds=perf_counter() - start,
                                cpu_seconds=process_time() - cpu_start,
                                histograms=[dict(h) for h in histograms],
                                paths_sha256=digest.hexdigest(),
                            )
                            if sampler is not None:
                                row.update(decision_cache_statistics(sampler))
                                row["rejection_factor"] = str(
                                    getattr(sampler, "rejection_factor", "not_applicable")
                                )
                            emit(row)
                    print(archived["case"], power, k, "bulk recorded", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, choices=(1024, 4096), default=1024)
    parser.add_argument("--strengthened", action="store_true")
    args = parser.parse_args()
    run(args.output, args.batch_size, args.strengthened)
