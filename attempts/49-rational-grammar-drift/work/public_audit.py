"""Full-original-ID numerical audit. No neural execution or speed gate."""

import argparse
import hashlib
import io
import json
import platform
import subprocess
import traceback
from fractions import Fraction as F
from math import isqrt, lcm
from pathlib import Path
from time import perf_counter
from zipfile import ZipFile

import numpy as np
from scripts.exact_commit.full_head_packet import check

from mwpc_exact.cfg_posterior import CfgSampler, _Term
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

from . import optimal_planar_fast as optimal_planar
from .forest import certificate
from .frozen.posterior import Weights
from .frozen.stack_control import StackPosterior, StackPrepared
from .frozen.table import LexerTable

FROZEN = Path(__file__).parent / "frozen"


def prepare(adapter, canvas):
    return StackPrepared(
        LexerTable(adapter),
        canvas,
        max_edges=1_000_000,
        max_cells=200_000,
        max_terms=50_000_000,
        timeout_seconds=120,
    )


def bridge(prepared, state):
    """Disjoint original-ID leaves, deterministic suffix ORs, fixed-slot index0."""
    terms, nodes, groups = [(_Term(),)], {}, {}
    end = len(state.canvas)
    for i, accepting in enumerate(prepared.accepting):
        nodes[end, i] = 0 if accepting else None
    indices = [{t: i for i, t in enumerate(row)} for row in state.support.rows]

    def add(alternatives):
        if not alternatives:
            return None
        terms.append(tuple(alternatives))
        return len(terms) - 1

    for p in reversed(range(end)):
        for i, outgoing in enumerate(prepared.arcs[p]):
            alternatives = []
            for target, gids in outgoing:
                suffix = nodes[p + 1, target]
                if suffix is None:
                    continue
                for gid in gids:
                    key = p, gid
                    if key not in groups:
                        groups[key] = add(
                            [
                                _Term(choice=(p, indices[p][t]))
                                for t in prepared.members[key]
                                if t in indices[p]
                            ]
                        )
                    if groups[key] is not None:
                        alternatives.append(_Term(children=(groups[key], suffix)))
            nodes[p, i] = add(alternatives)
    return CfgSampler(
        state,
        state.grammar,
        tuple(terms),
        tuple(range(len(terms))),
        nodes[0, 0],
        prepared.retained_nodes,
        prepared.retained_edges,
    )


