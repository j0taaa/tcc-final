"""Independent rational tails and complete original-word law reconstruction."""

import argparse
import importlib
import itertools
import json
import math
import random
import subprocess
import traceback
from fractions import Fraction as F
from pathlib import Path

from mwpc_exact.cfg_posterior import compile_cfg_sampler
from mwpc_exact.eos_policy import EOSMode, EOSPolicy
from mwpc_exact.mass_certificate import ProbabilityInput
from mwpc_exact.reference.byte_grammars import _SourceGrammarBuilder
from mwpc_exact.reference.json_grammar import json_source_grammar
from mwpc_exact.reference.normalization import normalize_to_cnf
from mwpc_exact.state import SelectionInput
from mwpc_exact.support import SupportPolicy, build_per_position_support
from mwpc_exact.tokenizer_bytes import CompositionalByteLevelAdapter
from mwpc_exact.types import SupportKind

ref = importlib.import_module("attempts.50-grammar-residual-coupling.work.residual")


def tails(atoms, threshold):
    return sum(w for r, w in atoms if r > threshold)


def tail_oracle():
    choices = tuple(itertools.product([F(0), F(1, 2), F(1), F(2)], [1, 2, 8]))
    checks = merges = 0
    for size in range(5):
        for atoms in itertools.product(choices, repeat=size):
            for eta in [F(1), F(1, 2), F(1, 10)]:
                compressed = ref.coarsen(atoms, eta)
                assert sum(w for _, w in atoms) == sum(w for _, w in compressed)
                merges += len(compressed) < len(set(r for r, _ in atoms))
                for threshold in [F(0), F(1, 4), F(1, 2), F(3, 4), F(1), F(3, 2), F(2)]:
                    exact = tails(atoms, threshold)
                    lower = tails(compressed, threshold)
                    assert lower <= exact <= (1 + eta) * lower, (atoms, eta, threshold)
                    checks += 1
    rng = random.Random(20261013050)
    for _ in range(120):
        first = [(F(rng.randrange(12), 7), rng.randrange(1, 10000)) for _ in range(12)]
        second = [(F(rng.randrange(12), 11), rng.randrange(1, 10000)) for _ in range(8)]
        eta = F(1, 3)
        original = [(r * s, w * z) for r, w in first for s, z in second]
        compact = ref.coarsen(
            [
                (r * s, w * z)
                for r, w in ref.coarsen(first, eta)
                for s, z in ref.coarsen(second, eta)
            ],
            eta,
        )
        points = sorted({F(0), *(r for r, _ in original)})
        points += [(a + b) / 2 for a, b in itertools.pairwise(points)]
        for threshold in points:
            assert (
                tails(compact, threshold)
                <= tails(original, threshold)
                <= (1 + eta) ** 3 * tails(compact, threshold)
            )
            checks += 1
    return checks, merges


def source_dyck():
    builder = _SourceGrammarBuilder(("S", "N"), start="S")
    builder.rule("S", "N", "S")
    builder.rule("S")
    builder.rule("N", b"(", "S", b")")
    builder.rule("N", b"[", "S", b"]")
    return builder.build()


def valid(word, kind):
    if kind == "json":
        try:
            json.loads(word)
            return True
        except (ValueError, UnicodeError):
            return False
    stack = []
    for byte in word:
        if byte in b"([":
            stack.append(byte)
        elif not stack or stack.pop() != {41: 40, 93: 91}.get(byte):
            return False
    return not stack


def fixtures():
    yield (
        "dyck",
        "dyck",
        (b"(", b")", b"[", b"]", b"("),
        ((0, 2, 4), (0, 1, 2, 3), (0, 1, 2, 3), (1, 3)),
        None,
    )
    yield "macro", "dyck", (b"()", b"[]", b"(", b")", b"[]"), ((0, 1, 2, 4), (0, 1, 3, 4)), None
    yield (
        "json-prefix-alias",
        "json",
        (b"[", b"0]", b"[0", b"]", b"0]", b"[]"),
        ((0, 2, 5), (1, 3, 4, 5)),
        None,
    )
    yield (
        "json-fixed",
        "json",
        (b"[", b"0", b"1", b"[]", b"null", b"]"),
        ((0,), (1, 2, 3, 4), (5,)),
        (0, None, 5),
    )
    yield (
        "json-string",
        "json",
        (b'"', b"a", b"b", b'\\"', b'"a', b'b"'),
        ((0, 4), (1, 2, 3), (0, 5)),
        None,
    )
    yield "impossible", "dyck", (b"(", b"["), ((0, 1),), None


