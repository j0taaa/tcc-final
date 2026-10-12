"""All18 V12 functional audit rows; strengthened controls and complete costs."""

import argparse
import hashlib
import io
import json
import platform
import subprocess
import traceback
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter, process_time
from zipfile import ZipFile

import numpy as np

from . import (
    adaptive_angular,
    angular_control,
    angular_streamed,
    calibrated_endpoint,
    hybrid_endpoint,
    ordered_planar,
)
from . import public_audit as old
from .forest import certificate
from .mass_aware_controls import controls as strengthened_controls
from .sampler_overlap import controls as overlap_controls

ENGINES = [angular_control, calibrated_endpoint, hybrid_endpoint]


def clock():
    return perf_counter(), process_time()


def elapsed(start):
    return tuple(a - b for a, b in zip(clock(), start, strict=True))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(output, streamed=False, adaptive=False, massaware=False, ordered=False, overlap=False):
    engines = [angular_streamed, calibrated_endpoint, hybrid_endpoint] if streamed else ENGINES
    if adaptive:
        engines = [adaptive_angular, calibrated_endpoint, hybrid_endpoint]
    if ordered:
        if not adaptive or not massaware:
            raise ValueError("ordered audit requires the strongest adaptive/scalar controls")
        engines.append(ordered_planar)
    if overlap and not ordered:
        raise ValueError("overlap audit requires all four engines/strong controls")
    output.mkdir(parents=True, exist_ok=False)
    started = clock()
    packet = old.FROZEN / "packet.zip"
    origin = json.loads((old.FROZEN / "provenance.json").read_text())
    for name, record in origin["files"].items():
        assert digest(old.FROZEN / name) == record["sha256"]
    metadata = dict(
        producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        packet_sha256=digest(packet),
        scope="Functional development, same public packet; NOT independent/native timing gate",
        new_forwards=0,
        engines={e.__name__: digest(e.__file__) for e in engines},
        reference_files=origin["files"],
        python=platform.python_version(),
        numpy=np.__version__,
        machine=platform.machine(),
        max_rows=1_000_000,
        exact_passthrough=adaptive,
        mass_aware_scalar_controls=massaware,
        sampler_overlap_controls=overlap,
    )
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    try:
        head_origin = old.check(packet)
        with ZipFile(packet) as archive:
            name = json.loads(archive.read("manifest.json"))["case"]
            case = json.loads(archive.read(name + ".json"))
            matrix = np.load(io.BytesIO(archive.read(name + ".npy")), allow_pickle=False)
            adapter = old.CompositionalByteLevelAdapter.from_token_pieces(
                json.loads(archive.read("vocabulary.json"))
            )
        support = old.build_per_position_support(
            canvas=case["canvas"],
            policy=old.SupportPolicy(old.SupportKind.FULL, adapter.vocabulary_size),
            explicit_support={
                p: tuple(range(adapter.vocabulary_size)) if fixed is None else (fixed,)
                for p, fixed in enumerate(case["canvas"])
            },
        )
        state = old.SelectionInput(
            old.normalize_to_cnf(old.json_source_grammar()).grammar,
            tuple(case["canvas"]),
            (),
            support,
            adapter,
            old.EOSPolicy(old.EOSMode.ABSENT),
        )

        def rows(table):
            by_position = dict(zip(case["positions"], table, strict=True))
            return [by_position.get(p, ()) for p in range(len(state.canvas))]

        first, first_weights = old.inputs(state, rows(matrix))
        input_cost = elapsed(started)
        began = clock()
        prepared = old.prepare(adapter, state.canvas)
        plan = old.bridge(prepared, state)
        preparation_cost = elapsed(began)
        began = clock()
        first_mass = plan.evaluate(first).valid_mass
        assert first_mass == old.StackPosterior(prepared, first_weights).mass
        count = old.scalar(plan, tuple((1,) * len(s) for s in state.support.rows))
        first_norm_and_count_cost = elapsed(began)
        completed = refusals = errors = 0
        with (output / "rows.jsonl").open("w") as stream:
            for kind in ["binary32", "binary16", "bfloat16"]:
                began = clock()
                table = old.rounded(matrix, kind)
                second, second_weights = old.inputs(state, rows(table))
                second_mass = plan.evaluate(second).valid_mass
                assert second_mass == old.StackPosterior(prepared, second_weights).mass
                conversion_cost = elapsed(began)
                began = clock()
                baseline = old.controls(plan, first, second)
                if massaware:
                    baseline["mass_aware"] = strengthened_controls(plan, first, second)
                if overlap:
                    baseline["sampler_overlap"] = overlap_controls(plan, first, second)
                control_cost = elapsed(began)
                for epsilon in [F(1, 2), F(1, 10)]:
                    for engine in engines:
                        began = clock()
                        try:
                            report = certificate(
                                plan,
                                first,
                                second,
                                epsilon,
                                max_rows=1_000_000,
                                compressor=engine,
                                exact_passthrough=adaptive,
                            )
                            assert report["lower"] <= min(
                                baseline["range_upper"], baseline["hellinger_upper"]
                            )
                            if massaware:
                                assert report["lower"] <= baseline["mass_aware"]["upper"]
                            if overlap:
                                assert report["lower"] <= baseline["sampler_overlap"]["upper"]
                            completed += 1
                        except RuntimeError as exc:
                            report = dict(status="RESOURCE_REFUSAL", reason=str(exc))
                            refusals += 1
                        except Exception:
                            report = dict(status="ERROR", traceback=traceback.format_exc())
                            errors += 1
                        core_cost = elapsed(began)
                        costs = dict(
                            input=input_cost,
                            preparation=preparation_cost,
                            first_normalizer_and_count=first_norm_and_count_cost,
                            conversion_and_second_normalizer=conversion_cost,
                            controls=control_cost,
                            core=core_cost,
                        )
                        row = dict(
                            format=kind,
                            epsilon=str(epsilon),
                            engine=engine.__name__,
                            **report,
                            controls=baseline,
                            source_case=case["case"],
                            full_vocabulary=adapter.vocabulary_size,
                            free_positions=case["positions"],
                            valid_original_assignments=count,
                            first_valid_mass=first_mass,
                            second_valid_mass=second_mass,
                            zeroed_original_entries=int(
                                np.count_nonzero((matrix > 0) & (table == 0))
                            ),
                            costs_wall_cpu=costs,
                            full_first_audit_wall_cpu=[
                                sum(v[j] for v in costs.values()) for j in [0, 1]
                            ],
                        )
                        stream.write(json.dumps(row, default=str) + "\n")
                        stream.flush()
                        print(
                            json.dumps(
                                {k: row[k] for k in ["format", "epsilon", "engine", "status"]}
                                | dict(core_wall_cpu=core_cost)
                            ),
                            flush=True,
                        )
        summary = dict(
            status="FUNCTIONAL_DEVELOPMENT_ONLY",
            rows=6 * len(engines),
            completed=completed,
            refusals=refusals,
            errors=errors,
            head_origin=head_origin,
            wall_cpu=elapsed(started),
            original_assignment_count=count,
        )
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    except Exception:
        (output / "failure.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--streamed", action="store_true")
    parser.add_argument("--adaptive", action="store_true")
    parser.add_argument("--massaware", action="store_true")
    parser.add_argument("--ordered", action="store_true")
    parser.add_argument("--overlap", action="store_true")
    args = parser.parse_args()
    run(args.output, args.streamed, args.adaptive, args.massaware, args.ordered, args.overlap)
