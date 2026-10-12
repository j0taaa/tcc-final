"""All predeclared original-ID drift audit rows, with isolated resource guards."""

import argparse
import json
import multiprocessing as mp
import os
import resource
import signal
import subprocess
import traceback
from contextlib import contextmanager
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter, process_time

import numpy as np

from mwpc_exact.cfg_posterior import CompilationLimit

from . import adaptive_angular, calibrated_endpoint, hybrid_endpoint, ordered_planar
from . import public_audit as old
from .forest import certificate
from .mass_aware_controls import controls as scalar_controls
from .public_controls import digest
from .sampler_overlap import controls as overlap_controls

WORK = Path(__file__).resolve().parent
ENGINES = [adaptive_angular, calibrated_endpoint, hybrid_endpoint, ordered_planar]
CTX = mp.get_context("fork")


def clock():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return perf_counter(), process_time() + children.ru_utime + children.ru_stime


def elapsed(start):
    return [a - b for a, b in zip(clock(), start, strict=True)]


@contextmanager
def deadline(seconds):
    def expired(*_):
        raise TimeoutError("shared-stage wall deadline; no certificate")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def failure(exc):
    if isinstance(exc, (CompilationLimit, MemoryError, TimeoutError, RuntimeError)):
        return dict(status="RESOURCE_REFUSAL", reason=str(exc) or type(exc).__name__)
    return dict(
        status="ERROR",
        traceback=traceback.format_exc().replace(str(WORK.parents[2]), "<REPOSITORY>"),
    )


def core(send, plan, first, second, epsilon, engine, limit):
    try:
        result = certificate(
            plan, first, second, epsilon, max_rows=limit, compressor=engine, exact_passthrough=True
        )
    except Exception as exc:
        result = failure(exc)
    send.send(result)
    send.close()


def guarded_core(plan, first, second, epsilon, engine, protocol):
    receive, send = CTX.Pipe(duplex=False)
    process = CTX.Process(
        target=core,
        args=(
            send,
            plan,
            first,
            second,
            epsilon,
            engine,
            protocol["core"]["max_materialized_rows"],
        ),
    )
    start = clock()
    process.start()
    send.close()
    if receive.poll(protocol["core"]["hard_wall_seconds"]):
        try:
            result = receive.recv()
        except EOFError:
            result = dict(status="ERROR", reason="core child exited without a result")
    else:
        process.terminate()
        result = dict(status="RESOURCE_REFUSAL", reason="core150s wall deadline; no certificate")
    process.join(5)
    if process.is_alive():
        process.kill()
        process.join()
    receive.close()
    return result, elapsed(start)


def state_worker(source, frame_path, folder, protocol):
    os.setsid()
    limit = protocol["core"]["child_virtual_memory_gib"] << 30
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    frame = json.loads(frame_path.read_text())
    base = dict(
        source_case=frame["case"],
        mask_count=frame["mask_count"],
        audit_split=frame["audit_split"],
        free_positions=frame["positions"],
    )
    costs = {}
    shared = None
    try:
        start = clock()
        with deadline(protocol["core"]["hard_wall_seconds"]):
            matrix = np.load(source / (frame_path.stem + ".npy"), allow_pickle=False)
            assert digest(source / (frame_path.stem + ".npy")) == frame["probabilities_sha256"]
            adapter = old.CompositionalByteLevelAdapter.from_token_pieces(
                json.loads((source / "vocabulary.json").read_text())
            )
            assert matrix.shape == (frame["mask_count"], adapter.vocabulary_size)
            support = old.build_per_position_support(
                canvas=frame["canvas"],
                policy=old.SupportPolicy(old.SupportKind.FULL, adapter.vocabulary_size),
                explicit_support={
                    p: tuple(range(adapter.vocabulary_size)) if t is None else (t,)
                    for p, t in enumerate(frame["canvas"])
                },
            )
            state = old.SelectionInput(
                old.normalize_to_cnf(old.json_source_grammar()).grammar,
                tuple(frame["canvas"]),
                (),
                support,
                adapter,
                old.EOSPolicy(old.EOSMode.ABSENT),
            )

            def rows(table):
                by_position = dict(zip(frame["positions"], table, strict=True))
                return [by_position.get(p, ()) for p in range(len(state.canvas))]

            first, weights = old.inputs(state, rows(matrix))
            costs["input"] = elapsed(start)
            start = clock()
            prepared = old.prepare(adapter, state.canvas)
            plan = old.bridge(prepared, state)
            costs["preparation"] = elapsed(start)
            start = clock()
            mass = plan.evaluate(first).valid_mass
            assert mass == old.StackPosterior(prepared, weights).mass
            count = old.scalar(plan, tuple((1,) * len(row) for row in state.support.rows))
            costs["first_normalizer_and_count"] = elapsed(start)
            base.update(
                first_valid_mass=mass,
                valid_original_assignments=count,
                full_vocabulary=adapter.vocabulary_size,
            )
            if not mass:
                shared = dict(status="ZERO_VALID_MASS_UNDEFINED_TV")
    except Exception as exc:
        shared = failure(exc)
        costs["shared_failed_stage"] = elapsed(start)
    with (folder / "rows.jsonl").open("w") as stream:
        for kind in protocol["formats"]:
            refused = shared
            baseline = None
            local_costs = dict(costs)
            if refused is None:
                try:
                    start = clock()
                    with deadline(protocol["core"]["hard_wall_seconds"]):
                        table = old.rounded(matrix, kind)
                        second, weights = old.inputs(state, rows(table))
                        mass = plan.evaluate(second).valid_mass
                        assert mass == old.StackPosterior(prepared, weights).mass
                        local_costs["conversion_and_second_normalizer"] = elapsed(start)
                        if not mass:
                            refused = dict(status="ZERO_VALID_MASS_UNDEFINED_TV")
                        else:
                            start = clock()
                            baseline = old.controls(plan, first, second)
                            baseline["mass_aware"] = scalar_controls(plan, first, second)
                            baseline["sampler_overlap"] = overlap_controls(plan, first, second)
                            local_costs["controls"] = elapsed(start)
                except Exception as exc:
                    refused = failure(exc)
                    local_costs["format_failed_stage"] = elapsed(start)
            for epsilon in protocol["tolerances"]:
                for engine in ENGINES:
                    row_costs = dict(local_costs)
                    if refused is not None:
                        report = dict(refused, shared_refusal=True)
                    else:
                        report, row_costs["core_with_process_management"] = guarded_core(
                            plan, first, second, F(epsilon), engine, protocol
                        )
                        if report["status"] == "CERTIFIED_ON_ADMITTED_FOREST":
                            assert report["lower"] <= min(
                                baseline["hellinger_upper"],
                                baseline["range_upper"],
                                baseline["mass_aware"]["upper"],
                                baseline["sampler_overlap"]["upper"],
                            )
                            assert (
                                report["lower"]
                                <= report["upper"]
                                <= min(1, (1 + F(epsilon)) * report["lower"])
                            )
                    row = dict(
                        base,
                        format=kind,
                        epsilon=epsilon,
                        engine=engine.__name__.rsplit(".", 1)[-1],
                        **report,
                        controls=baseline,
                        costs_wall_cpu=row_costs,
                        full_first_audit_wall_cpu=[
                            sum(v[i] for v in row_costs.values()) for i in [0, 1]
                        ],
                        capture_forward_and_softmax_wall_cpu=frame.get(
                            "forward_and_softmax_wall_cpu"
                        ),
                    )
                    stream.write(json.dumps(row, default=str) + "\n")
                    stream.flush()
                    print(
                        json.dumps(
                            {
                                k: row[k]
                                for k in [
                                    "source_case",
                                    "mask_count",
                                    "format",
                                    "epsilon",
                                    "engine",
                                    "status",
                                ]
                            }
                        ),
                        flush=True,
                    )


