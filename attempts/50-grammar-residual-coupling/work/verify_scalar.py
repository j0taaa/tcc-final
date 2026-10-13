"""Enumerate channel/trace laws and compare independently recognized original words."""

import argparse
import importlib
import itertools
import json
import math
import random
import subprocess
import traceback
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.reference.json_grammar import json_source_grammar

base = importlib.import_module("attempts.50-grammar-residual-coupling.work.verify")
upper_oracle = importlib.import_module("attempts.50-grammar-residual-coupling.work.verify_upper")
ref = importlib.import_module("attempts.50-grammar-residual-coupling.work.scalar")


def enumerators(solver):
    @lru_cache(None)
    def traces(node):
        result = {}
        for t, term in enumerate(solver.plan.terms[node]):
            kernel = solver.kernels[node][t]
            if not max(kernel[:2]):
                continue
            if term.choice is not None:
                i, j = term.choice
                parts = {((i, solver.ids[i][j]),): ((F(1), F(1), F(1)), 0)}
            elif not term.children:
                parts = {(): ((F(1), F(1), F(1)), 0)}
            else:
                parts = {}
                for x, (a, dx) in traces(term.children[0]).items():
                    for y, (b, dy) in traces(term.children[1]).items():
                        assert not {i for i, _ in x} & {i for i, _ in y}
                        marks = tuple(sorted((*x, *y)))
                        assert marks not in parts
                        parts[marks] = (tuple(v * w for v, w in zip(a, b, strict=True)), dx + dy)
            for marks, (values, size) in parts.items():
                assert marks not in result
                result[marks] = (
                    tuple(v * w for v, w in zip(kernel, values, strict=True)),
                    size + 1,
                )
        return result

    @lru_cache(None)
    def channel(node, mode):
        cumulative, actions = solver.channels[node][mode]
        result = {}
        for probability, (t, child_modes) in zip(
            upper_oracle.portions(cumulative), actions, strict=True
        ):
            if not probability:
                continue
            term = solver.plan.terms[node][t]
            if term.choice is not None:
                i, j = term.choice
                parts = {((i, solver.ids[i][j]),): F(1)}
            elif not term.children:
                parts = {(): F(1)}
            else:
                parts = {}
                for x, px in channel(term.children[0], child_modes[0]).items():
                    for y, py in channel(term.children[1], child_modes[1]).items():
                        marks = tuple(sorted((*x, *y)))
                        parts[marks] = parts.get(marks, F(0)) + px * py
            for marks, value in parts.items():
                result[marks] = result.get(marks, F(0)) + probability * value
        return result

    return traces, channel