def integers(data):
    result = []
    for row in data.probabilities:
        denominator = lcm(*(p.denominator for p in row))
        result.append(tuple(p.numerator * (denominator // p.denominator) for p in row))
    return tuple(result)


def scalar(plan, values):
    inside = []
    for alternatives in plan.terms:
        inside.append(sum(plan.term_mass(term, values, inside) for term in alternatives))
    return 0 if plan.root is None else inside[plan.root]


def controls(plan, first, second):
    left, right = integers(first), integers(second)
    a, b = scalar(plan, left), scalar(plan, right)
    if not a or not b:
        return dict(status="UNDEFINED_ZERO_MASS")
    ranges = []
    for alternatives in plan.terms:
        choices = []
        for term in alternatives:
            if term.choice is not None:
                p, i = term.choice
                if not left[p][i]:
                    assert not right[p][i], "range control assumes Q support subset P"
                    continue
                ratio = F(right[p][i], left[p][i])
                choices.append((ratio, ratio))
            elif term.children:
                x, y = (ranges[c] for c in term.children)
                if x is not None and y is not None:
                    choices.append((x[0] * y[0], x[1] * y[1]))
            else:
                choices.append((F(1), F(1)))
        ranges.append(
            None if not choices else (min(x[0] for x in choices), max(x[1] for x in choices))
        )
    lower, upper = (F(a, b) * x for x in ranges[plan.root])
    assert lower <= 1 <= upper
    range_upper = F() if lower == upper else (1 - lower) * (upper - 1) / (upper - lower)
    precision = 64
    square_roots = tuple(
        tuple(isqrt(x * y << (2 * precision)) for x, y in zip(lrow, rrow, strict=True))
        for lrow, rrow in zip(left, right, strict=True)
    )
    affinity_lower_squared = F(
        scalar(plan, square_roots) ** 2, a * b << (2 * precision * len(plan.state.canvas))
    )
    assert 0 <= affinity_lower_squared <= 1
    tv_squared_upper = 1 - affinity_lower_squared
    scaled = F(1 << (2 * precision)) * tv_squared_upper
    rounded = isqrt(scaled.numerator // scaled.denominator)
    if F(rounded * rounded) < scaled:
        rounded += 1
    return dict(
        likelihood_min=lower,
        likelihood_max=upper,
        range_upper=range_upper,
        hellinger_upper=F(rounded, 1 << precision),
        sqrt_fraction_bits=precision,
    )


def rounded(matrix, kind):
    if kind in ("binary32", "binary16"):
        return matrix.astype("float32" if kind == "binary32" else "float16").astype("float64")
    # Standard bfloat16 round-to-nearest/ties-to-even on the binary32 lift.
    bits = matrix.astype("float32").view("uint32")
    bits = (bits + np.uint32(0x7FFF) + ((bits >> 16) & 1)) & np.uint32(0xFFFF0000)
    return bits.view("float32").astype("float64")


def inputs(state, rows):
    weights = Weights(rows, state.canvas, state.tokenizer_adapter.vocabulary_size)
    rational = tuple(
        tuple(F(weights.at(p, t), weights.denominators[p]) for t in support)
        for p, support in enumerate(state.support.rows)
    )
    return ProbabilityInput(state, rational), weights


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    packet = FROZEN / "packet.zip"
    origin = json.loads((FROZEN / "provenance.json").read_text())
    for name, record in origin["files"].items():
        assert hashlib.sha256((FROZEN / name).read_bytes()).hexdigest() == record["sha256"]
    metadata = dict(
        producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        packet_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(),
        scope="Numerical probability-table audit; no quantized neural execution or speed benchmark",
        new_forwards=0,
        reference_files=origin["files"],
        core_module=optimal_planar.__name__,
        core_sha256=hashlib.sha256(Path(optimal_planar.__file__).read_bytes()).hexdigest(),
        python=platform.python_version(),
        numpy=np.__version__,
        machine=platform.machine(),
        processor=platform.processor(),
    )
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    try:
        audit = check(packet)
        with ZipFile(packet) as archive:
            name = json.loads(archive.read("manifest.json"))["case"]
            case = json.loads(archive.read(name + ".json"))
            matrix = np.load(io.BytesIO(archive.read(name + ".npy")), allow_pickle=False)
            adapter = CompositionalByteLevelAdapter.from_token_pieces(
                json.loads(archive.read("vocabulary.json"))
            )
        support = build_per_position_support(
            canvas=case["canvas"],
            policy=SupportPolicy(SupportKind.FULL, adapter.vocabulary_size),
            explicit_support={
                p: tuple(range(adapter.vocabulary_size)) if fixed is None else (fixed,)
                for p, fixed in enumerate(case["canvas"])
            },
        )
        state = SelectionInput(
            normalize_to_cnf(json_source_grammar()).grammar,
            tuple(case["canvas"]),
            (),
            support,
            adapter,
            EOSPolicy(EOSMode.ABSENT),
        )

        def rows(table):
            by_position = dict(zip(case["positions"], table, strict=True))
            return [by_position.get(p, ()) for p in range(len(state.canvas))]

        first, first_weights = inputs(state, rows(matrix))
        input_seconds = perf_counter() - started
        began = perf_counter()
        prepared = prepare(adapter, state.canvas)
        plan = bridge(prepared, state)
        preparation_seconds = perf_counter() - began
        first_mass = plan.evaluate(first).valid_mass
        assert first_mass == StackPosterior(prepared, first_weights).mass
        count = scalar(plan, tuple((1,) * len(s) for s in state.support.rows))
        with (output / "rows.jsonl").open("w") as stream:
            for kind in ["binary32", "binary16", "bfloat16"]:
                began = perf_counter()
                table = rounded(matrix, kind)
                second, second_weights = inputs(state, rows(table))
                second_mass = plan.evaluate(second).valid_mass
                assert second_mass == StackPosterior(prepared, second_weights).mass
                conversion_seconds = perf_counter() - began
                began = perf_counter()
                baseline = controls(plan, first, second)
                control_seconds = perf_counter() - began
                for epsilon in [F(1, 2), F(1, 10)]:
                    began = perf_counter()
                    report = certificate(
                        plan, first, second, epsilon, max_rows=1_000_000, compressor=optimal_planar
                    )
                    core_seconds = perf_counter() - began
                    if "lower" in report:
                        assert report["lower"] <= min(
                            baseline["range_upper"], baseline["hellinger_upper"]
                        )
                    row = dict(
                        format=kind,
                        epsilon=str(epsilon),
                        **report,
                        controls=baseline,
                        source_case=case["case"],
                        full_vocabulary=adapter.vocabulary_size,
                        free_positions=case["positions"],
                        valid_original_assignments=count,
                        first_valid_mass=first_mass,
                        second_valid_mass=second_mass,
                        zeroed_original_entries=int(np.count_nonzero((matrix > 0) & (table == 0))),
                        input_seconds=input_seconds,
                        preparation_seconds=preparation_seconds,
                        conversion_and_normalizer_seconds=conversion_seconds,
                        control_seconds=control_seconds,
                        core_seconds=core_seconds,
                        full_first_audit_seconds=input_seconds
                        + preparation_seconds
                        + conversion_seconds
                        + control_seconds
                        + core_seconds,
                    )
                    stream.write(json.dumps(row, default=str) + "\n")
                    stream.flush()
                    print(
                        json.dumps(
                            {k: row[k] for k in ["format", "epsilon", "status", "core_seconds"]}
                        ),
                        flush=True,
                    )
        summary = dict(
            status="FUNCTIONAL_AUDIT_ONLY",
            rows=6,
            head_origin=audit,
            original_assignment_count=count,
            wall_seconds=perf_counter() - started,
        )
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    except Exception:
        (output / "failure.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