def inputs(source, emissions, rows, canvas, mode, rng):
    canvas = (None,) * len(rows) if canvas is None else canvas
    support = build_per_position_support(
        canvas=canvas,
        policy=SupportPolicy(kind=SupportKind.EXPLICIT, vocabulary_size=len(emissions)),
        explicit_support=dict(enumerate(rows)),
    )
    state = SelectionInput(
        normalize_to_cnf(source).grammar,
        canvas,
        (),
        support,
        CompositionalByteLevelAdapter(emissions),
        EOSPolicy(EOSMode.ABSENT),
    )
    draft = [tuple(F(1, len(row)) for _ in row) for row in support.rows]
    target = list(draft)
    if mode == "different":
        for i, row in enumerate(target):
            raw = [rng.randrange(1, 10) for _ in row]
            target[i] = tuple(F(v, sum(raw)) for v in raw)
    elif mode == "singular":
        i = next(i for i, row in enumerate(target) if len(row) > 1)
        draft[i] = (F(0), *(F(1, len(draft[i]) - 1) for _ in draft[i][1:]))
        target[i] = tuple(F(1, len(draft[i])) for _ in draft[i])
    elif mode == "tiny":
        i = next(i for i, row in enumerate(target) if len(row) > 1)
        target[i] = tuple(
            p + (F(1, 1 << 4096) if j == 0 else -F(1, 1 << 4096) if j == 1 else F(0))
            for j, p in enumerate(target[i])
        )
    elif mode == "low-mass":
        target = [
            tuple(p / (1 << (64 * (i + 1))) for p in row) if canvas[i] is None else row
            for i, row in enumerate(target)
        ]
    elif mode == "zero-target":
        i = next(i for i, value in enumerate(canvas) if value is None)
        target[i] = tuple(F(0) for _ in target[i])
    return ProbabilityInput(state, tuple(target)), ProbabilityInput(state, tuple(draft))