def run(source, output, development=False):
    if subprocess.check_output(["git", "status", "--porcelain"]).strip():
        raise ValueError("freeze source before audit")
    output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads((WORK / "protocol-v25.json").read_text())
    origin = json.loads((source / "metadata.json").read_text())
    assert origin["vocabulary_sha256"] == digest(source / "vocabulary.json")
    frames = [p for p in sorted(source.glob("*.json")) if p.stem not in ["metadata", "vocabulary"]]
    if development:
        assert len(frames) == 1
        assert frames[0].stem == protocol["seen_development_document"] + "-4"
    else:
        expected = {
            f"{r['key']}-{n}"
            for r in protocol["source_corpus"]["cases"]
            for n in protocol["mask_counts"]
        }
        assert {p.stem for p in frames} == expected
        assert origin["protocol_sha256"] == digest(WORK / "protocol-v25.json")
    metadata = dict(
        producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        source_metadata_sha256=digest(source / "metadata.json"),
        vocabulary_sha256=digest(source / "vocabulary.json"),
        protocol_sha256=digest(WORK / "protocol-v25.json"),
        source_origin=origin,
        development_only=development,
        expected_rows=24 * len(frames),
        engines={e.__name__: digest(e.__file__) for e in ENGINES},
        scalar_source_hashes={
            name: digest(WORK / name)
            for name in ["public_audit.py", "mass_aware_controls.py", "sampler_overlap.py"]
        },
    )
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    start = clock()
    for frame in frames:
        folder = output / frame.stem
        folder.mkdir()
        process = CTX.Process(target=state_worker, args=(source, frame, folder, protocol))
        process.start()
        process.join()
        if process.exitcode:
            (folder / "worker-failure.json").write_text(
                json.dumps(
                    dict(
                        exitcode=process.exitcode,
                        scope="No fabricated missing certificates; audit incomplete",
                    )
                )
                + "\n"
            )
        (folder / "exit.json").write_text(json.dumps(dict(exitcode=process.exitcode)) + "\n")
    all_rows = []
    missing = 0
    for frame_path in frames:
        frame = json.loads(frame_path.read_text())
        path = output / frame_path.stem / "rows.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        found = {(r["format"], r["epsilon"], r["engine"]) for r in rows}
        assert len(found) == len(rows)
        for kind in protocol["formats"]:
            for epsilon in protocol["tolerances"]:
                for engine in protocol["engines"]:
                    if (kind, epsilon, engine) not in found:
                        rows.append(
                            dict(
                                source_case=frame["case"],
                                mask_count=frame["mask_count"],
                                audit_split=frame["audit_split"],
                                format=kind,
                                epsilon=epsilon,
                                engine=engine,
                                status="NOT_EXECUTED_WORKER_FAILURE",
                                reason="Worker failed before this row; no bound/timing fabricated",
                            )
                        )
                        missing += 1
        all_rows.extend(rows)
    (output / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in all_rows))
    statuses = {
        s: sum(r["status"] == s for r in all_rows) for s in sorted({r["status"] for r in all_rows})
    }
    summary = dict(
        status="COMPLETE_FUNCTIONAL_AUDIT" if not missing else "INCOMPLETE",
        rows=len(all_rows),
        expected_rows=24 * len(frames),
        counts=statuses,
        wall_cpu=elapsed(start),
        development_only=development,
        new_forwards_in_audit=0,
        missing_due_to_worker_failure=missing,
    )
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--development", action="store_true")
    args = parser.parse_args()
    run(args.source, args.output, args.development)