def run(output, rounded=False, grid=None):
    output.mkdir(parents=True, exist_ok=False)
    counts = dict(
        word_checks=0,
        channel_laws=0,
        residual_laws=0,
        sampled_valid=0,
        undefined=0,
        bounded_failures=0,
        precision_gate_losses=0,
        marginal_lower_checks=0,
    )
    try:
        rng = random.Random(20261013058)
        head_rng = random.Random(202610130581)
        factory = (
            importlib.import_module(
                "attempts.50-grammar-residual-coupling.work.rounded"
            ).RoundedResidual
            if rounded
            else ref.ScalarResidual
        )
        options = dict(grid=grid) if rounded else {}
        with (output / "rows.jsonl").open("w") as stream:
            for name, kind, emissions, rows, canvas in upper_oracle.fixtures():
                source = base.source_dyck() if kind == "dyck" else json_source_grammar()
                for mode in ["equal", "different", "singular", "tiny", "low-mass", "zero-target"]:
                    target, draft = base.inputs(source, emissions, rows, canvas, mode, head_rng)
                    paths = list(itertools.product(*target.state.support.rows))
                    raw = [
                        {
                            ids: math.prod(
                                data.probabilities[i][rows[i].index(v)] for i, v in enumerate(ids)
                            )
                            if base.valid(b"".join(emissions[v] for v in ids), kind)
                            else F(0)
                            for ids in paths
                        }
                        for data in [target, draft]
                    ]
                    masses = [sum(values.values(), F(0)) for values in raw]
                    plan = compile_cfg_sampler(source, target.state)
                    if not all(masses):
                        try:
                            factory(plan, target, draft, **options)
                        except ValueError:
                            counts["undefined"] += 1
                            stream.write(
                                json.dumps(dict(case=name, mode=mode, undefined=True)) + "\n"
                            )
                            continue
                        raise AssertionError("undefined posterior admitted")
                    p, q = [
                        {ids: v / z for ids, v in rawrow.items()}
                        for rawrow, z in zip(raw, masses, strict=True)
                    ]
                    solver = factory(plan, target, draft, **options)
                    traces, channels = enumerators(solver)
                    trace_law = traces(plan.root)
                    truth_common = {}
                    for marks, ((a, b, common), _) in trace_law.items():
                        ids = tuple(v for _, v in marks)
                        assert a == p[ids] and b == q[ids] and common <= min(a, b)
                        truth_common[ids] = common
                    assert sum(truth_common.values(), F(0)) == solver.common[plan.root]
                    residual = {ids: max(F(0), p[ids] - q[ids]) for ids in paths}
                    delta = sum(residual.values(), F(0))
                    d = max(size for _, size in trace_law.values())
                    assert delta <= solver.envelope
                    if rounded:
                        true_lower = max(
                            abs(
                                sum(p[ids] for ids in paths if ids[i] == v)
                                - sum(q[ids] for ids in paths if ids[i] == v)
                            )
                            for i, row in enumerate(rows)
                            for v in row
                        )
                        assert solver.lower == true_lower and (true_lower == 0) == (delta == 0)
                        assert solver.trace_bound == d
                        counts["marginal_lower_checks"] += 1
                        if grid is None:
                            assert solver.envelope <= (2 * d + F(1, 2)) * delta
                        else:
                            counts["precision_gate_losses"] += (
                                solver.envelope > (2 * d + F(1, 2)) * delta
                            )
                    else:
                        assert solver.envelope <= 2 * d * delta
                    for channel in [0, 1, 2]:
                        mass = (
                            F(1)
                            if channel == 0
                            else solver.common[plan.root]
                            if channel == 1
                            else solver.envelope
                        )
                        law = channels(plan.root, channel)
                        assert sum(law.values(), F(0)) == (1 if mass else 0)
                        for ids in paths:
                            weight = (
                                p[ids]
                                if channel == 0
                                else truth_common.get(ids, F(0))
                                if channel == 1
                                else p[ids] - truth_common.get(ids, F(0))
                            )
                            marks = tuple(enumerate(ids))
                            assert law.get(marks, F(0)) == (weight / mass if mass else F(0))
                        counts["channel_laws"] += 1
                    if delta:
                        proposals = channels(plan.root, 2)
                        accepted = {}
                        for ids in paths:
                            probability = proposals.get(tuple(enumerate(ids)), F(0))
                            common = truth_common.get(ids, F(0))
                            accepted[ids] = (
                                probability * solver.correction(p[ids], q[ids], common)
                                if probability
                                else F(0)
                            )
                        rate = sum(accepted.values(), F(0))
                        assert rate == delta / solver.envelope
                        assert all(accepted[ids] / rate == residual[ids] / delta for ids in paths)
                        counts["residual_laws"] += 1
                        for _ in range(24):
                            ids, attempts = solver.sample(
                                rng, max_attempts=1 if grid is not None else None
                            )
                            if ids is None:
                                assert grid is not None and attempts == 1
                                counts["bounded_failures"] += 1
                            else:
                                assert residual[ids] > 0 and attempts >= 1
                                counts["sampled_valid"] += 1
                        assert solver.sample(rng, max_attempts=0) == (None, 0)
                    else:
                        assert not solver.envelope
                    counts["word_checks"] += len(paths)
                    stream.write(
                        json.dumps(
                            dict(
                                case=name,
                                mode=mode,
                                delta=str(delta),
                                envelope=str(solver.envelope),
                                attempt_ratio=str(solver.envelope / delta) if delta else None,
                                trace_bound=d,
                                grid_bits=solver.grid.bit_length() if rounded else None,
                                **counts,
                            )
                        )
                        + "\n"
                    )
        summary = dict(
            status="CORRECTNESS_ONLY",
            **counts,
            producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            rounded=rounded,
            fixed_grid=grid,
        )
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    except Exception:
        (output / "failure.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounded", action="store_true")
    parser.add_argument("--grid", type=int)
    arguments = parser.parse_args()
    run(arguments.output, arguments.rounded, arguments.grid)