def run(output, outside=False):
    output.mkdir(parents=True, exist_ok=False)
    try:
        tail_checks, merges = tail_oracle()
        counts = dict(
            tail_checks=tail_checks,
            nontrivial_tail_merges=merges,
            word_points=0,
            prefix_bounds=0,
            proposal_laws=0,
            coupling_laws=0,
            sampled_valid=0,
            undefined=0,
            marginal_bounds=0,
        )
        rng = random.Random(20261013051)
        factory = (
            importlib.import_module(
                "attempts.50-grammar-residual-coupling.work.outside"
            ).OutsideResidual
            if outside
            else ref.Residual
        )
        with (output / "rows.jsonl").open("w") as stream:
            for name, kind, emissions, rows, canvas in fixtures():
                source = source_dyck() if kind == "dyck" else json_source_grammar()
                for mode in ["equal", "different", "singular", "tiny", "low-mass", "zero-target"]:
                    target, draft = inputs(source, emissions, rows, canvas, mode, rng)
                    paths = list(itertools.product(*target.state.support.rows))
                    raw = [
                        {
                            ids: math.prod(
                                data.probabilities[i][data.state.support.rows[i].index(v)]
                                for i, v in enumerate(ids)
                            )
                            if valid(b"".join(emissions[v] for v in ids), kind)
                            else F(0)
                            for ids in paths
                        }
                        for data in [target, draft]
                    ]
                    masses = [sum(row.values(), F(0)) for row in raw]
                    plan = compile_cfg_sampler(source, target.state)
                    if not all(masses):
                        try:
                            factory(plan, target, draft)
                        except ValueError:
                            counts["undefined"] += 1
                            stream.write(
                                json.dumps(dict(case=name, mode=mode, undefined=True)) + "\n"
                            )
                            continue
                        raise AssertionError("zero-mass posterior was admitted")
                    p, q = [
                        {ids: value / z for ids, value in row.items()}
                        for row, z in zip(raw, masses, strict=True)
                    ]
                    residual = {ids: max(F(0), p[ids] - q[ids]) for ids in paths}
                    delta = sum(residual.values(), F(0))
                    solver = factory(plan, target, draft)
                    for ids in paths:
                        assert solver.point(ids, 0) == p[ids] and solver.point(ids, 1) == q[ids]
                        counts["word_points"] += 1
                    xi = F(1, 4 * len(rows))
                    prefixes = sorted({ids[:i] for ids in paths for i in range(len(rows) + 1)})
                    lower_cache = {}
                    marginal_cache = {}
                    for prefix in prefixes:
                        evidence = dict(enumerate(prefix))
                        for multiplier in [F(0), F(1, 2), F(1), F(2)]:
                            truth = sum(
                                (
                                    max(F(0), p[ids] - multiplier * q[ids])
                                    for ids in paths
                                    if ids[: len(prefix)] == prefix
                                ),
                                F(0),
                            )
                            lower, upper = solver.bound(evidence, xi=xi, multiplier=multiplier)
                            assert lower <= truth <= upper <= (1 + xi) * lower
                            assert (lower == 0) == (truth == 0)
                            counts["prefix_bounds"] += 1
                            if multiplier == 1:
                                lower_cache[prefix] = lower
                            if outside:
                                marginals = solver.marginals(evidence, xi=xi, multiplier=multiplier)
                                for i, row in enumerate(rows):
                                    for j, value in enumerate(row):
                                        exact_marginal = sum(
                                            (
                                                max(F(0), p[ids] - multiplier * q[ids])
                                                for ids in paths
                                                if ids[: len(prefix)] == prefix and ids[i] == value
                                            ),
                                            F(0),
                                        )
                                        lo, hi = marginals[i][j]
                                        assert lo <= exact_marginal <= hi <= (1 + xi) * lo
                                        assert (lo == 0) == (exact_marginal == 0)
                                        counts["marginal_bounds"] += 1
                                if multiplier == 1:
                                    marginal_cache[prefix] = marginals
                    if delta:
                        proposals = {}
                        for ids in paths:
                            density = F(1)
                            for i, v in enumerate(ids):
                                prefix = ids[:i]
                                weights = (
                                    [pair[0] for pair in marginal_cache[prefix][i]]
                                    if outside
                                    else [lower_cache[(*prefix, value)] for value in rows[i]]
                                )
                                total = sum(weights, F(0))
                                if not total:
                                    density = F(0)
                                    break
                                density *= weights[rows[i].index(v)] / total
                            proposals[ids] = density
                        assert sum(proposals.values(), F(0)) == 1
                        k = (1 + xi) ** len(rows)
                        upper = solver.bound(xi=xi)[1]
                        accepted = {}
                        for ids in paths:
                            assert (
                                residual[ids] / delta / k
                                <= proposals[ids]
                                <= k * residual[ids] / delta
                            )
                            if proposals[ids]:
                                acceptance = residual[ids] / (k * upper * proposals[ids])
                                assert 0 <= acceptance <= 1
                                accepted[ids] = proposals[ids] * acceptance
                            else:
                                assert not residual[ids]
                                accepted[ids] = F(0)
                        rate = sum(accepted.values(), F(0))
                        assert rate > F(1, 2)
                        assert all(accepted[ids] / rate == residual[ids] / delta for ids in paths)
                        counts["proposal_laws"] += 1
                        joint = {
                            (x, y): (
                                min(p[x], q[x])
                                if x == y
                                else max(F(0), q[x] - p[x]) * accepted[y] / rate
                            )
                            for x in paths
                            for y in paths
                        }
                        assert all(sum(joint[x, y] for y in paths) == q[x] for x in paths)
                        assert all(sum(joint[x, y] for x in paths) == p[y] for y in paths)
                        assert sum(joint[x, x] for x in paths) == 1 - delta
                        counts["coupling_laws"] += 1
                        for _ in range(16):
                            ids, attempts = solver.sample(rng)
                            assert residual[ids] > 0 and attempts >= 1
                            counts["sampled_valid"] += 1
                        assert solver.sample(rng, max_attempts=0) == (None, 0)
                    else:
                        try:
                            solver.sample(rng)
                        except ValueError:
                            pass
                        else:
                            raise AssertionError("zero residual sampled")
                    invalid = next((ids for ids in paths if not q[ids]), None)
                    if invalid is not None:
                        try:
                            solver.correct_draft(invalid, rng)
                        except ValueError:
                            pass
                        else:
                            raise AssertionError("invalid/zero-density draft admitted")
                    stream.write(
                        json.dumps(
                            dict(
                                case=name,
                                mode=mode,
                                delta=str(delta),
                                queries=solver.profile_queries,
                                **counts,
                            )
                        )
                        + "\n"
                    )
        summary = dict(
            status="CORRECTNESS_ONLY",
            **counts,
            producer=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            shared_outside=outside,
        )
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    except Exception:
        (output / "failure.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--outside", action="store_true")
    arguments = parser.parse_args()
    run(arguments.output, arguments.outside)
